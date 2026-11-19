window.renderTuning=function(d,history){
  const fg='#f2f5f2',mu='#9caaa3',cyan='#80d5ec';
  const t=(x,y,v,s=28,c=fg,w=600,a='start')=>`<text x="${x}" y="${y}" fill="${c}" font-family="Arial,Helvetica,sans-serif" font-size="${s}" font-weight="${w}" text-anchor="${a}">${v}</text>`;
  const valid=v=>v!=null&&Number.isFinite(Number(v));
  const f=(v,n=0)=>valid(v)?Number(v).toFixed(n):'—';
  let s=t(55,50,'TUNING / TRACE',27,cyan);

  // The four primary readings have their own space; the target belongs to O₂.
  s+=t(55,112,'ENGINE',26,mu)+t(55,207,f(d.rpm),96)+t(55,247,'RPM',26,mu);
  s+=t(355,112,'LOAD',26,mu)+t(355,207,f(d.map),96)+t(355,247,'kPa ABS',26,mu);
  s+=t(630,112,'O₂ / RAW AFR',26,mu)+t(630,207,f(d.afr,1),96)+t(630,247,'LOGGED TARGET  '+f(d.target,1),26,mu);
  s+=t(1040,112,'THROTTLE',26,mu)+t(1040,207,f(d.tps),96)+t(1040,247,'TPS %',26,mu);

  // Every lane uses the same time axis and only samples already recorded.
  const lanes=[['rpm','RPM',8000,365,cyan],['map','MAP · kPa',180,475,'#b1ebd4'],['tps','TPS · %',100,585,'#ffc16b']];
  for(const [key,label,max,base,color] of lanes){
    s+=t(55,base-20,label,26,color);
    const points=(valid(d.time)?history:[]).filter(p=>valid(p.time)&&valid(p[key])&&p.time>=d.time-8&&p.time<=d.time)
      .map(p=>`${(250+(p.time-(d.time-8))/8*970).toFixed(1)},${(base-Math.max(0,Math.min(max,Number(p[key])))/max*70).toFixed(1)}`);
    if(points.length>1)s+=`<polyline points="${points.join(' ')}" fill="none" stroke="${color}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>`;
    if(points.length){const [x,y]=points[points.length-1].split(',');s+=`<circle cx="${x}" cy="${y}" r="5" fill="${color}"/>`;}
  }
  s+=t(250,631,'−8 s',26,mu)+t(1220,631,'NOW',26,mu,500,'end');
  const metrics=[['ADVANCE',f(d.advance,1)+'°'],['PW',f(d.pw,2)+' ms'],['DUTY',f(d.duty,1)+'%'],['CLT / IAT',f(d.coolant)+' / '+f(d.iat)+' °F'],['BATTERY',f(d.battery,1)+' V']];
  const xs=[55,280,505,730,1030];
  metrics.forEach((m,i)=>{s+=t(xs[i],700,m[0],26,mu)+t(xs[i],755,m[1],38);});
  return s;
};
