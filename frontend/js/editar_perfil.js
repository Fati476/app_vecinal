const idUsuario = localStorage.getItem("id_usuario");

if (!idUsuario) {
  window.location.href = "login.html";
}

// 🔹 Cargar datos actuales
fetch(`http://127.0.0.1:5000/api/perfil/${idUsuario}`)
  .then(res => res.json())
  .then(data => {
    document.getElementById("nombre").value = data.nombre || "";
    document.getElementById("telefono").value = data.telefono || "";
    document.getElementById("direccion").value = data.direccion || "";
  });

// 🔹 Guardar cambios
function guardarCambios() {
  const datos = {
    nombre: document.getElementById("nombre").value,
    telefono: document.getElementById("telefono").value,
    direccion: document.getElementById("direccion").value
  };

  fetch(`http://127.0.0.1:5000/api/perfil/${idUsuario}`, {
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
