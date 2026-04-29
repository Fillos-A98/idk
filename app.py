import json
import os
import secrets
import sqlite3
from http import cookies
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB = 'game.db'
SESSIONS = {}

SKINS = [
    ("Mil-Spec", "P250 | Valence", 48, "https://steamcommunity-a.akamaihd.net/economy/image/class/730/3077972088/330x192"),
    ("Restricted", "AK-47 | Ice Coaled", 360, "https://steamcommunity-a.akamaihd.net/economy/image/class/730/4582713970/330x192"),
    ("Classified", "M4A1-S | Player Two", 1950, "https://steamcommunity-a.akamaihd.net/economy/image/class/730/2069777122/330x192"),
    ("Covert", "AWP | Asiimov", 5600, "https://steamcommunity-a.akamaihd.net/economy/image/class/730/479216206/330x192"),
    ("Knife", "★ Karambit | Doppler", 49800, "https://steamcommunity-a.akamaihd.net/economy/image/class/730/2102485320/330x192"),
]

CASES = {
    "Starter": {"price": 120, "weights": [55, 25, 12, 7, 1]},
    "Pro": {"price": 650, "weights": [35, 30, 20, 12, 3]},
    "Elite": {"price": 2500, "weights": [20, 30, 25, 20, 5]},
}

def db():
    return sqlite3.connect(DB)

def init_db():
    con = db(); cur = con.cursor()
    cur.execute('create table if not exists users(id integer primary key, username text unique, password text, balance int default 0, is_admin int default 0)')
    cur.execute('create table if not exists inventory(id integer primary key, user_id int, skin_name text, category text, price int, image text)')
    con.commit(); con.close()


def json_response(h, code, payload):
    h.send_response(code)
    h.send_header('Content-Type','application/json; charset=utf-8')
    h.end_headers()
    h.wfile.write(json.dumps(payload).encode())


def get_user(handler):
    c = cookies.SimpleCookie(handler.headers.get('Cookie'))
    sid = c.get('sid')
    if not sid or sid.value not in SESSIONS:
        return None
    uid = SESSIONS[sid.value]
    con=db(); cur=con.cursor(); cur.execute('select id,username,balance,is_admin from users where id=?',(uid,)); row=cur.fetchone(); con.close()
    return row

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path).path
        if p == '/' or p.endswith('.html') or p.endswith('.css') or p.endswith('.js'):
            fp = 'public/index.html' if p=='/' else 'public'+p
            if not os.path.exists(fp): self.send_error(404); return
            ctype='text/html' if fp.endswith('.html') else ('text/css' if fp.endswith('.css') else 'text/javascript')
            self.send_response(200); self.send_header('Content-Type',ctype+'; charset=utf-8'); self.end_headers(); self.wfile.write(open(fp,'rb').read()); return
        if p == '/api/me':
            u=get_user(self)
            if not u: return json_response(self,200,{"auth":False})
            uid,un,b,adm=u
            con=db(); cur=con.cursor(); cur.execute('select skin_name,category,price,image from inventory where user_id=?',(uid,)); inv=[{"name":r[0],"category":r[1],"price":r[2],"image":r[3]} for r in cur.fetchall()]; con.close()
            return json_response(self,200,{"auth":True,"user":{"id":uid,"username":un,"balance":b,"is_admin":bool(adm)},"inventory":inv,"skins":[{"category":s[0],"name":s[1],"price":s[2],"image":s[3]} for s in SKINS],"cases":CASES})
        self.send_error(404)

    def do_POST(self):
        p = urlparse(self.path).path
        ln = int(self.headers.get('Content-Length','0')); body = json.loads(self.rfile.read(ln) or b'{}')
        if p=='/api/register':
            con=db(); cur=con.cursor()
            try:
                cur.execute('insert into users(username,password,balance) values(?,?,?)',(body['username'],body['password'],500)); con.commit()
            except Exception:
                con.close(); return json_response(self,400,{"error":"username taken"})
            con.close(); return json_response(self,200,{"ok":True})
        if p=='/api/login':
            con=db(); cur=con.cursor(); cur.execute('select id,password from users where username=?',(body['username'],)); row=cur.fetchone(); con.close()
            if not row or row[1]!=body['password']: return json_response(self,401,{"error":"bad creds"})
            sid=secrets.token_hex(16); SESSIONS[sid]=row[0]
            self.send_response(200); self.send_header('Set-Cookie',f'sid={sid}; Path=/; HttpOnly'); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b'{"ok":true}') ; return
        u=get_user(self)
        if not u: return json_response(self,401,{"error":"login first"})
        uid,_,bal,is_admin=u
        if p=='/api/open_case':
            case=body['case']; data=CASES.get(case)
            if not data: return json_response(self,400,{"error":"bad case"})
            if bal < data['price']: return json_response(self,400,{"error":"not enough funds"})
            import random
            idx=random.choices(range(len(SKINS)),weights=data['weights'])[0]; s=SKINS[idx]
            con=db(); cur=con.cursor(); cur.execute('update users set balance=balance-? where id=?',(data['price'],uid)); cur.execute('insert into inventory(user_id,skin_name,category,price,image) values(?,?,?,?,?)',(uid,s[1],s[0],s[2],s[3])); con.commit(); con.close()
            return json_response(self,200,{"won":{"category":s[0],"name":s[1],"price":s[2],"image":s[3]}})
        if p=='/api/upgrade':
            chance=float(body['chance']); from_price=int(body['from_price']); to_skin=body['to_skin']
            import random
            win=random.random()*100<chance
            con=db(); cur=con.cursor()
            if win:
                s=next((x for x in SKINS if x[1]==to_skin),None)
                cur.execute('insert into inventory(user_id,skin_name,category,price,image) values(?,?,?,?,?)',(uid,s[1],s[0],s[2],s[3]))
            con.commit(); con.close()
            return json_response(self,200,{"win":win})
        if p=='/api/admin/grant':
            if not is_admin: return json_response(self,403,{"error":"admin only"})
            con=db(); cur=con.cursor(); cur.execute('update users set balance=balance+? where username=?',(int(body.get('money',0)),body['username']))
            for sn in body.get('skins',[]):
                s=next((x for x in SKINS if x[1]==sn),None)
                if s: cur.execute('insert into inventory(user_id,skin_name,category,price,image) select id,?,?,?,? from users where username=?',(s[1],s[0],s[2],s[3],body['username']))
            con.commit(); con.close(); return json_response(self,200,{"ok":True})
        if p=='/api/admin/make_me_admin':
            con=db(); cur=con.cursor(); cur.execute('update users set is_admin=1 where id=?',(uid,)); con.commit(); con.close(); return json_response(self,200,{"ok":True})
        return json_response(self,404,{"error":"not found"})

if __name__ == '__main__':
    init_db()
    HTTPServer(('0.0.0.0', 8080), H).serve_forever()
