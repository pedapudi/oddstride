const data=await fetch('./comparison.json').then(r=>r.json());
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let referenceMode='concept';
function refreshReference(){
 const key=window.currentProposal; const previous=referenceMode==='previous' && key!=='baseline';
 document.querySelector('#reference-image').src=previous?(data.proposals[key].previous_image||`${key}/design/iterations/${key==='compact'?'09':'08'}-studio.png`):data.reference;
 document.querySelector('#reference-image').alt=previous?'Previous body CAD before nose refinement':'Original studio concept';
 document.querySelector('#reference-caption').textContent=previous?'PREVIOUS BODY / CAD':'ORIGINAL STUDIO CONCEPT';
 document.querySelector('#reference-note').textContent=previous?'Same camera and stance':'Original body reference';
 for(const b of document.querySelectorAll('[data-reference]')){const on=b.dataset.reference===referenceMode;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));}
}
function choose(key){const p=data.proposals[key];if(!p)return;document.querySelector('#proposal-image').src=p.image;document.querySelector('#proposal-caption').textContent=p.title.toUpperCase()+' / CAD';document.querySelector('#detail-title').textContent=p.title;document.querySelector('#detail-label').textContent=p.label;document.querySelector('#detail-description').textContent=p.description;document.querySelector('#change-list').innerHTML=p.changes.map(x=>`<li>${esc(x)}</li>`).join('');document.querySelector('#proposal-links').innerHTML=p.links.map((x,i)=>`<a class="${i===0?'primary':''}" href="${esc(x.href)}" target="_blank">${esc(x.label)}</a>`).join('');for(const b of document.querySelectorAll('[data-proposal]')){const on=b.dataset.proposal===key;b.classList.toggle('active',on);b.setAttribute('aria-selected',String(on));}document.querySelector('#body-detail').hidden=!p.detail_image;if(p.detail_image)document.querySelector('#body-detail-image').src=p.detail_image;window.currentProposal=key;refreshReference();}
for(const b of document.querySelectorAll('[data-proposal]'))b.onclick=()=>choose(b.dataset.proposal);
document.querySelector('#metrics').innerHTML=data.metrics.map(r=>`<tr>${r.map((x,i)=>i?`<td>${esc(x)}</td>`:`<td>${esc(x)}</td>`).join('')}</tr>`).join('');
document.querySelector('#iteration-list').innerHTML=['compact','sculpted'].map(key=>{const p=data.proposals[key];return `<h3>${esc(p.title)}</h3><div class="iteration-row">${p.iterations.map((v,i)=>`<article class="iteration-card"><img src="${esc(v.image)}" alt="${esc(p.title)} geometry pass ${i+1}"><div class="text"><h4>${esc(v.title)}</h4><p>${esc(v.correction)}</p><p>${esc(v.remaining||'')}</p></div></article>`).join('')}</div>`}).join('');
for(const b of document.querySelectorAll('[data-reference]'))b.onclick=()=>{referenceMode=b.dataset.reference;refreshReference();};
document.querySelector('#limb-metrics').innerHTML=(data.limb_metrics||[]).map(r=>`<tr>${r.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('');
choose('sculpted');window.proposalReview={data,choose,refreshReference};
