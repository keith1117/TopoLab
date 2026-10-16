/* Independent implementation of standard Hex8/SIMP/OC equations in PROVENANCE.
 * Fixed storage, no library numerical dispatch, recursion or allocation. */
#include "query.h"

static struct {
    I1Case c;
    int ne, nf, band;
    double ke[576];
    double filter[I1_ELEMENTS][I1_ELEMENTS], rows[I1_ELEMENTS];
    double matrix[I1_DOFS][I1_BAND + 1], factor[I1_DOFS][I1_BAND + 1];
    double solution[I1_DOFS], rhs[I1_DOFS], grad[I1_ELEMENTS];
    double x[I1_ELEMENTS], rho[I1_ELEMENTS], next[I1_ELEMENTS];
    double scratch[I1_ELEMENTS], dv[I1_ELEMENTS], dc[I1_ELEMENTS];
    float input[13 * I1_ELEMENTS], first[16 * I1_ELEMENTS], second[16 * I1_ELEMENTS];
    I1History history,attempt;
    float nn_input[10 * I1_ELEMENTS],nn_label[I1_ELEMENTS];
    char nn_last[75];
    char nn_selected[75];
    int nn_count,preparation_analyses,attempt_status;
    double nn_distance;
} work;

_Static_assert(sizeof(work) <= 256UL * 1024 * 1024, "producer arena overflow");
_Static_assert(sizeof(I1Case)==120&&sizeof(I1History)==9993960,"public history/case layout");

static double absolute(double x) { return x < 0 ? -x : x; }
static double maximum(double a, double b) { return a > b ? a : b; }
static double minimum(double a, double b) { return a < b ? a : b; }
static double clip(double x, double lo, double hi) { return minimum(maximum(x, lo), hi); }
static int finite(double x) {
    union { double d; unsigned long long u; } v = { .d = x };
    return (v.u & 0x7ff0000000000000ULL) != 0x7ff0000000000000ULL;
}
static double root(double x) { return __builtin_sqrt(x); }
static double power(double x, int p) { return p == 1 ? x : p == 2 ? x*x : x*x*x; }

/* Range reduction and finite Taylor series; no libm/IFUNC/allocator dependency.
 * The public parity tests, not this formula, determine numerical compatibility. */
static double exponential(double x) {
    int k = (int)(x / 0.69314718055994530942);
    double r = x - k * 0.69314718055994530942, sum = 1, term = 1;
    for (int j = 1; j <= 24; ++j) { term *= r / j; sum += term; }
    union { double d; unsigned long long u; } scale;
    scale.u = (unsigned long long)(k + 1023) << 52;
    return sum * scale.d;
}

unsigned long i1_storage_bytes(void) { return sizeof(work); }
const I1History *i1_history(void) { return &work.history; }
const double *i1_last_solution(void) {return work.solution;}
const I1History *i1_attempt_history(void) { return &work.attempt; }
int i1_attempt_status(void) {return work.attempt_status;}

int i1_element(double dx, double dy, double dz, double nu, double *matrix) {
    if (!finite(dx) || !finite(dy) || !finite(dz) || !finite(nu) ||
        dx <= 0 || dy <= 0 || dz <= 0 || nu <= -1 || nu >= 0.5) return 1;
    const int sx[8] = {-1,1,1,-1,-1,1,1,-1};
    const int sy[8] = {-1,-1,1,1,-1,-1,1,1};
    const int sz[8] = {-1,-1,-1,-1,1,1,1,1};
    double d[6][6] = {{0}};
    double mu = 1 / (2 * (1 + nu));
    double lam = nu / ((1 + nu) * (1 - 2 * nu));
    for (int i=0;i<3;++i) for(int j=0;j<3;++j) d[i][j] = lam + (i==j ? 2*mu : 0);
    for (int i=3;i<6;++i) d[i][i] = mu;
    for (int i=0;i<576;++i) matrix[i]=0;
    const double g = 0.57735026918962576451;
    for (int ix=-1;ix<=1;ix+=2) for(int iy=-1;iy<=1;iy+=2) for(int iz=-1;iz<=1;iz+=2) {
        double b[6][24]={{0}};
        double x=ix*g, y=iy*g, z=iz*g;
        for(int a=0;a<8;++a) {
            double gx=sx[a]*(1+sy[a]*y)*(1+sz[a]*z)/(4*dx);
            double gy=sy[a]*(1+sx[a]*x)*(1+sz[a]*z)/(4*dy);
            double gz=sz[a]*(1+sx[a]*x)*(1+sy[a]*y)/(4*dz);
            b[0][3*a]=gx; b[1][3*a+1]=gy; b[2][3*a+2]=gz;
            b[3][3*a]=gy; b[3][3*a+1]=gx;
            b[4][3*a+1]=gz; b[4][3*a+2]=gy;
            b[5][3*a]=gz; b[5][3*a+2]=gx;
        }
        double det=dx*dy*dz/8;
        for(int a=0;a<24;++a) for(int bidx=0;bidx<24;++bidx)
            for(int i=0;i<6;++i) for(int j=0;j<6;++j)
                matrix[24*a+bidx] += b[i][a]*d[i][j]*b[j][bidx]*det;
    }
    for(int i=0;i<576;++i) if(!finite(matrix[i])) return 1;
    return 0;
}

