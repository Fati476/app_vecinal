const idUsuario = localStorage.getItem("id_usuario");

if (!idUsuario) {
  window.location.href = "login.html";
}

// 🔹 Cargar datos actuales
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

// 🔹 Guardar cambios
function guardarCambios() {
  const datos = {
    nombre: document.getElementById("nombre").value,
    telefono: document.getElementById("telefono").value,
    direccion: document.getElementById("direccion").value
  };

  fetch(`/api/perfil/${idUsuario}`,  {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(datos)
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Perfil actualizado ✅");
        window.location.href = "admin_perfil.html";
      } else {
        alert("Error al actualizar ❌");
      }
    })
    .catch(err => {
      console.error(err);
      alert("Error de conexión ❌");
    });
}
