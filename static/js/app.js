document.addEventListener('DOMContentLoaded',()=>{
 const links=[...document.querySelectorAll('[data-nav]')];
 let chosen=links.filter(a=>location.pathname===a.dataset.nav || (a.dataset.nav!='/manage/' && location.pathname.startsWith(a.dataset.nav))).sort((a,b)=>b.dataset.nav.length-a.dataset.nav.length)[0];
 if(chosen){chosen.classList.add('active');chosen.setAttribute('aria-current','page');}
 const menu=document.querySelector('.menu-button'),sidebar=document.querySelector('.sidebar');
 menu?.addEventListener('click',()=>{let open=sidebar.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));});
 document.querySelector('.close-menu')?.addEventListener('click',()=>{sidebar.classList.remove('open');menu?.setAttribute('aria-expanded','false');});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){sidebar?.classList.remove('open');menu?.setAttribute('aria-expanded','false');}});
 document.querySelectorAll('[data-prompt]').forEach(b=>b.addEventListener('click',()=>{const q=document.querySelector('#id_question');q.value=b.dataset.prompt;q.focus();}));
 document.querySelectorAll('form').forEach(form=>form.addEventListener('submit',()=>{const b=form.querySelector('[data-loading]');if(b){b.disabled=true;b.textContent=b.dataset.loading;}}));
 document.querySelector('.copy-answer')?.addEventListener('click',async e=>{try{await navigator.clipboard.writeText(document.querySelector('#answer-text').textContent);e.target.textContent='Copied ✓';}catch{e.target.textContent='Select the answer to copy it';}});
});
