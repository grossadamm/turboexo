#!/usr/bin/env python3
"""Conditional analytical model of the wake input. Not a Pi J2 threshold model.

Models the optocoupler input as constant total LED drop + module R1.
All output currents are LED currents, not collector or J2 currents.
The installed LED drops, capacitor tolerance/leakage and J2 load are unmeasured.
"""
import itertools, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def model(v=12.6,vf=3.2,ri=1000.,rs=470.,cap=220e-6,shunt=None):
    if shunt is None:
        rt=ri;vt=vf
    else:
        rt=ri*shunt/(ri+shunt);vt=vf*shunt/(ri+shunt)
    tau=(rs+rt)*cap
    itotal=max(0.,(v-vt)/(rs+rt))
    def current(t):
        # valid during LED conduction; clamp after turnoff
        return max(0.,(vt+rt*itotal*math.exp(-t/tau)-vf)/ri)
    def above(a):
        threshold=(vf+ri*a-vt)/rt
        if threshold<=0:return None
        return max(0.,tau*math.log(itotal/threshold)) if itotal>threshold else 0.
    return dict(initial_LED_mA=current(0)*1000,LED_at_200ms_mA=current(.2)*1000,
        current_decay_tau_s=tau,time_above_1mA_s=above(.001),
        time_above_5mA_s=above(.005),ideal_constant_drop_LED_cutoff_s=above(0))

def ramp_peak(v=12.6,vf=3.2,ri=1000.,rs=470.,cap=220e-6,shunt=None,rise=1.):
    # Resistor/LED threshold circuit with capacitor state q (voltage).
    # RK4 integration handles initial charging through a shunt before LEDs turn on.
    dt=min(.00005,rise/2000);steps=math.ceil(rise/dt);dt=rise/steps
    def branch(t,q):
        source=min(v,v*t/rise);diff=source-q
        off=diff if shunt is None else diff*shunt/(rs+shunt)
        if off<=vf:
            i=0. if shunt is None else diff/(rs+shunt)
            return i/cap,0.
        rt=ri if shunt is None else ri*shunt/(ri+shunt)
        vt=vf if shunt is None else vf*shunt/(ri+shunt)
        i=(diff-vt)/(rs+rt);node=vt+rt*i
        return i/cap,max(0.,(node-vf)/ri)
    q=0.;peak=0.
    for k in range(steps):
        t=k*dt
        a,led=branch(t,q);peak=max(peak,led)
        b,_=branch(t+dt/2,q+a*dt/2);c,_=branch(t+dt/2,q+b*dt/2);d,_=branch(t+dt,q+c*dt)
        q+=dt*(a+2*b+2*c+d)/6
    peak=max(peak,branch(rise,q)[1]);return peak*1000

def main():
    nominal=model();shunted=model(shunt=4700.)
    assert abs(nominal['initial_LED_mA']-6.3945578)<1e-6
    assert 2.57<shunted['LED_at_200ms_mA']<2.60
    # This is a deliberately chosen scenario envelope, not measured or guaranteed parts.
    corners=[]
    for v,vf,ri,rs,cap,rsh in itertools.product((12.,13.2),(2.7,3.7),(950.,1050.),(446.5,493.5),(176e-6,264e-6),(4465.,4935.)):
        corners.append(model(v,vf,ri,rs,cap,rsh))
    bounds={key:[min(c[key] for c in corners),max(c[key] for c in corners)] for key in shunted}
    ramps=[dict(rise_s=t,original_peak_LED_mA=ramp_peak(rise=t),shunted_peak_LED_mA=ramp_peak(rise=t,shunt=4700.)) for t in (.05,.2,.5,1.,3.)]
    # Check unshunted ramp numerical integration against independent closed form.
    for r in ramps:
        t=r['rise_s'];slope=12.6/t;expected=220e-6*slope*(1-math.exp(-(t-3.2/slope)/((1000+470)*220e-6)))*1000
        assert abs(r['original_peak_LED_mA']-expected)<.002,(r,expected)
    result=dict(status='DESIGN CALCULATIONS ONLY; no measured current or Pi wake validation',
       sources=dict(opto='https://global.sharp/products/device/lineup/data/pdf/datasheet/PC817XxNSZ1B_e.pdf',
         capacitor_example='https://www.nichicon.co.jp/products/pdfs/upw.pdf',
         empirical_200ms='https://forums.raspberrypi.com/viewtopic.php?p=2326617'),
       assumptions=dict(source_nominal_V=12.6,LED_drop_nominal_V=3.2,module_R1_ohm=1000,external_series_ohm=470,
         capacitor_uF=220,source_bleed_ohm=10000,input_shunt_proposed_ohm=4700,
         module_R1_evidence='matching seller photo, not installed measurement',
         scenario_ranges='Vs12.0..13.2V, Vf2.7..3.7V, R1/R8/R9+/-5%, C+/-20%; assumed design scenarios, not warranted installed limits'),
       current_circuit=nominal,with_proposed_input_shunt=shunted,shunted_scenario_bounds=bounds,source_ramps=ramps,
       leakage_example=dict(description='Nichicon UPW limit at rated voltage20C after1min; example cap, not installed cap',
          rule='max(0.03*C_uF*V_rated,4) microamps',example_220uF_25V_uA=165,
          input_voltage_with_4k7_nominal_V=165e-6*4700,input_voltage_with_4k7_plus5percent_V=165e-6*4935),
       known_resistor_checks=dict(source_bleed_mA=12.6/10000*1000,source_bleed_mW=12.6**2/10000*1000,
          series_reset_peak_mA_upper_no_diode_drop=12.6/470*1000,series_reset_peak_W_upper=12.6**2/470,
          shunt_peak_W= ((3.2+1000*shunted['initial_LED_mA']/1000)**2)/4700),
       reset=dict(stiff_zero_source_tau_s=470*220e-6,floating_source_with_bleed_approx_tau_s=(10000+470)*220e-6,
          note='Approximate diode-conducting reset; upstream capacitance, backfeed and source impedance alter timing'),
       interpretation=['4.7k shunt diverts capacitor DC leakage around series LEDs; upstream10k does not.',
          'Shunt improves release but reduces LED drive. It does not create a fixed200ms output pulse.',
          'Times above1mA/5mA are comparison markers, not J2 thresholds. CTR specified atVCE5V is not a saturation guarantee.',
          'No sourcedJ2 lowthreshold/pullup current/minwake duration available. Empirical200ms is a design reference only.',
          'A charger edge still presses button whilePi runs. No powerpolicy or board change applied by this calculation.'])
    out=ROOT/'docs/hardware/sensor-board-components/wake-analysis/calculations_2026-10-31.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
