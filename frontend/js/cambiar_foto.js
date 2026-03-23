const idUsuario = localStorage.getItem("id_usuario");

if (!idUsuario) {
  window.location.href = "login.html";
}

function subirFoto() {
  const input = document.getElementById("foto");

  if (!input.files.length) {
    alert("Selecciona una foto 📸");
    return;
  }

  const formData = new FormData();
  formData.append("foto", input.files[0]);
  formData.append("id_usuario", idUsuario);

  fetch(`${API_URL}/api/perfil/foto`, {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {

        // 🔥 ahora es URL completa (Cloudinary)
        sessionStorage.setItem("foto_actualizada", data.foto);

        document.body.classList.add("fade-out");

        const rol = localStorage.getItem("rol");

        setTimeout(() => {
          if (rol === "admin") {
            window.location.href = "admin_perfil.html";
          } else {
            window.location.href = "vecino_perfil.html";
          }
        }, 300);

      } else {
        alert(data.message || "Error al subir la foto ❌");
      }
    })
    .catch(err => {
      console.error(err);
      alert("Error de conexión ❌");
    });
}