const API_URL = "";

document.addEventListener("DOMContentLoaded", cargarSolicitudes);
console.log("ADMIN SOLICITUDES JS CARGADO");
function cargarSolicitudes() {
  fetch(`${API_URL}/admin/solicitudes`)
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById("tablaSolicitudes");
      tbody.innerHTML = "";

      if (data.length === 0) {
        tbody.innerHTML = `
          <tr class="fila-animada">
            <td colspan="4" style="text-align:center;">
              No hay solicitudes pendientes
            </td>
          </tr>
        `;
        return;
      }

      data.forEach(s => {
        const fila = document.createElement("tr");
        fila.classList.add("fila-animada");

        fila.innerHTML = `
          <td>${s.nombre}</td>
          <td>${s.correo}</td>
          <td>${s.fecha}</td>
          <td>
            <button class="btn aprobar" onclick="aprobar(${s.id_usuario})">
              Aprobar
            </button>
            <button class="btn rechazar" onclick="rechazar(${s.id_usuario})">
              Rechazar
            </button>
          </td>
        `;

        tbody.appendChild(fila);
      });
    })
    .catch(err => console.error("Error:", err));
}

function aprobar(id) {
  console.log("🟡 Aprobando ID:", id);

  fetch(`/admin/aprobar/${id}`, {
    method: "POST"
  })
    .then(res => {
      console.log("📡 Status:", res.status);
      return res.json();
    })
    .then(data => {
      console.log("📨 Respuesta:", data);

      if (data.error) {
        alert("Error: " + data.error);
      } else {
        alert(data.mensaje);
      }

      cargarSolicitudes();
    })
    .catch(err => {
      console.error("❌ Error:", err);
      alert("Error en la petición");
    });
}

function rechazar(id) {
  fetch(`${API_URL}/admin/rechazar/${id}`, { method: "POST" })
    .then(() => cargarSolicitudes());
}
