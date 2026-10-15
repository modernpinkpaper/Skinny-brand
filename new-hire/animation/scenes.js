// ===== New-hire video: the nicer office, step illustrations, and the frame() that draws everything =====
// Palette: white + warm cream, gold accents, brand pink and navy.
const PINK="#ff5fa8", PINK2="#ffd3e6", NAVY="#1f2a5c", GOLD="#d4a84b", CREAM="#fbf5ee", INK="#1b1230";
const SCEN={intro:1,nozzle:1,bin:1,paper:1,test:1,run:1,env:1,check:1,pack:1,inserts:1,label:1,repeat:1,outro:1};
const R=(g,x,y,w,h,fill,stroke,r,sw)=>el("rect",{x,y,width:w,height:h,rx:r||0,fill:fill||"none",stroke:stroke||"none","stroke-width":sw||0},g);
const C=(g,x,y,r,fill,stroke,sw)=>el("circle",{cx:x,cy:y,r,fill:fill||"none",stroke:stroke||"none","stroke-width":sw||0},g);
const P=(g,d,fill,stroke,sw,extra)=>el("path",Object.assign({d,fill:fill||"none",stroke:stroke||"none","stroke-width":sw||0,"stroke-linecap":"round","stroke-linejoin":"round"},extra||{}),g);
const T=(g,x,y,s,size,fill,anchor,stroke)=>{const t=el("text",{x,y,"font-size":size||40,fill:fill||INK,"text-anchor":anchor||"middle"},g);if(stroke){t.setAttribute("stroke",stroke);t.setAttribute("stroke-width",size/6);t.setAttribute("paint-order","stroke")}t.textContent=s;return t};
const pop=(p,a,b)=>ease(clamp((p-a)/(b-a||.001),0,1));            // 0..1 ease between two progress points
const back=(x)=>{const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)};
const popB=(p,a,b)=>back(clamp((p-a)/(b-a||.001),0,1));            // springy pop

// ---------- the room (drawn once) ----------
function buildBgs(){
 const g=$("bgs"), defs=document.querySelector("defs");
 const w=el("linearGradient",{id:"wallG",x1:0,y1:0,x2:0,y2:1},defs); el("stop",{offset:0,"stop-color":"#fffaf5"},w); el("stop",{offset:1,"stop-color":"#f4e8de"},w);
 const gl=el("radialGradient",{id:"glow"},defs); el("stop",{offset:0,"stop-color":"#fff2c4","stop-opacity":.9},gl); el("stop",{offset:1,"stop-color":"#fff2c4","stop-opacity":0},gl);
 const sk=el("linearGradient",{id:"skyG",x1:0,y1:0,x2:0,y2:1},defs); el("stop",{offset:0,"stop-color":"#dff1ff"},sk); el("stop",{offset:1,"stop-color":"#fff6e8"},sk);
 R(g,0,0,1080,1920,"url(#wallG)");
 // wainscot panel + gold rail
 R(g,0,1180,1080,740,"#f0e4d8"); R(g,0,1172,1080,12,GOLD);
 // window (left) with blinds
 R(g,56,250,360,520,"#fff","#e4d6c6",10,10); R(g,76,270,320,480,"url(#skyG)");
 for(let i=0;i<16;i++)R(g,76,270+i*30,320,14,"#ffffff",null,4).setAttribute("opacity",.85);
 R(g,236,270,8,480,"#fff");
 // shelf wall (right): white frame, gold edges, colour-coded envelope boxes
 R(g,610,240,420,700,"#fff","#e4d6c6",8,8); R(g,606,236,428,8,GOLD); R(g,606,936,428,8,GOLD);
 const pal=[["#ffb3d1","#ff7fb4","#ffd3e6","#ff5fa8"],["#2c3a78","#1f2a5c","#3a4a94","#16204a"],["#f3d9a4","#e6c07a","#fbe9c4","#d4a84b"],["#fff","#f1e8de","#e8ddd0","#fbf5ee"],["#c9e3d4","#a9d1bb","#dff0e6","#8fc2a6"],["#d9c9f2","#bfa9e6","#ece3fb","#a88fd9"]];
 for(let r=0;r<6;r++)for(let c=0;c<4;c++){const x=624+c*98,y=256+r*112; R(g,x,y,90,100,"#fbf7f2","#eadfd2",6,3); const col=pal[r][c];
  R(g,x+8,y+18,74,64,col,"rgba(0,0,0,.18)",5,2); R(g,x+8,y+18,74,16,"rgba(255,255,255,.35)",null,5); R(g,x+30,y+6,30,8,"#fff","#eadfd2",3,1)}
 // gold pendants + glow
 for(const x of[300,780]){ R(g,x-2,-20,4,170,GOLD); P(g,`M${x-48} 200 Q${x} 110 ${x+48} 200 Z`,GOLD,"#a98230",4); C(g,x,215,16,"#fff6d6","#a98230",3); el("circle",{cx:x,cy:220,r:150,fill:"url(#glow)"},g)}
 // plant + frame art
 R(g,110,800,60,50,"#fff","#e4d6c6",8,4);
 for(let i=0;i<7;i++){const a=-70+i*23; P(g,`M140 800 Q${140+Math.sin(a*Math.PI/180)*60} ${730-Math.abs(i-3)*8} ${140+Math.sin(a*Math.PI/180)*90} ${700+Math.abs(i-3)*14}`,null,"#6fae8a",12)}
 // back desk line
 R(g,0,1520,1080,12,GOLD); R(g,0,1532,1080,388,"#ffffff");
 for(let i=0;i<5;i++)R(g,40+i*210,1560,190,90,"#faf6f1","#eadfd2",10,3), C(g,135+i*210,1605,8,GOLD);
}

