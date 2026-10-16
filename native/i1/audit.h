/* I1 independent-reviewer numerical API. ABI declarations only. */
#ifndef TOPOLAB_I1_AUDIT_H
#define TOPOLAB_I1_AUDIT_H

typedef struct {
    int nx, ny, nz;
    double lx, ly, lz, young, nu, emin, radius, volume, minimum, move;
    int load_x, load_y, load_z, direction;
    double magnitude;
} AuditCase;

int i1_audit_case_valid(const AuditCase *);
int i1_audit_analysis(const AuditCase *, const double *, int, double *, double *, double *);
int i1_audit_density(const AuditCase *, const double *, const double *, double, double *);
int i1_audit_full(const AuditCase *, const double *, const double *, const double *);
unsigned long i1_audit_storage_bytes(void);
void i1_audit_reset_count(void);
unsigned long i1_audit_analysis_count(void);
#endif
