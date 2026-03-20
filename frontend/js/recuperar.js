// ===============================
// 🔄 CAMBIAR ENTRE PASOS
// ===============================
function mostrarPaso2() {
    document.getElementById("paso1").style.display = "none";
    document.getElementById("paso2").style.display = "block";
}

function mostrarPaso1() {
    document.getElementById("paso2").style.display = "none";
    document.getElementById("paso1").style.display = "block";
}

// ===============================
// 📧 ENVIAR CÓDIGO
// ===============================
function enviarCodigo() {
    const correo = document.getElementById("correo").value.trim();
    const mensaje = document.getElementById("mensaje");

    if (!correo) {
        mensaje.innerText = "Ingresa tu correo";
        mensaje.style.color = "red";
        return;
    }

    localStorage.setItem("correo_recuperacion", correo);

    fetch("/recuperar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correo })
    })
    .then(res => res.json())
    .then(data => {
        mensaje.innerText = data.error || data.mensaje;
        mensaje.style.color = data.error ? "red" : "green";

        if (!data.error) {
            mostrarPaso2(); // 🔥 pasa al paso 2 automáticamente
        }
    })
    .catch(() => {
        mensaje.innerText = "Error al conectar con el servidor";
        mensaje.style.color = "red";
    });
}

// ===============================
// 🔁 REENVIAR CÓDIGO
// ===============================
function reenviarCodigo() {
    const correo = localStorage.getItem("correo_recuperacion");
    const mensaje = document.getElementById("mensaje");

    if (!correo) {
        mensaje.innerText = "Primero ingresa tu correo";
        mensaje.style.color = "red";
        return;
    }

    fetch("/recuperar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correo })
    })
    .then(res => res.json())
    .then(data => {
        mensaje.innerText = data.error || "Código reenviado correctamente";
        mensaje.style.color = data.error ? "red" : "green";
    })
    .catch(() => {
        mensaje.innerText = "Error al reenviar el código";
        mensaje.style.color = "red";
    });
}

// ===============================
// 🔐 CAMBIAR CONTRASEÑA
// ===============================
function cambiarPassword() {
    const codigo = document.getElementById("codigo").value.trim();
    const password = document.getElementById("password").value;
    const password2 = document.getElementById("password2").value;
    const mensaje = document.getElementById("mensaje");

    if (!codigo || !password || !password2) {
        mensaje.innerText = "Todos los campos son obligatorios";
        mensaje.style.color = "red";
        return;
    }

    if (password !== password2) {
        mensaje.innerText = "Las contraseñas no coinciden";
        mensaje.style.color = "red";
        return;
    }

    // 🔥 VALIDACIÓN SEGURA
    const regex = /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

    if (!regex.test(password)) {
        mensaje.innerText = "Contraseña insegura (usa mayúscula, número y símbolo)";
        mensaje.style.color = "red";
        return;
    }

    fetch("/resetear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            correo: localStorage.getItem("correo_recuperacion"),
            codigo: codigo,
            password: password
        })
    })
    .then(res => res.json())
    .then(data => {
        mensaje.innerText = data.error || data.mensaje;
        mensaje.style.color = data.error ? "red" : "green";

        if (!data.error) {
            localStorage.removeItem("correo_recuperacion");
            setTimeout(() => {
                window.location.href = "login.html";
            }, 2000);
        }
    })
    .catch(() => {
        mensaje.innerText = "Error al conectar con el servidor";
        mensaje.style.color = "red";
    });
}

// ===============================
// 👁 MOSTRAR / OCULTAR PASSWORD
// ===============================
function togglePassword(id){
    const input = document.getElementById(id);

    if(input.type === "password"){
        input.type = "text";
    }else{
        input.type = "password";
    }
}

// ===============================
// 🔒 INDICADOR SEGURIDAD
// ===============================
document.getElementById("password").addEventListener("input", function(){

    const pass = this.value;
    const seguridad = document.getElementById("seguridad");

    let nivel = 0;

    if(pass.length >= 8) nivel++;
    if(/[A-Z]/.test(pass)) nivel++;
    if(/[0-9]/.test(pass)) nivel++;
    if(/[^A-Za-z0-9]/.test(pass)) nivel++;

    if(nivel <= 1){
        seguridad.innerText = "🔴 Contraseña débil";
        seguridad.style.color = "red";
    }
    else if(nivel === 2 || nivel === 3){
        seguridad.innerText = "🟡 Contraseña media";
        seguridad.style.color = "orange";
    }
    else{
        seguridad.innerText = "🟢 Contraseña segura";
        seguridad.style.color = "green";
    }

});