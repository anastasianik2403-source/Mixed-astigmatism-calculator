const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const http=require('http'), fs=require('fs'), path=require('path');
const root=path.join(process.cwd(),'site');
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]); if(p==='/')p='/index.html'; const f=path.join(root,p);
  fs.readFile(f,(e,d)=>{ if(e){s.writeHead(404);s.end();return;} const ext=path.extname(f); s.writeHead(200,{'Content-Type':{'.html':'text/html','.js':'application/javascript','.png':'image/png','.json':'application/json','.ttf':'font/ttf'}[ext]||'application/octet-stream'}); s.end(d);});
}).listen(0);
(async()=>{
  const port=srv.address().port;
  const fps=+process.argv[2]||30, outdir=process.argv[3]||'frames', which=process.argv[4]||'all', workers=+process.argv[5]||4;
  fs.mkdirSync(outdir,{recursive:true});
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--no-sandbox']});
  const probe=await b.newPage(); await probe.goto(`http://localhost:${port}/index.html`); await probe.evaluate(()=>window.COVER.ready); const DUR=await probe.evaluate(()=>window.COVER.DURATION); await probe.close();
  let times=[]; if(which==='all'){ const n=Math.round(DUR*fps)+1; for(let i=0;i<n;i++) times.push([i,i/fps]); } else { which.split(',').forEach((s,i)=>times.push([i,+s])); }
  let next=0;
  async function worker(){
    const p=await b.newPage({viewport:{width:600,height:900}}); await p.goto(`http://localhost:${port}/index.html`); await p.evaluate(()=>window.COVER.ready);
    while(true){ const k=next++; if(k>=times.length)break; const [i,t]=times[k];
      const d=await p.evaluate((t)=>{window.COVER.drawFrame(t);return document.getElementById('c').toDataURL('image/png');},t);
      fs.writeFileSync(path.join(outdir,which==='all'?`f_${String(i).padStart(4,'0')}.png`:`t_${t.toFixed(2)}.png`),Buffer.from(d.split(',')[1],'base64')); }
    await p.close();
  }
  await Promise.all(Array.from({length:workers},worker));
  await b.close(); srv.close(); console.log('done',times.length);
})();
