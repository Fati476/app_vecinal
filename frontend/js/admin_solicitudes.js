const API_URL = "https://app-vecinal.onrender.com";

document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 ADMIN SOLICITUDES CARGADO");
  cargarSolicitudes();
});

// 🔥 FUNCIÓN PARA FORMATEAR FECHA
function formatearFecha(fecha) {
  const f = new Date(fecha);

  return f.toLocaleString("es-MX", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

// 🔹 CARGAR SOLICITUDES
function cargarSolicitudes() {
  console.log("📥 Cargando solicitudes...");

  fetch(`${API_URL}/admin/solicitudes`)
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById("tablaSolicitudes");
      tbody.innerHTML = "";

      if (!data || data.length === 0) {
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
          <td>${formatearFecha(s.fecha)}</td> <!-- 🔥 AQUÍ SE USA -->
          <td>
            <button class="btn aprobar" onclick="aprobar(${s.id_usuario})">
              ✅ Aprobar
            </button>
            <button class="btn rechazar" onclick="rechazar(${s.id_usuario})">
              ❌ Rechazar
            </button>
          </td>
        `;

        tbody.appendChild(fila);
      });
    })
    .catch(err => {
      console.error("❌ Error cargando solicitudes:", err);
    });
}

// 🔹 APROBAR USUARIO
function aprobar(id) {
  console.log("🟡 Aprobando usuario ID:", id);

  fetch(`${API_URL}/admin/aprobar/${id}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    }
  })
    .then(res => {
      console.log("📡 Status:", res.status);
      return res.json();
    })
    .then(data => {
      console.log("📨 Respuesta:", data);

      if (data.error) {
        alert("❌ " + data.error);
      } else {
        alert("✅ " + data.mensaje);
      }

      cargarSolicitudes();
    })
    .catch(err => {
      console.error("❌ Error al aprobar:", err);
      alert("Error al aprobar usuario");
    });
}

// 🔹 RECHAZAR USUARIO
function rechazar(id) {
  console.log("🔴 Rechazando usuario ID:", id);

  fetch(`${API_URL}/admin/rechazar/${id}`, {
    method: "POST"
  })
    .then(res => res.json())
    .then(data => {
      console.log("📨 Respuesta:", data);
      cargarSolicitudes();
    })
    .catch(err => {
      console.error("❌ Error al rechazar:", err);
    });
}