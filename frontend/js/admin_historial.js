const API_URL = "https://app-vecinal.onrender.com";

fetch(`${API_URL}/admin/aprobados`)
  .then(res => res.json())
  .then(data => {
    const tabla = document.getElementById("tablaAprobados");
    tabla.innerHTML = "";

    if (!data || data.length === 0) {
      tabla.innerHTML = `
        <tr class="fila-animada">
          <td colspan="6" style="text-align:center;">
            No hay usuarios aprobados
          </td>
        </tr>
      `;
      return;
    }

    data.forEach(u => {
      const fila = document.createElement("tr");
      fila.classList.add("fila-animada");

      // 🔥 FORMATEAR FECHA BONITA
      let fechaBonita = "";
      if (u.fecha) {
        fechaBonita = new Date(u.fecha).toLocaleString("es-MX", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit"
        });
      }

      fila.innerHTML = `
        <td>${u.nombre}</td>
        <td>${u.correo}</td>
        <td>${u.telefono}</td>
        <td>${u.direccion}</td>
        <td>${fechaBonita}</td>
        <td>
          <button class="btn btn-eliminar" onclick="eliminar(${u.id})">
            🗑️ Eliminar
          </button>
        </td>
      `;

      tabla.appendChild(fila);
    });
  })
  .catch(err => console.error("❌ Error:", err));


// 🔥 ELIMINAR USUARIO
function eliminar(id) {
  if (!confirm("¿Eliminar este usuario?")) return;

  fetch(`${API_URL}/admin/eliminar/${id}`, {
    method: "DELETE"
  })
    .then(res => res.json())
    .then(data => {
      console.log("📨 Respuesta:", data);

      const boton = document.querySelector(
        `button[onclick="eliminar(${id})"]`
      );

      if (!boton) return;

      const fila = boton.closest("tr");

      // 🔥 animación chida
      fila.style.transition = "all 0.4s ease";
      fila.style.opacity = "0";
      fila.style.transform = "translateX(30px)";

      setTimeout(() => fila.remove(), 400);
    })
    .catch(err => console.error("❌ Error eliminando:", err));
}