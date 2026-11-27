// Puente seguro entre la página de Kiara y la ventana de Electron
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("kiara", {
  traspasar: si => ipcRenderer.send("traspasar", si),  // true = los clics pasan a los programas de abajo
  cerrar: () => ipcRenderer.send("cerrar"),
});
