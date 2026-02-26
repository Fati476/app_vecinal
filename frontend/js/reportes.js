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
  let mapaEditar, marcadorEditar;

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
          const div = document.createElement("div");
          div.className = "reporte";

          div.innerHTML = `
            <div class="reporte-header">
              <span>👤 ${r.autor || "Anónimo"}</span>
              <span>📅 ${r.fecha || ""}</span>
            </div>

            <div class="reporte-titulo">🚧 ${r.titulo}</div>
            <p>${r.descripcion}</p>

            ${r.foto ? `<img src="${API}/uploads/${r.foto}">` : ""}

            <div class="acciones">
              <button class="btn-mapa">📍 Ir a la ubicación</button>
            </div>
          `;

          div.querySelector(".btn-mapa").onclick = () => {
            irUbicacion(r.lat, r.lng);
          };

          if (usuario.id == r.id_usuario) {
            const acciones = div.querySelector(".acciones");

            const btnEditar = document.createElement("button");
            btnEditar.textContent = "✏️ Editar";
            btnEditar.onclick = () => editarReporte(r);

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
     📍 MAPS
  ================================ */
  function irUbicacion(lat, lng) {
    if (!lat || !lng) return;
    window.open(`https://www.google.com/maps?q=${lat},${lng}`, "_blank");
  }

  /* ===============================
     🚀 INICIAR
  ================================ */
  cargarReportes();
});