static int free_dof(int x,int y,int z,int d) {
    if(x==0) return -1;
    return 3*(z+(work.c.nz+1)*(y+(work.c.ny+1)*(x-1)))+d;
}

static void element_dofs(int e,int *dofs) {
    int x=e%work.c.nx, y=e/work.c.nx%work.c.ny, z=e/(work.c.nx*work.c.ny);
    const int ox[8]={0,1,1,0,0,1,1,0}, oy[8]={0,0,1,1,0,0,1,1};
    for(int a=0;a<8;++a) for(int d=0;d<3;++d)
        dofs[3*a+d]=free_dof(x+ox[a],y+oy[a],z+(a>=4),d);
}

int i1_setup(const I1Case *c) {
    if(!c || c->nx<1 || c->nx>24 || c->ny<1 || c->ny>12 || c->nz<1 || c->nz>6)
        return 1;
    int ne=c->nx*c->ny*c->nz;
    int nf=3*c->nx*(c->ny+1)*(c->nz+1);
    int band=3*((c->ny+1)*(c->nz+1)+(c->nz+1)+1)+2;
    if(ne>I1_ELEMENTS || nf>I1_DOFS || band>I1_BAND) return 1;
    if(!finite(c->lx)||!finite(c->ly)||!finite(c->lz)||!finite(c->young)||!finite(c->nu)||
       !finite(c->emin)||!finite(c->radius)||!finite(c->volume)||!finite(c->minimum)||
       !finite(c->move)||!finite(c->magnitude)||c->lx<=0||c->ly<=0||c->lz<=0||
       c->young<=0||c->emin<=0||c->emin>=c->young||c->radius<=0||
       c->minimum<=0||c->minimum>=c->volume||c->volume>1||c->move<=0||c->move>1||
       c->magnitude==0||c->direction<0||c->direction>2||c->load_x<1||c->load_x>c->nx||
       c->load_y<0||c->load_y>c->ny||c->load_z<0||c->load_z>c->nz) return 1;
    if(i1_element(c->lx/c->nx,c->ly/c->ny,c->lz/c->nz,c->nu,work.ke)) return 1;
    work.c=*c; work.ne=ne; work.nf=nf; work.band=band;
    for(int i=0;i<nf;++i) work.rhs[i]=0;
    work.rhs[free_dof(c->load_x,c->load_y,c->load_z,c->direction)]=c->magnitude;
    for(int i=0;i<ne;++i) {
        double row=0;
        int x=i%c->nx, y=i/c->nx%c->ny, z=i/(c->nx*c->ny);
        for(int j=0;j<ne;++j) {
            double dx=(x-j%c->nx)*c->lx/c->nx;
            double dy=(y-j/c->nx%c->ny)*c->ly/c->ny;
            double dz=(z-j/(c->nx*c->ny))*c->lz/c->nz;
            double w=maximum(0,c->radius-root(dx*dx+dy*dy+dz*dz));
            if(!finite(w)) return 1;
            work.filter[i][j]=w; row+=w;
        }
        if(!finite(row)||row<=0) return 1;
        work.rows[i]=row;
    }
    for(int j=0;j<ne;++j) {
        work.dv[j]=0;
        for(int i=0;i<ne;++i) work.dv[j]+=work.filter[i][j]/work.rows[i]/ne;
    }
    work.history.updates=0;work.history.analyses=0;work.history.converged=0;
    work.history.selected=0;work.history.initial_analyses=0;work.history.polish_rechecks=0;
    work.history.polish_updates=0;work.history.phase_count=0;work.preparation_analyses=0;
    return 0;
}