// ---------- small reusable pictures ----------
function printer(g,x,y,s,label,on,t){            // a Canon-style desk printer
 const k=g.appendChild(el("g",{transform:`translate(${x} ${y}) scale(${s})`}));
 R(k,-170,-50,340,120,"#cfd5dd","#2c3340",24,8); R(k,-150,-90,300,50,"#e8ecf1","#2c3340",16,7);   // body + paper tray
 R(k,-130,-20,260,34,"#10151d","#2c3340",8,5);                                                  // output slot
 C(k,134,34,9,on?"#37d67a":"#9aa3b1","#2c3340",4); R(k,60,24,50,20,"#aab3c0","#2c3340",6,3);
 if(label) T(k,0,106,label,30,NAVY);
 return k;
}
function sheet(g,x,y,w,h,rot,fill){ return el("rect",{x:x-w/2,y:y-h/2,width:w,height:h,rx:6,fill:fill||"#fff",stroke:"#2c3340","stroke-width":5,transform:`rotate(${rot||0} ${x} ${y})`},g) }
function check(g,x,y,r,t0,p){ const s=popB(p,t0,t0+.08); const k=el("g",{transform:`translate(${x} ${y}) scale(${s})`},g); C(k,0,0,r,"#2fcf63",INK,5); P(k,`M${-r*.45} 0 L${-r*.1} ${r*.38} L${r*.5} ${-r*.35}`,null,"#fff",r*.24); return k }
function magnifier(g,x,y,s,rot){ const k=el("g",{transform:`translate(${x} ${y}) rotate(${rot||0}) scale(${s})`},g); C(k,0,0,60,"rgba(255,255,255,.35)",INK,10); P(k,"M42 42 L100 100",null,INK,16); P(k,"M-30 -30 Q-10 -48 14 -42",null,"#fff",8); return k }
function box(g,x,y,s,open,t){ const k=el("g",{transform:`translate(${x} ${y}) scale(${s})`},g);
 R(k,-170,-60,340,170,"#d9a66a",INK,10,8); R(k,-170,-60,340,36,"#c98f52",INK,10,6);
 if(open){ P(k,"M-170 -60 L-210 -150 L-60 -150 L-40 -60 Z","#e0b179",INK,7); P(k,"M170 -60 L210 -150 L60 -150 L40 -60 Z","#e0b179",INK,7) } else { R(k,-175,-100,350,50,"#e0b179",INK,10,8); R(k,-30,-100,60,50,"#ff9fc7",INK,4) }
 return k }
