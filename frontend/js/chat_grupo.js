const socket = io(); {
    transports: ["polling"]
};
let ultimaFechaMostrada = null;
const grupo_id = 1;
const usuario_id = localStorage.getItem("id_usuario");

if (!usuario_id) {
    console.error("No hay usuario logueado");
}

const chat = document.getElementById("chat");
const input = document.getElementById("mensaje");


// 🔹 Cuando conecta
socket.on("connect", function () {
    console.log("Conectado al servidor");

    // Unirse al grupo
    socket.emit("unirse_grupo", { grupo_id: grupo_id });

    // Cargar mensajes anteriores
    socket.emit("cargar_mensajes", { grupo_id: grupo_id });

    // Registrar usuario activo
    socket.emit("registrar_usuario", { usuario_id: usuario_id });
});


// 🔹 Recibir mensajes nuevos en tiempo real
socket.on("nuevo_mensaje", function (data) {
    agregarMensaje(data);
    chat.scrollTop = chat.scrollHeight;
});


// 🔹 Recibir mensajes anteriores
socket.on("mensajes_anteriores", function (mensajes) {
    ultimaFechaMostrada = null; // 🔥 reiniciar control de fecha
    chat.innerHTML = "";        // opcional: limpiar chat

    mensajes.forEach(function (data) {
        agregarMensaje(data);
    });

    chat.scrollTop = chat.scrollHeight;
});


let timeoutEscribiendo;

input.addEventListener("input", function () {
    socket.emit("usuario_escribiendo", {
        grupo_id: grupo_id,
        usuario_id: usuario_id
    });

    clearTimeout(timeoutEscribiendo);

    timeoutEscribiendo = setTimeout(() => {
        socket.emit("usuario_dejo_escribir", {
            grupo_id: grupo_id
        });
    }, 2000);
});



const escribiendoDiv = document.getElementById("escribiendo");

socket.on("mostrar_escribiendo", function (data) {
    escribiendoDiv.innerText = data.nombre + " está escribiendo...";
});

socket.on("ocultar_escribiendo", function () {
    escribiendoDiv.innerText = "";
});


// 🔹 Función para mostrar mensaje



// 🔹 Enviar mensaje
function enviarMensaje() {
    const mensaje = input.value.trim();
    if (!mensaje) return;

    socket.emit("enviar_mensaje_grupo", {
        grupo_id: grupo_id,
        usuario_id: usuario_id,
        mensaje: mensaje
    });

    input.value = "";
}

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

function agregarMensaje(data) {
    const div = document.createElement("div");

    const fecha = new Date(data.fecha + " UTC");
    const hora = fecha.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const esMio = parseInt(data.usuario_id) === parseInt(usuario_id);


    const etiquetaFecha = obtenerEtiquetaFecha(data.fecha);

    if (ultimaFechaMostrada !== etiquetaFecha) {
        const separador = document.createElement("div");
        separador.classList.add("separador-fecha");
       separador.innerText = etiquetaFecha;
        chat.appendChild(separador);

        ultimaFechaMostrada = etiquetaFecha;
    }

    div.classList.add("mensaje");

    if (esMio) {
        div.classList.add("mio");
    } else {
        div.classList.add("otro");
    }

    div.innerHTML = `
        <div class="contenido">
            <strong>${data.nombre}</strong>
            <p>${data.mensaje}</p>
            <span class="hora">${hora}</span>
        </div>
    `;

    chat.appendChild(div);
}

input.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        enviarMensaje();
    }
});