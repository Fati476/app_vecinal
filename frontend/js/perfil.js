// 🔐 Obtener ID del usuario
const idUsuario = localStorage.getItem("id_usuario");

// 🚫 Si no hay sesión → regresar al login
if (!idUsuario) {
  window.location.href = "login.html";
}

// 🌐 URL base (IMPORTANTE en producción)
const API_URL = "https://app-vecinal.onrender.com";

// ==============================
// 🔹 CARGAR DATOS DEL PERFIL
// ==============================

function cargarPerfil() {
  fetch(`${API_URL}/api/perfil/${idUsuario}`)
    .then(res => res.json())
    .then(data => {

      document.getElementById("nombre").textContent = data.nombre;
      document.getElementById("correo").textContent = data.correo;
      document.getElementById("rol").textContent = data.rol;

      document.getElementById("telefono").textContent =
        data.telefono || "No registrado";

      document.getElementById("direccion").textContent =
        data.direccion || "No registrada";

      const fotoPerfil = document.getElementById("fotoPerfil");

      // 🧠 1️⃣ Si viene foto recién actualizada
      const fotoNueva = sessionStorage.getItem("foto_actualizada");

      if (fotoNueva) {
        fotoPerfil.src = fotoNueva;
        sessionStorage.removeItem("foto_actualizada");
      }

      // 🧠 2️⃣ Si ya existe foto en BD
      else if (data.foto) {
        fotoPerfil.src = fotoNueva;
      }

      // 🧠 3️⃣ Default
      else {
        fotoPerfil.src = "img/default.jpg";
      }
    })
    .catch(err => {
      console.error("Error al cargar perfil:", err);
    });
}

// 🔥 Ejecutar al cargar
cargarPerfil();


// ==============================
// 🔁 REDIRECCIONES
// ==============================

function editarPerfil() {
  window.location.href = "editar_perfil.html";
}

function cambiarFoto() {
  window.location.href = "cambiar_foto.html";
}

function cerrarSesion() {
  localStorage.clear();
  window.location.href = "login.html";
}


// ==============================
// 🗑 MODAL ELIMINAR FOTO
// ==============================

// 🔴 Abrir modal
function eliminarFoto() {
  document.getElementById("modalConfirm").style.display = "flex";
}

// ❌ Cerrar modal
function cerrarModal() {
  document.getElementById("modalConfirm").style.display = "none";
}

// ✅ Confirmar eliminación
function confirmarEliminar() {
  fetch(`${API_URL}/api/perfil/foto/${idUsuario}`, {
    method: "DELETE"
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {

        const fotoPerfil = document.getElementById("fotoPerfil");

        // 🔥 Cambiar a default inmediatamente
        fotoPerfil.src = "img/default.jpg?t=" + Date.now();

        cerrarModal();
      }
    })
    .catch(err => {
      console.error("Error eliminando foto:", err);
    });
}