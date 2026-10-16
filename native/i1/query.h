/* Original TopoLab I1 software interface; not a scientific launch contract. */
#ifndef TOPOLAB_I1_QUERY_H
#define TOPOLAB_I1_QUERY_H

#define I1_ELEMENTS 1728
#define I1_DOFS 6552
#define I1_FULL_DOFS 6825
#define I1_BAND 299
#define I1_STATES 361
#define I1_PARAMETERS 26433

typedef struct {
    int nx, ny, nz;
    double lx, ly, lz, young, nu, emin, radius, volume, minimum, move;
    int load_x, load_y, load_z, direction;
    double magnitude;
} I1Case;

typedef struct {
    int updates, analyses, converged, phase_count;
    int selected, polish_updates, initial_analyses, polish_rechecks;
    int penalty[I1_STATES];
    double compliance[I1_STATES], volume[I1_STATES];
    double design_change[I1_STATES], physical_change[I1_STATES];
    double design[I1_STATES][I1_ELEMENTS];
    double physical[I1_STATES][I1_ELEMENTS];
} I1History;

/* These entry points are exercised only with new public software fixtures. */
int i1_setup(const I1Case *spec);
int i1_model_role(const I1Case *spec, int method);
int i1_encode(float *output);
int i1_predict(const float *parameters, float *output);
int i1_project(const double *raw, double *design, double *physical);
int i1_filter(const double *design, double *physical);
int i1_analyze(const double *physical, int penalty, double *compliance,
               double *gradient, double *displacement);
int i1_update(const double *design, const double *physical_gradient, double *updated);
int i1_run(const double *raw, int homotopy, int limit);
int i1_physics_raw(double *raw);
int i1_encode_legacy(float *output);
int i1_nn_begin(void);
int i1_nn_offer(const float *input, const float *label, const char *case_id);
int i1_nn_result(double *raw);
int i1_nn_metadata(char *case_id,double *distance);
int i1_polish_keep(int limit);
int i1_evaluate(const double *raw, int method, int limit, double reference,
                 int *succeeded, int *used_fallback);
const I1History *i1_attempt_history(void);
int i1_attempt_status(void);
const I1History *i1_history(void);
const double *i1_last_solution(void);
int i1_recover(const I1Case *,const double *,int,const double *,double *,double *);
unsigned long i1_storage_bytes(void);
int i1_element(double dx, double dy, double dz, double nu, double *matrix);
int i1_model_read(const unsigned char *bytes, unsigned long length, float *parameters);
int i1_case_read(const unsigned char *bytes, unsigned long length, I1Case *spec,
                 int *homotopy, int *limit, int *initialization);

#endif
