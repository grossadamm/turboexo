// Explicit D2Q9 two-relaxation-time solver with linear curved-wall bounce-back.
// Compile with clang++ -O3 -ffast-math -fno-finite-math-only -Xpreprocessor -fopenmp
// and link -lomp, or omit OpenMP flags for serial.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

struct Link { int p,k; float q; };
const int ex[]={0,1,0,-1,0,1,-1,-1,1}, ez[]={0,0,1,0,-1,1,1,-1,-1}, opp[]={0,3,4,1,2,7,8,5,6};
const float L=211.761f;
struct Params {
    float a,b,sp,sm,rest, U, eq[9];
};
static inline __attribute__((always_inline)) void pair_collision(float v, float w, float common,float xu,float ir,float weight,
                                  const Params& pa,float& h,float& q) {
    const float even = pa.sp*weight*(common + 4.5f*xu*xu*ir);
    const float odd = pa.sm*3.f*weight*xu;
    h=pa.a*v+pa.b*w+even+odd;
    q=pa.a*w+pa.b*v+even-odd;
}
static inline __attribute__((always_inline)) void collide(float g0,float g1,float g2,float g3,float g4,
                           float g5,float g6,float g7,float g8,float s,
                           const Params& p,float& h0,float& h1,float& h2,float& h3,
                           float& h4,float& h5,float& h6,float& h7,float& h8) {
    const float rho = (g0+g1+g2)+(g3+g4+g5)+(g6+g7+g8);
    const float mx = (g1-g3)+(g5-g7)+(g8-g6);
    const float mz = (g2-g4)+(g5-g7)+(g6-g8);
    const float ir = 1.f/rho;
    const float common = rho - 1.5f*(mx*mx + mz*mz)*ir;
    h0=p.eq[0]+s*(p.rest*g0 + p.sp*(4.f/9.f)*common-p.eq[0]);
    pair_collision(g1,g3,common,mx,ir,1.f/9.f,p,h1,h3);
    pair_collision(g2,g4,common,mz,ir,1.f/9.f,p,h2,h4);
    pair_collision(g5,g7,common,mx+mz,ir,1.f/36.f,p,h5,h7);
    pair_collision(g6,g8,common,mz-mx,ir,1.f/36.f,p,h6,h8);
    h1=p.eq[1]+s*(h1-p.eq[1]); h3=p.eq[3]+s*(h3-p.eq[3]);
    h2=p.eq[2]+s*(h2-p.eq[2]); h4=p.eq[4]+s*(h4-p.eq[4]);
    h5=p.eq[5]+s*(h5-p.eq[5]); h7=p.eq[7]+s*(h7-p.eq[7]);
    h6=p.eq[6]+s*(h6-p.eq[6]); h8=p.eq[8]+s*(h8-p.eq[8]);
}
static inline void collide_border(const float *g, float s, const Params& p, float** n,int i) {
    collide(g[0],g[1],g[2],g[3],g[4],g[5],g[6],g[7],g[8],s,p,n[0][i],n[1][i],n[2][i],n[3][i],n[4][i],n[5][i],n[6][i],n[7][i],n[8][i]);
}
static inline void row(const float* __restrict f0,const float* __restrict f1,const float* __restrict f2,
                       const float* __restrict f3,const float* __restrict f4,const float* __restrict f5,
                       const float* __restrict f6,const float* __restrict f7,const float* __restrict f8,
                       float* __restrict n0,float* __restrict n1,float* __restrict n2,
                       float* __restrict n3,float* __restrict n4,float* __restrict n5,
                       float* __restrict n6,float* __restrict n7,float* __restrict n8,
                       const float* __restrict sponge, const int nx, const Params& p) {
    #pragma clang loop vectorize(enable)
    for(int i=1;i<nx-1;i++) {
        collide(f0[i],f1[i-1],f2[i-nx],f3[i+1],f4[i+nx],f5[i-nx-1],f6[i-nx+1],f7[i+nx+1],f8[i+nx-1],
                sponge[i],p,n0[i],n1[i],n2[i],n3[i],n4[i],n5[i],n6[i],n7[i],n8[i]);
    }
}
static inline float reflected(float q,float outgoing,float inner_outgoing,float incoming) {
    return q<.5f ? 2.f*q*outgoing + (1.f-2.f*q)*inner_outgoing
                  : (outgoing + (2.f*q-1.f)*incoming)/(2.f*q);
}
static inline float moving_ground_pop(float outgoing,float rho,float U,int sign) {
    return outgoing+sign*rho*U/6.f;
}
static inline void pull(float** f, int i, int W, float* g) {
    for(int k=0;k<9;k++) g[k]=f[k][i-ez[k]*W-ex[k]];
}
static void measure(float** f,int nx,int nz,const std::vector<uint8_t>& osm,char* stem,int step,double tt,float U){
    const int N=nx*nz;
    std::vector<float> v(3*N);
    const float nan=std::numeric_limits<float>::quiet_NaN();
    double meanrho=0, minrho=1e3, maxrho=-1e3, umax=0, fluxin=0, fluxout=0, fluxnorm=0;
    int fluid=0, bad=0;
    for(int i=0;i<N;i++){
        if(osm[i]) {v[i]=v[N+i]=v[2*N+i]=nan;continue;}
        float g[9];
        for(int k=0;k<9;k++) g[k]=f[k][i];
        double rho=0;
        for(int k=0;k<9;k++) rho+=g[k];
        double u=((g[1]-g[3])+(g[5]-g[7])+(g[8]-g[6]))/rho;
        double w=((g[2]-g[4])+(g[5]-g[7])+(g[6]-g[8]))/rho;
        if(!std::isfinite(rho)||!std::isfinite(u)||!std::isfinite(w)) bad++;
        v[i]=u/U; v[N+i]=w/U; v[2*N+i]=rho;
        meanrho+=rho; fluid++;
        minrho=std::min(minrho,rho); maxrho=std::max(maxrho,rho);
        umax=std::max(umax,std::sqrt(u*u+w*w));
        if (i%nx==0) fluxin+=rho*u;
        if (i%nx==nx-1) fluxout+=rho*u;
        if (i%nx==1) fluxnorm+=U;
    }
    printf("step=%d t*=%.5f mean_rho=%.7f min=%.7f max=%.7f maxMach=%.5f mass_flux_imbalance_pct=%.5f bad=%d\n",
          step,tt,meanrho/fluid,minrho,maxrho,umax*std::sqrt(3.),(fluxin-fluxout)*100./fluxnorm,bad);
    fflush(stdout);
    if (bad || minrho<.5 || maxrho>1.5) exit(2);
    char path[4096];
    snprintf(path,sizeof(path),"%s_%05d.flow",stem,step);
    FILE *of=fopen(path,"wb");
    if(!of) {perror(path);exit(2);}
    fwrite(v.data(),sizeof(float),3*N,of); fclose(of);
}
int main(int argc,char **argv) {
    if(argc!=8 && argc!=9) {fprintf(stderr,"Usage: solve grid output_stem Re end_tstar U nthreads snapshot_tstar [first_saved_tstar]\n"); return 1;}
    FILE*in=fopen(argv[1],"rb"); if(!in){perror(argv[1]);return 1;}
    int nx,nz,nlinks;
    double dx,xmin,zmin;
    if(fread(&nx,4,1,in)!=1 || fread(&nz,4,1,in)!=1 || fread(&dx,8,1,in)!=1 ||
       fread(&xmin,8,1,in)!=1 || fread(&zmin,8,1,in)!=1 || fread(&nlinks,4,1,in)!=1) return 2;
    const int N=nx*nz;
    std::vector<uint8_t> solid(N);
    std::vector<Link> links(nlinks);
    if(fread(solid.data(),1,N,in)!=size_t(N) || fread(links.data(),sizeof(Link),nlinks,in)!=size_t(nlinks)) return 3;
    fclose(in);
    const double re=atof(argv[3]), ttend=atof(argv[4]), dtout=atof(argv[7]);
    const float U=atof(argv[5]);
    const double first=argc==9?atof(argv[8]):0.;
    const int nthreads=atoi(argv[6]),steps=round(ttend*L/(U*dx)), interval=round(dtout*L/(U*dx));
    const float tau=.5f+3.f*U*L/(dx*re);
    const float sm=1.f/(.5f+.1875f/(tau-.5f));
    const float sp=1.f/tau;
    Params p{1.f-.5f*(sp+sm),.5f*(sm-sp),sp,sm,1.f-sp,U,{}};
    for(int k=0;k<9;k++){
        float w=k==0?4.f/9.f:k<5?1.f/9.f:1.f/36.f;
        float eu=ex[k]*U;
        p.eq[k]=w*(1.f+3.f*eu+4.5f*eu*eu-1.5f*U*U);
    }
    std::vector<float> va(9*N),vb(9*N),sponge(N,1.f);
    float* A[9],*B[9];
    for(int k=0;k<9;k++){
        A[k]=va.data()+k*N; B[k]=vb.data()+k*N;
        std::fill(A[k],A[k]+N,p.eq[k]);
    }
    for(int j=0;j<nz;j++)for(int i=0;i<nx;i++){
        float rx=std::clamp((i*dx + xmin - 580.)/190.,0.,1.);
        float rz=std::clamp((j*dx + zmin - 390.)/80.,0.,1.);
        sponge[j*nx+i]=1.f-.038f*std::max(rx*rx,rz*rz);
    }
    printf("grid=%s nx=%d nz=%d dx=%.3f Re_c=%.2f U_lat=%.5f Ma_inf=%.5f tau_plus=%.7f tau_minus=%.7f steps=%d links=%d\n",argv[1],nx,nz,dx,re,U,U*std::sqrt(3.),tau,1./sm,steps,nlinks); fflush(stdout);
    auto t0=std::chrono::steady_clock::now();
    #pragma omp parallel num_threads(nthreads)
    {
        for(int t=1;t<=steps;t++) {
            float** f=t%2?A:B, ** next=t%2?B:A;
            #pragma omp for schedule(static)
            for(int j=1;j<nz-1;j++) {
                const int a=j*nx;
                row(a+f[0],a+f[1],a+f[2],a+f[3],a+f[4],a+f[5],a+f[6],a+f[7],a+f[8],
                    a+next[0],a+next[1],a+next[2],a+next[3],a+next[4],a+next[5],a+next[6],a+next[7],a+next[8],
                    a+sponge.data(),nx,p);
            }
            #pragma omp single
            {
                float g[9];
                for(int j=1;j<nz-1;j++){
                    int i=j*nx; // Zou-He velocity inlet
                    g[0]=f[0][i];g[2]=f[2][i-nx];g[4]=f[4][i+nx];g[3]=f[3][i+1];g[6]=f[6][i-nx+1];g[7]=f[7][i+nx+1];
                    const float rho=(g[0]+g[2]+g[4]+2.f*(g[3]+g[6]+g[7]))/(1.f-U);
                    g[1]=g[3]+(2.f/3.f)*rho*U; g[5]=g[7]+.5f*(g[4]-g[2])+rho*U/6.f; g[8]=g[6]+.5f*(g[2]-g[4])+rho*U/6.f;
                    collide_border(g,sponge[i],p,next,i);
                    i+=nx-1; // Zou-He density outlet
                    g[0]=f[0][i];g[2]=f[2][i-nx];g[4]=f[4][i+nx];g[1]=f[1][i-1];g[5]=f[5][i-nx-1];g[8]=f[8][i+nx-1];
                    const float ux=-1.f+g[0]+g[2]+g[4]+2.f*(g[1]+g[5]+g[8]);
                    g[3]=g[1]-(2.f/3.f)*ux; g[6]=g[8]+.5f*(g[4]-g[2])-ux/6.f; g[7]=g[5]+.5f*(g[2]-g[4])-ux/6.f;
                    collide_border(g,sponge[i],p,next,i);
                }
                for(int i=1;i<nx-1;i++){
                    g[0]=f[0][i];g[1]=f[1][i-1];g[3]=f[3][i+1];g[4]=f[4][i+nx];g[7]=f[7][i+nx+1];g[8]=f[8][i+nx-1];
                    float rho=0.f;for(int k=0;k<9;k++)rho+=f[k][i];
                    g[2]=f[4][i];g[5]=moving_ground_pop(f[7][i],rho,U,1);g[6]=moving_ground_pop(f[8][i],rho,U,-1);
                    collide_border(g,sponge[i],p,next,i);
                    const int b=(nz-1)*nx+i;
                    g[0]=f[0][b];g[1]=f[1][b-1];g[3]=f[3][b+1];g[2]=f[2][b-nx];g[5]=f[5][b-nx-1];g[6]=f[6][b-nx+1];
                    g[4]=f[2][b];g[7]=f[6][b+1];g[8]=f[5][b-1];
                    collide_border(g,sponge[b],p,next,b);
                }
                for(int i:{0,nx-1,N-nx,N-1})for(int k=0;k<9;k++)next[k][i]=p.eq[k];
                for(int w=0;w<nlinks;){
                    const int i=links[w].p;
                    pull(f,i,nx,g);
                    do {
                        const int k=links[w].k,o=opp[k];
                        const float q=links[w].q;
                        g[k]=reflected(q,f[o][i],f[o][i+ex[k]+ez[k]*nx],f[k][i]);
                        w++;
                    } while(w<nlinks && links[w].p==i);
                    collide_border(g,sponge[i],p,next,i);
                }
                // Reset inactive solid sites so wall stencil never reads a divergent interior proxy.
                for(int w=0;w<nlinks;w++){
                    const int k=links[w].k;
                    const int i=links[w].p-ex[k]-ez[k]*nx;
                    if(solid[i]) for(int l=0;l<9;l++) next[l][i]=p.eq[l];
                }
                if(t==steps || (t%interval==0 && (t+.5)*U*dx/L >= first)) {
                    measure(next,nx,nz,solid,argv[2],t,t*U*dx/L,U);
                    printf("elapsed_s=%.2f\n",std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count());fflush(stdout);
                }
            }
        }
    }
    return 0;
}
