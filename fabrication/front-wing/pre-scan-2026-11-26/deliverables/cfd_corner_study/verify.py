import numpy as np,json
from flow import solve,OUT,axis

def check():
    checks={}
    for h in (5.0,2.5):
        radius=40.
        e=[axis(-400,400,-70,70,h,22),axis(0,400,0,70,h,22),axis(0,400,0,70,h,22)]
        a,b,c=np.meshgrid(*[(d[1:]+d[:-1])/2 for d in e],indexing='ij',sparse=True)
        r=np.sqrt(a*a+b*b+c*c);solid=r<radius
        v,_,d=solve(e,solid)
        ok=(r>1.6*radius)&(r<2.8*radius)
        exact=[1.+radius**3/(2*r**3)*(1.-3*a*a/r**2),
               -1.5*radius**3*a*b/r**5,-1.5*radius**3*a*c/r**5]
        errors=np.sqrt(sum((i[ok]-j[ok])**2 for i,j in zip(v,exact)))
        d['rms_vector_error_fraction_U']=float(np.sqrt(np.mean(errors**2)))
        checks[str(h)]=d
    print({k:v["rms_vector_error_fraction_U"] for k,v in checks.items()},flush=True)
    assert checks['2.5']['rms_vector_error_fraction_U']<.015
    assert checks['2.5']['rms_vector_error_fraction_U']<checks['5.0']['rms_vector_error_fraction_U']
    (OUT/'sphere_check.json').write_text(json.dumps(checks,indent=2))
    print(checks)
if __name__=='__main__':check()
