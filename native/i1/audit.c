/* Authored by the owner-authorized independent I1 reviewer after seeing the
 * primary draft; not a blinded derivation. No draft/candidate implementation
 * is reused. Hex8 uses analytic tensor-product basis integrals, not quadrature.
 * One in-place band LDL^T and explicit loops have no numerical-library calls. */
#include "audit.h"

#define ELEMENT_CAP 1728
#define FREE_CAP 6552
#define FULL_CAP 6825
#define HALF_BAND 299

static struct {
    double band[FREE_CAP][HALF_BAND + 1];
    double answer[FREE_CAP];
    double element[24 * 24];
    double force[FULL_CAP];
    unsigned long analyses_started;
} check;

_Static_assert(sizeof(AuditCase) == 120, "I1 public case ABI");
_Static_assert(sizeof(check) < 256UL * 1024 * 1024, "I1 checker storage");

static int finite_value(double x) {
    union { double number; unsigned long long word; } value = {.number = x};
    return ((value.word >> 52) & 2047) != 2047;
}
static double magnitude(double x) { return x >= 0 ? x : -x; }

int i1_audit_case_valid(const AuditCase *c) {
    if (!c || c->nx < 1 || c->nx > 24 || c->ny < 1 || c->ny > 12 ||
        c->nz < 1 || c->nz > 6 || c->direction < 0 || c->direction > 2 ||
        c->load_x < 1 || c->load_x > c->nx || c->load_y < 0 ||
        c->load_y > c->ny || c->load_z < 0 || c->load_z > c->nz) return 0;
    double scalars[11] = {c->lx, c->ly, c->lz, c->young, c->nu, c->emin,
        c->radius, c->volume, c->minimum, c->move, c->magnitude};
    for (int j = 0; j != 11; ++j) if (!finite_value(scalars[j])) return 0;
    return c->lx > 0 && c->ly > 0 && c->lz > 0 && c->nu > -1 && c->nu < 0.5 &&
        c->young > c->emin && c->emin > 0 && c->radius > 0 &&
        c->minimum > 0 && c->minimum < c->volume && c->volume <= 1 &&
        c->move > 0 && c->move <= 1 && c->magnitude != 0;
}

/* Bottom/top faces traverse a two-bit Gray cycle: x,y then z, per conventions. */
static int corner_bit(int corner, int axis) {
    return axis == 0 ? ((corner ^ (corner >> 1)) & 1) :
        axis == 1 ? ((corner >> 1) & 1) : ((corner >> 2) & 1);
}
static int index_free(const AuditCase *c, int x, int y, int z, int axis) {
    if (x == 0) return -1;
    return 3 * (((x - 1) * (c->ny + 1) + y) * (c->nz + 1) + z) + axis;
}
static int index_full(const AuditCase *c, int x, int y, int z, int axis) {
    return 3 * ((z * (c->ny + 1) + y) * (c->nx + 1) + x) + axis;
}
static void element_map(const AuditCase *c, int e, int *free_ids, int *full_ids) {
    int base[3] = {e % c->nx, (e / c->nx) % c->ny, e / (c->nx * c->ny)};
    for (int node = 0; node != 8; ++node) {
        int x = base[0] + corner_bit(node, 0);
        int y = base[1] + corner_bit(node, 1);
        int z = base[2] + corner_bit(node, 2);
        for (int axis = 0; axis != 3; ++axis) {
            if (free_ids) free_ids[3 * node + axis] = index_free(c, x, y, z, axis);
            if (full_ids) full_ids[3 * node + axis] = index_full(c, x, y, z, axis);
        }
    }
}

/* For linear endpoint functions phi on [0,h]:
 * integral(phi_a phi_b)=h*(2 if a=b else 1)/6,
 * integral(phi'_a phi'_b)=sign_a sign_b/h,
 * integral(phi'_a phi_b)=sign_a/2. Products integrate exactly in 3D.
 * Elasticity: K_(a,i),(b,j)=lambda I_ij+mu I_ji+delta_ij mu sum_d I_dd. */
