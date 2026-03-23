const socket = io();
let ultimaFechaMostrada = null;

const grupo_id = 1;
const usuario_id = localStorage.getItem("id_usuario");

if (!usuario_id) {
    console.error("No hay usuario logueado");
}

const chat = document.getElementById("chat");
const input = document.getElementById("mensaje");
const escribiendoDiv = document.getElementById("escribiendo");

// 🌐 URL API (IMPORTANTE)
const API_URL = "https://app-vecinal.onrender.com";


// ==============================
// 🔌 CONEXIÓN
// ==============================
socket.on("connect", function () {
    console.log("Conectado al servidor");

    socket.emit("unirse_grupo", { grupo_id });
    socket.emit("cargar_mensajes", { grupo_id });
    socket.emit("registrar_usuario", { usuario_id });
});


// ==============================
// 📩 MENSAJES NUEVOS
// ==============================
socket.on("nuevo_mensaje", function (data) {
    agregarMensaje(data);
    chat.scrollTop = chat.scrollHeight;
});


// ==============================
// 📜 MENSAJES ANTERIORES
// ==============================
socket.on("mensajes_anteriores", function (mensajes) {
    ultimaFechaMostrada = null;
    chat.innerHTML = "";

    mensajes.forEach(function (data) {
        agregarMensaje(data);
    });

    chat.scrollTop = chat.scrollHeight;
});


// ==============================
// ✍️ ESCRIBIENDO...
// ==============================
let timeoutEscribiendo;

input.addEventListener("input", function () {
    socket.emit("usuario_escribiendo", {
        grupo_id,
        usuario_id
    });

    clearTimeout(timeoutEscribiendo);

    timeoutEscribiendo = setTimeout(() => {
        socket.emit("usuario_dejo_escribir", { grupo_id });
    }, 2000);
});

socket.on("mostrar_escribiendo", function (data) {
    escribiendoDiv.innerText = data.nombre + " está escribiendo...";
});

socket.on("ocultar_escribiendo", function () {
    escribiendoDiv.innerText = "";
});


// ==============================
// 📤 ENVIAR MENSAJE
// ==============================
function enviarMensaje() {
    const mensaje = input.value.trim();
    if (!mensaje) return;

    socket.emit("enviar_mensaje_grupo", {
        grupo_id,
        usuario_id,
        mensaje
    });

    input.value = "";
}

input.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        enviarMensaje();
    }
});


// ==============================
// 📅 FECHAS BONITAS
// ==============================
function obtenerEtiquetaFecha(fechaMensaje) {
    const hoy = new Date();
    const fecha = new Date(fechaMensaje + " UTC");

    const inicioHoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
    const inicioMensaje = new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());

    const diferencia = (inicioHoy - inicioMensaje) / (1000 * 60 * 60 * 24);

    if (diferencia === 0) return "Hoy";
    if (diferencia === 1) return "Ayer";

    return fecha.toLocaleDateString("es-MX", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    });
}


// ==============================
// 💬 MOSTRAR MENSAJE
// ==============================
function agregarMensaje(data) {
    const div = document.createElement("div");

    const fecha = new Date(data.fecha + " UTC");
    const hora = fecha.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    const esMio = parseInt(data.usuario_id) === parseInt(usuario_id);

    const etiquetaFecha = obtenerEtiquetaFecha(data.fecha);

    // 🔥 Separador de fecha
    if (ultimaFechaMostrada !== etiquetaFecha) {
        const separador = document.createElement("div");
        separador.classList.add("separador-fecha");
        separador.innerText = etiquetaFecha;
        chat.appendChild(separador);

        ultimaFechaMostrada = etiquetaFecha;
    }

    div.classList.add("mensaje");
    div.classList.add(esMio ? "mio" : "otro");

    // 🖼️ FOTO PERFIL (Cloudinary o default)
    const foto = data.foto
        ? data.foto
        : "img/default.jpg";

    div.innerHTML = `
        <div class="mensaje-contenedor">
            <img src="${foto}" class="foto-chat">
            <div class="contenido">
                <strong>${data.nombre}</strong>
                <p>${data.mensaje}</p>
                <span class="hora">${hora}</span>
            </div>
        </div>
    `;

    chat.appendChild(div);
}