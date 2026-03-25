// 🔐 Obtener ID del usuario
const idUsuario = localStorage.getItem("id_usuario");

// 🚫 Si no hay sesión → regresar al login
if (!idUsuario) {
  window.location.href = "login.html";
}

// 🌐 URL base
const API_URL = "https://app-vecinal.onrender.com";

// ==============================
// 🔹 CARGAR DATOS
// ==============================
function cargarPerfil() {
  fetch(`${API_URL}/api/perfil/${idUsuario}`)
    .then(res => res.json())
    .then(data => {

      // 👇 IMPORTANTE: usar .value (no textContent)
      document.getElementById("nombre").value = data.nombre || "";
      document.getElementById("telefono").value = data.telefono || "";
      document.getElementById("direccion").value = data.direccion || "";

    })
    .catch(err => {
      console.error("Error al cargar perfil:", err);
    });
}

cargarPerfil();


// ==============================
// 🔥 VALIDAR TELÉFONO EN TIEMPO REAL
// ==============================
const inputTelefono = document.getElementById("telefono");

inputTelefono.addEventListener("input", () => {

  // ❌ quitar letras
  inputTelefono.value = inputTelefono.value.replace(/\D/g, "");

  // 🔢 máximo 10
  if (inputTelefono.value.length > 10) {
    inputTelefono.value = inputTelefono.value.slice(0, 10);
  }
});


// ==============================
// 💾 GUARDAR CAMBIOS
// ==============================
function guardarCambios() {

  const nombre = document.getElementById("nombre").value.trim();
  const telefono = document.getElementById("telefono").value.trim();
  const direccion = document.getElementById("direccion").value.trim();

  // 🔥 VALIDACIÓN TELÉFONO
  if (telefono && !/^\d{10}$/.test(telefono)) {
    alert("⚠️ El teléfono debe tener exactamente 10 números");
    return;
  }

  fetch(`${API_URL}/api/perfil/${idUsuario}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      nombre,
      telefono,
      direccion
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("✅ Perfil actualizado");
      window.location.href = "perfil.html";
    } else {
      alert("❌ Error al actualizar");
    }
  })
  .catch(err => {
    console.error("Error:", err);
  });
}