function logo(g,x,y,s,p){ const k=el("g",{transform:`translate(${x} ${y}) scale(${s})`},g);
 T(k,0,-40,"Modern",92,NAVY).setAttribute("font-style","italic"); const pk=T(k,0,70,"Pink",150,PINK); pk.setAttribute("font-style","italic"); T(k,0,150,"Paper",92,NAVY).setAttribute("font-style","italic");
 for(let i=0;i<5;i++){const a=i*1.3+p*6; const sx=Math.cos(a)*300, sy=Math.sin(a*1.3)*160; P(k,`M${sx} ${sy-18} L${sx+5} ${sy-5} L${sx+18} ${sy} L${sx+5} ${sy+5} L${sx} ${sy+18} L${sx-5} ${sy+5} L${sx-18} ${sy} L${sx-5} ${sy-5} Z`,GOLD,null,0)}
 return k }

// ---------- one big illustration per step (drawn inside the white panel; panel origin 80,300; size 920x700) ----------
function stage(sc,p,lt,sd){
 const root=$("panel"); root.innerHTML="";
 const g=el("g",{},root);
 const S=(a,b)=>pop(p,a,b), B=(a,b)=>popB(p,a,b);
 if(sc==="intro"||sc==="outro"){
  logo(g,460,300,1+Math.sin(lt*2)*.015,lt);
  const xs=[170,370,570,770]; xs.forEach((x,i)=>{const b=B(.15+i*.1,.3+i*.1); const k=printer(g,x,560-Math.abs(Math.sin(lt*3+i))*10,.36*b,i==3?"labels":"printer",true); });
  if(sc==="outro"){ for(let i=0;i<9;i++){const hh=(lt*.5+i/9)%1; P(g,"M0 14 C-34 -18 -34 -46 -10 -46 C0 -46 0 -34 0 -30 C0 -34 0 -46 10 -46 C34 -46 34 -18 0 14Z",PINK,null,0,{transform:`translate(${80+i*95} ${640-hh*560}) scale(${.8+.4*((i*37)%3)/3})`,opacity:1-hh})}}
 }
 if(sc==="nozzle"){
  printer(g,230,400,1.15,"nozzle check",true);
  const out=B(.05,.2), gx=470+ (1-out)*-120;
  const ok=p<.45||p>.78, broken=p>=.45&&p<.62, cleaning=p>=.62&&p<=.78;
  const sh=sheet(g,640,380,300,360,0,"#fff");
  const cols=[["C","#19b4ff"],["M","#ff3d9a"],["Y","#ffd21a"],["K","#2c2c33"]];
  cols.forEach(([n,col],i)=>{ T(g,520+i*68,236,n,28,col); for(let j=0;j<7;j++){ const miss=(n==="M"&&j===3&&(broken||cleaning)); if(miss){ P(g,`M${500+i*68} ${262+j*30} h16 M${528+i*68} ${262+j*30} h14`,null,col,7,{opacity:.5}); continue } R(g,500+i*68,258+j*30,44,12,col,null,5) } });
  if(p<.45){ magnifier(g,650+Math.sin(lt*2)*40,360+Math.cos(lt*2)*20,1.1,0); check(g,830,250,34,.18,p) }
  if(broken){ P(g,"M610 392 L640 420 M640 392 L610 420",null,"#ff3b4a",10); T(g,700,540,"line missing!",40,"#ff3b4a"); }
  if(cleaning){ for(let i=0;i<6;i++){const a=lt*5+i*1.1; P(g,`M${580+i*40} ${330+Math.sin(a)*14} l8 -16 l8 16 l8 -16`,null,"#37b6ff",6)} T(g,700,540,"run a cleaning",40,"#2c7be5"); }
  if(p>.78){ check(g,830,250,40,.8,p); T(g,700,540,"all clear. print!",40,"#1b9e4a") }
 }
 if(sc==="bin"){
  // order bin (white basket) with slips
  const bi=B(.02,.18); const b=el("g",{transform:`translate(190 ${520+(1-bi)*200}) scale(${bi})`},g);
  R(b,-130,-60,260,170,"#fff",INK,18,8); for(let i=0;i<5;i++)R(b,-100+i*14,-100-i%2*12,110,80,["#ffd3e6","#fff2c4","#dbe9ff","#fff","#d9f2e3"][i],INK,6,4);
  R(b,-60,-6,120,36,"#eef2f6",null,8); T(b,0,20,"ORDERS",26,NAVY);
  // monitor with file list
  const m=el("g",{transform:`translate(580 ${360})`},g); R(m,-250,-210,500,330,"#2a3140",INK,26,8); R(m,-232,-192,464,290,"#fff");
  R(m,-40,120,80,60,"#aab3c0",INK,6,5); R(m,-120,176,240,26,"#cfd5dd",INK,12,6);
  const rows=["Smith - 120 - FLAT.indd","Jones - 30 - WHITE.indd","Lee - 50 - INVITE.indd","Reyes - 20 - KRAFT.indd"];
  const sel=p>.42;
  rows.forEach((r,i)=>{ const yy=-160+i*58; if(i===1&&sel) R(m,-222,yy-24,444,48,"#fff0f7",PINK,10,5); T(m,-208,yy+10,r,28,"#444b5a","start") });
  if(p>.5){ const q=B(.5,.62); const n=el("g",{transform:`translate(520 560) scale(${q})`},g); R(n,-150,-48,300,96,PINK,INK,48,6); T(n,0,12,"the number = how many",30,"#fff"); }
  if(p>.64){ const q=B(.64,.78); const n=el("g",{transform:`translate(520 660) scale(${q})`},g); R(n,-170,-48,340,96,NAVY,INK,48,6); T(n,0,12,"the last word = style / color",28,"#fff"); }
 }
 if(sc==="paper"){
  printer(g,460,380,1.7,"",true);
  const k=B(.05,.3); const y=120+ (1-k)*-300; // paper stack slides into the tray
  for(let i=0;i<4;i++) sheet(g,460,y-i*4+10,260,70,0,i==3?"#fff":"#fbf8f2");
  const a=B(.45,.6); const lab=(x,yy,txt,col,sc2)=>{const n=el("g",{transform:`translate(${x} ${yy}) scale(${sc2})`},g); R(n,-190,-40,380,80,col,INK,40,6); T(n,0,12,txt,32,"#fff")};
  lab(240,610,"cards → side printers",PINK,a); lab(700,610,"envelopes → extra printer",NAVY,B(.62,.78));
 }
 if(sc==="test"){
  const card=el("g",{transform:`translate(300 380) rotate(-4)`},g); R(card,-170,-230,340,460,"#fff","#2c3340",16,8); R(card,-148,-208,296,416,"none",GOLD,8,4);
  P(card,"M-60 -70 Q0 -150 60 -70 Q0 -20 -60 -70Z",PINK2,PINK,6); T(card,0,80,"Name Here",52,NAVY).setAttribute("font-style","italic"); R(card,-90,110,180,8,"#d7dce4",null,4); R(card,-60,136,120,8,"#e6e9ef",null,4);
  if(p<.9) magnifier(g,300+Math.sin(lt*1.6)*60,330+Math.cos(lt*1.3)*50,1.2,0);
  const items=["names","spelling","colors","edges"]; items.forEach((t,i)=>{ const q=B(.34+i*.12,.42+i*.12); const n=el("g",{transform:`translate(690 ${200+i*110}) scale(${q})`},g); R(n,-170,-40,340,80,"#fff","#e4d6c6",40,6); C(n,-122,0,28,"#2fcf63",INK,5); P(n,"M-136 0 L-124 12 L-106 -10",null,"#fff",8); T(n,18,12,t,38,NAVY) });
  const one=B(.05,.2); const bdg=el("g",{transform:`translate(150 120) scale(${one})`},g); C(bdg,0,0,70,PINK,INK,8); T(bdg,0,16,"1",90,"#fff"); T(bdg,0,52,"copy",28,"#fff");
 }
 if(sc==="run"){
  const prog=(x,y,delay,rate)=>{ const v=clamp((lt-delay)*rate,0,1); const n=Math.floor(v*40); printer(g,x,y,.82,"",true);
    R(g,x-150,y+90,300,30,"#eef0f4",INK,15,5); R(g,x-150,y+90,300*v,30,PINK,INK,15,5); T(g,x,y+175,`${n} / 40`,46,NAVY);
    for(let i=0;i<Math.min(5,Math.ceil(v*5));i++) sheet(g,x+10+i*4,y-100-i*6,200,46,0,"#fff") };
  prog(240,300,.3,.18); prog(680,300,1.6,.15);
  const tiles=[0,1,2]; tiles.forEach(i=>{ const q=B(.55+i*.1,.65+i*.1); const n=el("g",{transform:`translate(${240+i*220} 620) scale(${q})`},g); R(n,-90,-48,180,96,i<2?PINK:NAVY,INK,24,6); T(n,0,14,"40",62,"#fff") });
  T(g,460,545,"batches of about 40",36,NAVY);
 }
 if(sc==="env"){
  const cols=[["white","#fff"],["kraft","#c9a574"],["navy","#2c3a78"],["blush","#ffc9dc"],["sage","#bcd9c6"]];
  cols.forEach(([n,c],i)=>{ const q=B(.04+i*.04,.14+i*.04); const e=el("g",{transform:`translate(${110+i*175} 140) scale(${q})`},g); R(e,-70,-46,140,92,c,INK,8,6); P(e,"M-70 -46 L0 12 L70 -46",null,INK,6); T(e,0,86,n,26,NAVY) });
  // counting stack
  const cs=Math.floor(clamp((p-.12)*3.2,0,1)*20); for(let i=0;i<Math.min(8,Math.ceil(cs/3));i++) R(g,170,380-i*10,200,120,"#c9a574",INK,8,5);
  T(g,270,520,String(cs),110,PINK); T(g,270,590,"count them out",34,NAVY);
  // envelope with return address going through the extra printer
  printer(g,640,430,1.0,"extra printer",true);
  const q=B(.5,.68); const e=el("g",{transform:`translate(${640+(1-q)*-120} ${300+(1-q)*60}) scale(${.7+.3*q})`},g); R(e,-150,-90,300,180,"#c9a574",INK,10,7); P(e,"M-150 -90 L0 20 L150 -90",null,INK,6);
  if(p>.62){ R(e,-132,-76,92,8,"#3a2e22",null,3); R(e,-132,-58,70,8,"#3a2e22",null,3); R(e,-132,-40,84,8,"#3a2e22",null,3) }
  if(p>.7){ const t2=B(.7,.82); const n=el("g",{transform:`translate(560 640) scale(${t2})`},g); R(n,-300,-44,600,88,PINK,INK,44,6); T(n,0,12,"R A  =  return address",42,"#fff") }
 }
 if(sc==="check"){
  for(let i=0;i<8;i++) sheet(g,230,560-i*10,260,330,i%2?-1:1,"#fff");
  const n=Math.floor(clamp(p*1.2,0,1)*12);
  for(let i=0;i<n;i++){ const q=clamp((p*1.2-i/12)*12,0,1); const x=700+((i%3)-1)*150, y=520-Math.floor(i/3)*110; const k=el("g",{transform:`translate(${x} ${y}) scale(${.6*q})`},g); sheet(k,0,0,200,260,0,"#fff"); check(k,70,-90,50,0,1) }
  const f=el("g",{transform:`translate(${300+Math.sin(lt*3)*10} 330) rotate(${Math.sin(lt*2)*3})`},g); sheet(f,0,0,300,380,0,"#fff"); R(f,-120,-150,240,10,"#d7dce4",null,4);R(f,-120,-120,160,10,"#e6e9ef",null,4);R(f,-80,0,160,70,PINK2,PINK,12,5);
  magnifier(g,380+Math.sin(lt*3)*30,330,1.0,0);
  T(g,460,650,"every single sheet",50,NAVY);
 }
 if(sc==="pack"){
  const o=p<.7; box(g,460,420,1.4,o,lt);
  if(o){ for(let i=0;i<4;i++){ const q=clamp((p-.08-i*.1)*4,0,1); sheet(g,460+Math.sin(i)*6,260+(1-q)*-180+i*-3,200,260,-3+i*2,i==3?"#fff":"#fbf8f2").setAttribute("opacity",q) } }
  const hw=B(.35,.5); const n=el("g",{transform:`translate(700 640) scale(${hw})`},g); R(n,-210,-52,420,104,"#fff7d6",INK,52,7); T(n,10,14,"handle with care",40,"#b34700"); 
  P(n,"M-170 -22 H-134 L-152 12 V28 M-170 28 H-134",null,INK,6);
  if(p>.7){ const s2=B(.7,.85); const t2=el("g",{transform:`translate(460 ${250}) scale(${s2})`},g); T(t2,0,0,"packed",70,PINK) }
 }
 if(sc==="inserts"){
  box(g,460,520,1.2,true,lt);
  const cards=[["BRANDING",PINK,"#fff","send love"],["THANK YOU","#fff5e1",NAVY,"♥ thank you ♥"],["ACCURACY","#fff",NAVY,"checked ✓"]];
  cards.forEach(([t,fill,tc,sub],i)=>{ const q=B(.06+i*.24,.2+i*.24); const x=200+i*260, y=230+(1-q)*-200+Math.sin(lt*2+i)*8;
   const k=el("g",{transform:`translate(${x} ${y}) rotate(${(i-1)*6}) scale(${q})`},g); R(k,-100,-120,200,240,fill,"#2c3340",14,7); R(k,-82,-102,164,204,"none",GOLD,8,3); T(k,0,-10,t,26,tc); T(k,0,40,sub,24,tc); if(i===2){ P(k,"M-50 80 Q-20 55 0 80 T50 70",null,PINK,5) } });
  if(p>.7){ const q=B(.7,.86); const n=el("g",{transform:`translate(460 640) scale(${q})`},g); R(n,-340,-44,680,88,NAVY,INK,44,6); T(n,0,12,"the accuracy card shows who did your order",30,"#fff") }
 }
 if(sc==="label"){
  box(g,330,470,1.2,false,lt);
  const st=B(.1,.24); const s1=el("g",{transform:`translate(200 390) scale(${st}) rotate(${(1-st)*40})`},g); C(s1,0,0,50,PINK,"#fff",8); T(s1,0,12,"♥",50,"#fff");
  printer(g,720,330,.9,"label printer",true);
  const lb=clamp((p-.32)/.28,0,1), x=720+(330-720)*ease(lb), y=300+(500-300)*ease(lb), sc2=.6+.4*ease(lb);
  if(p>.3){ const k=el("g",{transform:`translate(${x} ${y}) scale(${sc2}) rotate(${(1-ease(lb))*-15})`},g); R(k,-110,-70,220,140,"#fff","#2c3340",8,6); for(let i=0;i<22;i++)R(k,-88+i*8,10,(i%3)+3,44,INK); R(k,-88,-48,100,10,"#9aa3b1",null,4); R(k,-88,-28,70,10,"#c8ced8",null,4) }
  if(p>.66){ const q=B(.66,.8); const n=el("g",{transform:`translate(460 640) scale(${q})`},g); R(n,-290,-52,580,104,"#2fcf63",INK,52,7); T(n,0,16,"ready to go!",60,"#fff") }
 }
 if(sc==="repeat"){
  const steps=["nozzle","order","paper","test","print","envelope","check","pack","insert","label"];
  const rot=lt*.35; const cx=460,cy=330,rr=235;
  C(g,cx,cy,rr,"none","#eadfd2",16);
  steps.forEach((s,i)=>{ const a=-Math.PI/2+i*2*Math.PI/10; const x=cx+Math.cos(a)*rr, y=cy+Math.sin(a)*rr; const act=Math.floor((lt*1.3)%10)===i; C(g,x,y,act?44:34,act?PINK:"#fff",NAVY,6); T(g,x,y+(act?14:11),String(i+1),act?44:34,act?"#fff":NAVY) });
  P(g,`M${cx+rr*.55} ${cy-rr*.9} q60 -10 60 50 l-26 -22 m26 22 l22 -34`,null,PINK,10);
  const order=1+Math.floor(lt*1.6); T(g,cx,cy-6,"ORDER",44,"#9aa3b1"); T(g,cx,cy+80,String(order),120,NAVY);
  for(let i=0;i<4;i++){ const q=((lt*.4+i*.25)%1); const bx=40+q*880; const k=el("g",{transform:`translate(${bx} 640) scale(.55)`},g); R(k,-120,-60,240,120,"#fff",INK,12,8); R(k,-80,-20,160,34,PINK2,null,8); }
  T(g,460,690,"same steps, next order",40,NAVY);
 }
}

