function registrar() {
    const nombre = document.getElementById("nombre").value.trim();
    const correo = document.getElementById("correo").value.trim();
    const telefono = document.getElementById("telefono").value.trim();
    const direccion = document.getElementById("direccion").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirm = document.getElementById("confirm").value.trim();
    const mensaje = document.getElementById("mensaje");

    mensaje.innerText = "";

    // Campos obligatorios
    if (!nombre || !correo || !telefono || !direccion || !password || !confirm) {
        mensaje.innerText = "Todos los campos son obligatorios";
        mensaje.style.color = "red";
        return;
    }

    // Validar contraseña
    const regex = /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

    if (!regex.test(password)) {
        mensaje.innerText =
            "La contraseña debe tener mínimo 8 caracteres, una mayúscula, un número y un símbolo";
        mensaje.style.color = "red";
        return;
    }

    // Confirmar contraseña
    if (password !== confirm) {
        mensaje.innerText = "Las contraseñas no coinciden";
        mensaje.style.color = "red";
        return;
    }

    fetch("/registro", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            nombre,
            correo,
            telefono,
            direccion,
            password,
            password2: confirm
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            mensaje.innerText = "⚠️ " + data.error;
            mensaje.style.color = "red";
        } else {
            alert("✅ Registro enviado. Un administrador revisará tu solicitud.");
            window.location.href = "login.html";
        }
    })
    .catch(() => {
        mensaje.innerText = "❌ Error al conectar con el servidor";
        mensaje.style.color = "red";
    });
}
