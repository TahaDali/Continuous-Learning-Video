'use strict';
// Check numeric arguments at the actual Canvas method boundary, including glyph
// internals absent from actor registries. This is not a raster or meaning audit.
const installed=new WeakMap();
const required={moveTo:2,lineTo:2,rect:4,fillRect:4,strokeRect:4,clearRect:4,
  roundRect:4,arc:5,arcTo:5,ellipse:7,bezierCurveTo:6,quadraticCurveTo:4,
  translate:2,scale:2,rotate:1,transform:6,
  createLinearGradient:4,createRadialGradient:6,createConicGradient:3};

function install(g) {
  if(installed.has(g))return installed.get(g);
  const counts={};
  const finite=(value,label)=>{
    if(typeof value!=='number'||!Number.isFinite(value))
      throw new TypeError('Non-finite/non-numeric Canvas '+label);
  };
  function wrap(name,check) {
    if(typeof g[name]!=='function')return;
    const original=g[name].bind(g);
    g[name]=(...args)=>{check(args);counts[name]=(counts[name]||0)+1;return original(...args);};
  }
  for(const [name,n] of Object.entries(required))wrap(name,args=>{
    for(let i=0;i<n;i++)finite(args[i],name+' argument '+i);
    if(name==='roundRect'&&args[4]!==undefined) {
      const radii=Array.isArray(args[4])?args[4]:[args[4]];
      for(const radius of radii) {
        if(typeof radius==='object'&&radius!==null) {
          finite(radius.x===undefined?0:radius.x,'roundRect radius.x');
          finite(radius.y===undefined?0:radius.y,'roundRect radius.y');
        } else finite(radius,'roundRect radius');
      }
    }
  });
  for(const name of ['fillText','strokeText'])wrap(name,args=>{
    for(const i of [1,2])finite(args[i],name+' position '+i);
    if(args[3]!==undefined)finite(args[3],name+' maxWidth');
  });
  wrap('drawImage',args=>{
    if(![3,5,9].includes(args.length))throw new TypeError('Canvas drawImage requires image and 2, 4 or 8 numeric coordinates');
    for(let i=1;i<args.length;i++)finite(args[i],'drawImage argument '+i);
  });
  wrap('setLineDash',args=>{
    if(!Array.isArray(args[0]))throw new TypeError('Canvas setLineDash requires an array');
    args[0].forEach(value=>finite(value,'setLineDash segment'));
  });
  wrap('setTransform',args=>{
    if(args.length===0)return;
    if(args.length===1&&args[0]!==null&&typeof args[0]==='object') {
      const matrix=args[0];
      for(const [key,fallback] of Object.entries({a:1,b:0,c:0,d:1,e:0,f:0,m11:1,m12:0,m21:0,m22:1,m41:0,m42:0}))
        finite(matrix[key]===undefined?fallback:matrix[key],'setTransform '+key);
    } else for(let i=0;i<6;i++)finite(args[i],'setTransform argument '+i);
  });
  installed.set(g,counts);
  return counts;
}

module.exports={install};
