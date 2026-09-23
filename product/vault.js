(function(){
  // storage that never breaks the page
  const store={get(k){try{return localStorage.getItem('slv:'+k)}catch(e){return null}},
    set(k,v){try{localStorage.setItem('slv:'+k,v)}catch(e){}}};
  const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];

  // drawer
  const drawer=$('#drawer'), scrim=$('#scrim');
  const open=()=>{drawer.classList.add('open');scrim.classList.add('on');drawer.setAttribute('aria-hidden','false')};
  const close=()=>{drawer.classList.remove('open');scrim.classList.remove('on');drawer.setAttribute('aria-hidden','true')};
  $('#menuBtn').onclick=open; $('#closeBtn').onclick=close; scrim.onclick=close;
  drawer.addEventListener('click',e=>{if(e.target.closest('a'))close()});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});

  // saved inputs
  $$('[data-save]').forEach(el=>{
    const k=el.dataset.save, v=store.get(k);
    if(el.type==='checkbox'){el.checked=v==='1';el.addEventListener('change',()=>{store.set(k,el.checked?'1':'0');refresh()})}
    else{if(v!==null)el.value=v;el.addEventListener('input',()=>{store.set(k,el.value);refresh()})}
  });

  function refresh(){
    const tried=$$('[data-save^="tried-"]').filter(x=>x.checked).length;
    $('#progN').textContent=tried; $('#progBar').style.width=(tried/TOTAL*100)+'%';
    const favs=$$('[data-fav]').filter(x=>x.checked).map(x=>FAVS[x.dataset.fav]);
    $('#favList').innerHTML=favs.length?favs.map(f=>`<a href="#${f.id}">${f.t}<small>${f.c}</small></a>`).join('')
      :'<p class="muted">No favorites yet. Tap ★ Favorite on any hack.</p>';
    const ws=$$('.w').map(x=>parseFloat(x.value)).filter(n=>!isNaN(n));
    const avg=ws.length?ws.reduce((a,b)=>a+b,0)/ws.length:null;
    $('#avgNow').textContent=avg?avg.toFixed(1):'—';
    const last=parseFloat($('#lastWeek').value);
    $('#avgDiff').textContent=(avg&&!isNaN(last))?`Change vs last week: ${(avg-last>0?'+':'')}${(avg-last).toFixed(1)} — ${Math.abs(avg-last)<0.3?'steady. Maintenance is working.':avg<last?'trending down. Keep going.':'up a little. Check your anchor habits — no panic.'}`:'';
  }
  $('#newWeek').onclick=()=>{
    const cur=$('#avgNow').textContent; if(cur!=='—'){$('#lastWeek').value=cur;store.set('w-last',cur)}
    $$('.w').forEach(x=>{x.value='';store.set(x.dataset.save,'')}); refresh();
  };

  // search + tag filter
  let tag=null;
  const results=$('#results'), search=$('#search');
  function runSearch(){
    const q=search.value.trim().toLowerCase();
    if(!q&&!tag){results.innerHTML='';return}
    const words=q.split(/\s+/).filter(Boolean);
    const hits=INDEX.filter(h=>(!tag||h.tags.includes(tag))&&words.every(w=>h.x.includes(w)));
    results.innerHTML=hits.length?`<div class="dlabel">${hits.length} hack${hits.length>1?'s':''}${tag?' · '+TAGNAMES[tag]:''}</div>`+
      hits.slice(0,40).map(h=>`<a href="#${h.id}">#${String(h.n).padStart(3,'0')} ${h.t}<small>${h.c}</small></a>`).join('')
      :'<p class="none">No hacks found. Try another word.</p>';
  }
  search.addEventListener('input',runSearch);
  $$('.chip').forEach(c=>c.onclick=()=>{
    tag=tag===c.dataset.tag?null:c.dataset.tag;
    $$('.chip').forEach(x=>x.classList.toggle('on',x.dataset.tag===tag)); runSearch();
  });

  // quiz
  const showType=k=>{
    const t=QUIZ[k]; if(!t)return; const r=$('#quizResult');
    const ids=t.read, titles=t.readTitles;
    r.innerHTML=`<div class="label" style="color:#FFC2CF">Your eating type</div><h3>${t.emoji} ${t.name}</h3><p>${t.desc}</p><p><b>${t.first}</b></p>
      <p>Read these Laws first:<br>${ids.map((id,i)=>`<a href="#${id}">${titles[i]}</a>`).join(' · ')}</p>`;
    r.hidden=false;
  };
  $('#quizForm').addEventListener('submit',e=>{
    e.preventDefault();
    const n=QUIZ?Object.keys(QUIZ):[]; const count={}; let answered=0;
    $$('#quizForm input:checked').forEach(i=>{count[i.value]=(count[i.value]||0)+1;answered++});
    if(answered<3){alert('Answer at least 3 questions first.');return}
    const best=n.sort((a,b)=>(count[b]||0)-(count[a]||0))[0];
    store.set('quiz',best); showType(best); $('#quizResult').scrollIntoView({behavior:'smooth',block:'center'});
  });
  if(store.get('quiz'))showType(store.get('quiz'));

  refresh();
})();
