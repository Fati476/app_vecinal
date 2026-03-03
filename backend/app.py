import threading

from flask import Flask, render_template, request, jsonify, send_from_directory

from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
from datetime import datetime, timedelta,timezone
import random

import os
from werkzeug.utils import secure_filename

from flask_socketio import SocketIO, emit, join_room
from dotenv import load_dotenv
from zoneinfo import ZoneInfo


load_dotenv()



API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
usuarios_online = {}
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

print("API KEY:", API_KEY)

# CONFIG CORREO


app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.environ.get("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")

app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_DEFAULT_SENDER")  

app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEBUG'] = True
app.config['MAIL_TIMEOUT'] = 15
mail = Mail(app)

print("MAIL_USERNAME:", app.config['MAIL_USERNAME'])
print("MAIL_PASSWORD existe:", app.config['MAIL_PASSWORD'] is not None)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "vecinal.db")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
print("DB PATH:", DB_PATH)
print("EXISTE:", os.path.exists(DB_PATH))

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)



@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "login.html")

# permitir abrir cualquier archivo html
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)

# -----------------------------
# Conexión a la base de datos
# -----------------------------
def conectar_db():
    return sqlite3.connect(DB_PATH)

# -----------------------------
# Ruta de prueba
# -----------------------------

# -----------------------------
# API: Registro de usuario
# -----------------------------
@app.route('/registro', methods=['POST'])
def registro():
    datos = request.get_json()

    if not datos:
        return jsonify({"error": "No se enviaron datos"}), 400

    nombre = datos.get('nombre')
    correo = datos.get('correo')
    telefono = datos.get('telefono')
    direccion = datos.get('direccion')
    password = datos.get('password')
    password2 = datos.get('password2')

    # 1️ Validar campos vacíos
    if not all([nombre, correo, telefono, direccion, password, password2]):
        return jsonify({"error": "Faltan datos"}), 400

    # 2️ Validar contraseñas iguales
    if password != password2:
        return jsonify({"error": "Las contraseñas no coinciden"}), 400

    # 3️ Validar contraseña segura
    patron = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$'

    if not re.match(patron, password):
        return jsonify({
            "error": "La contraseña debe tener mínimo 8 caracteres, letras, números y un símbolo"
        }), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    # 4️ Verificar correo duplicado
    cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = ?", (correo,))
    if cursor.fetchone():
        conexion.close()
        return jsonify({"error": "El correo ya está registrado"}), 400

    # 5️ Hash de contraseña
    password_hash = generate_password_hash(password)

    # 6️ Insertar usuario (PENDIENTE)
    cursor.execute("""
        INSERT INTO usuarios 
        (nombre, correo, contraseña, telefono, direccion, rol, estado, fecha_registro)
        VALUES (?, ?, ?, ?, ?, 'vecino', 'pendiente', DATE('now'))
    """, (nombre, correo, password_hash, telefono, direccion))

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Registro enviado. Tu cuenta será revisada por el administrador."
    })

# -----------------------------
# API: Login
# -----------------------------
@app.route('/login', methods=['POST'])
def login():
    datos = request.get_json()

    correo = datos.get('correo')
    password = datos.get('password')

    if not correo or not password:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_usuario, nombre, rol, contraseña, estado
        FROM usuarios
        WHERE correo = ?
    """, (correo,))

    usuario = cursor.fetchone()
    conexion.close()

    if not usuario or not check_password_hash(usuario[3], password):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    if usuario[4] == 'pendiente':
        return jsonify({"error": "Tu cuenta aún no ha sido aprobada"}), 403

    if usuario[4] == 'rechazado':
        return jsonify({"error": "Tu solicitud fue rechazada"}), 403

    return jsonify({
        "id_usuario": usuario[0],
        "nombre": usuario[1],
        "rol": usuario[2]
    })




@app.route('/usuarios', methods=['GET'])
def ver_usuarios():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_usuario, nombre, correo, rol, fecha_registro
        FROM usuarios
    """)

    datos = cursor.fetchall()
    conexion.close()

    lista = []

    for u in datos:
        lista.append({
            "id": u[0],
            "nombre": u[1],
            "correo": u[2],
            "rol": u[3],
            "fecha": u[4]
        })

    return jsonify(lista)

