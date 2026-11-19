(()=>{
const data=window.REPLAY_DATA,rows=data.samples.map(row=>Object.fromEntries(data.columns.map((key,i)=>[key,row[i]]))),start=rows[0].time,end=rows.at(-1).time;
const display=document.getElementById('display'),play=document.getElementById('play'),seek=document.getElementById('seek'),rate=document.getElementById('rate'),clock=document.getElementById('clock'),elapsed=document.getElementById('elapsed');
let mode='street',position=20,playing=false,last=null;
seek.max=end-start;
// Preview-only inputs; independent of the recorded stationary engine revs.
function simulatedInputs(time){
 const t=Math.max(0,Math.min(end-start,time-start));
 const keys=[[0,32],[12,46],[20,64],[28,78],[33,92],[42,55],[end-start,30]];
 let i=0;while(i<keys.length-2&&t>keys[i+1][0])i++;
 const a=keys[i],b=keys[i+1],u=Math.max(0,Math.min(1,(t-a[0])/(b[0]-a[0]))),smooth=u*u*(3-2*u);
 return {speed:a[1]+(b[1]-a[1])*smooth,fuel:62-0.2*t/(end-start),oiltemp:206+6*Math.sin(t/(end-start)*Math.PI)};
}
function at(time){let lo=0,hi=rows.length-1;while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(rows[mid].time<=time)lo=mid;else hi=mid-1;}const a=rows[lo],b=rows[Math.min(lo+1,rows.length-1)],fraction=b.time>a.time?Math.max(0,Math.min(1,(time-a.time)/(b.time-a.time))):0;return {...a,...simulatedInputs(time),visualRpm:a.rpm+(b.rpm-a.rpm)*fraction};}
function draw(){const d=at(start+position),content=mode==='street'?window.renderStreet(d):mode==='track'?window.renderTrack(d):window.renderTuning(d,rows);display.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 800" role="img" aria-label="${mode} cluster replay"><title>${mode} cluster replay</title><rect width="1280" height="800" fill="#050606"/>${content}</svg>`;seek.value=position;clock.textContent='LOG '+(start+position).toFixed(2)+' s';elapsed.textContent=position.toFixed(1)+' / '+(end-start).toFixed(1)+' s';play.textContent=playing?'Pause':'Play';}
function frame(now){if(playing&&last!=null){position=Math.min(end-start,position+(now-last)/1000*Number(rate.value));if(position>=end-start)playing=false;draw();}last=now;requestAnimationFrame(frame);}
play.addEventListener('click',()=>{if(position>=end-start)position=0;playing=!playing;last=null;draw();});seek.addEventListener('input',()=>{position=Number(seek.value);draw();});document.getElementById('revs').addEventListener('click',()=>{position=23;playing=true;last=null;draw();});document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));draw();}));
window.replayTest={at,draw,getState:()=>({position,mode,playing}),seek:(p)=>{position=p;draw();}};
draw();requestAnimationFrame(frame);
})();
