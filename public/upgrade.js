async function j(u,o={}){return fetch(u,{headers:{'Content-Type':'application/json'},...o}).then(r=>r.json())}
(async()=>{const me=await j('/api/me'); if(!me.auth){location='/';return;} const cats=[...new Set(me.skins.map(x=>x.category))];
const el=document.getElementById('upgrade'); el.innerHTML=`<div class=card><label>Шанс %<input id=ch type=number value=35></label><label>Поточна ціна <input id=fp type=number value=500></label><label>Категорія <select id=cat>${cats.map(c=>`<option>${c}</option>`)}</select></label><label>Цільовий скін <select id=ts></select></label><button onclick='go()'>Апгрейд</button><div>Результат чесний: win = random(0-100) < шанс.</div></div>`;
window.fill=()=>{ts.innerHTML=me.skins.filter(s=>s.category===cat.value).map(s=>`<option>${s.name}</option>`).join('')}; cat.onchange=fill; fill();
window.go=async()=>{const r=await j('/api/upgrade',{method:'POST',body:JSON.stringify({chance:Number(ch.value),from_price:Number(fp.value),to_skin:ts.value})}); alert(r.win?'Успіх':'Не пощастило')}
})();
