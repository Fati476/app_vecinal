document.addEventListener("DOMContentLoaded", () => {

  const API = "";

  /* ===============================
     👤 USUARIO
  ================================ */
  const usuario = {
    id: localStorage.getItem("id_usuario"),
    rol: localStorage.getItem("rol")
  };

  if (!usuario.id || !usuario.rol) {
    alert("Sesión no válida");
    window.location.href = "login.html";
    return;
  }

  const latInput = document.getElementById("lat");
  const lngInput = document.getElementById("lng");

  let mapa, marcador;

  /* ===============================
     📍 MAPA CREAR
  ================================ */
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
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
      },
      () => alert("No se pudo obtener la ubicación")
    );
  }

  /* ===============================
     ➕ CREAR REPORTE
  ================================ */
  document.getElementById("formReporte").addEventListener("submit", e => {
    e.preventDefault();

    const formData = new FormData(e.target);
    formData.append("id_usuario", usuario.id);

    fetch(`${API}/reportes`, {
      method: "POST",
      body: formData
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

        const cont = document.getElementById("listaReportes");
        cont.innerHTML = "";

        data.forEach(r => {

          // 🔥 FECHA BONITA (igual que admin)
          const fechaBonita = r.fecha
            ? new Date(r.fecha).toLocaleString("es-MX", {
                day: "2-digit",
                month: "short",
                year: "numeric",
                hour: "numeric",
                minute: "2-digit"
              })
            : "";

          const div = document.createElement("div");
          div.className = "reporte";

          div.innerHTML = `
            <strong>🚧 ${r.titulo}</strong>
            <p>${r.descripcion}</p>
            <small>👤 ${r.autor || "Anónimo"} | 📅 ${fechaBonita}</small>
            ${r.foto ? `<img src="${API}/uploads/${r.foto}?t=${Date.now()}" class="img-reporte">` : ""}
            <div class="acciones">
              <button class="btn-mapa">📍 Ir a la ubicación</button
            </div>

          `;

          // 📍 ir a maps
          div.querySelector(".btn-mapa").onclick = () => {
            window.open(`https://www.google.com/maps?q=${r.lat},${r.lng}`, "_blank");
          };

          // 🔥 SOLO SI ES SU REPORTE
          if (usuario.id == r.id_usuario) {
            const acciones = div.querySelector(".acciones");

            // ✏️ EDITAR
            const btnEditar = document.createElement("button");
            btnEditar.textContent = "✏️ Editar";
            btnEditar.onclick = () => editarReporte(r);

            // 🗑 ELIMINAR
            const btnEliminar = document.createElement("button");
            btnEliminar.textContent = "🗑 Eliminar";
            btnEliminar.onclick = () => eliminarReporte(r.id);

            acciones.appendChild(btnEditar);
            acciones.appendChild(btnEliminar);
          }

          cont.appendChild(div);
        });
      });
  }

  /* ===============================
     ✏️ EDITAR (BÁSICO POR AHORA)
  ================================ */
  function editarReporte(r) {

  const modal = document.getElementById("modalEditar");
  modal.style.display = "flex";

  // 🔥 llenar datos
  document.getElementById("edit_id").value = r.id;
  document.getElementById("edit_titulo").value = r.titulo;
  document.getElementById("edit_descripcion").value = r.descripcion;
  document.getElementById("edit_lat").value = r.lat;
  document.getElementById("edit_lng").value = r.lng;

  const preview = document.getElementById("preview_foto");

  // 🖼️ mostrar foto actual
  if (r.foto) {
    preview.src = `${API}/uploads/${r.foto}?t=${Date.now()}`;
    preview.style.display = "block";
  } else {
    preview.style.display = "none";
  }

  // 🗺️ mapa editar
  setTimeout(() => {

    if (mapaEditar) mapaEditar.remove();

    mapaEditar = L.map("mapaEditar").setView([r.lat, r.lng], 16);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
      .addTo(mapaEditar);

    marcadorEditar = L.marker([r.lat, r.lng], { draggable: true })
      .addTo(mapaEditar);

    marcadorEditar.on("dragend", e => {
      const p = e.target.getLatLng();
      document.getElementById("edit_lat").value = p.lat;
      document.getElementById("edit_lng").value = p.lng;
    });

  }, 300);
  
}

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

    document.getElementById("modalEditar").style.display = "none";

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

    fetch(`${API}/reportes/${id}?id_usuario=${usuario.id}&rol=${usuario.rol}`, {
      method: "DELETE"
    })
      .then(() => cargarReportes());
  }

  /* ===============================
     🚀 INICIAR
  ================================ */
  cargarReportes();
});