# -----------------------------
# API: Registrar incidencia
# -----------------------------
@app.route('/incidencias', methods=['POST'])
def crear_incidencia():
    print("🚨 ENDPOINT /incidencias LLAMADO", flush=True)

    data = request.get_json()

    titulo = data.get('titulo')
    descripcion = data.get('descripcion')
    tipo = data.get('tipo')
    lat = data.get('lat')
    lng = data.get('lng')
    id_usuario = data.get('id_usuario')

    if not all([titulo, descripcion, tipo, lat, lng, id_usuario]):
        return jsonify({"error": "Faltan datos"}), 400

    try:
        lat = float(lat)
        lng = float(lng)
        id_usuario = int(id_usuario)
    except ValueError:
        return jsonify({"error": "Datos inválidos"}), 400
    
    fecha_mexico = datetime.now(ZoneInfo("America/Mexico_City")).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO incidencias
        (titulo, descripcion, tipo, estado, fecha, lat, lng, id_usuario, activo)
        VALUES (?, ?, ?, 'activa', ?, ?, ?, ?, 1)
    """, (titulo, descripcion, tipo, fecha_mexico, lat, lng, id_usuario))

    conn.commit()
    conn.close()

    print("📧 Llamando función de correo...", flush=True)

    try:
        resultado = enviar_correo_incidencia(titulo, descripcion, lat, lng, tipo)
        print("📧 Resultado envio:", resultado, flush=True)
    except Exception as e:
        print("💥 ERROR AL ENVIAR CORREO:", str(e), flush=True)

    print("📧 CONFIG SMTP:", flush=True)
    print("SERVER:", app.config.get('MAIL_SERVER'), flush=True)
    print("PORT:", app.config.get('MAIL_PORT'), flush=True)
    print("USER:", app.config.get('MAIL_USERNAME'), flush=True)
    print("SENDER:", app.config.get('MAIL_DEFAULT_SENDER'), flush=True)

    return jsonify({"mensaje": "🚨 Incidencia creada correctamente"}), 200








@app.route("/incidencias/activas", methods=["GET"])
def incidencias_activas():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            i.id_incidencia AS id,
            i.titulo,
            i.descripcion,
            i.lat,
            i.lng,
            i.fecha,
            u.nombre AS usuario
        FROM incidencias i
        JOIN usuarios u ON i.id_usuario = u.id_usuario
        WHERE i.activo = 1
        ORDER BY datetime(i.fecha) DESC
        LIMIT 100
    """)

    incidencias = cursor.fetchall()
    conn.close()

    return jsonify([dict(i) for i in incidencias])






# -----------------------------
# API: Ver incidencias por usuario
# -----------------------------
@app.route('/incidencias', methods=['GET'])
def ver_incidencias():
    conn = get_db()

    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            i.id_incidencia AS id,
            i.titulo,
            i.descripcion,
            i.tipo,
            i.estado,
            i.fecha,
            i.lat,
            i.lng,
            u.nombre AS usuario
        FROM incidencias i
        JOIN usuarios u ON i.id_usuario = u.id_usuario
        ORDER BY datetime(i.fecha) DESC
        LIMIT 100
    """)

    datos = cursor.fetchall()
    conn.close()

    return jsonify([dict(i) for i in datos])




#apartado de incidencias en el menu 
@app.route('/incidencias/menu', methods=['GET'])
def listar_incidencias_menu():
    id_usuario = request.args.get('id_usuario', type=int)

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            i.id_incidencia,
            i.titulo,
            i.tipo,
            i.estado,
            i.fecha,
            u.nombre AS usuario,
            i.id_usuario AS id_dueno,

            -- 📍 COORDENADAS (LO NUEVO)
            i.lat,
            i.lng,

            CASE 
                WHEN i.id_usuario = ? THEN 1 ELSE 0 
            END AS es_mia,

            (
              SELECT CASE 
                WHEN rol = 'admin' THEN 1 ELSE 0 
              END
              FROM usuarios
              WHERE id_usuario = ?
            ) AS es_admin

        FROM incidencias i
        JOIN usuarios u ON i.id_usuario = u.id_usuario
        WHERE i.activo = 1
        ORDER BY datetime(i.fecha) DESC
        LIMIT 100
    """, (id_usuario, id_usuario))

    datos = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(datos), 200










