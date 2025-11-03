from flask import Flask, request, jsonify, render_template_string
import json, os

app = Flask(__name__)

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "variables_catalog.json")
with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    CATALOG = json.load(f)

def search_variable(q: str):
    q = q.lower().strip()
    for v in CATALOG:
        tokens = [v["name"].lower()] + [a.lower() for a in v.get("aliases", [])]
        if q in " ".join(tokens):
            return v
    for v in CATALOG:
        if q in v["name"].lower():
            return v
    for v in CATALOG:
        if any(q in a.lower() for a in v.get("aliases", [])):
            return v
    return None

def pretty_variable(v):
    return (
        f"**{v['name']}**\n"
        f"- Concepto: {v['concept']}\n"
        f"- Fuente: {v['source_name']} ({v['source_url']})\n"
        f"- Unidad de medida: {v['unit']}\n"
        f"- Tipificación: {v['type']}\n"
        f"- Escala de medición: {v['scale']}\n"
        f"- Campos de aplicación: {', '.join(v['applications'])}"
    )

def help_text():
    return (
        "Puedo ayudar a identificar variables del comercio internacional y su ficha:\n"
        "- Escriba el nombre de una variable: 'Valor FOB', 'Código HS', 'Incoterm', 'Tiempo de tránsito', etc.\n"
        "- Escriba 'lista' para ver todas las variables.\n"
        "También explico tipificación (cualitativa/cuantitativa; discreta/continua) y escalas (nominal, ordinal, intervalo, razón)."
    )

@app.post("/chat")
def chat():
    data = request.get_json(force=True)
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"reply": "Escriba el nombre de una variable o 'lista' para ver opciones."})
    low = msg.lower()
    if low in ["ayuda", "help", "¿qué puedes hacer?", "que puedes hacer", "menu", "menú"]:
        return jsonify({"reply": help_text()})
    if "lista" in low or "variables" in low:
        names = [v["name"] for v in CATALOG]
        return jsonify({"reply": "Variables disponibles:\n- " + "\n- ".join(names)})
    if any(w in low for w in ["cualitativa","cuantitativa","escala","discreta","continua"]):
        return jsonify({"reply": (
            "Tipificación:\n"
            "- Cualitativa nominal: categorías sin orden (p. ej., Incoterm, país).\n"
            "- Cualitativa ordinal: categorías con orden (p. ej., nivel de prioridad).\n"
            "- Cuantitativa discreta: conteos enteros (p. ej., tamaño de pedido).\n"
            "- Cuantitativa continua: valores en un intervalo (p. ej., peso, tiempo).\n\n"
            "Escalas de medición:\n"
            "- Nominal: etiquetas (sin orden).\n"
            "- Ordinal: orden sin distancia fija.\n"
            "- Intervalo: diferencias significativas, cero arbitrario (p. ej., °C).\n"
            "- Razón: cero absoluto, proporciones válidas (p. ej., USD, kg, días)."
        )})
    v = search_variable(low)
    if v:
        return jsonify({"reply": pretty_variable(v)})
    return jsonify({"reply": "No encontré esa variable. Escriba 'lista' para ver alternativas o intente con otro nombre."})

HTML = """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Chatbot · Variables de comercio internacional</title>
<style>
body{font-family:system-ui,Segoe UI,Roboto,Arial;margin:0;background:#f6f7fb}
header{background:#0f172a;color:white;padding:16px 20px;font-size:18px}
main{max-width:820px;margin:20px auto;background:white;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.06);padding:16px}
#log{height:520px;overflow:auto;border:1px solid #e5e7eb;border-radius:12px;padding:12px;display:flex;flex-direction:column}
.msg{margin:8px 0;padding:10px 12px;border-radius:12px;max-width:82%;white-space:pre-wrap}
.user{background:#e0f2fe;align-self:flex-end}
.bot{background:#eef2ff;align-self:flex-start}
.row{display:flex;gap:8px;margin-top:12px}
input[type=text]{flex:1;padding:12px;border:1px solid #d1d5db;border-radius:10px;font-size:16px}
button{padding:12px 16px;border:0;border-radius:10px;background:#4f46e5;color:white;font-weight:600;cursor:pointer}
.small{color:#6b7280;font-size:12px;margin-top:8px}
</style>
</head>
<body>
<header>Chatbot · Variables de comercio internacional</header>
<main>
  <div id="log"></div>
  <div class="row">
    <input id="txt" type="text" placeholder="Escriba: 'Valor FOB', 'Código HS', 'Tiempo de tránsito'… o 'lista'." />
    <button id="send">Enviar</button>
  </div>
  <div class="small">Sugerencia: 'Valor CIF', 'Incoterm', 'Arancel ad valorem', 'Tipo de cambio'.</div>
</main>
<script>
const log = document.getElementById('log');
const txt = document.getElementById('txt');
const send = document.getElementById('send');

function add(role, text){
  const d = document.createElement('div');
  d.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

async function ask(){
  const m = txt.value.trim();
  if(!m) return;
  add('user', m);
  txt.value='';
  try{
    const r = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:m})});
    const j = await r.json();
    add('bot', j.reply || 'Sin respuesta');
  }catch(e){
    add('bot', 'Error de conexión');
  }
}
send.onclick = ask;
txt.addEventListener('keydown', e => { if(e.key === 'Enter') ask(); });

add('bot','Hola. Escriba el nombre de una variable o "lista" para ver todas. También explico tipificación y escalas.');
</script>
</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

