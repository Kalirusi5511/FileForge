import html, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from .models import Pokemon
from .service import Service

svc = Service()

def page(title, body):
    css = "body{font-family:system-ui;margin:0;background:#f4f4f4;color:#222}" \
          "header{padding:18px 24px;background:#111;color:white}" \
          "main{max-width:1100px;margin:24px auto;padding:0 16px}" \
          ".card{background:white;border-radius:12px;padding:18px;margin-bottom:18px;box-shadow:0 2px 8px #0001}" \
          ".grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}" \
          ".slot{min-height:85px;background:#eee;border-radius:8px;padding:8px;font-size:13px}" \
          "input,button{padding:8px;border:1px solid #ccc;border-radius:7px}"
    return "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" \
           f"<title>{html.escape(title)}</title><style>{css}</style></head><body><header><b>Pokémon Preservation MVP</b></header><main>{body}</main></body></html>"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.home()
        elif self.path == "/download":
            data = json.dumps(svc.lib.to_dict(), indent=2, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Content-Disposition","attachment; filename=library.json")
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length","0"))
        q = parse_qs(self.rfile.read(n).decode())
        if self.path == "/add":
            p = Pokemon(
                species=q.get("species",["Unknown"])[0],
                nickname=q.get("nickname",[""])[0],
                generation=max(1,min(9,int(q.get("generation",["9"])[0]))),
                level=max(1,min(100,int(q.get("level",["1"])[0]))))
            svc.add_pokemon(p)
        elif self.path == "/box":
            svc.add_box(q.get("name",["New Box"])[0])
        elif self.path == "/delete":
            svc.delete_pokemon(q.get("id",[""])[0])
        elif self.path == "/backup":
            dest = svc.backup()
            self.respond(page("Backup", f"<div class='card'><h2>Backup erstellt</h2><p>{html.escape(str(dest))}</p><a href='/'>Zurück</a></div>"))
            return
        self.redirect()

    def redirect(self):
        self.send_response(303); self.send_header("Location","/"); self.end_headers()

    def respond(self, text, status=200):
        raw = text.encode()
        self.send_response(status)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers(); self.wfile.write(raw)

    def home(self):
        boxes = []
        for b in svc.lib.boxes:
            slots = []
            for pid in b.slots:
                p = svc.lib.pokemon.get(pid) if pid else None
                if p:
                    slots.append(
                        "<div class='slot'><b>" + html.escape(p.nickname or p.species) + "</b><br>" +
                        f"Gen {p.generation} · Lv {p.level}" +
                        "<form method='post' action='/delete'><input type='hidden' name='id' value='" +
                        html.escape(p.id) + "'><button>Entfernen</button></form></div>")
                else:
                    slots.append("<div class='slot'>leer</div>")
            boxes.append("<div class='card'><h2>"+html.escape(b.name)+"</h2><div class='grid'>"+"".join(slots)+"</div></div>")

        body = f"""
<div class='card'>
<h1>Deine Sammlung</h1>
<p>{len(svc.lib.pokemon)} Pokémon · {len(svc.lib.boxes)} Boxen</p>
<form method='post' action='/add'>
<input name='species' value='Pikachu' placeholder='Spezies'>
<input name='nickname' placeholder='Spitzname'>
<input name='generation' type='number' min='1' max='9' value='9'>
<input name='level' type='number' min='1' max='100' value='1'>
<button>Pokémon hinzufügen</button>
</form>
<form method='post' action='/box' style='margin-top:10px'>
<input name='name' placeholder='Neue Box'><button>Box erstellen</button>
</form>
</div>
<div class='card'>
<form method='post' action='/backup' style='display:inline'><button>Backup erstellen</button></form>
<a href='/download' style='margin-left:12px'>Bibliothek herunterladen</a>
</div>
""" + "".join(boxes)
        self.respond(page("Pokémon Preservation MVP", body))

def run():
    print("Pokémon Preservation MVP -> http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1",8765), Handler).serve_forever()
