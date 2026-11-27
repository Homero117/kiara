// Kiara de escritorio: ventana transparente, sin marco y siempre encima de tus programas.
const { app, BrowserWindow, ipcMain, screen, session, dialog } = require("electron");
const { spawn } = require("child_process");
const http = require("http");
const path = require("path");

const URL_KIARA = "http://127.0.0.1:5000";
let servidor = null;
let ventana = null;

// Que pueda hablar sola (comentarios espontáneos) sin esperar un clic
app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");

function servidorVivo() {
  return new Promise(listo => {
    const req = http.get(URL_KIARA + "/api/config", r => { r.resume(); listo(r.statusCode === 200); });
    req.on("error", () => listo(false));
    req.setTimeout(1500, () => { req.destroy(); listo(false); });
  });
}

// Usa el servidor si ya está abierto; si no, arranca python app.py
async function asegurarServidor() {
  if (await servidorVivo()) return;
  servidor = spawn("python", ["app.py"], { cwd: path.join(__dirname, ".."), windowsHide: true });
  servidor.on("error", () => {});
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 250));
    if (await servidorVivo()) return;
  }
  throw new Error("No pude arrancar el servidor de Kiara. Prueba abrir una terminal en la carpeta Kiara y ejecutar: python app.py");
}

function crearVentana() {
  const area = screen.getPrimaryDisplay().workArea;
  const ancho = 600, alto = 780;
  ventana = new BrowserWindow({
    width: ancho, height: alto,
    x: area.x + area.width - ancho - 16, y: area.y + area.height - alto,
    transparent: true, frame: false, hasShadow: false, resizable: false,
    alwaysOnTop: true, backgroundColor: "#00000000", title: "Kiara",
    webPreferences: { preload: path.join(__dirname, "preload.js") },
  });
  ventana.setAlwaysOnTop(true, "floating");
  // Los clics en las partes vacías pasan a los programas de abajo
  ventana.setIgnoreMouseEvents(true, { forward: true });
  ventana.loadURL(URL_KIARA + "/?escritorio=1");
}

ipcMain.on("traspasar", (_e, si) => { if (ventana) ventana.setIgnoreMouseEvents(si, { forward: true }); });
ipcMain.on("cerrar", () => app.quit());

app.whenReady().then(async () => {
  session.defaultSession.setPermissionRequestHandler((_wc, permiso, ok) => ok(permiso === "media"));
  try {
    await asegurarServidor();
  } catch (e) {
    dialog.showErrorBox("Kiara", e.message);
    app.quit();
    return;
  }
  crearVentana();
});

app.on("window-all-closed", () => app.quit());
app.on("will-quit", () => { if (servidor) servidor.kill(); });
