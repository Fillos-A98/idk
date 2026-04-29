async function j(u,o={}){return fetch(u,{headers:{'Content-Type':'application/json'},...o}).then(r=>r.json())}
(async()=>{const me=await j('/api/me'); if(!me.auth){location='/';return;} const el=document.getElementById('admin');
el.innerHTML=`<div class=card><button onclick='meAdmin()'>Зробити мій аккаунт адміном (через БД endpoint)</button></div><div class=card><input id=u placeholder='username'><input id=m type=number placeholder='грн'><input id=s placeholder='скіни через кому'><button onclick='grant()'>Видати кошти/скіни</button></div>`;
window.meAdmin=async()=>alert(JSON.stringify(await j('/api/admin/make_me_admin',{method:'POST',body:'{}'})));
window.grant=async()=>alert(JSON.stringify(await j('/api/admin/grant',{method:'POST',body:JSON.stringify({username:u.value,money:Number(m.value||0),skins:s.value.split(',').map(x=>x.trim()).filter(Boolean)})})));
})();
