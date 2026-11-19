window.renderStreet=function(d){
 const u=window.clusterLayout,mint='#b1ebd4',muted='#b7c4bd',valid=v=>v!=null&&Number.isFinite(Number(v));
 const clamp=v=>Math.max(0,Math.min(1,v));
 const point=(a,inset=0)=>{const r=a*Math.PI/180;return [640+(540-inset)*Math.cos(r),390+(300-inset)*Math.sin(r)]};
 const arc=(a,b)=>{const p=point(a),q=point(b);return `M${p[0]} ${p[1]}A540 300 0 0 1 ${q[0]} ${q[1]}`};
 let s=u.t(45,43,'STREET',27,muted,'start')+u.t(1235,43,'RPM × 1000',29,muted,'end');
 s+=`<path d="${arc(180,360)}" fill="none" stroke="#293c31" stroke-width="12" stroke-linecap="round"/>`;
 const rpm=d.visualRpm??d.rpm;
 if(valid(rpm)&&rpm>0)s+=`<path d="${arc(180,180+180*clamp(rpm/8000))}" fill="none" stroke="${mint}" stroke-width="13" stroke-linecap="round"/>`;
 for(let i=0;i<=16;i++){const angle=180+i*11.25,p=point(angle,20),q=point(angle,i%2===0?38:30);s+=`<path d="M${p[0]} ${p[1]}L${q[0]} ${q[1]}" stroke="${muted}" stroke-width="${i%2===0?3:2}"/>`;if(i%2===0){const n=point(angle,68);s+=u.t(n[0],n[1]+11,i/2,34,muted)}}
 s+=u.t(640,398,u.n(d.speed),258,u.ink,'middle',700)+u.t(640,451,'MPH',36,muted)+u.value(640,525,u.n(d.rpm),'RPM',76);
 const boost=valid(d.map)&&valid(d.baro)?(d.map-d.baro)*.1450377:null;
 const groups=[
 {x:175,label:'OIL PRESSURE',icon:'oil-can',v:d.oil,unit:'psi',min:0,max:100,scale:['0','50','100']},
 {x:485,label:'COOLANT',icon:'thermometer',v:d.coolant,unit:'°F',min:120,max:280,scale:['120','200','280']},
 {x:795,label:'FUEL',icon:'fuel',v:d.fuel,unit:'%',min:0,max:100,scale:['E','½','F']},
 {x:1105,label:'BOOST / VAC',icon:'gauge',v:boost,unit:'psi',min:-15,max:15,scale:['−15','0','+15'],signed:true}
 ];
 for(const g of groups){
 s+=u.label(g.x,610,g.label,g.icon)+u.value(g.x,675,(g.signed&&g.v>0?'+':'')+u.n(g.v,g.signed?1:0),g.unit,60);
 const left=g.x-117,w=234,y=700,h=18;
 s+=`<rect x="${left}" y="${y}" width="${w}" height="${h}" fill="#293c31"/>`;
 if(valid(g.v)){
  const fraction=clamp((g.v-g.min)/(g.max-g.min)),zero=g.signed?clamp((0-g.min)/(g.max-g.min)):0;
  const x=left+w*Math.min(zero,fraction),width=w*Math.abs(fraction-zero);
  s+=`<rect x="${x}" y="${y}" width="${width}" height="${h}" fill="${mint}"/>`;
 }
 for(let i=0;i<=4;i++){
  const x=left+w*i/4,major=i%2===0;
  s+=`<path d="M${x} ${y+h+4}v${major?8:4}" stroke="${muted}" stroke-width="2"/>`;
  if(major)s+=u.t(x,756,g.scale[i/2],28,muted);
 }
 if(g.signed)s+=`<path d="M${g.x} ${y-3}v${h+6}" stroke="#f2f5f2" stroke-width="2"/>`;
 }
 return s;
};
