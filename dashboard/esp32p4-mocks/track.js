window.renderTrack=function(d){
 const u=window.clusterLayout,amber='#ffc16b',rpm=Math.max(0,Math.min(8000,d.visualRpm??d.rpm??0));
 const top=x=>167-.10*(x-60)+.000035*(x-60)*(x-60);
 const ribbon=end=>{if(end<=60)return '';let a=[],b=[];for(let i=0;i<=60;i++){const x=60+(end-60)*i/60,h=18+(x-60)/1160*50;a.push(`${x},${top(x)}`);b.unshift(`${x},${top(x)+h}`)}return `M${a.join('L')}L${b.join('L')}Z`};
 let s=u.t(55,43,'TRACK',27,u.muted,'start')+u.t(1225,43,'RPM × 1000',27,u.muted,'end');
 for(let i=0;i<=8;i++){const x=60+i*145;s+=u.t(x,top(x)-19,i,29,u.muted)}
 s+=`<path d="${ribbon(1220)}" fill="${u.base}"/><path d="${ribbon(60+1160*rpm/8000)}" fill="${amber}"/>`;
 s+=u.t(55,439,u.n(d.rpm),214,u.ink,'start',700)+u.t(65,491,'RPM',32,amber,'start');
 s+=u.t(1220,433,u.n(d.speed),140,u.ink,'end',700)+u.t(1220,491,'MPH',32,u.muted,'end');
 const boost=d.map==null||d.baro==null?null:(d.map-d.baro)*.1450377;
 const groups=[{x:190,label:'OIL PRESSURE',icon:'oil-can',v:d.oil,unit:'psi',lo:0,hi:100}, {x:490,label:'OIL TEMP',icon:'thermometer',v:d.oiltemp,unit:'°F',lo:140,hi:300}, {x:790,label:'COOLANT',icon:'thermometer',v:d.coolant,unit:'°F',lo:120,hi:240}, {x:1090,label:'BOOST / VAC',icon:'gauge',v:boost,unit:'psi',lo:-15,hi:15,kind:'boost'}];
 // Compact orange bars; boost fills outward from its zero point.
 const gauge=g=>{
  const width=225,left=g.x-width/2,y=700,h=18;
  let bar=`<rect x="${left}" y="${y}" width="${width}" height="${h}" fill="#383126"/>`;
  if(g.v!=null&&Number.isFinite(Number(g.v))){
   const t=Math.max(0,Math.min(1,(Number(g.v)-g.lo)/(g.hi-g.lo))),zero=g.kind==='boost'?(0-g.lo)/(g.hi-g.lo):0;
   bar+=`<rect x="${left+width*Math.min(t,zero)}" y="${y}" width="${width*Math.abs(t-zero)}" height="${h}" fill="${amber}"/>`;
  }
  for(let i=0;i<=4;i++){
   const x=left+width*i/4,major=i%2===0,value=g.lo+(g.hi-g.lo)*i/4;
   bar+=`<path d="M${x} ${y+h+4}v${major?8:4}" stroke="${u.muted}" stroke-width="2"/>`;
   if(major)bar+=u.t(x,756,(g.kind==='boost'&&value>0?'+':'')+String(value).replace('-','−'),28,u.muted);
  }
  if(g.kind==='boost')bar+=`<path d="M${g.x} ${y-3}v${h+6}" stroke="#f2f5f2" stroke-width="2"/>`;
  return bar;
 };
 for(const g of groups){s+=u.label(g.x,610,g.label,g.icon)+u.value(g.x,675,(g.kind==='boost'&&g.v>0?'+':'')+u.n(g.v,g.kind==='boost'?1:0),g.unit,70)+gauge(g);}
 return s;
};