@app.route('/incidencias/<int:id>/atender', methods=['PUT'])
def marcar_atendida(id):
    data = request.get_json()
    id_usuario = data.get('id_usuario')

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 🔎 Usuario
    cursor.execute(
        "SELECT id_usuario, rol FROM usuarios WHERE id_usuario = ?",
        (id_usuario,)
    )
    usuario = cursor.fetchone()

    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no válido"}), 403

    # 🔎 Incidencia
    cursor.execute(
        "SELECT id_usuario FROM incidencias WHERE id_incidencia = ?",
        (id,)
    )
    incidencia = cursor.fetchone()

    if not incidencia:
        conn.close()
        return jsonify({"error": "Incidencia no encontrada"}), 404

    # 🔐 REGLAS
    if usuario["rol"] == "vecino" and incidencia["id_usuario"] != id_usuario:
        conn.close()
        return jsonify({"error": "No autorizado"}), 403

    # ✅ Marcar atendida
    cursor.execute(
        "UPDATE incidencias SET estado = 'atendida' WHERE id_incidencia = ?",
        (id,)
    )
    
    print("ID USUARIO REQUEST:", id_usuario)
    print("ROL USUARIO:", usuario["rol"])
    print("ID DUEÑO INCIDENCIA:", incidencia["id_usuario"])

    conn.commit()
    conn.close()
    
    return jsonify({"mensaje": "Incidencia atendida correctamente"}), 200





















#api de inicidencias de usuarios 

@app.route('/incidencias/usuario/<int:id_usuario>', methods=['GET'])
def incidencias_usuario(id_usuario):
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_incidencia, titulo, descripcion, tipo, estado, fecha
        FROM incidencias
        WHERE id_usuario = ?
        ORDER BY fecha DESC
    """, (id_usuario,))

    datos = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "id": i[0],
            "titulo": i[1],
            "descripcion": i[2],
            "tipo": i[3],
            "estado": i[4],
            "fecha": i[5]
        } for i in datos
    ])








@app.route('/incidencias_mapa', methods=['GET'])
def incidencias_mapa():

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT i.id_incidencia, i.titulo, i.descripcion, i.tipo,
               g.latitud, g.longitud
        FROM incidencias i
        JOIN geolocalizacion g
        ON i.id_incidencia = g.id_incidencia
    """)

    datos = cursor.fetchall()
    conexion.close()

    lista = []

    for i in datos:
        lista.append({
            "id_incidencia": i[0],
            "titulo": i[1],
            "descripcion": i[2],
            "tipo": i[3],
            "latitud": i[4],
            "longitud": i[5]
        })

    return jsonify(lista)



@app.route('/geolocalizacion', methods=['POST'])
def guardar_geolocalizacion():
    datos = request.get_json()

    if not datos:
        return jsonify({"error": "No se enviaron datos"}), 400

    latitud = datos.get('latitud')
    longitud = datos.get('longitud')
    id_incidencia = datos.get('id_incidencia')

    if not latitud or not longitud or not id_incidencia:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO geolocalizacion (latitud, longitud, id_incidencia)
        VALUES (?, ?, ?)
    """, (latitud, longitud, id_incidencia))

    conexion.commit()
    conexion.close()

    return jsonify({"mensaje": "Ubicación registrada correctamente"})
@app.route('/mapa/incidencias', methods=['GET'])
def incidencias_con_ubicacion():

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT i.id_incidencia, i.titulo, i.descripcion, i.tipo,
               g.latitud, g.longitud
        FROM incidencias i
        JOIN geolocalizacion g
        ON i.id_incidencia = g.id_incidencia
    """)

    datos = cursor.fetchall()
    conexion.close()

    resultado = []

    for d in datos:
        resultado.append({
            "id_incidencia": d[0],
            "titulo": d[1],
            "descripcion": d[2],
            "tipo": d[3],
            "latitud": d[4],
            "longitud": d[5]
        })

    return jsonify(resultado)



@app.route('/notificaciones', methods=['POST'])
def crear_notificacion():
    datos = request.get_json()

    mensaje = datos.get('mensaje')
    id_usuario = datos.get('id_usuario')

    if not mensaje or not id_usuario:
        return jsonify({"error": "Faltan datos"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO notificaciones (mensaje, fecha, leida, id_usuario)
        VALUES (?, DATE('now'), 0, ?)
    """, (mensaje, id_usuario))

    conexion.commit()
    conexion.close()

    return jsonify({"mensaje": "Notificación creada correctamente"})

@app.route('/notificaciones/<int:id_usuario>', methods=['GET'])
def ver_notificaciones(id_usuario):

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_notificacion, mensaje, fecha, leida
        FROM notificaciones
        WHERE id_usuario = ?
        ORDER BY fecha DESC
    """, (id_usuario,))

    datos = cursor.fetchall()
    conexion.close()

    lista = []

    for n in datos:
        lista.append({
            "id_notificacion": n[0],
            "mensaje": n[1],
            "fecha": n[2],
            "leida": n[3]
        })

    return jsonify(lista)


@app.route('/notificaciones/leida/<int:id_notificacion>', methods=['PUT'])
def marcar_leida(id_notificacion):

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE notificaciones
        SET leida = 1
        WHERE id_notificacion = ?
    """, (id_notificacion,))

    conexion.commit()
    conexion.close()

    return jsonify({"mensaje": "Notificación marcada como leída"})




@app.route('/mensajes/<int:usuario1>/<int:usuario2>', methods=['GET'])
def ver_conversacion(usuario1, usuario2):

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT mensaje, fecha, id_emisor
        FROM mensajes
        WHERE (id_emisor = ? AND id_receptor = ?)
           OR (id_emisor = ? AND id_receptor = ?)
        ORDER BY fecha
    """, (usuario1, usuario2, usuario2, usuario1))

    datos = cursor.fetchall()
    conexion.close()

    chat = []

    for m in datos:
        chat.append({
            "mensaje": m[0],
            "fecha": m[1],
            "id_emisor": m[2]
        })

    return jsonify(chat)