int i1_model_role(const I1Case *c,int method) {
    if(method<0||method>2||c->direction<1||c->direction>2||
       !((c->nx==12&&c->ny==6&&c->nz==3)||(c->nx==24&&c->ny==12&&c->nz==6))) return -1;
    return c->nx==24&&c->direction==1&&c->volume>=0.55 ? 3 : method;
}

int i1_encode(float *out) {
    int n=work.ne;
    for(int z=0;z<work.c.nz;++z) for(int y=0;y<work.c.ny;++y) for(int x=0;x<work.c.nx;++x) {
        int e=x+work.c.nx*(y+work.c.ny*z);
        for(int d=0;d<3;++d) out[d*n+e]=x==0;
        for(int d=0;d<3;++d) out[(3+d)*n+e]=d==work.c.direction ? (work.c.magnitude>0 ? 1 : -1) : 0;
        out[6*n+e]=((float)x+0.5f)/work.c.nx;
        out[7*n+e]=((float)y+0.5f)/work.c.ny;
        out[8*n+e]=((float)z+0.5f)/work.c.nz;
        out[9*n+e]=(float)work.c.volume;
        out[10*n+e]=out[6*n+e]-(float)((double)work.c.load_x/work.c.nx);
        out[11*n+e]=out[7*n+e]-(float)((double)work.c.load_y/work.c.ny);
        out[12*n+e]=out[8*n+e]-(float)((double)work.c.load_z/work.c.nz);
    }
    return 0;
}

int i1_encode_legacy(float *out) {
    i1_encode(work.input);
    int n=work.ne;
    for(int i=0;i<10*n;++i) out[i]=work.input[i];
    int neighbors=(work.c.load_x<work.c.nx ? 2 : 1)*
        (work.c.load_y>0&&work.c.load_y<work.c.ny ? 2 : 1)*
        (work.c.load_z>0&&work.c.load_z<work.c.nz ? 2 : 1);
    for(int z=0;z<work.c.nz;++z) for(int y=0;y<work.c.ny;++y) for(int x=0;x<work.c.nx;++x) {
        int incident=x<=work.c.load_x&&work.c.load_x<=x+1&&
            y<=work.c.load_y&&work.c.load_y<=y+1&&z<=work.c.load_z&&work.c.load_z<=z+1;
        int e=x+work.c.nx*(y+work.c.ny*z);
        for(int d=0;d<3;++d) out[(3+d)*n+e]=incident&&d==work.c.direction ?
            (float)((work.c.magnitude>0 ? 1.0 : -1.0)/neighbors) : 0;
    }
    return 0;
}

int i1_nn_begin(void) {
    i1_encode_legacy(work.nn_input);
    work.nn_count=0;work.nn_distance=1e300;
    for(int i=0;i<75;++i) work.nn_last[i]=0;
    return 0;
}
int i1_nn_offer(const float *input,const float *label,const char *case_id) {
    if(work.nn_count>=528) return 1;
    const char *prefix="tlcase-v1-";
    for(int i=0;i<10;++i) if(case_id[i]!=prefix[i]) return 1;
    for(int i=10;i<74;++i) if(!((case_id[i]>='0'&&case_id[i]<='9')||
                               (case_id[i]>='a'&&case_id[i]<='f'))) return 1;
    if(case_id[74]) return 1;
    if(work.nn_count) {
        int order=0;
        for(int i=0;i<74;++i) if(case_id[i]!=work.nn_last[i]) {
            order=case_id[i]>work.nn_last[i] ? 1 : -1;break;
        }
        if(order!=1) return 1;
    }
    double distance=0;
    for(int i=0;i<10*work.ne;++i) {
        if(!finite(input[i])) return 1;
        double delta=(double)input[i]-work.nn_input[i];distance+=delta*delta;
    }
    for(int i=0;i<work.ne;++i) if(!finite(label[i])||label[i]<0||label[i]>1) return 1;
    distance/=10*work.ne;
    if(!finite(distance)) return 1;
    if(distance<work.nn_distance) {
        work.nn_distance=distance;
        for(int i=0;i<work.ne;++i) work.nn_label[i]=label[i];
        for(int i=0;i<75;++i) work.nn_selected[i]=case_id[i];
    }
    for(int i=0;i<75;++i) work.nn_last[i]=case_id[i];
    ++work.nn_count;
    return 0;
}
int i1_nn_result(double *raw) {
    if(!work.nn_count) return 1;
    for(int i=0;i<work.ne;++i) raw[i]=work.nn_label[i];
    return 0;
}
int i1_nn_metadata(char *case_id,double *distance) {
    if(!work.nn_count) return 1;
    for(int i=0;i<75;++i) case_id[i]=work.nn_selected[i];
    *distance=work.nn_distance;return 0;
}

