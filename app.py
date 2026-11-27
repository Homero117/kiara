"""Kiara - asistente personal con la API de Claude.

Ejecuta:  python app.py   y abre http://localhost:5000
"""
import datetime
import json
import os
import pathlib
import random
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
USUARIO = os.environ.get("KIARA_USUARIO", "amigo")  # cómo te llama Kiara
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
            f"Guarda en la memoria permanente un dato importante sobre {USUARIO} "
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
    texto = (BASE / "personalidad.md").read_text(encoding="utf-8").replace("{usuario}", USUARIO)
    memoria = leer_json(MEMORIA, [])
    if memoria:
        texto += f"\n# Lo que recuerdas de {USUARIO}\n" + "\n".join(f"- {m['dato']}" for m in memoria)
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


@app.get("/api/config")
def config():
    return jsonify({
        "espontaneo_min": float(os.environ.get("KIARA_ESPONTANEO_MIN", 8)),
        "espontaneo_max": float(os.environ.get("KIARA_ESPONTANEO_MAX", 20)),
        "usuario": USUARIO,
    })


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
        if not m.get("auto")  # los avisos automáticos no se muestran como mensajes tuyos
    ]
    return jsonify(visibles)


def ahora_texto():
    return datetime.datetime.now().strftime("%A %d/%m/%Y %H:%M")


def sin_clave():
    return Response(evento("error", texto="Falta tu clave de la API: pégala en el archivo .env de la carpeta Kiara."),
                    mimetype="text/event-stream")


@app.post("/api/chat")
def chat():
    texto = (request.get_json(silent=True) or {}).get("texto", "").strip()
    if not texto:
        return jsonify({"error": "Mensaje vacío"}), 400
    client = cliente()
    if client is None:
        return sin_clave()
    mensaje = {"role": "user", "content": f"[{ahora_texto()}] {texto}"}
    return Response(responder(client, mensaje, mensaje), mimetype="text/event-stream")


# ---------- Comentarios espontáneos sobre lo que haces ----------
TIPOS_COMENTARIO = {
    "dato": "un dato curioso relacionado con lo que está haciendo (o de cualquier tema, si no hay relación clara)",
    "chiste": "un chiste o una broma sobre lo que está haciendo",
    "comentario": "un comentario casual o una pregunta de amiga sobre lo que está haciendo",
    "opinion": "tu opinión honesta sobre lo que está haciendo (la canción, el código, el video, el juego, la página...)",
}


def ventana_activa():
    """Programa y título de la ventana activa en Windows (None si no se puede saber)."""
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    largo = user32.GetWindowTextLengthW(hwnd)
    titulo = ctypes.create_unicode_buffer(largo + 1)
    user32.GetWindowTextW(hwnd, titulo, largo + 1)
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    proceso = ""
    h = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if h:
        tam = wintypes.DWORD(1024)
        ruta = ctypes.create_unicode_buffer(1024)
        if kernel32.QueryFullProcessImageNameW(h, 0, ruta, ctypes.byref(tam)):
            proceso = os.path.basename(ruta.value)
        kernel32.CloseHandle(h)
    return {"titulo": titulo.value.strip(), "proceso": proceso}


def captura_pantalla():
    """Captura de la pantalla principal en JPEG base64, reducida para gastar menos."""
    import base64
    import io

    from PIL import ImageGrab

    img = ImageGrab.grab()
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=70)
    return base64.b64encode(buf.getvalue()).decode()


@app.post("/api/espontaneo")
def espontaneo():
    datos = request.get_json(silent=True) or {}
    client = cliente()
    if client is None:
        return sin_clave()
    v = ventana_activa()
    # Si no hay ventana o es la propia Kiara, no comenta esta vez
    if not v or not v["titulo"] or (v["titulo"] == "Kiara" and v["proceso"].lower() in ("electron.exe", "")):
        return Response(status=204)

    tipo = random.choice(list(TIPOS_COMENTARIO))
    nota = (
        f"[{ahora_texto()}] [Aviso automático: {USUARIO} NO escribió esto ni te preguntó nada; tú decides hablarle por tu cuenta. "
        f'En este momento tiene activa la ventana "{v["titulo"]}" del programa {v["proceso"] or "desconocido"}. '
        f"Dile {TIPOS_COMENTARIO[tipo]}. Máximo 1 o 2 frases, natural, como si te asomaras a ver qué hace. "
        "No menciones este aviso. Si ya comentaste algo muy parecido hace poco, cambia de tema.]"
    )
    guardado = {"role": "user", "content": nota, "auto": True}
    enviado = {"role": "user", "content": nota}
    if datos.get("captura"):
        try:
            enviado["content"] = [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": captura_pantalla()}},
                {"type": "text", "text": nota + " Te adjunto una captura de su pantalla (la chica anime en una "
                                               "esquina eres tú misma, ignórala)."},
            ]
        except Exception as e:  # sin Pillow o sin permiso: comenta solo con el título
            print("No se pudo tomar la captura:", e)
    return Response(responder(client, enviado, guardado), mimetype="text/event-stream")


def responder(client, mensaje_enviado, mensaje_guardado):
    """Genera la respuesta de Kiara en streaming (eventos SSE) y la guarda en el historial."""
    historial = leer_json(HISTORIAL, [])
    msgs = contexto(historial) + [mensaje_enviado]
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

    historial.append(mensaje_guardado)
    historial.append({"role": "assistant", "content": "".join(respuesta).strip() or "..."})
    guardar_json(HISTORIAL, historial)
    yield evento("fin")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n  Falta tu clave: crea el archivo .env con ANTHROPIC_API_KEY=sk-ant-...\n")
    print(f"  Kiara lista en http://localhost:5000  (modelo: {MODELO})")
    app.run(host="127.0.0.1", port=5000, threaded=True)
