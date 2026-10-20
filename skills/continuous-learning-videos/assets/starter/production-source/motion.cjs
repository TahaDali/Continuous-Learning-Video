'use strict';
const palette = {bg:'#f5f2e9', ink:'#17353d', muted:'#536c70', line:'#bfd0ca', teal:'#087e79', mint:'#c8e7d8', gold:'#b77613', sand:'#f8e4bd'};
const clamp = x => Math.max(0,Math.min(1,x));
const mix = (a,b,p) => a+(b-a)*p;
const smooth = x => {x=clamp(x);return x*x*(3-2*x);};
const progress = (t,a,b) => smooth((t-a)/Math.max(.001,b-a));
function screenBounds(g,b) {
  const m=g.getTransform();
  const p=[[b.x,b.y],[b.x+b.w,b.y],[b.x,b.y+b.h],[b.x+b.w,b.y+b.h]].map(([x,y])=>({x:m.a*x+m.c*y+m.e,y:m.b*x+m.d*y+m.f}));
  const xs=p.map(p=>p.x),ys=p.map(p=>p.y);
  return {x:Math.min(...xs),y:Math.min(...ys),w:Math.max(...xs)-Math.min(...xs),h:Math.max(...ys)-Math.min(...ys)};
}
function createStage(g,course,camera={x:640,y:340,zoom:1}) {
  const {width:W,height:H}=course;
  // Default 16:9 safe zones; adapt together when the output dimensions change.
  const viewport={x:32,y:80,w:W-64,h:H-205};
  const safe={x:40,y:88,w:W-80,h:H-221};
  const items=[];
  g.resetTransform();g.globalAlpha=1;g.fillStyle=palette.bg;g.fillRect(0,0,W,H);
  g.fillStyle='#fffefa';g.fillRect(0,H-112,W,88);
  g.save();g.beginPath();g.rect(viewport.x,viewport.y,viewport.w,viewport.h);g.clip();
  g.translate(W/2,340);g.scale(camera.zoom,camera.zoom);g.translate(-camera.x,-camera.y);
  function record(id,b,kind,owner=null) {
    if(items.some(x=>x.id===id))throw new Error('Duplicate audit ID: '+id);
    items.push({id,kind,owner,bounds:screenBounds(g,b),alpha:g.globalAlpha});
  }
  function actor(id,b,draw) {record(id,b,'actor');g.save();draw(g);g.restore();}
  function label(id,text,x,y,{size=24,color=palette.ink,owner=null,align='center',weight=600}={}) {
    g.save();g.font=`${weight} ${size}px Arial`;g.textAlign=align;g.textBaseline='middle';
    const m=g.measureText(String(text)),w=m.width;
    record(id,{x:x-(align==='center'?w/2:align==='right'?w:0)-3,y:y-size*.65,w:w+6,h:size*1.3},'label',owner);
    g.fillStyle=color;g.fillText(String(text),x,y);g.restore();
  }
  function edge(points,color=palette.line,width=3) {
    g.save();g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.beginPath();
    points.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.stroke();g.restore();
  }
  return {g,actor,label,edge,finish(invariants={}){g.restore();return {items,safe,viewport,invariants};}};
}
module.exports={palette,clamp,mix,smooth,progress,createStage};
