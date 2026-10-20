'use strict';
const {palette:P,progress,mix,createStage}=require('./motion.cjs');

function conservedTransfer(g,lesson,t,course) {
  const moving=lesson.scenes[1],a=moving.speechStart??moving.start,b=moving.speechEnd??moving.end;
  const p=progress(t,a,b),inTransit=t>=a&&t<b;
  const left=t<a?100:90,right=t>=b?60:50,flight=inTransit?10:0;
  const stage=createStage(g,course,{x:mix(610,660,p),y:340,zoom:1});
  const {actor,label,edge}=stage;
  // Connections precede solid objects; both endpoints persist during the transfer.
  edge([[380,300],[800,300]],P.line,3);
  const build=progress(t,lesson.scenes[0].start,Math.min(lesson.scenes[0].end,lesson.scenes[0].start+1));
  for(const [id,x,value] of [['left',285,left],['right',915,right]]) {
    actor(id,{x:x-90,y:228,w:180,h:145},c=>{
      c.strokeStyle=P.ink;c.lineWidth=3;c.beginPath();c.moveTo(x-86,230);c.lineTo(x-86,370);c.lineTo(x+86,370);c.lineTo(x+86,230);c.stroke();
      const h=110*value/100*build;c.fillStyle=id==='left'?P.mint:P.sand;c.fillRect(x-80,365-h,160,h);
    });
    label(id+'-name',id==='left'?'Account A':'Account B',x,200,{size:24});
    label(id+'-value',String(value),x,410,{size:34});
  }
  if(inTransit) {
    const x=mix(425,775,p);
    actor('portion',{x:x-27,y:273,w:54,h:54},c=>{c.fillStyle=P.gold;c.beginPath();c.arc(x,300,25,0,Math.PI*2);c.fill();});
    label('portion-value','10',x,300,{owner:'portion',color:'#ffffff',size:24});
  }
  label('total','TOTAL 150',610,130,{size:28});
  label('balance-equation',`${left}  +  ${flight} in transit  +  ${right}  =  150`,610,500,{size:26});
  return stage.finish({totalUnits:left+flight+right,expectedTotal:150});
}

function draw(g,lesson,t,course) {
  if(lesson.visual==='conserved-transfer')return conservedTransfer(g,lesson,t,course);
  throw new Error(`No authored world for visual: ${lesson.visual}`);
}
module.exports={draw};
