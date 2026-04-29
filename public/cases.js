async function j(u,o={}){return fetch(u,{headers:{'Content-Type':'application/json'},...o}).then(r=>r.json())}
(async()=>{const me=await j('/api/me'); if(!me.auth){location='/';return;} const el=document.getElementById('cases');
el.innerHTML=Object.entries(me.cases).map(([n,v])=>`<div class=card><h3>${n} — ${v.price} грн</h3><button onclick="openCase('${n}')">Відкрити</button><div id='a${n}'></div></div>`).join('');
window.openCase=async(n)=>{const anim=document.getElementById('a'+n); anim.innerHTML=`<div class='roller'><div class='track'>${me.skins.concat(me.skins).map(s=>`<div class=card><img src='${s.image}'><small>${s.name}</small></div>`).join('')}</div></div>`; setTimeout(async()=>{const r=await j('/api/open_case',{method:'POST',body:JSON.stringify({case:n})}); alert(r.won?`Випав: ${r.won.name} (${r.won.price} грн)`:(r.error));},1900)}
})();