int i1_predict(const float *weights,float *out) {
    int n=work.ne, offset=0;
    i1_encode(work.input);
    for(int l=0;l<5;++l) {
        int in=l==0 ? 13 : 16, channels=l==4 ? 1 : 16, kernel=l==4 ? 1 : 3;
        int dy=l>=2 ? 2 : 1, dx=l==0 ? 1 : l==1 ? 2 : l==2 ? 4 : l==3 ? 8 : 1;
        const float *src=l==0 ? work.input : l%2 ? work.first : work.second;
        float *dst=l==4 ? out : l%2 ? work.second : work.first;
        const float *bias=weights+offset+channels*in*kernel*kernel*kernel;
        for(int oc=0;oc<channels;++oc) for(int z=0;z<work.c.nz;++z)
            for(int y=0;y<work.c.ny;++y) for(int x=0;x<work.c.nx;++x) {
                float sum=bias[oc];
                for(int ic=0;ic<in;++ic) for(int kz=0;kz<kernel;++kz)
                    for(int ky=0;ky<kernel;++ky) for(int kx=0;kx<kernel;++kx) {
                        int xx=x+(kx-kernel/2)*dx, yy=y+(ky-kernel/2)*dy, zz=z+kz-kernel/2;
                        if(xx<0||xx>=work.c.nx||yy<0||yy>=work.c.ny||zz<0||zz>=work.c.nz) continue;
                        int w=offset+(((oc*in+ic)*kernel+kz)*kernel+ky)*kernel+kx;
                        sum+=weights[w]*src[ic*n+xx+work.c.nx*(yy+work.c.ny*zz)];
                    }
                if(!finite(sum)) return 1;
                dst[oc*n+x+work.c.nx*(y+work.c.ny*z)]=l==4 ?
                    (sum>=104 ? 1 : sum<=-104 ? 0 : (float)(1/(1+exponential(-(double)sum))))
                    : maximum(0,sum);
            }
        offset+=channels*in*kernel*kernel*kernel+channels;
    }
    return offset!=I1_PARAMETERS;
}

static void filtered(const double *x,double *rho) {
    double lo=x[0], hi=x[0];
    for(int i=1;i<work.ne;++i) {lo=minimum(lo,x[i]); hi=maximum(hi,x[i]);}
    for(int i=0;i<work.ne;++i) {
        double sum=0;
        for(int j=0;j<work.ne;++j) sum+=work.filter[i][j]*x[j];
        rho[i]=clip(sum/work.rows[i],lo,hi);
    }
}

int i1_filter(const double *x,double *rho) {
    for(int i=0;i<work.ne;++i) if(!finite(x[i])||x[i]<0||x[i]>1) return 1;
    filtered(x,rho);
    return 0;
}

int i1_project(const double *raw,double *x,double *rho) {
    for(int i=0;i<work.ne;++i) if(!finite(raw[i])||raw[i]<0||raw[i]>1) return 1;
    double lo=-1,hi=1;
    for(int endpoint=0;endpoint<2;++endpoint) {
        double volume=0,offset=endpoint ? 1 : -1;
        for(int i=0;i<work.ne;++i) x[i]=clip(raw[i]+offset,work.c.minimum,1);
        filtered(x,rho);
        for(int i=0;i<work.ne;++i) volume+=rho[i]/work.ne;
        if(absolute(volume-work.c.volume)<=1e-6) return 0;
        if((!endpoint&&volume>work.c.volume)||(endpoint&&volume<work.c.volume)) return 1;
    }
    for(int it=0;it<100;++it) {
        double mid=(lo+hi)*0.5, mean=0;
        for(int i=0;i<work.ne;++i) x[i]=clip(raw[i]+mid,work.c.minimum,1);
        filtered(x,rho);
        for(int i=0;i<work.ne;++i) mean+=rho[i]/work.ne;
        if(absolute(mean-work.c.volume)<=1e-6) return 0;
        if(mean<work.c.volume) lo=mid; else hi=mid;
    }
    return 1;
}

