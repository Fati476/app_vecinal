var API = "https://app-vecinal.onrender.com";

const incidenciasMostradas = new Set();

document.addEventListener("DOMContentLoaded", () => {

  const socket = window.socket;

  if (!socket) {
    console.error("❌ Socket no cargado");
    return;
  }

  console.log("🟢 Socket disponible");

  let contadorBurbuja = 0;

  socket.off("nueva_incidencia");

  socket.on("connect", () => {
    console.log("🟢 Conectado al servidor");
  });

  socket.on("nueva_incidencia", (i) => {

    console.log("🚨 Nueva incidencia recibida", i);

    if (!i || !i.id) return;

    if (incidenciasMostradas.has(i.id)) return;

    const fechaInc = parsearFechaLocal(i.fecha);
    if (!fechaInc) return;

    const horas = (new Date() - fechaInc) / 3600000;

    if (horas > 24) return;

    incidenciasMostradas.add(i.id);

    crearBurbuja(i, contadorBurbuja++);

  });

  cargarIncidenciasIniciales();

});

/* ===============================
   CARGAR INCIDENCIAS
================================ */

function cargarIncidenciasIniciales(){

fetch(`${API}/incidencias/activas`)
.then(res=>res.json())
.then(data=>{

let index=0;
const ahora = new Date();

data.forEach(i=>{

const fechaInc = parsearFechaLocal(i.fecha);

if(!fechaInc) return;

const horas = (ahora - fechaInc) / 3600000;

if(horas > 24) return;

if (incidenciasMostradas.has(i.id)) return;

incidenciasMostradas.add(i.id);

crearBurbuja(i,index++);

});

})
.catch(err=>console.error("❌ Error incidencias",err));

}

/* ===============================
   CREAR BURBUJA
================================ */

function crearBurbuja(i,index){

const bubble=document.createElement("div");
bubble.className="burbuja-incidencia";

bubble.style.left=`${random(40,window.innerWidth-320)}px`;

const margenInferior=40;
const margenSuperior=140;

const rango=window.innerHeight-margenSuperior-margenInferior;
const offset=(index*120)%rango;

bubble.style.bottom=`${margenInferior+offset}px`;

bubble.innerHTML=`
<b>🚨 Incidencia activa</b>
<div><strong>${i.titulo}</strong></div>
<small>👤 ${i.usuario || "Vecino"} - ${i.rol || "usuario"}</small><br>
<small>🕒 ${formatearFecha(i.fecha)}</small>
<button>📍 Ir a ubicación</button>
`;

document.body.appendChild(bubble);

animarFlotacion(bubble);

bubble.querySelector("button").onclick=()=>{
window.open(`https://www.google.com/maps?q=${i.lat},${i.lng}`,"_blank");
};

}

/* ===============================
   FECHAS
================================ */

function parsearFechaLocal(fechaStr) {

  if (!fechaStr) return null;

  const [fecha, hora] = fechaStr.split(" ");

  const [y, m, d] = fecha.split("-").map(Number);
  const [hh, mm, ss] = hora.split(":").map(Number);

  return new Date(y, m - 1, d, hh, mm, ss);

}

function formatearFecha(fechaStr) {

  const fecha = parsearFechaLocal(fechaStr);
  if (!fecha) return "hora desconocida";

  const ahora = new Date();
  const diff = Math.floor((ahora - fecha) / 1000);

  if (diff < 60) return "justo ahora";

  const minutosTotales = Math.floor(diff / 60);

  if (minutosTotales < 60) {
    return `hace ${minutosTotales} minuto${minutosTotales === 1 ? "" : "s"}`;
  }

  const horas = Math.floor(minutosTotales / 60);
  const minutos = minutosTotales % 60;

  if (horas < 24) {

    if (minutos === 0) {
      return `hace ${horas} hora${horas === 1 ? "" : "s"}`;
    }

    return `hace ${horas} hora${horas === 1 ? "" : "s"} con ${minutos} minuto${minutos === 1 ? "" : "s"}`;

  }

  return fecha.toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  });

}



/* ===============================
   UTILIDADES
================================ */

function guardarVista(id) {

  const ROL = document.body.dataset.rol || "anon";
  const STORAGE_KEY = `incidencias_vistas_${ROL}`;

  let vistas = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];

  if (!vistas.includes(id)) {
    vistas.push(id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(vistas));
  }

}

function animarFlotacion(bubble) {

  let x = parseFloat(bubble.style.left);
  const y = parseFloat(bubble.style.bottom);

  let dx = Math.random() * 0.6 - 0.3;

  setInterval(() => {

    x += dx;

    if (x <= 20 || x >= window.innerWidth - 320) {
      dx *= -1;
    }

    bubble.style.left = `${x}px`;
    bubble.style.bottom = `${y}px`;

  }, 30);

}

function random(min, max) {
  return Math.random() * (max - min) + min;
}