/* get-lumic.com shared script: film players, scroll reveals, and links into closed <details>. Loaded at the end of <body> on every page. */
/* Film players: the "Why lumic" film in the hero and the overview film in #demo. Poster until the film comes near, muted
   autoplay inline while 40% of it is on screen, tap the film to pause or play. The Sound button starts the film again
   from 0 with sound and plays it once to the end; muted, it loops. One voice on the page at a time ('lumic:voice').
   Reduced motion: no autoplay, the poster and native controls. */
(function(){
  var still=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var apple=/Apple/.test(navigator.vendor||'');
  [].forEach.call(document.querySelectorAll('.fp'),function(f){
    var v=f.querySelector('video'),snd=f.querySelector('.snd');
    if(!v) return;
    var name=f.getAttribute('data-voice')||f.id||'film';
    var want=false,visible=false,userPaused=false,src={},url='';
    /* the file is set as the src attribute (Chrome ignores preload=none on an explicit load()); Safari takes the mp4 */
    [].forEach.call(v.querySelectorAll('source'),function(s){ src[/mp4/.test(s.type)?'mp4':'webm']=s.getAttribute('src'); });
    (apple?['mp4','webm']:['webm','mp4']).forEach(function(x){ if(!url&&src[x]&&v.canPlayType('video/'+x)) url=src[x]; });
    if(url) v.setAttribute('src',url);
    if(still){ v.controls=true; if(snd) snd.hidden=true; }
    function ui(){
      f.classList.toggle('paused',userPaused&&!still);
      if(snd){ snd.setAttribute('aria-pressed',want?'true':'false'); snd.title=want?'Turn sound off':'Turn sound on'; }
    }
    function play(){
      ui();
      if(still||!visible||userPaused) return;
      var pr=v.play();
      /* the browser refused (sound without a fresh tap, or iPhone Low Power Mode): show the play button; a tap plays it */
      if(pr&&pr.catch) pr.catch(function(e){ if(e&&e.name==='NotAllowedError'){ userPaused=true; ui(); } });
    }
    function mute(){ want=false; v.muted=true; ui(); }
    function poster(){ var ps=v.getAttribute('data-poster'); if(ps&&!v.getAttribute('poster')) v.poster=ps; }
    v.addEventListener('ended',function(){
      if(still) return;
      if(want){ userPaused=true; ui(); } else { try{ v.currentTime=0; }catch(e){} play(); }
    });
    document.addEventListener('lumic:voice',function(e){ if(e.detail!==name&&want) mute(); }); /* another film took the sound */
    if(snd) snd.addEventListener('click',function(e){
      e.stopPropagation();
      if(want){ mute(); return; }
      want=true; v.muted=false; userPaused=false;
      try{ v.currentTime=0; }catch(x){}
      document.dispatchEvent(new CustomEvent('lumic:voice',{detail:name}));
      ui();
      var pr=v.play(); if(pr&&pr.catch) pr.catch(function(){ mute(); });
    });
    f.addEventListener('click',function(e){
      if(still||(e.target.closest&&e.target.closest('.snd'))) return;
      if(v.paused){ userPaused=false; play(); } else { userPaused=true; v.pause(); ui(); }
    });
    /* phones and Data Saver: poster first, only the metadata ahead of play, so a cellular visit never pulls a whole film it
       may not watch; with Data Saver on, the film waits for a tap */
    var conn=navigator.connection||{},lite=conn.saveData||(window.matchMedia&&window.matchMedia('(max-width: 620px)').matches);
    if(conn.saveData&&!still){ userPaused=true; ui(); }
    var load=(still||lite)?'metadata':'auto';
    if(!('IntersectionObserver' in window)){ poster(); v.preload=load; visible=true; play(); return; }
    var nearIO=new IntersectionObserver(function(es){ if(es[0].isIntersecting){ poster(); v.preload=load; nearIO.disconnect(); } },{rootMargin:'800px 0px'});
    nearIO.observe(f);
    new IntersectionObserver(function(es){
      var vis=es[es.length-1].intersectionRatio>=.4;
      if(vis===visible) return;
      visible=vis;
      if(vis) play(); else v.pause();
    },{threshold:[0,.4]}).observe(f);
  });
})();

(function(){
  var doc = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduce) doc.classList.add('js');


  /* Scroll reveals (also reveal anything already passed, so jumps never leave blanks) */
  var rv = [].slice.call(document.querySelectorAll('.rv'));
  var ticking = false;
  function check(){
    ticking = false;
    var h = window.innerHeight;
    rv = rv.filter(function(el){
      if (el.getBoundingClientRect().top < h * 0.97) { el.classList.add('in'); return false; }
      return true;
    });
  }
  if (!reduce) {
    check();
    window.addEventListener('scroll', function(){ if (!ticking) { ticking = true; requestAnimationFrame(check); } }, {passive:true});
    window.addEventListener('resize', check);
  }


  /* A link to something inside a closed <details> (for example #sources) opens it first */
  function openTarget(){
    var id = location.hash.slice(1), el = id && document.getElementById(decodeURIComponent(id));
    var d = el && el.closest && el.closest('details');
    if (d && !d.open) { d.open = true; el.scrollIntoView(); }
  }
  openTarget();
  window.addEventListener('hashchange', openTarget);
})();

/* Checklist form: one email field. Posts to /api/checklist; on success the PDF link replaces the small print. */
(function(){
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  document.querySelectorAll('form.ck-form').forEach(function(f){
    var msg = f.parentNode.querySelector('[data-ck-msg]');
    f.addEventListener('submit', function(e){
      e.preventDefault();
      var email = f.email.value.trim();
      if (!EMAIL.test(email)) { msg.textContent = 'Enter a valid email address.'; f.email.focus(); return; }
      var btn = f.querySelector('button'); btn.disabled = true;
      fetch('/api/checklist', {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: email, website: f.website.value, page: f.page.value})})
        .then(function(r){ return r.json().then(function(j){ return {ok: r.ok, j: j}; }); })
        .then(function(x){
          if (!x.ok || !x.j.ok) { msg.textContent = 'Enter a valid email address.'; btn.disabled = false; return; }
          msg.innerHTML = 'Your checklist is ready: <a href="' + x.j.pdf + '" download>Download the PDF.</a>';
          var a = document.createElement('a'); a.href = x.j.pdf; a.download = ''; document.body.appendChild(a); a.click(); a.remove();
        })
        .catch(function(){ btn.disabled = false; f.submit(); });
    });
  });
})();
