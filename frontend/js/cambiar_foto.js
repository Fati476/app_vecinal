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

  fetch("http://127.0.0.1:5000/api/perfil/foto", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {

        // 🔑 avisamos al perfil que la foto cambió
        sessionStorage.setItem("foto_actualizada", data.foto);


        // 🎞️ animación suave al volver
        document.body.classList.add("fade-out");

        setTimeout(() => {
          history.back();
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