@app.route('/admin/solicitudes', methods=['GET'])
def solicitudes_pendientes():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_usuario, nombre, correo, fecha_registro
        FROM usuarios
        WHERE estado = 'pendiente'
    """)

    datos = cursor.fetchall()
    conexion.close()

    return jsonify([
        {
            "id": s[0],
            "nombre": s[1],
            "correo": s[2],
            "fecha": s[3]
        } for s in datos
    ])

@app.route('/admin/aprobar/<int:id_usuario>', methods=['PUT'])
def aprobar_usuario(id_usuario):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT correo, nombre
        FROM usuarios
        WHERE id_usuario = ?
    """, (id_usuario,))

    usuario = cursor.fetchone()

    if not usuario:
        conexion.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    correo, nombre = usuario

    cursor.execute("""
        UPDATE usuarios
        SET estado = 'aprobado'
        WHERE id_usuario = ?
    """, (id_usuario,))
    # Agregar automáticamente al grupo general (id = 1)
    cursor.execute("""
        INSERT OR IGNORE INTO miembros_grupo (grupo_id, usuario_id)
        VALUES (1, ?)
    """, (id_usuario,))

    conexion.commit()
    conexion.close()

    try:
        enviar_correo(
            correo,
            "Cuenta aprobada - ConectaVecinos",
            f"Hola {nombre},\n\nTu cuenta ha sido APROBADA.\nYa puedes iniciar sesión.\n\nConectaVecinos"
        )
    except Exception as e:
        print("ERROR AL ENVIAR CORREO:", e)
        return jsonify({"error": "No se pudo enviar el correo"}), 500

    return jsonify({"mensaje": "Usuario aprobado y correo enviado"})




@app.route('/admin/rechazar/<int:id_usuario>', methods=['PUT'])
def rechazar_usuario(id_usuario):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT correo, nombre
        FROM usuarios
        WHERE id_usuario = ?
    """, (id_usuario,))

    usuario = cursor.fetchone()

    cursor.execute("""
        UPDATE usuarios
        SET estado = 'rechazado'
        WHERE id_usuario = ?
    """, (id_usuario,))

    conexion.commit()
    conexion.close()

    # 📧 Enviar correo
    enviar_correo(
        usuario[0],
        "Solicitud rechazada - ConectaVecinos",
        f"Hola {usuario[1]},\n\nTu solicitud fue RECHAZADA.\nPara más información contacta al administrador.\n\nConectaVecinos"
    )

    return jsonify({"mensaje": "Usuario rechazado"})


def enviar_correo(destinatario, asunto, mensaje):
    msg = Message(
        subject=asunto,
        recipients=[destinatario]
    )

    msg.body = mensaje
    msg.charset = "utf-8"

    mail.send(msg)

@app.route('/admin/aprobados', methods=['GET'])
def usuarios_aprobados():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_usuario, nombre, correo, telefono, direccion, fecha_registro
        FROM usuarios
        WHERE estado = 'aprobado'
          AND rol = 'vecino'
    """)

    datos = cursor.fetchall()
    conexion.close()

    return jsonify([
        {
            "id": u[0],
            "nombre": u[1],
            "correo": u[2],
            "telefono": u[3],
            "direccion": u[4],
            "fecha": u[5]
        } for u in datos
    ])


