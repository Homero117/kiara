# Cómo instalar Kiara (guía rápida)

Kiara es una asistente de IA con personalidad, un avatar anime animado y voz. Se queda en una esquina de tu pantalla, encima de tus programas, platica contigo y de vez en cuando comenta lo que estás haciendo.

**Tiempo:** unos 10 minutos. **Necesitas:** Windows 10 u 11 e internet.

---

## 1. Consigue tu clave de Claude (obligatoria)

Kiara usa la IA de Claude para pensar y contestar. Necesitas tu propia clave:

1. Entra a **[console.anthropic.com](https://console.anthropic.com)** y crea una cuenta.
2. Ve a **Settings → Billing** y carga saldo. Con **5 dólares** puedes probarla bastante.
3. Ve a **API Keys → Create Key**, ponle de nombre "Kiara" y **cópiala**. Empieza con `sk-ant-` y solo se muestra una vez.

> La clave de la API es distinta de la suscripción de Claude (Pro/Max): no es mensualidad, se cobra solo lo que uses.

### Voz bonita (opcional)

Sin esto, Kiara habla con la voz de Windows. Para que tenga la voz de **Liz**:

1. Entra a **[elevenlabs.io](https://elevenlabs.io)** y crea una cuenta (hay plan gratis).
2. En **Voices → Voice Library**, busca **"Liz - Sweet & Warm Storyteller"** y dale **Add to My Voices**.
3. En **Developers → API Keys**, crea una clave y cópiala.

## 2. Descarga Kiara

1. En la página del proyecto en GitHub, dale al botón verde **Code → Download ZIP**.
2. Descomprime el ZIP en una carpeta que no vayas a borrar, por ejemplo `Documentos\Kiara`.

## 3. Ejecuta el instalador

1. Abre la carpeta y haz **doble clic en `instalar.bat`**.
   - Si Windows dice *"Windows protegió tu PC"*, dale a **Más información → Ejecutar de todos modos**.
2. El instalador hace todo solo y te va preguntando:
   - **Si falta Python o Node.js**, ofrece instalarlos. Si lo hace, cierra la ventana y vuelve a abrir `instalar.bat`.
   - **Licencia de Live2D:** para descargar el avatar, escribe `s` para aceptar.
   - **Tu nombre:** cómo quieres que te llame Kiara.
   - **Tus claves:** pega la de Claude (clic derecho para pegar y Enter). No se ve mientras la pegas, es normal. La de ElevenLabs es opcional: Enter para saltarla.
   - **Modelo:** elige **1 (Haiku)** para probar. Es rápido y cuesta centavos.
3. Al final te pregunta si quieres abrirla. ¡Listo!

## 4. Úsala

| Para | Haz |
|---|---|
| Tenerla sobre tus programas | Doble clic en **`iniciar-escritorio.bat`** |
| Hablarle con el micrófono | Doble clic en **`iniciar.bat`** (se abre en el navegador; usa Chrome o Edge) |

**En modo escritorio**, pasa el mouse por arriba de Kiara y aparece una barra:

| Botón | Qué hace |
|---|---|
| ✥ | Arrástralo para moverla |
| ⌨️ | Abre el chat para escribirle |
| 🔊 | Activa o silencia su voz |
| 💬 | Que comente por su cuenta lo que haces (cada 8–20 min) |
| 📸 | Que vea una captura de tu pantalla al comentar (apagado por defecto) |
| ✕ | Cerrarla |

Tócala y reacciona. Mueve el mouse cerca y te sigue con la mirada.

## Privacidad

- Cuando comenta por su cuenta, Kiara envía a Claude **el nombre del programa y de la ventana** que tienes abiertos.
- Con 📸 encendido, también envía **una captura de tu pantalla**. Puede incluir cosas privadas, así que úsalo con cuidado.
- Tus conversaciones y lo que Kiara recuerda de ti se guardan **solo en tu computadora**, en la carpeta `datos`.
- **No compartas el archivo `.env`:** tiene tus claves.

## ¿Cuánto cuesta?

| Modelo | Por mensaje | Platicando diario un mes |
|---|---|---|
| Haiku 5.5 (recomendado para probar) | ~0.05 centavos de dólar | ~1 dólar |
| Opus 5.5 (más inteligente) | ~1–3 centavos de dólar | ~15–45 dólares |

Puedes poner un límite de gasto en console.anthropic.com para no llevarte sorpresas.

## Si algo falla

| Problema | Solución |
|---|---|
| Kiara dice *"Falta tu clave de la API"* | Abre el archivo `.env` con el Bloc de notas y pega tu clave después de `ANTHROPIC_API_KEY=` |
| Dice *"La clave de la API no es válida"* o *"Error de la API (400)"* | Revisa que copiaste bien la clave y que tu cuenta de Anthropic tiene saldo |
| Habla con voz de robot | No hay clave de ElevenLabs, o falta agregar a Liz a *My Voices* |
| Se ve un dibujo sencillo en vez de la chica anime | No se descargó el avatar: vuelve a correr `instalar.bat` y acepta la licencia |
| El micrófono no funciona | Úsalo con `iniciar.bat` en Chrome o Edge; en modo escritorio todavía no hay micrófono |
| No abre nada | Vuelve a correr `instalar.bat`; si no se resuelve, mándale una captura de la ventana a quien te compartió Kiara |

Para cambiar tu nombre, el modelo o las claves, vuelve a correr `instalar.bat` y dile que sí a reemplazar la configuración, o edita el archivo `.env`.

---

*El avatar es "Miara", modelo de muestra oficial de Live2D Inc., para uso personal. Kiara es un proyecto personal en etapa de prueba (v0.2).*
