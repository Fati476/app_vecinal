// ===============================
// CONFIGURACIÓN
// ===============================
const API = "";
const idUsuario = Number(localStorage.getItem("id_usuario"));
const rol = localStorage.getItem("rol");

// ===============================
// VALIDACIÓN DE SESIÓN
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  if (!idUsuario || !rol) {
    alert("Sesión no válida");
    window.location.href = "login.html";
    return;
  }

  const esVistaAdmin = window.location.pathname.includes("admin");
  const esVistaVecino = window.location.pathname.includes("vecino");

  if (esVistaAdmin && rol !== "admin") {
    alert("Acceso solo para administradores");
    window.location.href = "login.html";
    return;
  }

  if (esVistaVecino && rol !== "vecino") {
    alert("Acceso solo para vecinos");
    window.location.href = "login.html";
    return;
  }

  cargarIncidencias();
});

// ===============================
// CARGAR INCIDENCIAS
// ===============================
function cargarIncidencias() {
  fetch(`${API}/incidencias/menu?id_usuario=${idUsuario}`)
    .then(res => res.json())
    .then(data => pintarTabla(data))
    .catch(err => {
      console.error("Error:", err);
      alert("Error al cargar incidencias");
    });
}

// ===============================
// PINTAR TABLA
// ===============================
function pintarTabla(incidencias) {
  const tbody = document.getElementById("tablaIncidencias");
  tbody.innerHTML = "";

  // ❌ ocultar atendidas con más de 7 días (solo front)
  incidencias = incidencias.filter(inc => {
    if (inc.estado === "atendida" && esMasViejaDe7Dias(inc.fecha)) {
      return false;
    }
    return true;
  });

  if (!incidencias || incidencias.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6">No hay incidencias</td>
      </tr>
    `;
    return;
  }

  incidencias.forEach(inc => {

    // 📍 SIEMPRE visible
    let acciones = botonUbicacion(inc.lat, inc.lng);

    // ✔ solo si está activa
    if (inc.estado === "activa") {

      // 👑 admin
      if (rol === "admin") {
        acciones += botonAtender(inc.id_incidencia);
      }

      // 👤 vecino (solo las suyas)
      if (rol === "vecino" && inc.es_mia === 1) {
        acciones += botonAtender(inc.id_incidencia);
      }
    }

    tbody.innerHTML += `
      <tr>
        <td>${inc.titulo}</td>
        <td>${inc.tipo}</td>
        <td>${inc.usuario}</td>
        <td>${new Date(inc.fecha).toLocaleString("es-MX")}</td>
        <td>
          <span class="estado ${
            inc.estado === "activa" ? "estado-activa" : "estado-atendida"
          }">
            ${inc.estado}
          </span>
        </td>
        <td>${acciones}</td>
      </tr>
    `;
  });
}

// ===============================
// BOTÓN ATENDER
// ===============================
function botonAtender(id) {
  return `
    <button class="btn-atender" onclick="marcarAtendida(${id})">
      ✔ Atender
    </button>
  `;
}

// ===============================
// MARCAR COMO ATENDIDA
// ===============================
function marcarAtendida(idIncidencia) {
  if (!confirm("¿Marcar esta incidencia como atendida?")) return;

  fetch(`${API}/incidencias/${idIncidencia}/atender`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_usuario: idUsuario })
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
      } else {
        alert("Incidencia marcada como atendida");
        cargarIncidencias();
      }
    })
    .catch(err => {
      console.error(err);
      alert("Error al actualizar incidencia");
    });
}

// ===============================
// BOTÓN UBICACIÓN
// ===============================
function botonUbicacion(lat, lng) {
  if (!lat || !lng) return "—";

  return `
    <button class="btn-mapa" onclick="irMapa(${lat}, ${lng})">
      📍 Ubicación
    </button>
  `;
}

function irMapa(lat, lng) {
  window.open(`https://www.google.com/maps?q=${lat},${lng}`, "_blank");
}

// ===============================
// FECHAS
// ===============================
function esMasViejaDe7Dias(fecha) {
  const hoy = new Date();
  const fechaInc = new Date(fecha);
  const diferencia = hoy - fechaInc;
  return diferencia / (1000 * 60 * 60 * 24) >= 7;
}