int i1_analyze(const double *rho,int penalty,double *compliance,double *gradient,double *u) {
    if(penalty<1||penalty>3) return 1;
    for(int i=0;i<work.nf;++i) for(int k=0;k<=work.band;++k) work.matrix[i][k]=0;
    for(int e=0;e<work.ne;++e) {
        if(!finite(rho[e])||rho[e]<=0||rho[e]>1) return 1;
        int dofs[24]; element_dofs(e,dofs);
        double factor=work.c.emin+(work.c.young-work.c.emin)*power(rho[e],penalty);
        for(int a=0;a<24;++a) if(dofs[a]>=0) for(int b=0;b<24;++b)
            if(dofs[b]>=0 && dofs[a]>=dofs[b]) {
                int k=dofs[a]-dofs[b];
                if(k>work.band) return 1;
                work.matrix[dofs[a]][k]+=factor*work.ke[24*a+b];
            }
    }
    double scale=0;
    for(int i=0;i<work.nf;++i) {
        scale=maximum(scale,absolute(work.matrix[i][0]));
        for(int k=0;k<=work.band;++k) work.factor[i][k]=work.matrix[i][k];
    }
    if(!finite(scale)||scale<=0) return 1;
    for(int i=0;i<work.nf;++i) {
        int begin=i-work.band; if(begin<0) begin=0;
        for(int j=begin;j<=i;++j) {
            double value=work.factor[i][i-j];
            int k0=i-work.band; if(k0<j-work.band) k0=j-work.band; if(k0<0) k0=0;
            for(int k=k0;k<j;++k) value-=work.factor[i][i-k]*work.factor[j][j-k];
            if(j==i) {
                if(!finite(value)||value<=work.nf*2.220446049250313e-16*scale) return 2;
                work.factor[i][0]=root(value);
            } else work.factor[i][i-j]=value/work.factor[j][0];
        }
    }
    for(int i=0;i<work.nf;++i) {
        double value=work.rhs[i];
        for(int k=1;k<=work.band&&k<=i;++k) value-=work.factor[i][k]*work.solution[i-k];
        work.solution[i]=value/work.factor[i][0];
    }
    for(int i=work.nf-1;i>=0;--i) {
        double value=work.solution[i];
        for(int k=1;k<=work.band&&i+k<work.nf;++k) value-=work.factor[i+k][k]*work.solution[i+k];
        work.solution[i]=value/work.factor[i][0];
        if(!finite(work.solution[i])) return 2;
    }
    double cc=0;
    for(int i=0;i<work.nf;++i) {cc+=work.rhs[i]*work.solution[i]; if(u) u[i]=work.solution[i];}
    if(!finite(cc)||cc<=0) return 2;
    for(int e=0;e<work.ne;++e) {
        int dofs[24]; element_dofs(e,dofs);
        double energy=0;
        for(int a=0;a<24;++a) if(dofs[a]>=0) for(int b=0;b<24;++b)
            if(dofs[b]>=0) energy+=work.solution[dofs[a]]*work.ke[24*a+b]*work.solution[dofs[b]];
        double derivative=penalty*(penalty==1 ? 1 : power(rho[e],penalty-1));
        if(!finite(energy)||!finite(derivative)) return 2;
        if(gradient) gradient[e]=-derivative*(work.c.young-work.c.emin)*energy;
        if(gradient&&!finite(gradient[e])) return 2;
    }
    *compliance=cc;
    return 0;
}

static double oc_candidate(const double *x,double lagrange,double *next) {
    for(int i=0;i<work.ne;++i)
        next[i]=clip(x[i]*root(maximum(0,-work.dc[i]/(work.dv[i]*lagrange))),
                     maximum(work.c.minimum,x[i]-work.c.move),minimum(1,x[i]+work.c.move));
    filtered(next,work.scratch);
    double volume=0;
    for(int i=0;i<work.ne;++i) volume+=work.scratch[i]/work.ne;
    return volume;
}

