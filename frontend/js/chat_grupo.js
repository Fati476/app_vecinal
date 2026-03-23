const socket = io();

let ultimaFechaMostrada = null;
const grupo_id = 1;
const usuario_id = localStorage.getItem("id_usuario");

const chat = document.getElementById("chat");
const input = document.getElementById("mensaje");
const escribiendoDiv = document.getElementById("escribiendo");
const imagenInput = document.getElementById("imagenInput");
const previewContainer = document.getElementById("previewContainer");

let usuariosActivos = [];

// ==============================
// 🔌 CONEXIÓN
// ==============================
socket.on("connect", () => {
    socket.emit("unirse_grupo", { grupo_id });
    socket.emit("cargar_mensajes", { grupo_id });
    socket.emit("registrar_usuario", { usuario_id });
});

// ==============================
// 🟢 USUARIOS ACTIVOS
// ==============================
socket.on("usuarios_activos", lista => {
    usuariosActivos = lista;

    const estado = document.getElementById("estadoUsuario");
    estado.innerText = "🟢 " + lista.length + " en línea";
});

// ==============================
// 👤 VER USUARIOS
// ==============================
function verUsuarios() {
    const contenedor = document.getElementById("listaUsuarios");
    contenedor.innerHTML = "";

    usuariosActivos.forEach(id => {
        if (parseInt(id) === parseInt(usuario_id)) return;

        const div = document.createElement("div");
        div.classList.add("usuario-item");
        div.innerText = "Usuario " + id;

        div.onclick = () => {
            alert("Chat privado después 😏");
        };

        contenedor.appendChild(div);
    });
}

// ==============================
// 💬 MENSAJES
// ==============================
socket.on("nuevo_mensaje", data => {
    agregarMensaje(data);
    chat.scrollTop = chat.scrollHeight;
});

socket.on("mensajes_anteriores", mensajes => {
    chat.innerHTML = "";
    ultimaFechaMostrada = null;

    mensajes.forEach(agregarMensaje);

    chat.scrollTop = chat.scrollHeight;
});

// ==============================
// ✍️ ESCRIBIENDO
// ==============================
let timeoutEscribiendo;

input.addEventListener("input", () => {
    socket.emit("usuario_escribiendo", { grupo_id, usuario_id });

    clearTimeout(timeoutEscribiendo);

    timeoutEscribiendo = setTimeout(() => {
        socket.emit("usuario_dejo_escribir", { grupo_id });
    }, 2000);
});

socket.on("mostrar_escribiendo", data => {
    escribiendoDiv.innerText = data.nombre + " está escribiendo...";
});

socket.on("ocultar_escribiendo", () => {
    escribiendoDiv.innerText = "";
});

// ==============================
// 🖼️ PREVIEW IMAGEN
// ==============================
imagenInput.addEventListener("change", () => {
    const file = imagenInput.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = e => {
        previewContainer.innerHTML = `
            <div class="preview-box">
                <img src="${e.target.result}" class="preview-img">
                <span class="cerrar-preview" onclick="quitarImagen()">✖</span>
            </div>
        `;
    };

    reader.readAsDataURL(file);
});

function quitarImagen() {
    imagenInput.value = "";
    previewContainer.innerHTML = "";
}

// ==============================
// 📤 ENVIAR MENSAJE
// ==============================
function enviarMensaje() {
    const mensaje = input.value.trim();
    const archivo = imagenInput.files[0];

    if (!mensaje && !archivo) return;

    if (archivo) {
        const formData = new FormData();
        formData.append("file", archivo);
        formData.append("upload_preset", "chat_upload");

        fetch("https://api.cloudinary.com/v1_1/dwpfvr7oz/image/upload", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            socket.emit("enviar_mensaje_grupo", {
                grupo_id,
                usuario_id,
                mensaje,
                imagen: data.secure_url
            });
        });

    } else {
        socket.emit("enviar_mensaje_grupo", {
            grupo_id,
            usuario_id,
            mensaje
        });
    }

    input.value = "";
    imagenInput.value = "";
    previewContainer.innerHTML = "";
}

// ==============================
// 📅 FECHA BONITA
// ==============================
function obtenerEtiquetaFecha(fechaMensaje) {
    const hoy = new Date();
    const fecha = new Date(data.fecha + "Z");

    const inicioHoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
    const inicioMensaje = new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());

    const diferencia = Math.floor((inicioHoy - inicioMensaje) / (1000 * 60 * 60 * 24));

    if (diferencia === 0) return "Hoy";
    if (diferencia === 1) return "Ayer";

    return fecha.toLocaleDateString("es-MX", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    });
}

// ==============================
// 💬 PINTAR MENSAJE
// ==============================
function agregarMensaje(data) {
    const div = document.createElement("div");

    const fecha = new Date(data.fecha + "Z");
    const hora = fecha.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    const esMio = parseInt(data.usuario_id) === parseInt(usuario_id);

    const etiquetaFecha = obtenerEtiquetaFecha(data.fecha);

    // 🔥 SEPARADOR DE DÍA
    if (ultimaFechaMostrada !== etiquetaFecha) {
        const separador = document.createElement("div");
        separador.classList.add("separador-fecha");
        separador.innerText = etiquetaFecha;
        chat.appendChild(separador);

        ultimaFechaMostrada = etiquetaFecha;
    }

    div.classList.add("mensaje", esMio ? "mio" : "otro");

    const foto = data.foto || "img/default.jpg";

    div.innerHTML = `
        <div class="mensaje-contenedor">
            <img src="${foto}" class="foto-chat">
            <div class="contenido">
                <strong>${data.nombre}</strong>
                <p>${data.mensaje || ""}</p>
                ${data.imagen ? `<img src="${data.imagen}" class="img-chat">` : ""}
                <span class="hora">${hora}</span>
            </div>
        </div>
    `;

    chat.appendChild(div);
}

// ==============================
// ⌨️ ENTER
// ==============================
input.addEventListener("keypress", e => {
    if (e.key === "Enter") enviarMensaje();
});

// ==============================
// 🔁 BOTÓN GRUPO
// ==============================
function irGrupo() {
    socket.emit("unirse_grupo", { grupo_id });
    socket.emit("cargar_mensajes", { grupo_id });

    chat.innerHTML = "";
}