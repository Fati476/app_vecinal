const API = "https://app-vecinal.onrender.com";

console.log("🔥 sos.js cargado");

document.addEventListener("DOMContentLoaded", () => {

  console.log("📄 DOM listo");

  const btnSOS = document.getElementById("btnSOS");

  if (!btnSOS) {
    console.error("❌ btnSOS NO existe en el HTML");
    return;
  }

  btnSOS.addEventListener("click", () => {
    console.log("🖱 CLICK en SOS");

    const id_usuario = localStorage.getItem("id_usuario");

    if (!id_usuario) {
      alert("Debes iniciar sesión");
      return;
    }

    if (!confirm("🚨 EMERGENCIA\n\n¿Enviar alerta inmediata?")) return;

    if (!navigator.geolocation) {
      alert("Geolocalización no soportada");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      pos => {
        console.log("📍 Ubicación obtenida:", pos.coords);
        enviarSOS(
          pos.coords.latitude,
          pos.coords.longitude,
          id_usuario
        );
      },
      err => {
        console.error("❌ Error geolocalización:", err);
        alert("No se pudo obtener la ubicación");
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );

  });

});

function enviarSOS(lat, lng, id_usuario) {

  console.log("📡 Enviando SOS al backend...");

  fetch(`${API}/incidencias`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      titulo: "🚨 Emergencia vecinal",
      descripcion: "Solicitud de ayuda inmediata",
      tipo: "SOS",
      lat: Number(lat),
      lng: Number(lng),
      id_usuario: Number(id_usuario)
    })
  })
  .then(res => res.json())
  .then(data => {
    console.log("✅ RESPUESTA:", data);
    alert("Incidencia enviada");
  })
  .catch(err => {
    console.error("❌ ERROR fetch:", err);
  });

}
