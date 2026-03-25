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

    // 📱 Validar teléfono (solo números y 10 dígitos)
    if (!/^\d{10}$/.test(telefono)) {
        mensaje.innerText = "El teléfono debe tener exactamente 10 números";
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
.then(async res => {

    const data = await res.json();

    if (!res.ok) {

        mensaje.innerText = "⚠️ " + (data.error || "Error en el registro");
        mensaje.style.color = "red";
        return;

    }

    if (data.mensaje && data.mensaje.toLowerCase().includes("reenviada")) {
        mensaje.innerText = "🔄 Tu solicitud fue reenviada para revisión";
        mensaje.style.color = "orange";
        alert("🔄 Tu solicitud fue reenviada para revisión");
        setTimeout(() => {
            window.location.href = "login.html";
        }, 2000);
        return;
    }

    mensaje.innerText = "✅ Registro exitoso. Un administrador revisará tu solicitud.";
    mensaje.style.color = "green";

    alert("✅ Registro enviado. Un administrador revisará tu solicitud.");

    setTimeout(() => {
        window.location.href = "login.html";
    }, 2000);

})
.catch(error => {

    console.error(error);

    mensaje.innerText = "❌ Error al conectar con el servidor";
    mensaje.style.color = "red";

});
}


/* =================================
👁 MOSTRAR / OCULTAR CONTRASEÑA
================================= */

function togglePassword(id){

    const input = document.getElementById(id);

    if(input.type === "password"){
        input.type = "text";
    }else{
        input.type = "password";
    }

}


/* =================================
🔒 INDICADOR SEGURIDAD CONTRASEÑA
================================= */

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

document.getElementById("telefono").addEventListener("input", function() {
    this.value = this.value.replace(/\D/g, "").slice(0, 10);
});