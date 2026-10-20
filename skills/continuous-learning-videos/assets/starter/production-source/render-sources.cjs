'use strict';
// Static discovery only: never execute the authored world to find its imports.
const fs=require('node:fs'),path=require('node:path'),{createRequire}=require('node:module');

function tokens(source,file) {
  const out=[];let i=0;
  const fail=message=>{throw new Error(`${file}: ${message}`);};
  while(i<source.length) {
    const c=source[i],next=source[i+1];
    if(/\s/.test(c)){i++;continue;}
    if(c==='/'&&next==='/'){i=source.indexOf('\n',i+2);if(i<0)break;continue;}
    if(c==='/'&&next==='*'){const end=source.indexOf('*/',i+2);if(end<0)fail('Unterminated comment');i=end+2;continue;}
    if(c==='"'||c==="'"||c==='`') {
      const quote=c,start=i++;let escaped=false,closed=false;
      for(;i<source.length;i++) {if(source[i]==='\\'){escaped=true;i++;continue;}if(source[i]===quote){i++;closed=true;break;}}
      if(!closed)fail('Unterminated string or template');
      const raw=source.slice(start+1,i-1);
      if(quote==='`'&&raw.includes('${')&&/\brequire\s*(?:\(|\.)/.test(raw))fail('Imports inside template interpolation are unsupported; move a literal require to module scope');
      out.push({kind:quote==='`'?'template':'string',value:raw,escaped});continue;
    }
    // Skip regex literals in expression-start positions; division remains punctuation.
    const previous=out.at(-1)?.value;
    if(c==='/'&&(!out.length||['=','(', '[','{',':',',','!','?',';','return','=>','&&','||','??'].includes(previous))) {
      i++;let inClass=false,closed=false;
      for(;i<source.length;i++){const ch=source[i];if(ch==='\\'){i++;continue;}if(ch==='[')inClass=true;if(ch===']')inClass=false;if(ch==='/'&&!inClass){i++;closed=true;break;}}
      if(!closed)fail('Unterminated regular expression');
      while(/[a-z]/i.test(source[i]||'')&&i<source.length)i++;
      out.push({kind:'regex',value:'<regex>'});continue;
    }
    const word=/^[A-Za-z_$][\w$]*/.exec(source.slice(i));
    if(word){out.push({kind:'identifier',value:word[0]});i+=word[0].length;continue;}
    const pair=source.slice(i,i+2);
    if(['=>','&&','||','??','?.'].includes(pair)){out.push({kind:'punctuation',value:pair});i+=2;continue;}
    out.push({kind:'punctuation',value:c});i++;
  }
  return out;
}

function imports(source,file) {
  const ts=tokens(source,file),found=[];
  for(let i=0;i<ts.length;i++)if((ts[i].kind==='identifier'&&ts[i].value==='import')||
      (ts[i].kind==='identifier'&&ts[i].value==='createRequire')||
      (ts[i].value==='module'&&ts[i+1]?.value==='['&&ts[i+2]?.value==='require'))
    throw new Error(`${file}: dynamic or alternate module loading is unsupported; use direct literal require('./file.cjs')`);
  for(let i=0;i<ts.length;i++)if(ts[i].kind==='identifier'&&ts[i].value==='require') {
    if(['.','?.'].includes(ts[i-1]?.value))throw new Error(`${file}: module/property require is unsupported; use literal require('./file.cjs')`);
    if(ts[i+1]?.value==='.'&&['main','cache'].includes(ts[i+2]?.value))continue;
    if(ts[i+1]?.value!=='('||ts[i+2]?.kind!=='string'||ts[i+2].escaped||ts[i+3]?.value!==')')
      throw new Error(`${file}: dynamic, aliased or escaped require is unsupported; use a direct literal require('./file.cjs') and declare non-module assets in renderSources`);
    found.push(ts[i+2].value);i+=3;
  }
  return found;
}

function sourcePaths(project,course) {
  const root=fs.realpathSync(project),sources=new Set(),queue=[];
  function add(relative,scan=true) {
    if(typeof relative!=='string'||!relative||path.isAbsolute(relative))throw new Error('Render sources must be project-relative regular files');
    const absolute=path.resolve(root,relative),rel=path.relative(root,absolute);
    if(rel==='..'||rel.startsWith('..'+path.sep))throw new Error('Render dependency escapes the project: '+relative);
    let current=root;
    for(const part of rel.split(path.sep)){current=path.join(current,part);if(fs.lstatSync(current).isSymbolicLink())throw new Error('Render dependency contains a symlink: '+relative);}
    if(!fs.statSync(absolute).isFile())throw new Error('Render dependency must be a regular file: '+relative);
    const normalized=rel.split(path.sep).join('/');
    if(!sources.has(normalized)){sources.add(normalized);if(scan&&/\.(?:cjs|js)$/.test(absolute))queue.push(absolute);}
  }
  const declared=course.renderSources||[];
  if(!Array.isArray(declared)||new Set(declared).size!==declared.length)throw new Error('Invalid renderSources list');
  add('production-source/world.cjs');add('production-source/motion.cjs');
  for(const name of declared)add(name);
  // Keep the discovery contract and installed dependency declaration in its identity.
  for(const name of ['production-source/render-sources.cjs','production-source/package.json',
      'production-source/package-lock.json','production-source/npm-shrinkwrap.json'])if(fs.existsSync(path.join(root,name)))add(name,false);
  while(queue.length) {
    const file=queue.pop();
    for(const specifier of imports(fs.readFileSync(file,'utf8'),path.relative(root,file))) {
      if(path.isAbsolute(specifier))throw new Error('Absolute render imports are unsupported: '+specifier);
      if(!specifier.startsWith('.'))continue; // External packages use the package declaration, not a copied node_modules tree.
      const candidate=path.resolve(path.dirname(file),specifier),candidateRelative=path.relative(root,candidate);
      if(candidateRelative==='..'||candidateRelative.startsWith('..'+path.sep))throw new Error('Render dependency escapes the project: '+specifier);
      // Node resolves symlinks to their targets; inspect the original route first.
      let current=root;
      for(const part of candidateRelative.split(path.sep)) {
        current=path.join(current,part);
        let entry;
        try{entry=fs.lstatSync(current);}catch(error){if(error.code==='ENOENT')break;throw error;}
        if(entry.isSymbolicLink())throw new Error('Render dependency contains a symlink: '+specifier);
      }
      let resolved;
      try{resolved=createRequire(file).resolve(specifier);}catch(error){throw new Error(`Cannot resolve render dependency ${specifier} from ${path.relative(root,file)}: ${error.code}`);}
      if(!/\.(?:cjs|js|json)$/.test(resolved))throw new Error('Unsupported local module type; declare non-module assets in renderSources: '+specifier);
      add(path.relative(root,resolved));
    }
  }
  return [...sources].sort();
}

module.exports={sourcePaths,imports};
if(require.main===module) {
  try{const root=path.resolve(process.argv[2]);console.log(JSON.stringify(sourcePaths(root,JSON.parse(fs.readFileSync(path.join(root,'course.json'),'utf8')))));}
  catch(error){console.error(error.message);process.exitCode=1;}
}