@app.route('/admin/eliminar/<int:id_usuario>', methods=['DELETE'])
def eliminar_usuario(id_usuario):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM usuarios
        WHERE id_usuario = ?
          AND rol = 'vecino'
    """, (id_usuario,))

    conexion.commit()
    conexion.close()

    return jsonify({"mensaje": "Usuario eliminado correctamente"})

@app.route('/admin/dashboard')
def dashboard():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE estado='pendiente'")
    pendientes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE estado='aprobado'")
    aprobados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE estado='rechazado'")
    rechazados = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "pendientes": pendientes,
        "aprobados": aprobados,
        "rechazados": rechazados
    })



@app.route('/recuperar', methods=['POST'])
def recuperar():
    correo = request.json.get("correo")

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_usuario, estado
        FROM usuarios
        WHERE correo = ?
    """, (correo.strip(),))

    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "Correo no registrado"}), 400

    if user[1] != "aprobado":
        return jsonify({"error": "Cuenta no aprobada"}), 403

    codigo = str(random.randint(100000, 999999))

    # ⏱ EXPIRA EN 10 MINUTOS
    expira = datetime.now() + timedelta(minutes=10)

    cursor.execute("""
        UPDATE usuarios
        SET reset_code = ?, reset_expira = ?
        WHERE correo = ?
    """, (codigo, expira, correo.strip()))

    conn.commit()
    conn.close()

    enviar_correo(
        correo,
        "Recuperar contraseña - ConectaVecinos",
        f"""Tu código de recuperación es:

{codigo}

⏱ Este código expira en 10 minutos.
Si no lo solicitaste, ignora este correo.
"""
    )

    return jsonify({"mensaje": "Código enviado al correo"})




@app.route('/resetear', methods=['POST'])
def resetear():
    data = request.json

    correo = data.get('correo')
    codigo = data.get('codigo')
    nueva = data.get('password')

    print("📩 DATA RECIBIDA:", data)

    if not correo or not codigo or not nueva:
        print("❌ Faltan datos")
        return jsonify({"error": "Completa todos los campos"}), 400

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT reset_code, reset_expira
        FROM usuarios
        WHERE correo = ?
    """, (correo.strip(),))

    user = cursor.fetchone()
    print("🧾 Resultado BD:", user)

    if not user or not user[0]:
        return jsonify({"error": "Código no válido o ya expirado"}), 400

    codigo_bd, expira = user

    # ⏳ VALIDAR EXPIRACIÓN (FORMA SEGURA)
    if expira:
        try:
            expira_dt = datetime.strptime(expira.split(".")[0], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expira_dt:
                return jsonify({"error": "El código ha expirado, solicita uno nuevo"}), 400
        except Exception as e:
            print("⚠️ Error al validar fecha:", e)

    # 🔢 VALIDAR CÓDIGO
    if codigo.strip() != codigo_bd.strip():
        return jsonify({"error": "Código incorrecto"}), 400

    # 🔐 VALIDAR CONTRASEÑA
    regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$'
    if not re.match(regex, nueva):
        return jsonify({"error": "Contraseña insegura"}), 400

    hash_pass = generate_password_hash(nueva)

    cursor.execute("""
        UPDATE usuarios
        SET contraseña = ?, reset_code = NULL, reset_expira = NULL
        WHERE correo = ?
    """, (hash_pass, correo.strip()))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Contraseña actualizada correctamente"})






@app.route('/reportes', methods=['POST'])
def crear_reporte():
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    id_usuario = request.form.get('id_usuario')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    foto = request.files.get('foto')

    if not titulo or not descripcion or not id_usuario or not lat or not lng:
        return jsonify({"error": "Faltan datos"}), 400

    ruta_foto = None

    if foto:
        filename = secure_filename(foto.filename.lower())
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        foto.save(ruta)
        ruta_foto = filename

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reportes (titulo, descripcion, foto, fecha, id_usuario, lat, lng, activo)
        VALUES (?, ?, ?, DATE('now'), ?, ?, ?, 1)
    """, (titulo, descripcion, ruta_foto, id_usuario, lat, lng))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Reporte creado correctamente"})




@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)





@app.route('/reportes', methods=['GET'])
def ver_reportes():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.id_reporte, r.titulo, r.descripcion, r.foto, r.fecha,
               u.nombre, r.id_usuario, r.lat, r.lng
        FROM reportes r
        JOIN usuarios u ON r.id_usuario = u.id_usuario
        WHERE r.activo = 1
        ORDER BY r.fecha DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "titulo": r[1],
            "descripcion": r[2],
            "foto": r[3],
            "fecha": r[4],
            "autor": r[5],
            "id_usuario": r[6],
            "lat": r[7],
            "lng": r[8]
        } for r in datos
    ])




