// conexión global al servidor
window.socket = io("https://app-vecinal.onrender.com", {
    transports: ["websocket", "polling"]
});

window.socket.on("connect", () => {
    console.log("🟢 Socket conectado:", window.socket.id);
});

window.socket.on("disconnect", () => {
    console.log("🔴 Socket desconectado");
});