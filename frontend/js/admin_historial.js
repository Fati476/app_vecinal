fetch("/admin/aprobados")
  .then(res => res.json())
  .then(data => {
    const tabla = document.getElementById("tablaAprobados")
    tabla.innerHTML = ""

    if (data.length === 0) {
      tabla.innerHTML = `
        <tr class="fila-animada">
          <td colspan="6" style="text-align:center;">No hay usuarios aprobados</td>
        </tr>
      `
      return
    }

    data.forEach(u => {
      const fila = document.createElement("tr")
      fila.classList.add("fila-animada")

      fila.innerHTML = `
        <td>${u.nombre}</td>
        <td>${u.correo}</td>
        <td>${u.telefono}</td>
        <td>${u.direccion}</td>
        <td>${u.fecha}</td>
        <td>
          <button class="btn btn-eliminar" onclick="eliminar(${u.id})">
            Eliminar
          </button>
        </td>
      `

      tabla.appendChild(fila)
    })
  })

function eliminar(id) {
  if (!confirm("¿Eliminar este usuario?")) return

  fetch(`/admin/eliminar/${id}`, {
  method: "DELETE"
  })
  .then(() => {
    const boton = document.querySelector(
      `button[onclick="eliminar(${id})"]`
    )
    const fila = boton.closest("tr")

    fila.style.transition = "all 0.4s ease"
    fila.style.opacity = "0"
    fila.style.transform = "translateX(30px)"

    setTimeout(() => fila.remove(), 400)
  })
}
