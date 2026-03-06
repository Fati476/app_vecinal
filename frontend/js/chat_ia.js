/* ===============================
   SOCKET GLOBAL
================================ */

const socketIA = window.socket;

if (!socketIA) {
    console.error("❌ Socket no disponible");
}

/* ===============================
   CUANDO CARGA EL DOM
================================ */

document.addEventListener("DOMContentLoaded", () => {

    const chat = document.getElementById("mensajesIA");
    const input = document.getElementById("inputIA");
    const btnIA = document.getElementById("btnIA");
    const panelIA = document.getElementById("panelIA");
    const cerrarIA = document.getElementById("cerrarIA");

    const CLAVE_CHAT = "chat_ia_historial";

    if (!chat || !input || !btnIA || !panelIA) {
        console.warn("⚠ Elementos del chat IA no encontrados");
        return;
    }

    /* ===============================
       ABRIR / CERRAR CHAT
    ================================ */

    btnIA.addEventListener("click", () => {
        panelIA.classList.toggle("oculto");
    });

    if (cerrarIA) {
        cerrarIA.addEventListener("click", () => {
            panelIA.classList.add("oculto");
        });
    }

    /* ===============================
       GUARDAR MENSAJE
    ================================ */

    function guardarMensaje(texto, tipo) {
        const historial = JSON.parse(localStorage.getItem(CLAVE_CHAT)) || [];
        historial.push({ texto, tipo });
        localStorage.setItem(CLAVE_CHAT, JSON.stringify(historial));
    }

    /* ===============================
       AGREGAR MENSAJE
    ================================ */

    function agregarMensaje(texto, tipo, guardar = true) {

        const div = document.createElement("div");
        div.classList.add("message", tipo);
        div.innerText = texto;

        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;

        if (guardar) {
            guardarMensaje(texto, tipo);
        }
    }

    /* ===============================
       CARGAR HISTORIAL
    ================================ */

    function cargarHistorial() {

        const historial = JSON.parse(localStorage.getItem(CLAVE_CHAT)) || [];

        historial.forEach(msg => {
            agregarMensaje(msg.texto, msg.tipo, false);
        });

    }

    cargarHistorial();

    /* ===============================
       ENVIAR MENSAJE
    ================================ */

    function enviarMensajeIA() {

        const mensaje = input.value.trim();
        if (!mensaje) return;

        agregarMensaje(mensaje, "user");

        input.value = "";

        const typing = document.createElement("div");
        typing.classList.add("message", "ia", "typing");
        typing.id = "typingMsg";
        typing.innerText = "Asistente está escribiendo...";

        chat.appendChild(typing);

        if (socketIA) {
            socketIA.emit("mensaje_ia", { mensaje });
        }

    }

    /* ===============================
       RECIBIR RESPUESTA IA
    ================================ */

    if (socketIA) {

        socketIA.on("respuesta_ia", (data) => {

            const typingMsg = document.getElementById("typingMsg");
            if (typingMsg) typingMsg.remove();

            agregarMensaje(data.respuesta, "ia");

        });

    }

    /* ===============================
       ENTER PARA ENVIAR
    ================================ */

    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") enviarMensajeIA();
    });

});