static int form_element(const AuditCase *c) {
    double side[3] = {c->lx / c->nx, c->ly / c->ny, c->lz / c->nz};
    double shear = 1.0 / (2.0 * (1.0 + c->nu));
    double lame = c->nu / ((1.0 + c->nu) * (1.0 - 2.0 * c->nu));
    for (int a = 0; a != 8; ++a) for (int b = 0; b != 8; ++b) {
        double integral[3][3];
        for (int r = 0; r != 3; ++r) for (int s = 0; s != 3; ++s) {
            double product = 1;
            for (int axis = 0; axis != 3; ++axis) {
                int bit_a = corner_bit(a, axis), bit_b = corner_bit(b, axis);
                double sign_a = bit_a ? 1 : -1, sign_b = bit_b ? 1 : -1;
                if (r == axis && s == axis) product *= sign_a * sign_b / side[axis];
                else if (r == axis) product *= sign_a * 0.5;
                else if (s == axis) product *= sign_b * 0.5;
                else product *= side[axis] * (bit_a == bit_b ? 2.0 : 1.0) / 6.0;
            }
            integral[r][s] = product;
        }
        for (int i = 0; i != 3; ++i) for (int j = 0; j != 3; ++j) {
            double entry = lame * integral[i][j] + shear * integral[j][i];
            if (i == j) for (int d = 0; d != 3; ++d) entry += shear * integral[d][d];
            if (!finite_value(entry)) return 1;
            check.element[24 * (3 * a + i) + 3 * b + j] = entry;
        }
    }
    return 0;
}

static double modulus(const AuditCase *c, double density, int penalty) {
    double value = c->young - c->emin;
    for (int k = 0; k != penalty; ++k) value *= density;
    return c->emin + value;
}

int i1_audit_analysis(const AuditCase *c, const double *density, int penalty,
                      double *compliance, double *gradient, double *result) {
    ++check.analyses_started; /* Attempt is charged before validation/assembly. */
    if (!i1_audit_case_valid(c) || penalty < 1 || penalty > 3 || form_element(c)) return 1;
    int n = 3 * c->nx * (c->ny + 1) * (c->nz + 1);
    int ne = c->nx * c->ny * c->nz;
    int width = 3 * ((c->ny + 1) * (c->nz + 1) + c->nz + 2) + 2;
    if (n > FREE_CAP || ne > ELEMENT_CAP || width > HALF_BAND) return 1;
    for (int row = 0; row != n; ++row)
        for (int distance = 0; distance <= width; ++distance) check.band[row][distance] = 0;
    for (int e = 0; e != ne; ++e) {
        if (!finite_value(density[e]) || density[e] <= 0 || density[e] > 1) return 1;
        double young = modulus(c, density[e], penalty);
        int local[24]; element_map(c, e, local, 0);
        for (int a = 0; a != 24; ++a) for (int b = 0; b != 24; ++b) {
            int row = local[a], col = local[b];
            if (col < 0 || row < col) continue;
            if (row - col > width) return 1;
            check.band[row][row - col] += young * check.element[24 * a + b];
        }
    }
    double scale = 0;
    for (int row = 0; row != n; ++row) {
        double diagonal = magnitude(check.band[row][0]);
        if (!finite_value(diagonal)) return 2;
        if (diagonal > scale) scale = diagonal;
    }
    if (!(scale > 0)) return 2;
    /* Unit lower triangle in nonzero slots, D on slot0. No fill outside the band. */
    for (int row = 0; row != n; ++row) {
        int start = row > width ? row - width : 0;
        for (int col = start; col < row; ++col) {
            double numerator = check.band[row][row - col];
            for (int k = start; k < col; ++k)
                numerator -= check.band[row][row - k] * check.band[k][0] * check.band[col][col - k];
            double coefficient = numerator / check.band[col][0];
            if (!finite_value(coefficient)) return 2;
            check.band[row][row - col] = coefficient;
        }
        double pivot = check.band[row][0];
        for (int col = start; col < row; ++col) {
            double coefficient = check.band[row][row - col];
            pivot -= coefficient * coefficient * check.band[col][0];
        }
        if (!finite_value(pivot) || pivot <= n * 2.220446049250313e-16 * scale) return 2;
        check.band[row][0] = pivot;
    }
    int loaded = index_free(c, c->load_x, c->load_y, c->load_z, c->direction);
    for (int row = 0; row != n; ++row) {
        double value = row == loaded ? c->magnitude : 0;
        int start = row > width ? row - width : 0;
        for (int col = start; col < row; ++col) value -= check.band[row][row - col] * check.answer[col];
        check.answer[row] = value;
    }
    for (int row = 0; row != n; ++row) check.answer[row] /= check.band[row][0];
    for (int row = n; row-- != 0;) {
        for (int col = row + 1; col < n && col <= row + width; ++col)
            check.answer[row] -= check.band[col][col - row] * check.answer[col];
        if (!finite_value(check.answer[row])) return 2;
        if (result) result[row] = check.answer[row];
    }
    double external_work = c->magnitude * check.answer[loaded], internal_work = 0;
    if (!finite_value(external_work) || external_work <= 0) return 2;
    for (int e = 0; e != ne; ++e) {
        int local[24]; element_map(c, e, local, 0);
        double energy = 0;
        for (int a = 0; a != 24; ++a) if (local[a] >= 0)
            for (int b = 0; b != 24; ++b) if (local[b] >= 0)
                energy += check.answer[local[a]] * check.element[24 * a + b] * check.answer[local[b]];
        internal_work += modulus(c, density[e], penalty) * energy;
        if (gradient) {
            double slope = penalty * (c->young - c->emin);
            for (int k = 1; k < penalty; ++k) slope *= density[e];
            gradient[e] = -slope * energy;
            if (!finite_value(gradient[e])) return 2;
        }
    }
    if (!finite_value(internal_work) || magnitude(internal_work - external_work) > 1e-9 * magnitude(external_work)) return 3;
    *compliance = external_work;
    return 0;
}

