window.clusterLayout={
 ink:'#f2f5f2',muted:'#a9b5af',base:'#2a3830',
 n(v,p=0){return v==null||!Number.isFinite(Number(v))?'—':Number(v).toFixed(p)},
 t(x,y,v,size=30,color='#f2f5f2',anchor='middle',weight=600){return `<text x="${x}" y="${y}" fill="${color}" font-family="Arial,Helvetica,sans-serif" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}">${v}</text>`},
 label(x,y,label,icon){const width=label.length*17,total=width+(icon?42:0),left=x-total/2;return (icon?window.clusterUI.icon(icon,left,y-27,32,'#a9b5af'):'')+this.t(left+(icon?42:0),y,label,28,'#a9b5af','start')},
 value(x,y,value,unit,size=70){return this.t(x,y,`${value}<tspan font-size="29" font-weight="500" fill="#a9b5af"> ${unit}</tspan>`,size)},
 gauge(x,y,width,value,min,max,color,kind='plain'){
 const valid=value!=null&&Number.isFinite(Number(value)),u=valid?Math.max(0,Math.min(1,(value-min)/(max-min))):0;
 const left=x-width/2,rise=80,point=t=>[left+width*t,y-2*rise*t*(1-t)];
 let s=`<path d="M${left} ${y} Q${x} ${y-rise} ${left+width} ${y}" fill="none" stroke="#384b40" stroke-width="6" stroke-linecap="round"/>`;
 if(valid){const p=point(u);s+=`<circle cx="${p[0]}" cy="${p[1]}" r="9" fill="${color}"/>`;}
 if(kind==='fuel')s+=this.t(left-15,y+8,'E',25,'#a9b5af','end')+this.t(left+width+15,y+8,'F',25,'#a9b5af','start');
 if(kind==='boost'){const p=point((0-min)/(max-min));s+=`<path d="M${p[0]} ${p[1]-9}v18" stroke="#dce5df" stroke-width="3"/>`+this.t(p[0],y+12,'0',24,'#a9b5af');}
 return s;
 }
};