@app.route('/reportes/<int:id_reporte>', methods=['DELETE'])
def eliminar_reporte(id_reporte):
    id_usuario = request.args.get('id_usuario')
    rol = request.args.get('rol')

    if not id_usuario or not rol:
        return jsonify({"error": "Datos insuficientes"}), 400

    id_usuario = int(id_usuario)

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_usuario
        FROM reportes
        WHERE id_reporte = ?
    """, (id_reporte,))

    reporte = cursor.fetchone()

    if not reporte:
        conn.close()
        return jsonify({"error": "Reporte no encontrado"}), 404

    dueño = reporte[0]

    if rol == "vecino" and id_usuario != dueño:
        conn.close()
        return jsonify({"error": "No autorizado"}), 403

    # ✅ ELIMINADO LÓGICO
    cursor.execute("""
        UPDATE reportes
        SET activo = 0
        WHERE id_reporte = ?
    """, (id_reporte,))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Reporte eliminado correctamente"})



@app.route('/reportes/<int:id_reporte>', methods=['PUT'])
def editar_reporte(id_reporte):
    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion")
    id_usuario = request.form.get("id_usuario")
    rol = request.form.get("rol")
    foto = request.files.get("foto")

    if not titulo or not descripcion or not id_usuario or not rol:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        id_usuario = int(id_usuario)
    except:
        return jsonify({"error": "Usuario inválido"}), 400

    if rol not in ["vecino", "admin"]:
        return jsonify({"error": "Rol no permitido"}), 403

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_usuario, foto
        FROM reportes
        WHERE id_reporte = ?
    """, (id_reporte,))

    reporte = cursor.fetchone()

    if not reporte:
        conn.close()
        return jsonify({"error": "Reporte no encontrado"}), 404

    dueño, foto_anterior = reporte

    # 🔐 Vecino solo edita lo suyo
    if rol == "vecino" and id_usuario != dueño:
        conn.close()
        return jsonify({"error": "No autorizado"}), 403

    nombre_foto = foto_anterior

    # 📸 si hay nueva imagen
    if foto:
        filename = secure_filename(foto.filename.lower())
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        foto.save(ruta)

        # borrar imagen vieja
        if foto_anterior:
            ruta_old = os.path.join(app.config["UPLOAD_FOLDER"], foto_anterior)
            if os.path.exists(ruta_old):
                os.remove(ruta_old)

        nombre_foto = filename

    cursor.execute("""
        UPDATE reportes
        SET titulo = ?, descripcion = ?, foto = ?
        WHERE id_reporte = ?
    """, (titulo, descripcion, nombre_foto, id_reporte))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Reporte actualizado correctamente"})


#correo incidencias 


def obtener_correos_vecinos():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT correo
        FROM usuarios
        WHERE rol = 'vecino'
        AND estado = 'aprobado'
    """)

    correos = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return correos


def obtener_correos_admin():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT correo
        FROM usuarios
        WHERE rol = 'admin'
        AND estado = 'aprobado'
    """)

    correos = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return correos




from flask import current_app
from flask_mail import Message

def enviar_correo_incidencia(titulo, descripcion, lat, lng, tipo):
    from datetime import datetime
    import requests, os

    print("📧 FUNCION DE CORREO EJECUTANDOSE", flush=True)

    try:
        correos = obtener_correos_admin()

        if tipo == "SOS":
            correos += obtener_correos_vecinos()

        correos = list(set(correos))

        print("📧 DESTINATARIOS:", correos, flush=True)

        if not correos:
            print("❌ No hay destinatarios", flush=True)
            return False

        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        data = {
            "personalizations": [
                {
                    "to": [{"email": c} for c in correos],
                    "subject": "🚨 Incidencia Vecinal"
                }
            ],
            "from": {
                "email": app.config['MAIL_DEFAULT_SENDER']
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": f"""
INCIDENCIA VECINAL

Título: {titulo}
Descripción: {descripcion}
Tipo: {tipo}
Fecha: {fecha}

Ubicación:
https://www.google.com/maps?q={lat},{lng}
"""
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {os.environ.get('MAIL_PASSWORD')}",
            "Content-Type": "application/json"
        }

        print("📤 Enviando por API...", flush=True)

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=data
        )

        print("📬 STATUS:", response.status_code, flush=True)
        print("📬 RESPUESTA:", response.text, flush=True)

        return response.status_code in (200, 202)

    except Exception as e:
        print("💥 ERROR ENVIO:", str(e), flush=True)
        return False

#perfil---------------------------------------------------------------------------------------------------------

@app.route("/api/perfil/<int:id_usuario>", methods=["GET"])
def obtener_perfil(id_usuario):
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, correo, rol, telefono, direccion, foto
        FROM usuarios
        WHERE id_usuario = ?
    """, (id_usuario,))

    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        return jsonify({
            "nombre": usuario[0],
            "correo": usuario[1],
            "rol": usuario[2],
            "telefono": usuario[3],
            "direccion": usuario[4],
            "foto": usuario[5]   # 👈 NUEVO
        })

    return jsonify({"error": "Usuario no encontrado"}), 404


@app.route("/api/perfil/foto", methods=["POST"])
def subir_foto_perfil():
    if "foto" not in request.files:
        return jsonify({"success": False, "message": "No se envió foto"}), 400

    foto = request.files["foto"]
    id_usuario = request.form.get("id_usuario")

    if not id_usuario or foto.filename == "":
        return jsonify({"success": False, "message": "Datos incompletos"}), 400

    extension = foto.filename.rsplit(".", 1)[1].lower()
    nombre_archivo = f"perfil_{id_usuario}.{extension}"
    ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre_archivo)

    foto.save(ruta)

    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE usuarios SET foto = ? WHERE id_usuario = ?",
        (nombre_archivo, id_usuario)
    )
    conn.commit()
    conn.close()

    return jsonify({
    "success": True,
    "foto": nombre_archivo
    })