int i1_audit_density(const AuditCase *c, const double *design, const double *physical,
                     double claim, double *actual) {
    if (!i1_audit_case_valid(c) || !finite_value(claim) || claim <= 0) return 1;
    int ne = c->nx * c->ny * c->nz;
    double low = 1, high = 0, volume = 0;
    for (int e = 0; e != ne; ++e) {
        if (!finite_value(design[e]) || !finite_value(physical[e]) || design[e] < c->minimum ||
            design[e] > 1 || physical[e] < c->minimum || physical[e] > 1) return 1;
        if (design[e] < low) low = design[e];
        if (design[e] > high) high = design[e];
        volume += physical[e] / ne;
    }
    if (magnitude(volume - c->volume) > 0.005) return 2;
    for (int row = 0; row != ne; ++row) {
        double weighted = 0, weights = 0;
        for (int col = 0; col != ne; ++col) {
            double dx = (row % c->nx - col % c->nx) * c->lx / c->nx;
            double dy = ((row / c->nx) % c->ny - (col / c->nx) % c->ny) * c->ly / c->ny;
            double dz = (row / (c->nx * c->ny) - col / (c->nx * c->ny)) * c->lz / c->nz;
            double weight = c->radius - __builtin_sqrt(dx * dx + dy * dy + dz * dz);
            if (weight > 0) { weights += weight; weighted += weight * design[col]; }
        }
        if (!finite_value(weights) || !finite_value(weighted) || weights <= 0) return 3;
        double expected = weighted / weights;
        if (!finite_value(expected)) return 3;
        if (expected < low) expected = low;
        if (expected > high) expected = high;
        if (magnitude(expected - physical[row]) > 1e-12) return 3;
    }
    if (i1_audit_analysis(c, physical, 3, actual, 0, 0)) return 4;
    return magnitude(*actual - claim) <= 1e-9 * magnitude(*actual) ? 0 : 5;
}

int i1_audit_full(const AuditCase *c, const double *density, const double *full, const double *reaction) {
    double compliance;
    if (i1_audit_analysis(c, density, 3, &compliance, 0, 0)) return 1;
    int count = 3 * (c->nx + 1) * (c->ny + 1) * (c->nz + 1);
    for (int i = 0; i != count; ++i) {
        if (!finite_value(full[i]) || !finite_value(reaction[i])) return 1;
        check.force[i] = 0;
    }
    for (int x = 0; x <= c->nx; ++x) for (int y = 0; y <= c->ny; ++y)
        for (int z = 0; z <= c->nz; ++z) for (int axis = 0; axis != 3; ++axis) {
            int f = index_full(c, x, y, z, axis), reduced = index_free(c, x, y, z, axis);
            double expected = reduced < 0 ? 0 : check.answer[reduced];
            if (magnitude(full[f] - expected) > 1e-9 * magnitude(expected) + 1e-10) return 2;
        }
    for (int e = 0; e != c->nx * c->ny * c->nz; ++e) {
        int local[24], global[24]; element_map(c, e, local, global);
        double young = modulus(c, density[e], 3);
        for (int a = 0; a != 24; ++a) for (int b = 0; b != 24; ++b)
            if (local[b] >= 0) check.force[global[a]] += young * check.element[24 * a + b] * check.answer[local[b]];
    }
    check.force[index_full(c, c->load_x, c->load_y, c->load_z, c->direction)] -= c->magnitude;
    double total[3] = {0, 0, 0};
    for (int i = 0; i != count; ++i) {
        if (!finite_value(check.force[i]) || magnitude(reaction[i] - check.force[i]) >
            1e-9 * magnitude(check.force[i]) + 1e-10 * magnitude(c->magnitude)) return 3;
        if (((i / 3) % (c->nx + 1)) != 0 && magnitude(reaction[i]) > 1e-10 * magnitude(c->magnitude)) return 4;
        total[i % 3] += reaction[i];
    }
    total[c->direction] += c->magnitude;
    for (int d = 0; d != 3; ++d) if (magnitude(total[d]) > 1e-10 * magnitude(c->magnitude)) return 4;
    return 0;
}
unsigned long i1_audit_storage_bytes(void) { return sizeof(check); }
void i1_audit_reset_count(void) { check.analyses_started = 0; }
unsigned long i1_audit_analysis_count(void) { return check.analyses_started; }
