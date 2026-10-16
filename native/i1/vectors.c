/* Original full-node displacement/reaction recovery for the selected solve.
 * No second solve or reference is performed; this completes its terminal fields. */
#include "query.h"
static int valid_number(double value) {
    union {double d;unsigned long long bits;} b={.d=value};
    return (b.bits>>52&2047)!=2047;
}
int i1_recover(const I1Case *c,const double *rho,int p,const double *free_solution,
               double *full,double *reaction) {
    if(c->nx<1||c->nx>24||c->ny<1||c->ny>12||c->nz<1||c->nz>6||p<1||p>3||
       c->load_x<1||c->load_x>c->nx||c->load_y<0||c->load_y>c->ny||
       c->load_z<0||c->load_z>c->nz||c->direction<0||c->direction>2||
       !valid_number(c->young)||!valid_number(c->emin)||!valid_number(c->magnitude)||
       c->emin<=0||c->young<=c->emin||c->magnitude==0) return 1;
    int count=3*(c->nx+1)*(c->ny+1)*(c->nz+1),ne=c->nx*c->ny*c->nz;
    if(count>I1_FULL_DOFS) return 1;
    double ke[576];
    if(i1_element(c->lx/c->nx,c->ly/c->ny,c->lz/c->nz,c->nu,ke)) return 1;
    for(int i=0;i<count;++i) {full[i]=0;reaction[i]=0;}
    for(int x=1;x<=c->nx;++x) for(int y=0;y<=c->ny;++y) for(int z=0;z<=c->nz;++z)
        for(int d=0;d<3;++d) {
            int source=3*(z+(c->nz+1)*(y+(c->ny+1)*(x-1)))+d;
            int target=3*(x+(c->nx+1)*(y+(c->ny+1)*z))+d;
            if(!valid_number(free_solution[source])) return 1;
            full[target]=free_solution[source];
        }
    const int ox[8]={0,1,1,0,0,1,1,0},oy[8]={0,0,1,1,0,0,1,1};
    for(int e=0;e<ne;++e) {
        if(!valid_number(rho[e])||rho[e]<=0||rho[e]>1) return 1;
        int x=e%c->nx,y=e/c->nx%c->ny,z=e/(c->nx*c->ny),ids[24];
        for(int a=0;a<8;++a) for(int d=0;d<3;++d)
            ids[3*a+d]=3*((x+ox[a])+(c->nx+1)*((y+oy[a])+(c->ny+1)*(z+(a>=4))))+d;
        double power=rho[e];for(int k=1;k<p;++k) power*=rho[e];
        double modulus=c->emin+(c->young-c->emin)*power;
        for(int a=0;a<24;++a) {
            double force=0;
            for(int b=0;b<24;++b) force+=ke[24*a+b]*full[ids[b]];
            reaction[ids[a]]+=modulus*force;
        }
    }
    int load=3*(c->load_x+(c->nx+1)*(c->load_y+(c->ny+1)*c->load_z))+c->direction;
    if(load<0||load>=count) return 1;
    reaction[load]-=c->magnitude;
    for(int i=0;i<count;++i) if(!valid_number(reaction[i])) return 1;
    return 0;
}
