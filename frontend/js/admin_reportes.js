document.addEventListener("DOMContentLoaded", () => {

  const API = "";

  /* ===============================
     👤 USUARIO
  ================================ */
  const usuario = {
    id: localStorage.getItem("id_usuario"),
    rol: localStorage.getItem("rol")
  };

  if (usuario.rol !== "admin") {
    alert("Acceso no autorizado");
    window.location.href = "login.html";
    return;
  }

  /* ===============================
     📌 ELEMENTOS DOM
  ================================ */
  const latInput = document.getElementById("lat");
  const lngInput = document.getElementById("lng");
  const modalEditar = document.getElementById("modalEditar");

  let mapa, marcador;
  let mapaEditar, marcadorEditar;

  /* ===============================
     📍 MAPA CREAR
  ================================ */
  if (document.getElementById("mapa")) {
    navigator.geolocation.getCurrentPosition(pos => {

      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;

      latInput.value = lat;
      lngInput.value = lng;

      mapa = L.map("mapa").setView([lat, lng], 16);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
        .addTo(mapa);

      marcador = L.marker([lat, lng], { draggable: true }).addTo(mapa);

      marcador.on("dragend", e => {
        const p = e.target.getLatLng();
        latInput.value = p.lat;
        lngInput.value = p.lng;
      });
    });
  }

  /* ===============================
     ➕ CREAR REPORTE
  ================================ */
  document.getElementById("formReporte").addEventListener("submit", e => {
    e.preventDefault();

    const fd = new FormData(e.target);
    fd.append("id_usuario", usuario.id);

    fetch(`${API}/reportes`, {
      method: "POST",
      body: fd
    })
      .then(r => r.json())
      .then(() => {
        alert("Reporte creado");
        e.target.reset();
        cargarReportes();
      });
  });

  /* ===============================
     📋 LISTAR REPORTES
  ================================ */
  function cargarReportes() {
    fetch(`${API}/reportes`)
      .then(r => r.json())
      .then(data => {

        console.log("DATOS DE REPORTES:", data);

        const cont = document.getElementById("listaReportes");
        cont.innerHTML = "";

        data.forEach(r => {

          const div = document.createElement("div");
          div.className = "reporte";

          div.innerHTML = `
            <strong>${r.titulo}</strong>
            <p>${r.descripcion}</p>
            <small>👤 ${r.autor} | 📅 ${r.fecha}</small>
            ${r.foto ? `<img src="${API}/uploads/${r.foto}" class="img-reporte">` : ""}
            <div class="acciones">
              <button class="btn-mapa">📍 Ir a la ubicación</button>
            </div>
          `;

          div.querySelector(".btn-mapa").onclick = () => {
            window.open(
              `https://www.google.com/maps?q=${r.lat},${r.lng}`,
              "_blank"
            );
          };

          const acciones = div.querySelector(".acciones");

          // ✏️ editar
          const btnEditar = document.createElement("button");
          btnEditar.textContent = "✏️ Editar";
          btnEditar.onclick = () => editarReporte(r);
          acciones.appendChild(btnEditar);

          // 🗑 eliminar
          const btnEliminar = document.createElement("button");
          btnEliminar.textContent = "🗑 Eliminar";
          btnEliminar.onclick = () => eliminarReporte(r.id);
          acciones.appendChild(btnEliminar);

          cont.appendChild(div);
        });
      });
  }

  /* ===============================
     ✏️ EDITAR
  ================================ */
  function editarReporte(r) {
    modalEditar.style.display = "flex";

    document.getElementById("edit_id").value = r.id;
    edit_titulo.value = r.titulo;
    edit_descripcion.value = r.descripcion;
    edit_lat.value = r.lat;
    edit_lng.value = r.lng;

    setTimeout(() => {
      if (mapaEditar) mapaEditar.remove();

      mapaEditar = L.map("mapaEditar").setView([r.lat, r.lng], 16);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
        .addTo(mapaEditar);

      marcadorEditar = L.marker([r.lat, r.lng], { draggable: true })
        .addTo(mapaEditar);

      marcadorEditar.on("dragend", e => {
        const p = e.target.getLatLng();
        edit_lat.value = p.lat;
        edit_lng.value = p.lng;
      });
    }, 300);
  }

  window.cerrarModal = () => {
    modalEditar.style.display = "none";
    if (mapaEditar) mapaEditar.remove();
  };

  /* ===============================
   💾 GUARDAR EDICIÓN
================================ */
document.getElementById("formEditar").addEventListener("submit", e => {

  e.preventDefault();

  const id = document.getElementById("edit_id").value;

  const fd = new FormData();

  fd.append("titulo", document.getElementById("edit_titulo").value);
  fd.append("descripcion", document.getElementById("edit_descripcion").value);
  fd.append("id_usuario", usuario.id);
  fd.append("rol", usuario.rol);

  const foto = document.getElementById("edit_foto").files[0];
  if (foto) {
    fd.append("foto", foto);
  }
  console.log("ID QUE SE ENVÍA:", id);

  fetch(`${API}/reportes/${id}`, {
    method: "PUT",
    body: fd
  })
  .then(r => r.json())
  .then(data => {

    if (data.error) {
      alert(data.error);
      return;
    }

    alert("Reporte actualizado");

    modalEditar.style.display = "none";

    cargarReportes();
  })
  .catch(err => {
    console.error(err);
    alert("Error al actualizar");
  });

});

  /* ===============================
     🗑 ELIMINAR
  ================================ */
  function eliminarReporte(id) {
    if (!confirm("¿Eliminar este reporte?")) return;

    fetch(`${API}/reportes/${id}?id_usuario=${usuario.id}&rol=admin`, {
      method: "DELETE"
    })
      .then(() => cargarReportes());
  }
  

  /* ===============================
     🚀 INICIAR
  ================================ */
  cargarReportes();
});
