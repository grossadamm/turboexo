/* Perspective depth test for already projected camera-space triangles. */
#include <math.h>
#include <stdint.h>
void draw(int w,int h,int faces,const double *uv,const double *z,const int32_t *indices,
          const uint8_t *colors,unsigned char *rgb,double *depth,int32_t *owner) {
 for(int f=0;f<faces;f++){
   const int32_t *idx=indices+f*3;
   int a=idx[0], b=idx[1], c=idx[2];
   if(z[a]<=.01 || z[b]<=.01 || z[c]<=.01) continue;
   double x=uv[2*a], y=uv[2*a+1], ux=uv[2*b]-x, uy=uv[2*b+1]-y, vx=uv[2*c]-x, vy=uv[2*c+1]-y;
   double det=ux*vy-uy*vx;
   if(fabs(det)<1e-12) continue;
   int xmin=(int)fmax(0,floor(x+fmin(0,fmin(ux,vx)))),xmax=(int)fmin(w-1,ceil(x+fmax(0,fmax(ux,vx))));
   int ymin=(int)fmax(0,floor(y+fmin(0,fmin(uy,vy)))),ymax=(int)fmin(h-1,ceil(y+fmax(0,fmax(uy,vy))));
   for(int j=ymin;j<=ymax;j++)for(int i=xmin;i<=xmax;i++){
     double u=((i+.5-x)*vy-(j+.5-y)*vx)/det, v=(ux*(j+.5-y)-uy*(i+.5-x))/det;
     if(u<0 || v<0 || u+v>1)continue;
     double iz=(1-u-v)/z[a]+u/z[b]+v/z[c];
     int k=j*w+i;
     if(iz>depth[k]){
       depth[k]=iz;owner[k]=f;
       for(int l=0;l<3;l++)rgb[3*k+l]=colors[3*f+l];
     }
   }
 }
}
