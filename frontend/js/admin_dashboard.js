fetch("/admin/dashboard")
  .then(res => res.json())
  .then(data => {
    document.getElementById("pendientes").innerText = data.pendientes
    document.getElementById("aprobados").innerText = data.aprobados
    document.getElementById("rechazados").innerText = data.rechazados
  })
