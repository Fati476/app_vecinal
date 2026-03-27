function login() {
    const correo = document.getElementById("correo").value;
    const password = document.getElementById("password").value;
    const mensaje = document.getElementById("mensaje");

    if (!correo || !password) {
        mensaje.innerText = "Completa todos los campos";
        mensaje.style.color = "red";
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            correo,
            password
        })
    })
    .then(res => res.json())
    .then(data => {

        // ❌ SI HAY ERROR, NO GUARDAR NADA
        if (data.error) {
            mensaje.innerText = data.error;
            mensaje.style.color = "red";
            return;
        }

        // 🧼 LIMPIAR SESIÓN ANTERIOR
        localStorage.clear();

        // 🔐 GUARDAR SESIÓN CORRECTA
        localStorage.setItem("id_usuario", data.id_usuario);
        localStorage.setItem("rol", data.rol);

        // 🚀 REDIRECCIÓN
        if (data.rol === "admin") {
            window.location.href = "admin.html";
        } else {
            window.location.href = "vecino.html";
        }
    })
    .catch(() => {
        mensaje.innerText = "Error de conexión con el servidor";
    });
}