int i1_update(const double *x,const double *gradient,double *next) {
    int negative=0;
    for(int j=0;j<work.ne;++j) {
        work.dc[j]=0;
        for(int i=0;i<work.ne;++i) work.dc[j]+=work.filter[i][j]*gradient[i]/work.rows[i];
        if(!finite(x[j])||x[j]<work.c.minimum||x[j]>1||!finite(work.dc[j])||
           work.dc[j]>0||work.dv[j]<=0) return 1;
        if(work.dc[j]<0) negative=1;
    }
    if(!negative) return 1;
    for(int i=0;i<work.ne;++i) next[i]=maximum(work.c.minimum,x[i]-work.c.move);
    filtered(next,work.scratch);
    double bound=0;
    for(int i=0;i<work.ne;++i) bound+=work.scratch[i]/work.ne;
    if(work.c.volume<=bound+1e-8) return 0;
    for(int i=0;i<work.ne;++i) next[i]=minimum(1,x[i]+work.c.move);
    filtered(next,work.scratch); bound=0;
    for(int i=0;i<work.ne;++i) bound+=work.scratch[i]/work.ne;
    if(work.c.volume>=bound-1e-8) return 0;
    double lo=0,hi=1;
    int bracket=0;
    for(int it=0;it<1024;++it) {
        if(oc_candidate(x,hi,next)<=work.c.volume) {bracket=1;break;}
        hi*=2;
        if(!finite(hi)) return 1;
    }
    if(!bracket) return 1;
    for(int it=0;it<100;++it) {
        double mid=0.5*(lo+hi),mean=oc_candidate(x,mid,next);
        if(absolute(mean-work.c.volume)<=1e-8) return 0;
        if(mean>work.c.volume) lo=mid; else hi=mid;
    }
    return 0;
}

int i1_run(const double *raw,int homotopy,int limit) {
    if(limit<1||limit>360||(homotopy!=0&&homotopy!=1)) return 1;
    I1History *h=&work.history;
    h->updates=0; h->analyses=work.preparation_analyses;h->initial_analyses=work.preparation_analyses;
    h->converged=0; h->phase_count=0;h->polish_updates=0;h->selected=0;
    h->polish_rechecks=0;
    h->design_change[0]=0;h->physical_change[0]=0;
    if(i1_project(raw,work.x,work.rho)) return 1;
    int active=homotopy && work.c.nx==24&&work.c.ny==12&&work.c.nz==6&&
        work.c.direction==1&&work.c.volume<0.55;
    int penalty=active ? 1 : 3, phase_states=0;
    for(int it=0;it<=limit;++it) {
        int p=active ? (it<=8 ? 1 : it<=16 ? 2 : 3) : 3;
        if(it>0 && (it==9||it==17) && active) {
            penalty=p; phase_states=0;
            double transition;
            ++h->analyses;
            if(i1_analyze(work.rho,penalty,&transition,work.grad,0)) return 2;
        }
        if(it>0) {
            if(i1_update(work.x,work.grad,work.next)) return 3;
            filtered(work.next,work.scratch);
            double change=0,physical=0;
            for(int i=0;i<work.ne;++i) {
                change=maximum(change,absolute(work.next[i]-work.x[i]));
                physical=maximum(physical,absolute(work.scratch[i]-work.rho[i]));
                work.x[i]=work.next[i]; work.rho[i]=work.scratch[i];
            }
            h->design_change[it]=change; h->physical_change[it]=physical;
        }
        h->penalty[it]=p;
        ++h->analyses;
        if(i1_analyze(work.rho,p,&h->compliance[it],work.grad,0)) return 2;
        h->volume[it]=0;
        for(int i=0;i<work.ne;++i) {
            h->design[it][i]=work.x[i]; h->physical[it][i]=work.rho[i];
            h->volume[it]+=work.rho[i]/work.ne;
        }
        if(it==0) continue;
        h->updates=it; ++phase_states;
        if(p==3) {
            int plateau=phase_states>=11;
            if(plateau) {
                for(int j=it-9;j<=it;++j) if(h->physical_change[j]>0.01) plateau=0;
                double relative=(h->compliance[it-10]-h->compliance[it])/h->compliance[it-10];
                if(relative<0||relative>0.0002) plateau=0;
            }
            if(h->design_change[it]<=0.01||plateau) {h->converged=1;break;}
        }
    }
    h->phase_count=phase_states;
    h->selected=h->updates;
    double final;
    ++h->analyses;
    if(i1_analyze(work.rho,h->penalty[h->updates],&final,0,0)) return 2;
    if(final!=h->compliance[h->updates]) return 2;
    return 0;
}

