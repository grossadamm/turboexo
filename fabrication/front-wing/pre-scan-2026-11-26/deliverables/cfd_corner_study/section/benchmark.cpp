// Plane laminar modes with invariant horizontal direction, hence periodic in x.
#define main wing_main
#include "solve.cpp"
#undef main
#include <array>
int main() {
    const float nu=.0105880f,tau=.5f+3.f*nu,U=.065f;
    const float sp=1.f/tau,sm=1.f/(.5f + .1875f/(tau-.5f));
    Params p{1.f-.5f*(sp+sm),.5f*(sm-sp),sp,sm,1.f-sp,U,{}};
    bool good=true;
    for(int icase=0;icase<2;icase++){
        const bool couette=icase==0;
        const double z1=couette?0.:1.8,z2=couette?32.:25.7,h=z2-z1,pi=acos(-1.);
        const int nt=couette?12000:6000,N=32;
        auto value=[&](int j,int t){
            const double y=j+.5-z1;
            return couette?U*(1-y/h):.036*sin(pi*y/h)*exp(-nu*(pi/h)*(pi/h)*t);
        };
        auto fluid=[&](int j){return j+.5>z1 && j+.5<z2;};
        using Node=std::array<float,9>;
        std::vector<Node> f(N),g(N);
        for(int j=0;j<N;j++) if(fluid(j)) for(int k=0;k<9;k++){
            float u=value(j,0),eu=ex[k]*u,w=k==0?4.f/9.f:k<5?1.f/9.f:1.f/36.f;
            f[j][k]=w*(1+3*eu+4.5f*eu*eu-1.5f*u*u);
        }
        for(int step=0;step<nt;step++){
            for(int j=0;j<N;j++)if(fluid(j)){
                Node in;
                for(int k=0;k<9;k++){
                    const int src=j-ez[k];
                    if(fluid(src)) in[k]=f[src][k];
                    else if(couette && ez[k]==1){
                        const float rho=(f[j][0]+f[j][1]+f[j][2]+f[j][3]+f[j][4]+f[j][5]+f[j][6]+f[j][7]+f[j][8]);
                        in[k]=moving_ground_pop(f[j][opp[k]],rho,U,ex[k]);
                    }else{
                        const float q=ez[k]>0 ? j+.5-z1 : z2-j-.5;
                        in[k]=reflected(q,f[j][opp[k]],f[j+ez[k]][opp[k]],f[j][k]);
                    }
                }
                auto &r=g[j];
                collide(in[0],in[1],in[2],in[3],in[4],in[5],in[6],in[7],in[8],1.,p,
                        r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8]);
            }
            f.swap(g);
        }
        double s2=0,smag=0,dot=0,fit2=0,max_err=0;
        for(int j=0;j<N;j++)if(fluid(j)){
            const auto &r=f[j];
            double rho=0;
            for(float v:r) rho+=v;
            const double u=((r[1]-r[3])+(r[5]-r[7])+(r[8]-r[6]))/rho;
            const double exact=value(j,nt),e=u-exact;
            s2+=e*e;
            smag+=exact*exact;
            dot+=u*value(j,0);
            fit2+=value(j,0)*value(j,0);
            max_err=std::max(std::abs(e),max_err);
        }
        const double rel_l2=sqrt(s2/smag);
        printf("%s: %d steps, nu=%.8f, relative L2 error=%.6f%%, max normalized absolute error=%.6f%%, fitted decay %.6f vs exact %.6f\n",
            couette?"Moving-wall Couette":"Off-grid no-slip sine decay",nt,nu,100*rel_l2,100*max_err/(couette?U:.036),dot/fit2,value(15,nt)/value(15,0));
        good=good && rel_l2<.025;
    }
    return good?0:2;
}
