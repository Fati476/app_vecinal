function mostrarPaso2() {
    document.getElementById("paso1").style.display = "none";
    document.getElementById("paso2").style.display = "block";
}

function mostrarPaso1() {
    document.getElementById("paso2").style.display = "none";
    document.getElementById("paso1").style.display = "block";
}

function enviarCodigo() {
    const correo = document.getElementById("correo").value.trim();
    const mensaje = document.getElementById("mensaje");

    if (!correo) {
        mensaje.innerText = "Ingresa tu correo";
        mensaje.style.color = "red";
        return;
    }

    // 🔐 Guardar correo para el paso 2
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
        
    })
    .catch(() => {
        mensaje.innerText = "Error al conectar con el servidor";
        mensaje.style.color = "red";
    });
}

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