int i1_physics_raw(double *raw) {
    for(int i=0;i<work.ne;++i) work.rho[i]=work.c.volume;
    double compliance;
    ++work.preparation_analyses;
    work.history.analyses=work.preparation_analyses;
    work.history.initial_analyses=work.preparation_analyses;
    if(i1_analyze(work.rho,3,&compliance,work.grad,0)) return 1;
    double lo=-work.grad[0],hi=lo;
    for(int i=0;i<work.ne;++i) {
        double score=maximum(0,-work.grad[i]);
        lo=minimum(lo,score);hi=maximum(hi,score);
    }
    for(int i=0;i<work.ne;++i) raw[i]=(float)(hi>lo ? (maximum(0,-work.grad[i])-lo)/(hi-lo) : work.c.volume);
    return 0;
}

static int plateau_at(const I1History *h,int end) {
    if(end<11) return 0;
    for(int j=end-10;j<=end;++j) if(h->penalty[j]!=3) return 0;
    for(int j=end-9;j<=end;++j) if(h->physical_change[j]>0.01) return 0;
    double relative=(h->compliance[end-10]-h->compliance[end])/h->compliance[end-10];
    return relative>=0&&relative<=0.0002;
}
int i1_polish_keep(int limit) {
    I1History *h=&work.history;
    if(limit<1||limit>360||h->updates<1||limit<h->updates) return 1;
    int before=h->updates;
    if(work.c.nx!=24||work.c.ny!=12||work.c.nz!=6||work.c.direction!=1||
       work.c.volume>=0.55||!h->converged||h->design_change[before]<=0.01||!plateau_at(h,before)) return 0;
    double cc;
    ++h->analyses;
    if(i1_analyze(work.rho,3,&cc,work.grad,0)||cc!=h->compliance[before]) return 2;
    int end=before+20;if(end>limit) end=limit;
    for(int it=before+1;it<=end;++it) {
        if(i1_update(work.x,work.grad,work.next)) return 3;
        filtered(work.next,work.scratch);
        h->design_change[it]=0;h->physical_change[it]=0;h->volume[it]=0;h->penalty[it]=3;
        for(int i=0;i<work.ne;++i) {
            h->design_change[it]=maximum(h->design_change[it],absolute(work.next[i]-work.x[i]));
            h->physical_change[it]=maximum(h->physical_change[it],absolute(work.scratch[i]-work.rho[i]));
            work.x[i]=work.next[i];work.rho[i]=work.scratch[i];
            h->design[it][i]=work.x[i];h->physical[it][i]=work.rho[i];h->volume[it]+=work.rho[i]/work.ne;
        }
        ++h->analyses;
        if(i1_analyze(work.rho,3,&h->compliance[it],work.grad,0)) return 2;
    }
    h->updates=end;h->polish_updates=end-before;h->phase_count=end;
    h->converged=h->polish_updates==20&&(h->design_change[end]<=0.01||plateau_at(h,end));
    h->selected=h->polish_updates==20&&!h->converged ? before : end;
    if(h->selected==before) h->converged=1;
    ++h->analyses;
    if(i1_analyze(h->physical[h->selected],3,&cc,0,0)||cc!=h->compliance[h->selected]) return 2;
    h->polish_rechecks=2;
    return 0;
}

int i1_evaluate(const double *raw,int method,int limit,double reference,int *succeeded,int *used_fallback) {
    if(!finite(reference)||reference<=0||method<0||method>2) return 1;
    /* method0 plain,1 H,2 legacy P-keep; no favorable reference-based witness selection. */
    *used_fallback=0;*succeeded=0;
    int code=i1_run(raw,method==1,limit);
    if(!code&&method==2) code=i1_polish_keep(limit);
    work.attempt=work.history;
    work.attempt_status=code;
    int at=work.attempt.selected;
    int accepted=!code&&work.attempt.converged&&work.attempt.penalty[at]==3&&
        absolute(work.attempt.volume[at]-work.c.volume)<=0.005&&
        work.attempt.compliance[at]<=1.001*reference;
    if(accepted) {*succeeded=1;return 0;}
    if(!code) work.attempt_status=4; /* failed terminal/quality, retained even if fallback succeeds */
    *used_fallback=1;
    for(int i=0;i<work.ne;++i) work.next[i]=work.c.volume;
    work.preparation_analyses=0;
    code=i1_run(work.next,0,limit);
    if(code) return code;
    at=work.history.selected;
    *succeeded=work.history.converged&&absolute(work.history.volume[at]-work.c.volume)<=0.005&&
        work.history.compliance[at]<=1.001*reference;
    return 0;
}