// ---------- Sally: shirt colour, poses ----------
POSES.present={L:[-400,330,"open"],R:[400,330,"open"]};
POSES.point_up={L:[-300,640,"fist"],R:[420,-110,"point"]};

function frame(f){
 const t=f/TL.fps, cam=$("cam");
 const sc=TL.scenes.find(s=>t>=s.start&&t<s.end)||TL.scenes[TL.scenes.length-1];
 const lt=t-sc.start, p=clamp(lt/(sc.end-sc.start),0,1);
 stage(sc.look,p,lt,sc.end-sc.start);
 // expression + mouth
 const kf=TL.expr; let cur=kf[0],prev=kf[0]; for(const k of kf){ if(k.t<=t){prev=cur;cur=k} }
 const k=clamp((t-cur.t)/.18,0,1); const base=mixExpr(EXPR[cur.expr===prev.expr?cur.expr:prev.expr],EXPR[cur.expr],cur.expr===prev.expr?1:ease(k));
 const open=(TL.mouth[f]||0); setExpr(base,t,open,f);
 $("hairUp").setAttribute("display","none"); $("hairDown").setAttribute("display","inline"); $("scrunchie").setAttribute("display","none"); $("phoneG").setAttribute("display","none");
 drawArms(t,open);
 const bob=Math.sin(t*2.4)*7+open*8, tilt=(base.tilt||0)+Math.sin(t*1.7)*1.5;
 $("char").setAttribute("transform",`translate(540 ${1262+bob}) rotate(${tilt}) scale(.8)`);
 // gentle camera: slow push + small punch when a new step starts
 let z=1.0+lt*.004;
 for(const s of TL.scenes){ const d=t-s.start; if(d>=0&&d<.5) z+=.03*Math.exp(-d*8)*Math.cos(d*18) }
 cam.setAttribute("transform",`translate(540 960) scale(${z}) translate(-540 -960)`);
 // transitions
 let fl=0; for(const tr of TL.transitions){const d=t-tr.t; if(d>=-.1&&d<.3) fl=Math.max(fl,tr.flash*(1-Math.abs(d)/.3))}
 $("flash").setAttribute("opacity",clamp(fl,0,1));
 // step chip + progress dots
 const chip=$("chip"); chip.innerHTML=""; const label=sc.chip||"";
 const w=Math.max(420,label.length*30+90); R(chip,540-w/2,70,w,96,sc.look==="intro"||sc.look==="outro"?NAVY:PINK,INK,48,6); T(chip,540,136,label,46,"#fff");
 const stepIdx=Math.min(10,Math.max(0,["nozzle","bin","paper","test","run","env","check","pack","inserts","label"].indexOf(sc.look)+1));
 for(let i=0;i<10;i++){ C(chip,540-135+i*30,196,i+1<=stepIdx&&stepIdx>0?9:6,i+1===stepIdx?PINK:(i+1<stepIdx?NAVY:"#d7cfc6"),INK,3) }
 // captions
 const cg=$("caps"); cg.innerHTML=""; const ph=TL.phrases.find(p2=>t>=p2.s&&t<p2.e+.15);
 if(ph){ const words=ph.words, fs=64; const half=Math.ceil(words.length/2); const rows=words.length>4?[words.slice(0,half),words.slice(half)]:[words,[]];
  rows.forEach((row,ri)=>{ if(!row.length)return; const chars=row.map(w2=>w2.w).join(" ").length+2; const fsr=Math.min(fs,960/(chars*.58));
   const tx=el("text",{x:540,y:1700+ri*84,"text-anchor":"middle","font-size":fsr,fill:"#fff",stroke:INK,"stroke-width":14,"paint-order":"stroke","stroke-linejoin":"round"},cg);
   row.forEach((w2,wi)=>{ const act=t>=w2.s&&t<w2.e+.02; const sp=el("tspan",{fill:act?"#ffe14d":"#fff","font-size":act?fsr*1.1:fsr},tx); sp.textContent=w2.w+(wi<row.length-1?" ":"") }) }) }
}
window.init=function(tl){TL=tl;buildBgs();return true};
window.frame=frame;
