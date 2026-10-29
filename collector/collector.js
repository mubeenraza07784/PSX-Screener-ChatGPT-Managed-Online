// PSX monitor collector — run in a stockanalysis.com tab via javascript_tool.
// Set window.MON_OPTS = {fundSlice: 0..4} before running (default: by weekday).
// Intraday mode: MON_OPTS = {noFund:true, only:['SYM',...], todayDate:'YYYY-MM-DD', today:{SYM:[o,h,l,c,v]}} – prices for the listed
// symbols only, with today's running candle (from the PSX data portal) appended when the source has no bar for today yet.
(function(){
const K100 = 'ABL,ABOT,AGP,AHCL,AICL,AIRLINK,AKBL,APL,ATLH,ATRL,BAFL,BAHL,BML,BNWM,BOP,BWCL,CHCC,CNERGY,COLG,CPHL,DCR,DGKC,EFERT,ENGROH,FABL,FATIMA,FCCL,FFC,FFL,FHAM,GADT,GAL,GHGL,GHNI,GLAXO,HALEON,HBL,HCAR,HGFA,HINOON,HMB,HUBC,IBFL,ILP,IMAGE,INDU,INIL,ISL,JDWS,JVDC,KAPCO,KEL,KOHC,KTML,LCI,LOTCHEM,LUCK,MARI,MCB,MEBL,MLCF,MTL,MUREB,NATF,NBP,NCPL,NESTLE,NML,NPL,OGDC,PAEL,PAKT,PGLC,PIBTL,PIOC,PKGS,POL,POWER,PPL,PSEL,PSO,PSX,PTC,SAZEW,SCBPL,SEARL,SHFA,SNGP,SRVI,SSGC,SSOM,SYS,TGL,THCCL,TPLRF1,TRG,UBL,UPFL,YOUW'.split(',');
const COURSEF = ['allD','allW','cwt','mtf','haLips','jaw','dow','swH','frL','div','fvgB','flip','pats','patN','patD','patK','patS','patE','patSL','patT','mktD','mktW'];  // stored per company (features.txt must stay < 256 KB)
const TECHF0 = ['P','s20','s50','s200','rsi','macdH','macdX','r1m','r3m','r6m','r1y','hi','lo','vol','beta','trend','sup','res','fibLeg','fibR','cds','vR','val','lastDate'];
const TECHF = TECHF0.concat(COURSEF);
const FUNDF = ['fy','ny','salesG','opG','npG','eps3v5','epsT','epsG','pe','pb','ps','dy','evebitda','mcap','opM','npM','taxR','intCov','de','debt3v5','cr','cfo3v5','ncfPos','ccfo','fat3v5','roe','fcfps3v5','fcfSales','fcfCfo3v5','croic','invT3v5','dso3v5','dio3v5','dpo3v5','ccc3v5','fcfps3','fcfpsT','cashps','bvps','dps'];
const _fetch = window.fetch.bind(window);
const sleep = ms => new Promise(r=>setTimeout(r,ms));
const ST = window.MON = {phase:'list', done:0, total:0, fundDone:0, fundTotal:0, blocked:false, running:true, started:Date.now(), errors:0};
async function get(u, json){ if(ST.blocked) return null; const ac=new AbortController(); const t=setTimeout(()=>ac.abort(),20000);
  try{ const r=await _fetch(u,{signal:ac.signal}); if(r.status===429||r.status===403){ ST.blocked=true; return null;} if(r.status!==200){ ST.errors++; return null;}
    if(json) return await r.json(); const t2=await r.text(); if(/<title>Just a moment/.test(t2)){ ST.blocked=true; return null;} return t2; }catch(e){ ST.errors++; return null; } finally{ clearTimeout(t);} }
function extractObj(t, key){ const i=t.indexOf(key+':{'); if(i<0) return null; let s=i+key.length+1, depth=0, inStr=false, q='';
  for(let k=s;k<t.length;k++){ const c=t[k]; if(inStr){ if(c==='\\'){k++;continue;} if(c===q) inStr=false; continue; }
    if(c==='"'||c==="'"||c==='`'){inStr=true;q=c;continue;} if(c==='{') depth++; else if(c==='}'){ depth--; if(depth===0) return (new Function('return ('+t.slice(s,k+1)+')'))(); } } return null; }
function pick(fd, keys){ if(!fd) return null; const o={}; for(const k of keys){ if(fd[k]!==undefined) o[k]=fd[k]; } return o; }
const IS=['datekey','revenue','cor','opinc','interestExpense','pretax','taxexp','netinc','epsdil','dps'];
const BS=['datekey','accountsReceivable','receivables','inventory','assetsc','netPPE','accountsPayable','currentLiabilities','equity','debt','bvps','netcashpershare'];
const CF=['datekey','ncfo','fcf','fcfps','ncf'];
const RT=['datekey','marketcap','pe','ps','pb','evebitda','dividendyield'];
const mean = a => { const b=a.filter(x=>x!=null&&isFinite(x)); return b.length? b.reduce((s,x)=>s+x,0)/b.length : null; };
const annual=(fd,key)=>{ if(!fd||!fd[key]||!fd.datekey) return []; const out=[]; for(let i=0;i<fd.datekey.length;i++){ const d=fd.datekey[i]; if(d==='TTM'||d==='Current'||d==null) continue; out.push(fd[key][i]); } return out.slice(0,5).reverse(); };
const ttm=(fd,key)=>{ if(!fd||!fd[key]||!fd.datekey) return null; const i=fd.datekey.indexOf('TTM'); return i>=0? fd[key][i] : (fd[key][0]??null); };
const cur=(fd,key)=>{ if(!fd||!fd[key]||!fd.datekey) return null; let i=fd.datekey.indexOf('Current'); if(i<0) i=fd.datekey.indexOf('TTM'); if(i<0) i=0; return fd[key][i]; };
const v3v5=(a,hg=true)=>{ const b=a.filter(x=>x!=null&&isFinite(x)); if(b.length<4) return null; const m3=mean(b.slice(-3)), m5=mean(b); return (hg? m3>m5 : m3<m5)?1:0; };
const yoy=a=>{ const n=a.length; if(n<2) return null; const x=a[n-1], y=a[n-2]; if(x==null||y==null||y<=0) return null; return (x/y-1)*100; };
const cagr=a=>{ const b=a.filter(x=>x!=null); if(b.length<3) return null; const f=b[0], l=b[b.length-1]; if(f<=0||l<=0) return null; return (Math.pow(l/f,1/(b.length-1))-1)*100; };
const avgPairs=a=>a.map((x,i)=> i===0? null : (x!=null&&a[i-1]!=null? (x+a[i-1])/2 : x));
function fund(r){ const is=r.is, bs=r.bs, cf=r.cf, rt=r.rt; if(!is&&!bs) return null;
  const rev=annual(is,'revenue'), op=annual(is,'opinc'), ni=annual(is,'netinc'), eps=annual(is,'epsdil'), pt=annual(is,'pretax'), tx=annual(is,'taxexp'), ie=annual(is,'interestExpense'), cor=annual(is,'cor');
  const eq=annual(bs,'equity'), debt=annual(bs,'debt').map(x=>x==null?0:x), ca=annual(bs,'assetsc'), cl=annual(bs,'currentLiabilities'), ppe=annual(bs,'netPPE'), inv=annual(bs,'inventory'), ar=annual(bs,'accountsReceivable').map((x,i)=> x!=null?x:annual(bs,'receivables')[i]), ap=annual(bs,'accountsPayable');
  const cfo=annual(cf,'ncfo'), fcf=annual(cf,'fcf'), fcfps=annual(cf,'fcfps'), ncf=annual(cf,'ncf'); const L=a=>a.length?a[a.length-1]:null;
  const revT=ttm(is,'revenue')??L(rev), opT=ttm(is,'opinc')??L(op), niT=ttm(is,'netinc')??L(ni), epsT=ttm(is,'epsdil')??L(eps);
  const fat=rev.map((x,i)=> x!=null&&ppe[i]? x/ppe[i]:null); const invAvg=avgPairs(inv), arAvg=avgPairs(ar), apAvg=avgPairs(ap);
  const invT=cor.map((x,i)=> x!=null&&invAvg[i]? Math.abs(x)/invAvg[i]:null), dso=rev.map((x,i)=> x&&arAvg[i]!=null? arAvg[i]/x*365:null);
  const dio=cor.map((x,i)=> x&&invAvg[i]!=null? invAvg[i]/Math.abs(x)*365:null), dpo=cor.map((x,i)=> x&&apAvg[i]!=null? apAvg[i]/Math.abs(x)*365:null);
  const ccc=dso.map((x,i)=> x!=null&&dio[i]!=null&&dpo[i]!=null? x+dio[i]-dpo[i]:null), fcfCfo=fcf.map((x,i)=> x!=null&&cfo[i]? x/cfo[i]:null);
  const sumCfo=cfo.filter(x=>x!=null).reduce((s,x)=>s+x,0), sumNi=ni.filter(x=>x!=null).reduce((s,x)=>s+x,0);
  const lastFY=(is&&is.datekey? is.datekey.find(d=>d&&d!=='TTM') : (bs&&bs.datekey? bs.datekey.find(d=>d&&d!=='TTM'):null));
  const pt3=pt.slice(-3), tx3=tx.slice(-3); let sp=0, st=0; for(let i=0;i<pt3.length;i++){ if(pt3[i]!=null&&tx3[i]!=null){sp+=pt3[i]; st+=tx3[i];} }
  const dy=cur(rt,'dividendyield'), fT=ttm(cf,'fcf')??L(fcf);
  return { fy:lastFY? lastFY.slice(0,7):'', ny:rev.length, salesG:yoy(rev), opG:yoy(op), npG:yoy(ni), eps3v5:v3v5(eps), epsT, epsG:cagr(eps),
    pe:cur(rt,'pe'), pb:cur(rt,'pb'), ps:cur(rt,'ps'), dy:dy!=null? dy*100:null, evebitda:cur(rt,'evebitda'), mcap:cur(rt,'marketcap'),
    opM:revT? opT/revT*100:null, npM:revT? niT/revT*100:null, taxR:sp>0? st/sp*100:null, intCov:(L(ie)&&L(op)!=null)? L(op)/Math.abs(L(ie)) : (L(op)!=null? 99:null),
    de:L(eq)? L(debt)/L(eq):null, debt3v5:v3v5(debt,false), cr:(L(ca)&&L(cl))? L(ca)/L(cl):null, cfo3v5:v3v5(cfo), ncfPos:L(ncf)!=null? (L(ncf)>0?1:0):null,
    ccfo:(cfo.length>=3&&ni.length>=3)? (sumCfo>sumNi?1:0):null, fat3v5:v3v5(fat), roe:L(eq)&&niT!=null? niT/L(eq)*100:null, fcfps3v5:v3v5(fcfps),
    fcfSales:fT!=null&&revT? fT/revT*100:null, fcfCfo3v5:v3v5(fcfCfo), croic:(L(fcf)!=null&&L(eq))? L(fcf)/(L(eq)+(L(debt)||0))*100:null,
    invT3v5:v3v5(invT), dso3v5:v3v5(dso,false), dio3v5:v3v5(dio,false), dpo3v5:v3v5(dpo), ccc3v5:v3v5(ccc,false),
    fcfps3:mean(fcfps.slice(-3)), fcfpsT:ttm(cf,'fcfps'), cashps:cur(bs,'netcashpershare')??L(annual(bs,'netcashpershare')), bvps:L(annual(bs,'bvps')), dps:ttm(is,'dps')??L(annual(is,'dps')) }; }
// ===== Technical course rules =====
// ---- Technical course (Sarmaaya CWT, Weeks 4-8) rules on daily OHLC bars [date,o,h,l,c,v], oldest first.
// Week 4: Alligator (SMMA 13/8/5 shifted 8/5/3) + Heikin-Ashi, CWT scenarios 1-3, KSE-100 trend filter, volume leaders.
// Week 6: Fair Value Gaps, buy-limit vs buy-stop, higher-timeframe (Weekly) vs lower (Daily) scenarios 1-3.
// Week 7: RSI divergence (>70 / <30), double top/bottom, head & shoulders (+inverse), rising/falling wedge, breakout of LH/HL.
// Week 8: support<->resistance flips (SBR/RBS), flags, cup & handle (+inverted), triangles, channels, projections, RR 1:3.
const CRS = (function(){
const smmaArr=(a,n)=>{ const o=new Array(a.length).fill(null); if(a.length<n) return o; let s=0; for(let i=0;i<n;i++) s+=a[i]; let v=s/n; o[n-1]=v; for(let i=n;i<a.length;i++){ v=(v*(n-1)+a[i])/n; o[i]=v; } return o; };
const shift=(a,k)=>{ const o=new Array(a.length).fill(null); for(let i=k;i<a.length;i++) o[i]=a[i-k]; return o; };
function gator(b){ // returns per-bar jaw/teeth/lips aligned to bar index (shifted forward as on the chart)
  const med=b.map(x=>(x[2]+x[3])/2);
  return { jaw:shift(smmaArr(med,13),8), teeth:shift(smmaArr(med,8),5), lips:shift(smmaArr(med,5),3) }; }
function gatorState(b){ // 'bull' | 'bear' | 'sleep' on the last bar, plus slope direction of the jaw
  const g=gator(b), n=b.length-1; const J=g.jaw[n], T=g.teeth[n], L=g.lips[n]; if(J==null||T==null||L==null) return {st:'', g};
  const P=b[n][4]; const spread=Math.abs(L-J)/P;
  const ordBull=L>T&&T>J, ordBear=L<T&&T<J;
  // "open mouth & parallel": same order for the last 3 bars and spread not collapsing
  let keep=true; for(let k=1;k<=3;k++){ const j=g.jaw[n-k],t=g.teeth[n-k],l=g.lips[n-k]; if(j==null){keep=false;break;} if(ordBull&&!(l>t&&t>j)) keep=false; if(ordBear&&!(l<t&&t<j)) keep=false; }
  const jawSlope=g.jaw[n-3]!=null? (J-g.jaw[n-3])/P : 0;
  let st='sleep'; if(ordBull&&keep&&spread>=0.01) st='bull'; else if(ordBear&&keep&&spread>=0.01) st='bear';
  return {st, J, T, L, jawSlope, g}; }
function heikin(b){ const o=[]; let ho=(b[0][1]+b[0][4])/2, hc=(b[0][1]+b[0][2]+b[0][3]+b[0][4])/4; o.push([ho,hc]);
  for(let i=1;i<b.length;i++){ const c=(b[i][1]+b[i][2]+b[i][3]+b[i][4])/4; const op=(o[i-1][0]+o[i-1][1])/2; o.push([op,c]); } return o; }
function weekly(b){ const W=[]; let cur=null, key=null;
  for(const x of b){ const d=new Date(x[0]+'T00:00:00Z'); const mon=new Date(d); mon.setUTCDate(d.getUTCDate()-((d.getUTCDay()+6)%7)); const k=mon.toISOString().slice(0,10);
    if(k!==key){ if(cur) W.push(cur); key=k; cur=[k,x[1],x[2],x[3],x[4],x[5]]; } else { cur[2]=Math.max(cur[2],x[2]); cur[3]=Math.min(cur[3],x[3]); cur[4]=x[4]; cur[5]+=x[5]; } }
  if(cur) W.push(cur); return W; }
function rsiArr(c,n=14){ const o=new Array(c.length).fill(null); if(c.length<n+1) return o; let g=0,l=0; for(let i=1;i<=n;i++){ const d=c[i]-c[i-1]; if(d>0) g+=d; else l-=d; } g/=n; l/=n; o[n]=l===0?100:100-100/(1+g/l);
  for(let i=n+1;i<c.length;i++){ const d=c[i]-c[i-1]; g=(g*(n-1)+Math.max(d,0))/n; l=(l*(n-1)+Math.max(-d,0))/n; o[i]=l===0?100:100-100/(1+g/l); } return o; }
function swings(b,w){ const H=[],L=[]; for(let i=w;i<b.length-w;i++){ let h=true,l=true; for(let j=i-w;j<=i+w;j++){ if(j===i) continue; if(j<i? b[j][2]>=b[i][2] : b[j][2]>b[i][2]) h=false; if(j<i? b[j][3]<=b[i][3] : b[j][3]<b[i][3]) l=false; } if(h) H.push([i,b[i][2]]); if(l) L.push([i,b[i][3]]); } return {H,L}; }
function fit(pts){ const n=pts.length; if(n<2) return null; let sx=0,sy=0,sxx=0,sxy=0; for(const [x,y] of pts){ sx+=x; sy+=y; sxx+=x*x; sxy+=x*y; } const d=n*sxx-sx*sx; if(!d) return null; const m=(n*sxy-sx*sy)/d; return {m, c:(sy-m*sx)/n, at:x=>m*x+(sy-m*sx)/n}; }
const pct=(a,b)=>(a-b)/b;

function patterns(b, sw, rsi){
  const n=b.length-1, P=b[n][4], out=[]; const H=sw.H.filter(x=>x[0]>=n-150), L=sw.L.filter(x=>x[0]>=n-150);
  const add=(name,dir,kind,status,entry,stop,target)=>out.push({name,dir,kind,status,entry,stop,target});
  const minBetween=(i,j,lo)=>{ let m=Infinity,M=-Infinity; for(let k=i;k<=j;k++){ m=Math.min(m,b[k][3]); M=Math.max(M,b[k][2]); } return lo?m:M; };
  // --- Double bottom / top (Week 7)
  if(L.length>=2){ const [a,c]=L.slice(-2); if(c[0]-a[0]>=8 && Math.abs(pct(c[1],a[1]))<=0.03){ const neck=minBetween(a[0],c[0],false); const low=Math.min(a[1],c[1]);
      const lowest=Math.min(...b.slice(Math.max(0,a[0]-20)).map(x=>x[3])); const before=b[Math.max(0,a[0]-30)][4];
      if(pct(neck,low)>=0.05 && n-c[0]<=25 && low<=lowest*1.005 && pct(before,low)>=0.08){ const ok=P>neck; add('Double bottom','bull','reversal', ok?'breakout':'forming', neck*1.005, low*0.99, neck+(neck-low)); } } }
  if(H.length>=2){ const [a,c]=H.slice(-2); if(c[0]-a[0]>=8 && Math.abs(pct(c[1],a[1]))<=0.03){ const neck=minBetween(a[0],c[0],true); const high=Math.max(a[1],c[1]);
      const highest=Math.max(...b.slice(Math.max(0,a[0]-20)).map(x=>x[2])); const before=b[Math.max(0,a[0]-30)][4];
      if(pct(high,neck)>=0.05 && n-c[0]<=25 && high>=highest*0.995 && pct(high,before)>=0.08){ const ok=P<neck; add('Double top','bear','reversal', ok?'breakdown':'forming', neck*0.995, high*1.01, neck-(high-neck)); } } }
  // --- Head & shoulders / inverse (Week 7)
  if(H.length>=3){ const [ls,hd,rs]=H.slice(-3); if(hd[1]>ls[1]*1.03&&hd[1]>rs[1]*1.03&&Math.abs(pct(rs[1],ls[1]))<=0.05&&n-rs[0]<=25&&hd[1]>=Math.max(...b.slice(Math.max(0,ls[0]-20)).map(x=>x[2]))*0.999&&pct(ls[1],b[Math.max(0,ls[0]-30)][4])>=0.05){
      const neck=Math.min(minBetween(ls[0],hd[0],true),minBetween(hd[0],rs[0],true)); const ok=P<neck; add('Head & shoulders','bear','reversal', ok?'breakdown':'forming', neck*0.995, rs[1]*1.01, neck-(hd[1]-neck)); } }
  if(L.length>=3){ const [ls,hd,rs]=L.slice(-3); if(hd[1]<ls[1]*0.97&&hd[1]<rs[1]*0.97&&Math.abs(pct(rs[1],ls[1]))<=0.05&&n-rs[0]<=25&&hd[1]<=Math.min(...b.slice(Math.max(0,ls[0]-20)).map(x=>x[3]))*1.001&&pct(b[Math.max(0,ls[0]-30)][4],ls[1])>=0.05){
      const neck=Math.max(minBetween(ls[0],hd[0],false),minBetween(hd[0],rs[0],false)); const ok=P>neck; add('Inverse head & shoulders','bull','reversal', ok?'breakout':'forming', neck*1.005, rs[1]*0.99, neck+(neck-hd[1])); } }
  // --- Lines through recent swing points: wedges, triangles, channels (Weeks 7-8)
  const h4=H.filter(x=>x[0]>=n-90).slice(-4), l4=L.filter(x=>x[0]>=n-90).slice(-4);
  if(h4.length>=2&&l4.length>=2&&(h4.length+l4.length)>=5){
    const fh=fit(h4), fl=fit(l4); const sh=fh.m/P*100, sl=fl.m/P*100; // % of price per bar
    const top=fh.at(n), bot=fl.at(n), width=(top-bot)/P, w0=(fh.at(Math.min(h4[0][0],l4[0][0]))-fl.at(Math.min(h4[0][0],l4[0][0])))/P;
    const flat=0.03, conv=width<w0*0.75;
    const inside=P<=top*1.01&&P>=bot*0.99, up=P>top, dn=P<bot, st=up?'breakout':dn?'breakdown':'forming';
    const startI=Math.min(h4[0][0],l4[0][0]); const prior=pct(b[startI][4], b[Math.max(0,startI-40)][4]);
    if(width>0&&(inside||((up||dn)&&Math.max(P/top,bot/P)<1.06))){
      if(sh>flat&&sl>flat&&conv&&sl>sh) add('Rising wedge','bear','reversal',st,bot*0.995,top*1.01,bot-(top-bot)*1.0);
      else if(sh<-flat&&sl<-flat&&conv&&sh<sl) add('Falling wedge','bull','reversal',st,top*1.005,bot*0.99,top+(fh.at(startI)-fl.at(startI)));
      else if(Math.abs(sh)<=flat&&sl>flat) add('Ascending triangle','bull','continuation',st,top*1.005,bot*0.99,top+(fh.at(startI)-fl.at(startI)));
      else if(Math.abs(sl)<=flat&&sh<-flat) add('Descending triangle','bear','continuation',st,bot*0.995,top*1.01,bot-(fh.at(startI)-fl.at(startI)));
      else if(sh<-flat&&sl>flat) { const d=prior>=0?'bull':'bear'; add('Symmetrical triangle',d,'continuation',st,d==='bull'?top*1.005:bot*0.995,d==='bull'?bot*0.99:top*1.01,d==='bull'?top+(fh.at(startI)-fl.at(startI)):bot-(fh.at(startI)-fl.at(startI))); }
      else if(sh>flat&&sl>flat&&!conv&&Math.abs(sh-sl)<=Math.max(Math.abs(sh),Math.abs(sl))*0.5) add('Ascending channel', prior<-0.1?'bear':'bull', 'continuation', st, prior<-0.1? bot*0.995 : bot, prior<-0.1? top*1.01 : bot*0.97, prior<-0.1? bot-(top-bot) : top);
      else if(sh<-flat&&sl<-flat&&!conv&&Math.abs(sh-sl)<=Math.max(Math.abs(sh),Math.abs(sl))*0.5) add('Descending channel', prior>0.1?'bull':'bear', 'continuation', st, prior>0.1? top*1.005 : top, prior>0.1? bot*0.99 : top*1.03, prior>0.1? top+(top-bot) : bot);
    } }
  // --- Flags (Week 8): pole >= 12% within <= 15 bars, then 4-20 bars of counter-trend drift retracing <= 50%
  for(const dir of ['bull','bear']){
    for(let len=4; len<=20; len++){ const s=n-len; if(s<16) break; let best=null;
      for(let p=3;p<=15;p++){ const a=s-p; if(a<0) break; const mv=pct(b[s][4],b[a][4]); if(dir==='bull'? mv>=0.12 : mv<=-0.12){ best=[a,mv]; } }
      if(!best) continue; const poleTop=dir==='bull'? Math.max(...b.slice(best[0],s+1).map(x=>x[2])) : Math.min(...b.slice(best[0],s+1).map(x=>x[3]));
      const poleBase=dir==='bull'? b[best[0]][3] : b[best[0]][2]; const pole=Math.abs(poleTop-poleBase);
      const seg=b.slice(s+1); const segH=Math.max(...seg.map(x=>x[2])), segL=Math.min(...seg.map(x=>x[3]));
      const retr=dir==='bull'? (poleTop-segL)/pole : (segH-poleTop)/pole; const drift=fit(seg.map((x,i)=>[i,x[4]]));
      const counter= drift && (dir==='bull'? drift.m<=P*0.002 : drift.m>=-P*0.002);
      if(retr<=0.5 && retr>=0.05 && counter && (dir==='bull'? segH<=poleTop*1.02 : segL>=poleTop*0.98)){
        const brk=dir==='bull'? segH : segL; const st=dir==='bull'? (P>brk*0.999&&b[n][2]>=segH?'breakout':'forming') : (P<brk*1.001&&b[n][3]<=segL?'breakdown':'forming');
        add(dir==='bull'?'Bull flag':'Bear flag', dir, 'continuation', st, dir==='bull'? brk*1.005 : brk*0.995, dir==='bull'? segL*0.99 : segH*1.01, dir==='bull'? brk+pole : brk-pole); break; } } }
  // --- Cup & handle (Week 8): prior advance into the left rim, rims are local highs within 5%, rounded cup 12-45% deep over 30-150 bars,
  //     handle of 3-20 bars that pulls back no more than 1/3 of the cup depth. Inverted version mirrors it after a decline.
  const isHi=i=>{ for(let k=Math.max(0,i-5);k<=Math.min(n,i+5);k++) if(b[k][2]>b[i][2]) return false; return true; };
  const isLo=i=>{ for(let k=Math.max(0,i-5);k<=Math.min(n,i+5);k++) if(b[k][3]<b[i][3]) return false; return true; };
  let cupDone=false, icupDone=false;
  for(let hl=3; hl<=20 && !(cupDone&&icupDone); hl++){ const r=n-hl; if(r<60) break;
    if(!cupDone && isHi(r)){ for(let w=30; w<=150 && r-w-30>=0; w+=5){ const l=r-w; if(!isHi(l)) continue; const rim1=b[l][2], rim2=b[r][2]; if(Math.abs(pct(rim2,rim1))>0.05) continue;
        const seg=b.slice(l,r+1); const cupLow=Math.min(...seg.map(x=>x[3])); const rimH=Math.max(rim1,rim2); const depth=pct(Math.min(rim1,rim2),cupLow); if(depth<0.12||depth>0.45) continue;
        if(Math.max(...b.slice(l+1,r).map(x=>x[2]))>rimH*1.01) continue;
        const lowI=l+seg.findIndex(x=>x[3]===cupLow); if(lowI-l<w*0.3||r-lowI<w*0.3) continue;
        if(pct(rim1, b[l-30][4])<0.10) continue; // needs an advance before the cup
        const hLow=Math.min(...b.slice(r,n+1).map(x=>x[3])); if((rimH-hLow)>(rimH-cupLow)/3 || hLow<cupLow+(rimH-cupLow)*0.5) continue;
        const st=P>rimH?'breakout':'forming'; if(st==='breakout'&&P>rimH*1.06) continue;
        add('Cup & handle','bull','continuation',st,rimH*1.005,hLow*0.99,rimH+(rimH-cupLow)); cupDone=true; break; } }
    if(!icupDone && isLo(r)){ for(let w=30; w<=150 && r-w-30>=0; w+=5){ const l=r-w; if(!isLo(l)) continue; const rim1=b[l][3], rim2=b[r][3]; if(Math.abs(pct(rim2,rim1))>0.05) continue;
        const seg=b.slice(l,r+1); const cupHi=Math.max(...seg.map(x=>x[2])); const rimL=Math.min(rim1,rim2); const depth=pct(cupHi,Math.max(rim1,rim2)); if(depth<0.12||depth>0.45) continue;
        if(Math.min(...b.slice(l+1,r).map(x=>x[3]))<rimL*0.99) continue;
        const hiI=l+seg.findIndex(x=>x[2]===cupHi); if(hiI-l<w*0.3||r-hiI<w*0.3) continue;
        if(pct(b[l-30][4], rim1)<0.10) continue; // needs a decline before the inverted cup
        const hHi=Math.max(...b.slice(r,n+1).map(x=>x[2])); if((hHi-rimL)>(cupHi-rimL)/3 || hHi>rimL+(cupHi-rimL)*0.5) continue;
        const st=P<rimL?'breakdown':'forming'; if(st==='breakdown'&&P<rimL*0.94) continue;
        add('Inverted cup & handle','bear','continuation',st,rimL*0.995,hHi*1.01,rimL-(cupHi-rimL)); icupDone=true; break; } } }
  return out; }

function divergence(b, sw, R){ // Week 7: compare the last two swing points; RSI extreme (<30 / >70) at the first one
  const n=b.length-1; const L=sw.L.filter(x=>x[0]>=n-80).slice(-2), H=sw.H.filter(x=>x[0]>=n-80).slice(-2);
  const lowR=i=>Math.min(...[i-1,i,i+1].map(k=>R[k]).filter(v=>v!=null)), highR=i=>Math.max(...[i-1,i,i+1].map(k=>R[k]).filter(v=>v!=null));
  if(L.length===2&&L[1][1]<L[0][1]&&lowR(L[1][0])>lowR(L[0][0])&&lowR(L[0][0])<30&&n-L[1][0]<=20) return 'bull';
  if(H.length===2&&H[1][1]>H[0][1]&&highR(H[1][0])<highR(H[0][0])&&highR(H[0][0])>70&&n-H[1][0]<=20) return 'bear';
  return ''; }

function fvg(b){ // Week 6: unfilled 3-candle gaps in the last 60 bars; nearest bullish one below price, bearish one above
  const n=b.length-1, P=b[n][4]; let bull=null, bear=null;
  for(let i=Math.max(2,n-60);i<=n;i++){
    if(b[i][3]>b[i-2][2]){ const lo=b[i-2][2], hi=b[i][3]; let minL=Infinity; for(let k=i+1;k<=n;k++) minL=Math.min(minL,b[k][3]); const top=Math.min(hi,minL); if(minL>lo && top<P && (!bull||top>bull[1])) bull=[lo, top]; }
    if(b[i][2]<b[i-2][3]){ const hi=b[i-2][3], lo=b[i][2]; let maxH=-Infinity; for(let k=i+1;k<=n;k++) maxH=Math.max(maxH,b[k][2]); if(maxH<hi && lo>P && (!bear||lo<bear[0])) bear=[Math.max(lo,maxH),hi]; } }
  return {bull, bear}; }

function analyse(b){ // b: daily bars oldest first, >= 60 bars
  const n=b.length-1; if(n<60) return null; const P=b[n][4]; const c=b.map(x=>x[4]);
  const D=gatorState(b), Wb=weekly(b), W=Wb.length>=30? gatorState(Wb) : {st:''};
  const ha=heikin(b); const haUp=ha[n][1]>ha[n][0];
  const lipsN=D.L, jawN=D.J;
  // CWT scenario on the daily chart (Week 4)
  let cwt='';
  if(D.st==='bull' && ha[n][1]>lipsN && Math.min(ha[n][0],ha[n][1])>lipsN*0.995) cwt='S1 Buy';
  else if(D.st==='bear' && ha[n][1]<lipsN && Math.max(ha[n][0],ha[n][1])<lipsN*1.005) cwt='S1 Sell';
  else if(D.st==='bear' && P>jawN) cwt='S2 Buy';
  else if(D.st==='bull' && P<jawN) cwt='S2 Sell';
  else if(D.st==='sleep') cwt='Sleeping';
  // Higher-timeframe alignment (Week 6: analyse Weekly, execute Daily)
  let mtf=''; if(W.st==='bull'){ mtf = D.st==='bull'? 'W+D up (S1)' : D.st==='bear'? 'W up, D pullback (S2)' : 'W up, D sideways (S3)'; }
  else if(W.st==='bear'){ mtf = D.st==='bear'? 'W+D down (S1)' : D.st==='bull'? 'W down, D bounce (S2)' : 'W down, D sideways (S3)'; }
  else if(W.st==='sleep') mtf='W sleeping';
  // Dow structure from 3-bar swings (Weeks 5-7: HH/HL, LH/LL)
  const sw3=swings(b,3); const Hs=sw3.H.slice(-2), Ls=sw3.L.slice(-2);
  let dow=''; if(Hs.length===2&&Ls.length===2){ if(Hs[1][1]>Hs[0][1]&&Ls[1][1]>Ls[0][1]) dow='HH-HL'; else if(Hs[1][1]<Hs[0][1]&&Ls[1][1]<Ls[0][1]) dow='LH-LL'; else dow='mixed'; }
  const swH=Hs.length? Hs[Hs.length-1][1] : null, swL=Ls.length? Ls[Ls.length-1][1] : null;
  // Fractal low below price for Scenario-2 stops ("below the blue dots")
  const fr=swings(b,2); const frL=fr.L.filter(x=>x[1]<P).slice(-1)[0];
  const R=rsiArr(c); const sw5=swings(b,5); const div=divergence(b,sw3,R);
  const F=fvg(b); const pats=patterns(b,sw5,R);
  // SBR / RBS (Week 8): a swing level that flipped role within the last 30 bars and price is retesting it (within 3%)
  let flip=''; for(const [i,lvl] of sw5.H.slice(-6)){ if(i<n-120) continue; const crossed=b.slice(i+1).findIndex(x=>x[4]>lvl*1.01); if(crossed>=0 && i+1+crossed>=n-30 && P>=lvl && pct(P,lvl)<=0.03) flip='RBS '+lvl.toFixed(2); }
  if(!flip) for(const [i,lvl] of sw5.L.slice(-6)){ if(i<n-120) continue; const crossed=b.slice(i+1).findIndex(x=>x[4]<lvl*0.99); if(crossed>=0 && i+1+crossed>=n-30 && P<=lvl && pct(lvl,P)<=0.03) flip='SBR '+lvl.toFixed(2); }
  const rank={breakout:0, breakdown:0, forming:1};
  pats.sort((a,b2)=> rank[a.status]-rank[b2.status]);
  const top=pats[0]||null; const r=x=>x==null?null:Math.round(x*100)/100;
  return { allD:D.st, allW:W.st, cwt, mtf, ha: haUp? 'green':'red', haLips: lipsN!=null? (ha[n][1]>lipsN?'above':'below'):'',
    jaw:r(jawN), teeth:r(D.T), lips:r(lipsN), dow, swH:r(swH), swL:r(swL), frL:frL? r(frL[1]):null, div,
    fvgB: F.bull? r(F.bull[0])+'-'+r(F.bull[1]) : '', fvgS: F.bear? r(F.bear[0])+'-'+r(F.bear[1]) : '', flip,
    pats: pats.map(p=>p.name+(p.status==='forming'?'':' ('+p.status+')')).join('+'),
    patN: top? top.name:'', patD: top? top.dir:'', patK: top? top.kind:'', patS: top? top.status:'', patE: top? r(top.entry):null, patSL: top? r(top.stop):null, patT: top? r(top.target):null }; }
return {analyse, gatorState, weekly, heikin};
})();

// ===== end course rules =====
const sma=(a,n)=> a.length>=n? a.slice(-n).reduce((s,x)=>s+x,0)/n : null;
function emaArr(a,n){ const k=2/(n+1); const o=[]; let e=a[0]; for(let i=0;i<a.length;i++){ e= i===0? a[0] : a[i]*k+e*(1-k); o.push(e);} return o; }
function rsi(a,n=14){ if(a.length<n+1) return null; let g=0,l=0; for(let i=1;i<=n;i++){ const d=a[i]-a[i-1]; if(d>0) g+=d; else l-=d; } g/=n; l/=n; for(let i=n+1;i<a.length;i++){ const d=a[i]-a[i-1]; g=(g*(n-1)+Math.max(d,0))/n; l=(l*(n-1)+Math.max(-d,0))/n; } return l===0?100:100-100/(1+g/l); }
function pivots(a,w=5){ const H=[],L=[]; for(let i=w;i<a.length-w;i++){ let isH=true,isL=true; for(let j=i-w;j<=i+w;j++){ if(a[j]>a[i]) isH=false; if(a[j]<a[i]) isL=false; } if(isH) H.push([i,a[i]]); if(isL) L.push([i,a[i]]); } return {H,L}; }
function candles(b, up){ const out=[]; const n=b.length; if(n<3) return out; const [,o,h,l,c]=b[n-1], [,po,ph,pl,pc]=b[n-2], [,qo,qh,ql,qc]=b[n-3];
  const body=Math.abs(c-o), rng=h-l||1e-9, upper=h-Math.max(o,c), lower=Math.min(o,c)-l;
  if(body<=0.1*rng) out.push('Doji'); if(lower>=2*body && upper<=Math.max(body,0.1*rng) && body>0) out.push(up?'Hanging Man':'Hammer');
  if(upper>=2*body && lower<=Math.max(body,0.1*rng) && body>0) out.push(up?'Shooting Star':'Inverted Hammer');
  if(pc<po && c>o && o<=pc && c>=po && body>Math.abs(pc-po)) out.push('Bullish Engulfing'); if(pc>po && c<o && o>=pc && c<=po && body>Math.abs(pc-po)) out.push('Bearish Engulfing');
  const qb=Math.abs(qc-qo), pb=Math.abs(pc-po); if(qc<qo && pb<0.5*qb && c>o && c>(qo+qc)/2) out.push('Morning Star'); if(qc>qo && pb<0.5*qb && c<o && c<(qo+qc)/2) out.push('Evening Star');
  if(body>=0.9*rng && rng>0) out.push(c>o?'Bullish Marubozu':'Bearish Marubozu');
  if(pc<po && c>o && o>pc && c<po && h<ph && l>pl) out.push('Bullish Harami'); if(pc>po && c<o && o<pc && c>po && h<ph && l>pl) out.push('Bearish Harami'); return out; }
const MKT_ST={d:'',w:''};
function tech(r, MKT){ if(!r.cl||r.cl.length<30) return null; const c=r.cl.map(x=>x[1]), d=r.cl.map(x=>x[0]); const P=c[c.length-1];
  const e12=emaArr(c,12), e26=emaArr(c,26); const macd=e12.map((x,i)=>x-e26[i]); const sig=emaArr(macd,9); const hist=macd.map((x,i)=>x-sig[i]);
  let mx=0; for(let k=1;k<=5&&k<hist.length;k++){ const a=hist[hist.length-k], b=hist[hist.length-k-1]; if(a>0&&b<=0){mx=1;break;} if(a<0&&b>=0){mx=-1;break;} }
  const y=c.slice(-250); const hi=Math.max(...y), lo=Math.min(...y); const hiI=y.lastIndexOf(hi), loI=y.lastIndexOf(lo); const pv=pivots(y,5); const H=pv.H.slice(-2), L=pv.L.slice(-2);
  let trend='Range'; if(H.length==2&&L.length==2){ if(H[1][1]>H[0][1]&&L[1][1]>L[0][1]) trend='Up'; else if(H[1][1]<H[0][1]&&L[1][1]<L[0][1]) trend='Down'; }
  const s50=sma(c,50), s200=sma(c,200), s20=sma(c,20); if(trend==='Range'&&s50&&s200){ if(P>s50&&s50>s200) trend='Up*'; else if(P<s50&&s50<s200) trend='Down*'; }
  const lowsBelow=pv.L.map(x=>x[1]).filter(x=>x<P*0.995), highsAbove=pv.H.map(x=>x[1]).filter(x=>x>P*1.005);
  const sup=lowsBelow.length? Math.max(...lowsBelow):lo, res=highsAbove.length? Math.min(...highsAbove):hi; const fibLeg=hiI>loI?'up':'down'; const fibR=hi>lo? (fibLeg==='up'?(hi-P)/(hi-lo):(P-lo)/(hi-lo)):null;
  const rets=[]; for(let i=Math.max(1,c.length-250);i<c.length;i++) rets.push(c[i]/c[i-1]-1); const r60=rets.slice(-60); const m=r60.reduce((s,x)=>s+x,0)/r60.length; const vol=Math.sqrt(r60.reduce((s,x)=>s+(x-m)**2,0)/r60.length)*Math.sqrt(250)*100;
  let beta=null; const xs=[],ys=[]; for(let i=Math.max(1,c.length-250);i<c.length;i++){ const mk=MKT[d[i]]; const rr=c[i]/c[i-1]-1; if(mk!=null&&isFinite(rr)&&Math.abs(rr)<0.25){xs.push(mk);ys.push(rr);} }
  if(xs.length>60){ const a=xs.reduce((s,x)=>s+x,0)/xs.length, b=ys.reduce((s,x)=>s+x,0)/ys.length; let cv=0,vx=0; for(let i=0;i<xs.length;i++){cv+=(xs[i]-a)*(ys[i]-b); vx+=(xs[i]-a)**2;} beta=vx? cv/vx:null; }
  const ret=n=> c.length>n? (P/c[c.length-1-n]-1)*100:null; const b=r.ohlc||[]; const cds=candles(b, s50? P>s50:false);
  const v=b.map(x=>x[5]); const v20=v.slice(-21,-1); const vR=v20.length? v[v.length-1]/(v20.reduce((s,x)=>s+x,0)/v20.length||1):null; const val=b.slice(-20).reduce((s,x)=>s+x[4]*x[5],0)/Math.max(1,Math.min(20,b.length));
  let crs=null; try{ crs= b.length>=60? CRS.analyse(b.slice(-500)) : null; }catch(e){ crs=null; }
  return {...(crs||{}), mktD:MKT_ST.d, mktW:MKT_ST.w, P,s20,s50,s200,rsi:rsi(c.slice(-300)),macdH:hist[hist.length-1]/P*100,macdX:mx,r1m:ret(21),r3m:ret(63),r6m:ret(126),r1y:ret(250),hi,lo,vol,beta,trend,sup,res,fibLeg,fibR,cds:cds.join('+'),vR,val,lastDate:new Date(d[d.length-1]).toISOString().slice(0,10)}; }
const fmt=v=>{ if(v==null||(typeof v==='number'&&!isFinite(v))) return ''; if(typeof v!=='number') return String(v).replace(/\|/g,'/'); const a=Math.abs(v); if(a>=1e9) return (v/1e9).toFixed(3)+'B'; if(a>=1e6) return (v/1e6).toFixed(2)+'M'; if(a>=100) return v.toFixed(1); if(a>=1) return v.toFixed(2); return v.toFixed(4).replace(/0+$/,'').replace(/\.$/,''); };
(async()=>{
  const lt = await get('/list/pakistan-stock-exchange/');
  let syms = lt? [...new Set([...lt.matchAll(/s:"psx\/([A-Z0-9]+)"/g)].map(m=>m[1]))] : [];
  if(!syms.length){ ST.phase='failed-list'; ST.running=false; return; }
  const k = new Set(K100); syms.sort((a,b)=> (k.has(b)-k.has(a)) || a.localeCompare(b));   // index names first
  const opts = window.MON_OPTS||{}; const slice = opts.fundSlice!=null? opts.fundSlice : (new Date().getDay()+4)%5;
  if(opts.only){ const only=new Set(opts.only); syms=syms.filter(s=>only.has(s)); }
  const fundSet = opts.noFund? new Set() : new Set([...syms].sort().filter((s,i)=> i%5===slice));
  ST.total=syms.length; ST.fundTotal=fundSet.size; ST.phase='prices'; ST.slice=slice;
  const RAW={}; window.__RAW=RAW;
  for(const s of syms){ if(ST.blocked) break; const rec={};
    const h5=await get('/api/symbol/a/PSX-'+s+'/history?range=5Y',true); await sleep(700);
    const hd= h5&&h5.data? (Array.isArray(h5.data)? h5.data : h5.data.data) : null;
    if(hd&&hd.length){ const bars=hd.slice(0,500).reverse(); rec.ohlc=bars.map(x=>[x.t,+x.o,+x.h,+x.l,+x.c,+x.v]); rec.cl=bars.slice(-400).map(x=>[Date.parse(x.t+'T00:00:00Z'),+x.c]);
      const tb = opts.today&&opts.today[s]; if(tb && opts.todayDate && rec.ohlc[rec.ohlc.length-1][0] < opts.todayDate){ rec.ohlc.push([opts.todayDate,+tb[0],+tb[1],+tb[2],+tb[3],+tb[4]]); rec.cl.push([Date.parse(opts.todayDate+'T00:00:00Z'),+tb[3]]); ST.todayAdded=(ST.todayAdded||0)+1; } }
    const hist= rec.ohlc? null : await get('/quote/psx/'+s+'/history/');
    if(!rec.ohlc){ const ch=await get('/api/symbol/a/PSX-'+s+'/history?type=chart',true); if(ch&&ch.data) rec.cl=ch.data.slice(-400); await sleep(700); }
    if(hist){ const re=/\{a:([-\d.e+]+|null),c:([-\d.e+]+),h:([-\d.e+]+),l:([-\d.e+]+),o:([-\d.e+]+),t:"(\d{4}-\d\d-\d\d)",v:([\d.e+]+)/g; rec.ohlc=[...hist.matchAll(re)].map(m=>[m[6],+m[5],+m[3],+m[4],+m[2],+m[7]]).reverse(); }
    if(fundSet.has(s) && !ST.blocked){ const base='/quote/psx/'+s+'/';
      for(const [kk,p,keys] of [['is','financials/income-statement/',IS],['bs','financials/balance-sheet/',BS],['cf','financials/cash-flow-statement/',CF],['rt','financials/ratios/',RT]]){ const t=await get(base+p); try{ rec[kk]= t? pick(extractObj(t,'financialData'),keys):null; }catch(e){ rec[kk]=null; } await sleep(700); }
      ST.fundDone++; }
    RAW[s]=rec; ST.done++; }
  ST.phase='compute';
  const R={},W={}; for(const s of K100){ const c=RAW[s]&&RAW[s].cl; if(!c) continue; for(let i=1;i<c.length;i++){ const ret=c[i][1]/c[i-1][1]-1; if(!isFinite(ret)||Math.abs(ret)>0.25) continue; R[c[i][0]]=(R[c[i][0]]||0)+ret; W[c[i][0]]=(W[c[i][0]]||0)+1; } }
  const MKT={}; for(const d in R) MKT[d]=R[d]/W[d];
  // KSE-100 trend filter (Week 4/6): Alligator on an equal-weight index built from the members' daily returns
  try{ let lvl=100; const ib=Object.keys(MKT).map(Number).sort((a,b)=>a-b).map(d=>{ lvl*=1+MKT[d]; return [new Date(d).toISOString().slice(0,10),lvl,lvl,lvl,lvl,0]; });
       MKT_ST.d=CRS.gatorState(ib).st; const wb=CRS.weekly(ib); MKT_ST.w= wb.length>=30? CRS.gatorState(wb).st : ''; }catch(e){}
  const TL=['sym|'+TECHF.join('|')], FL=['sym|'+FUNDF.join('|')];
  for(const s of Object.keys(RAW)){ const r=RAW[s]; let t=null,f=null; try{t=tech(r,MKT);}catch(e){} if(t) TL.push(s+'|'+TECHF.map(k=>fmt(t[k])).join('|'));
    if(r.is||r.bs){ try{f=fund(r);}catch(e){} if(f) FL.push(s+'|'+FUNDF.map(k=>fmt(f[k])).join('|')); } }
  window.__TECH=TL; window.__FUND=FL; ST.techLines=TL.length-1; ST.fundLines=FL.length-1; ST.phase='done'; ST.running=false; ST.secs=Math.round((Date.now()-ST.started)/1000);
})();
// Show output for get_page_text: MON_SHOW('tech'|'fund', chunkIndex, linesPerChunk)
window.MON_SHOW = function(kind, i, n){ n=n||(kind==='fund'?220:120);  // tech lines are longer now (course fields), keep each chunk under ~50k chars
  const L= kind==='fund'? window.__FUND : window.__TECH; const head=L[0]; const part=L.slice(1+i*n, 1+(i+1)*n);
  let o=document.getElementById('mon-out'); if(!o){ document.body.innerHTML='<main><article><pre id="mon-out"></pre></article></main>'; o=document.getElementById('mon-out'); }
  o.textContent = 'BEGIN '+kind+' '+i+'\n'+head+'\n'+part.join('\n')+'\nEND '+kind+' '+i+' ('+part.length+' lines, more='+(L.length-1>(i+1)*n)+')'; return part.length; };
})();