@app.route("/api/perfil/<int:id_usuario>", methods=["PUT"])
def actualizar_perfil(id_usuario):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False, "message": "Sin datos"}), 400

    nombre = data.get("nombre")
    telefono = data.get("telefono")
    direccion = data.get("direccion")

    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE usuarios
            SET nombre = ?, telefono = ?, direccion = ?
            WHERE id_usuario = ?
        """, (nombre, telefono, direccion, id_usuario))

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print("❌ ERROR PERFIL:", e)
        return jsonify({"success": False}), 500




@app.route("/uploads/<filename>")
def mostrar_foto(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/api/perfil/foto/<int:id_usuario>", methods=["DELETE"])
def eliminar_foto(id_usuario):
    conn = conectar_db()
    cursor = conn.cursor()

    # 🔎 Obtener nombre de la foto actual
    cursor.execute("SELECT foto FROM usuarios WHERE id_usuario = ?", (id_usuario,))
    usuario = cursor.fetchone()

    if usuario and usuario[0]:
        nombre_foto = usuario[0]
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto)

        # 🗑 borrar archivo físico si existe
        if os.path.exists(ruta):
            os.remove(ruta)

    # 🧹 poner foto en NULL en la BD
    cursor.execute(
        "UPDATE usuarios SET foto = NULL WHERE id_usuario = ?",
        (id_usuario,)
    )

    conn.commit()
    conn.close()

    return jsonify({"success": True})

#mensajes ------------------------------------------------------------------------------------------------








#asistente ---------------------------------------------------------------------------------
import requests

def obtener_reportes_activos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT descripcion FROM reportes WHERE activo = 1")
    resultados = cursor.fetchall()

    conn.close()

    if not resultados:
        return "📋 Actualmente no hay reportes activos."

    texto = "📋 Reportes activos:\n"
    for r in resultados:
        texto += f"- {r[0]}\n"

    return texto





def preguntar_ia(mensaje_usuario):

    contexto = """
    Eres el asistente virtual de la aplicación vecinal de la Sección 130 
    de San Mateo Tlalchichilpan, municipio de Almoloya de Juárez, Estado de México.

    Habla como un vecino amable y claro.
    Responde de forma breve (máximo 6 líneas).
    No uses títulos ni formato por secciones.
    No escribas textos largos.

    Si preguntan sobre la Sección 130, da información real de San Mateo Tlalchichilpan.
    Si preguntan sobre otras secciones, responde que solo tienes información de la Sección 130.
    Si preguntan sobre la aplicación, explica únicamente sus funciones reales:
    - Reportes de incidencias que es algo que al momento de crear un vecino una incidencia se generara en automatico las cuales se generaran en una burbuja flotante en la pagina con un boton de ir a la ubicacion, de igual forma se encontra un apartado den en el lado lateral del menu donde las podras visualizar y se encotraran en orden de fecha y hora, ademas de que se muestra quien la hizo y con el boton de ir a la ubicaicion, en caso de que sea de ellos la podran marcar como atendidas y en automatico se borran en 7 dias.
    - Reportes vecinales son como un reporte de luz, un bache, un poste caído, etc. que los vecinos pueden crear con una foto, descripción y ubicación. Estos reportes se muestran en un apartado del menú y en un mapa. Los vecinos pueden eliminar o editar sus propios reportes, y los administradores pueden eliminar cualquier reporte.
    - Envío de mensajes
    - Se envia una notificación a los vecinos cuando se crea un reporte SOS o una incidencia, y a los administradores por cualquier reporte o incidencia por correo electrónico.
    - Un perfil de usuario donde pueden actualizar su información y foto de perfil.
    - Un sistema de aprobación de cuentas donde los administradores aprueban o rechazan las solicitudes de registro, y se envía un correo al usuario con la decisión.
    - Un sistema de recuperación de contraseña con código enviado por correo.
    - Un dashboard para administradores con estadísticas de usuarios.
    - Un chat privado entre vecinos.
    - Un boton de emegencia SOS que notifica a todos los vecinos y administradores.

    No inventes funciones que no existen.
    Puedes responder preguntas generales, pero siempre mantente dentro del contexto comunitario.
    Sé profesional, amable y claro.
    """

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": contexto},
            {"role": "user", "content": mensaje_usuario}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    resultado = response.json()

    return resultado["choices"][0]["message"]["content"]



@socketio.on("mensaje_ia")
def manejar_mensaje(data):
    mensaje = data["mensaje"].lower()

    if "reporte" in mensaje or "activo" in mensaje or "pendiente" in mensaje:
        respuesta = obtener_reportes_activos()
    else:
        respuesta = preguntar_ia(mensaje)

    emit("respuesta_ia", {"respuesta": respuesta})






#mensaje 2.0



# ===== SOCKET CHAT GRUPO =====

@socketio.on("unirse_grupo")
def unirse_grupo(data):
    grupo_id = data["grupo_id"]
    join_room(str(grupo_id))


@socketio.on("enviar_mensaje_grupo")
def manejar_mensaje_grupo(data):
    grupo_id = data["grupo_id"]
    usuario_id = data["usuario_id"]
    mensaje = data["mensaje"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO mensajes_grupo (grupo_id, usuario_id, mensaje)
        VALUES (?, ?, ?)
    """, (grupo_id, usuario_id, mensaje))
    conn.commit()

    cursor.execute("""
        SELECT nombre FROM usuarios WHERE id_usuario = ?
    """, (usuario_id,))
    usuario = cursor.fetchone()
    conn.close()

    # 👇👇👇 AQUÍ 👇👇👇
    emit(
        "nuevo_mensaje",
        {
            "usuario_id": int(usuario_id),
            "nombre": usuario["nombre"],
            "mensaje": mensaje,
            "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        },
        room=str(grupo_id)
    )


usuarios_conectados = {}

@socketio.on("registrar_usuario")
def registrar(data):
    usuario_id = data["usuario_id"]
    usuarios_conectados[usuario_id] = request.sid

    emit("usuarios_activos",
         list(usuarios_conectados.keys()),
         broadcast=True)


@socketio.on("disconnect")
def desconectar():
    for usuario_id, sid in list(usuarios_conectados.items()):
        if sid == request.sid:
            del usuarios_conectados[usuario_id]

    emit("usuarios_activos",
         list(usuarios_conectados.keys()),
         broadcast=True)
    

@socketio.on("enviar_mensaje_privado")
def mensaje_privado(data):
    emisor = data["emisor_id"]
    receptor = data["receptor_id"]
    mensaje = data["mensaje"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO mensajes_privados (emisor_id, receptor_id, mensaje)
        VALUES (?, ?, ?)
    """, (emisor, receptor, mensaje))

    conn.commit()
    conn.close()

    # Enviar solo al receptor
    if receptor in usuarios_conectados:
        emit("mensaje_privado", data,
             room=usuarios_conectados[receptor])


@socketio.on("cargar_mensajes")
def cargar_mensajes(data):
    grupo_id = data["grupo_id"]

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
          mensajes_grupo.usuario_id,
          usuarios.nombre, 
          mensajes_grupo.mensaje, 
          mensajes_grupo.fecha
        FROM mensajes_grupo
        JOIN usuarios 
            ON mensajes_grupo.usuario_id = usuarios.id_usuario
        WHERE grupo_id = ?
        ORDER BY fecha ASC
    """, (grupo_id,))

    rows = cursor.fetchall()
    conn.close()

    mensajes = [dict(row) for row in rows]

    emit("mensajes_anteriores", mensajes)



@socketio.on("usuario_escribiendo")
def usuario_escribiendo(data):
    grupo_id = data["grupo_id"]
    usuario_id = data["usuario_id"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM usuarios WHERE id_usuario = ?", (usuario_id,))
    usuario = cursor.fetchone()
    conn.close()

    emit("mostrar_escribiendo", {
        "nombre": usuario["nombre"]
    }, room=str(grupo_id), include_self=False)

@socketio.on("usuario_dejo_escribir")
def usuario_dejo_escribir(data):
    grupo_id = data["grupo_id"]
    emit("ocultar_escribiendo", room=str(grupo_id))



@socketio.on("connect")
def test_connect():
    print("Nueva conexión:", request.sid)

# -----------------------------
# Ejecutar servidor
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        allow_unsafe_werkzeug=True
    )