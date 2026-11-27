"""Kiara - asistente personal con la API de Claude.

Ejecuta:  python app.py   y abre http://localhost:5000
"""
import datetime
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request

import anthropic
from flask import Flask, Response, jsonify, request, send_from_directory

BASE = pathlib.Path(__file__).parent
DATOS = BASE / "datos"
DATOS.mkdir(exist_ok=True)
HISTORIAL = DATOS / "historial.json"
MEMORIA = DATOS / "memoria.json"


def cargar_env():
    """Lee variables de un archivo .env junto a este script (ANTHROPIC_API_KEY=...)."""
    f = BASE / ".env"
    if not f.exists():
        return
    for linea in f.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if v:
                os.environ.setdefault(k.strip(), v)


cargar_env()

MODELO = os.environ.get("KIARA_MODELO", "claude-opus-5-5")
MAX_MENSAJES = 60  # cuántos mensajes recientes se mandan como contexto

_client = None


def cliente():
    """Crea el cliente al primer uso; relee .env por si pegaste la clave con el servidor abierto."""
    global _client
    if _client is None:
        cargar_env()
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return None
        _client = anthropic.Anthropic()
    return _client


app = Flask(__name__, static_folder="static")

HERRAMIENTAS = [
    {
        "name": "recordar",
        "description": (
            "Guarda en la memoria permanente un dato importante sobre Homero "
            "(gustos, planes, personas, proyectos, estado de ánimo) para recordarlo "
            "en futuras conversaciones. Escribe el dato como una frase corta y clara."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"dato": {"type": "string", "description": "El dato a recordar."}},
            "required": ["dato"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]


def leer_json(ruta, defecto):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return defecto


def guardar_json(ruta, datos):
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def prompt_sistema():
    texto = (BASE / "personalidad.md").read_text(encoding="utf-8")
    memoria = leer_json(MEMORIA, [])
    if memoria:
        texto += "\n# Lo que recuerdas de Homero\n" + "\n".join(f"- {m['dato']}" for m in memoria)
    return [{"type": "text", "text": texto, "cache_control": {"type": "ephemeral"}}]


def contexto(historial):
    """Últimos mensajes, empezando siempre por un mensaje del usuario."""
    msgs = historial[-MAX_MENSAJES:]
    while msgs and msgs[0]["role"] != "user":
        msgs = msgs[1:]
    return [{"role": m["role"], "content": m["content"]} for m in msgs]


def ejecutar_herramienta(bloque):
    if bloque.name == "recordar" and isinstance(bloque.input, dict) and isinstance(bloque.input.get("dato"), str):
        memoria = leer_json(MEMORIA, [])
        memoria.append({"dato": bloque.input["dato"].strip(), "fecha": datetime.date.today().isoformat()})
        guardar_json(MEMORIA, memoria)
        return {"type": "tool_result", "tool_use_id": bloque.id, "content": "Guardado."}
    return {"type": "tool_result", "tool_use_id": bloque.id, "content": "Entrada inválida.", "is_error": True}


def evento(tipo, **datos):
    return f"data: {json.dumps({'tipo': tipo, **datos}, ensure_ascii=False)}\n\n"


# ---------- Voz con ElevenLabs ----------
ELEVEN_API = "https://api.elevenlabs.io"
_voz = {"id": None, "nombre": None}


def eleven_pedir(ruta, cuerpo=None):
    req = urllib.request.Request(
        ELEVEN_API + ruta,
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
        method="POST" if cuerpo is not None else "GET",
    )
    return urllib.request.urlopen(req, timeout=30)


def voz_eleven():
    """Devuelve (voice_id, nombre) o (None, motivo). Usa ELEVENLABS_VOICE_ID o busca la voz por nombre."""
    cargar_env()
    if not os.environ.get("ELEVENLABS_API_KEY"):
        return None, "Falta ELEVENLABS_API_KEY en .env"
    if _voz["id"]:
        return _voz["id"], _voz["nombre"]
    if os.environ.get("ELEVENLABS_VOICE_ID"):
        _voz.update(id=os.environ["ELEVENLABS_VOICE_ID"], nombre=os.environ.get("ELEVENLABS_VOZ", "personalizada"))
        return _voz["id"], _voz["nombre"]
    buscar = os.environ.get("ELEVENLABS_VOZ", "Liz")
    try:
        with eleven_pedir("/v2/voices?" + urllib.parse.urlencode({"search": buscar, "page_size": 50})) as r:
            voces = json.load(r).get("voices", [])
    except urllib.error.HTTPError as e:
        return None, f"ElevenLabs respondió {e.code} al buscar la voz (¿clave correcta?)"
    except urllib.error.URLError:
        return None, "No hay conexión con ElevenLabs"
    if not voces:
        return None, f'No encontré la voz "{buscar}" en tu cuenta. Agrégala a "My Voices" en ElevenLabs.'
    # Prefiere la que diga "Sweet" o "Storyteller" en el nombre
    voces.sort(key=lambda v: ("sweet" not in v["name"].lower(), "storyteller" not in v["name"].lower()))
    _voz.update(id=voces[0]["voice_id"], nombre=voces[0]["name"])
    return _voz["id"], _voz["nombre"]


@app.get("/api/voz/estado")
def voz_estado():
    vid, info = voz_eleven()
    return jsonify({"activa": bool(vid), "voz": info if vid else None, "motivo": None if vid else info})


@app.post("/api/voz")
def voz():
    texto = (request.get_json(silent=True) or {}).get("texto", "").strip()
    vid, info = voz_eleven()
    if not vid:
        return jsonify({"error": info}), 503
    if not texto:
        return jsonify({"error": "Texto vacío"}), 400
    cuerpo = {
        "text": texto,
        "model_id": os.environ.get("ELEVENLABS_MODELO", "eleven_multilingual_v2"),
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3},
    }
    try:
        with eleven_pedir(f"/v1/text-to-speech/{vid}?output_format=mp3_44100_128", cuerpo) as r:
            audio = r.read()
    except urllib.error.HTTPError as e:
        detalle = e.read().decode(errors="replace")[:300]
        return jsonify({"error": f"ElevenLabs {e.code}: {detalle}"}), 502
    except urllib.error.URLError:
        return jsonify({"error": "No hay conexión con ElevenLabs"}), 502
    return Response(audio, mimetype="audio/mpeg")


@app.get("/")
def inicio():
    return send_from_directory(BASE / "static", "index.html")


@app.get("/api/historial")
def ver_historial():
    historial = leer_json(HISTORIAL, [])
    visibles = [
        {"role": m["role"], "texto": m["content"].split("] ", 1)[-1] if m["role"] == "user" else m["content"]}
        for m in historial[-40:]
    ]
    return jsonify(visibles)


@app.post("/api/chat")
def chat():
    texto = (request.get_json(silent=True) or {}).get("texto", "").strip()
    if not texto:
        return jsonify({"error": "Mensaje vacío"}), 400

    ahora = datetime.datetime.now().strftime("%A %d/%m/%Y %H:%M")
    mensaje_usuario = {"role": "user", "content": f"[{ahora}] {texto}"}

    client = cliente()
    if client is None:
        return Response(evento("error", texto="Falta tu clave de la API: pégala en el archivo .env de la carpeta Kiara."),
                        mimetype="text/event-stream")

    def generar():
        historial = leer_json(HISTORIAL, [])
        msgs = contexto(historial) + [mensaje_usuario]
        respuesta = []
        try:
            for _ in range(5):  # máximo 5 vueltas de herramientas por mensaje
                with client.beta.messages.stream(
                    model=MODELO,
                    max_tokens=4000,
                    system=prompt_sistema(),
                    messages=msgs,
                    tools=HERRAMIENTAS,
                    output_config={"effort": "low"},
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                ) as stream:
                    for trozo in stream.text_stream:
                        respuesta.append(trozo)
                        yield evento("texto", texto=trozo)
                    final = stream.get_final_message()

                if final.stop_reason == "refusal":
                    aviso = "Uy, de eso no puedo hablar. ¿Cambiamos de tema?"
                    respuesta.append(aviso)
                    yield evento("texto", texto=aviso)
                    break
                if final.stop_reason != "tool_use":
                    break

                msgs.append({"role": "assistant", "content": final.content})
                resultados = [ejecutar_herramienta(b) for b in final.content if b.type == "tool_use"]
                msgs.append({"role": "user", "content": resultados})
                yield evento("memoria")
        except anthropic.AuthenticationError:
            yield evento("error", texto="La clave de la API no es válida. Revisa el archivo .env")
            return
        except anthropic.RateLimitError:
            yield evento("error", texto="Demasiadas peticiones, espera un momento.")
            return
        except anthropic.APIStatusError as e:
            yield evento("error", texto=f"Error de la API ({e.status_code}): {e.message}")
            return
        except anthropic.APIConnectionError:
            yield evento("error", texto="No hay conexión con la API. ¿Tienes internet?")
            return

        historial.append(mensaje_usuario)
        historial.append({"role": "assistant", "content": "".join(respuesta).strip() or "..."})
        guardar_json(HISTORIAL, historial)
        yield evento("fin")

    return Response(generar(), mimetype="text/event-stream")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n  Falta tu clave: crea el archivo .env con ANTHROPIC_API_KEY=sk-ant-...\n")
    print(f"  Kiara lista en http://localhost:5000  (modelo: {MODELO})")
    app.run(host="127.0.0.1", port=5000, threaded=True)
