import threading

from flask import Flask, render_template, request, jsonify, send_from_directory

from flask_cors import CORS
from flask_mail import Mail, Message
import psycopg2
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
from psycopg2.extras import RealDictCursor

load_dotenv()



API_KEY = os.getenv("OPENROUTER_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
CORS(app)
print("🔥 VERSION NUEVA DESPLEGADA 🔥")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
usuarios_online = {}
#def get_db():
    #conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    #conn.row_factory = sqlite3.Row
    #return conn

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

DB_PATH = os.path.join(BASE_DIR, "vecinal.db")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
#print("DB PATH:", DB_PATH)
#print("EXISTE:", os.path.exists(DB_PATH))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads")
UPLOAD_FOLDER = os.path.abspath(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db():

    

    # Si estamos en Render usamos PostgreSQL
    if DATABASE_URL:
        print("🟢 Conectado a PostgreSQL")
        conn = psycopg2.connect(DATABASE_URL)
        return conn

    # Si estamos en local usamos SQLite
    else:
        print("🟡 Conectado a SQLite")
        conn = sqlite3.connect("backend/vecinal.db", timeout=15, check_same_thread=False)
        #conn.row_factory = sqlite3.Row
        return conn



historial_conversaciones = {}

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
#def conectar_db():
    #return sqlite3.connect(DB_PATH)

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

    conexion = get_db()
    cursor = conexion.cursor()

    # 4️ Verificar si el correo ya existe
    cursor.execute("""
        SELECT id_usuario, estado 
        FROM usuarios 
        WHERE correo = %s
    """, (correo,))

    usuario = cursor.fetchone()

    # 5️ Hash de contraseña
    password_hash = generate_password_hash(password)

    # 🔁 SI YA EXISTE
    if usuario:
        id_usuario, estado = usuario

        # 🔄 SI ESTÁ RECHAZADO → REACTIVAR
        if estado == "rechazado":
            print("🔄 Reactivando usuario rechazado...", flush=True)

            cursor.execute("""
                UPDATE usuarios
                SET nombre = %s,
                    contraseña = %s,
                    telefono = %s,
                    direccion = %s,
                    estado = 'pendiente',
                    fecha_registro = NOW()
                WHERE id_usuario = %s
            """, (nombre, password_hash, telefono, direccion, id_usuario))

            conexion.commit()
            conexion.close()

            return jsonify({
                "mensaje": "Solicitud reenviada. Será revisada nuevamente."
            }), 200

        # ❌ SI YA EXISTE (PENDIENTE O APROBADO)
        else:
            conexion.close()
            return jsonify({
                "error": "El correo ya está registrado"
            }), 400

    # 🆕 SI NO EXISTE → CREAR NUEVO
    cursor.execute("""
        INSERT INTO usuarios 
        (nombre, correo, contraseña, telefono, direccion, rol, estado, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, 'vecino', 'pendiente', NOW())
    """, (nombre, correo, password_hash, telefono, direccion))

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Registro exitoso. Tu cuenta será revisada por el administrador."
    }), 200

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

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_usuario, nombre, rol, contraseña, estado
        FROM usuarios
        WHERE correo = %s
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
    conexion = get_db()
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

    # Hora de México
    fecha_mexico = datetime.now(ZoneInfo("America/Mexico_City")).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 🔹 Obtener nombre y rol del usuario
    cursor.execute(
        "SELECT nombre, rol FROM usuarios WHERE id_usuario = %s",
        (id_usuario,)
    )
    usuario = cursor.fetchone()

    if usuario:
        nombre_usuario = usuario["nombre"]
        rol_usuario = usuario["rol"]
    else:
        nombre_usuario = "Vecino"
        rol_usuario = "usuario"

    # 🔹 Insertar incidencia
    cursor.execute("""
        INSERT INTO incidencias
        (titulo, descripcion, tipo, estado, fecha, lat, lng, id_usuario, activo)
        VALUES (%s, %s, %s, 'activa', %s, %s, %s, %s, 1)
        RETURNING id_incidencia
    """, (titulo, descripcion, tipo, fecha_mexico, lat, lng, id_usuario))

    # 🔹 Obtener ID de la incidencia creada
    id_incidencia = cursor.fetchone()["id_incidencia"]
    conn.commit()

    # 🔴 Emitir incidencia en tiempo real
    socketio.emit("nueva_incidencia", {
        "id": id_incidencia,
        "titulo": titulo,
        "descripcion": descripcion,
        "tipo": tipo,
        "lat": lat,
        "lng": lng,
        "fecha": fecha_mexico,
        "id_usuario": id_usuario,
        "usuario": nombre_usuario,
        "rol": rol_usuario
    })

    conn.close()

    print("📧 Llamando función de correo...", flush=True)

    try:
        resultado = enviar_correo_incidencia(titulo, descripcion, lat, lng, tipo, fecha_mexico,nombre_usuario)
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
    #conn.row_factory = sqlite3.Row
    cursor = conn.cursor(cursor_factory=RealDictCursor)
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
        ORDER BY i.fecha DESC
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

    #conn.row_factory = sqlite3.Row
    cursor = conn.cursor(cursor_factory=RealDictCursor)

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
        ORDER BY i.fecha DESC
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
    #conn.row_factory = sqlite3.Row
    cursor = conn.cursor(cursor_factory=RealDictCursor)

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
                WHEN i.id_usuario = %s THEN 1 ELSE 0 
            END AS es_mia,

            (
              SELECT CASE 
                WHEN rol = 'admin' THEN 1 ELSE 0 
              END
              FROM usuarios
              WHERE id_usuario = %s
            ) AS es_admin

        FROM incidencias i
        JOIN usuarios u ON i.id_usuario = u.id_usuario
        WHERE i.activo = 1
        ORDER BY i.fecha DESC
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
    #conn.row_factory = sqlite3.Row
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 🔎 Usuario
    cursor.execute(
        "SELECT id_usuario, rol FROM usuarios WHERE id_usuario = %s",
        (id_usuario,)
    )
    usuario = cursor.fetchone()

    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no válido"}), 403

    # 🔎 Incidencia
    cursor.execute(
        "SELECT id_usuario FROM incidencias WHERE id_incidencia = %s",
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
        "UPDATE incidencias SET estado = 'atendida' WHERE id_incidencia = %s",
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
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id_incidencia, titulo, descripcion, tipo, estado, fecha
        FROM incidencias
        WHERE id_usuario = %s
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

    conexion = get_db()
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

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO geolocalizacion (latitud, longitud, id_incidencia)
        VALUES (%s, %s, %s)
    """, (latitud, longitud, id_incidencia))

    conexion.commit()
    conexion.close()

    return jsonify({"mensaje": "Ubicación registrada correctamente"})
@app.route('/mapa/incidencias', methods=['GET'])
def incidencias_con_ubicacion():

    conexion = get_db()
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

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO notificaciones (mensaje, fecha, leida, id_usuario)
        VALUES (%s, NOW(), 0, %s)
    """, (mensaje, id_usuario))

    conexion.commit()
    conexion.close()

    return jsonify({"mensaje": "Notificación creada correctamente"})

@app.route('/notificaciones/<int:id_usuario>', methods=['GET'])
def ver_notificaciones(id_usuario):

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_notificacion, mensaje, fecha, leida
        FROM notificaciones
        WHERE id_usuario = %s
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

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE notificaciones
        SET leida = 1
        WHERE id_notificacion = %s
    """, (id_notificacion,))

    conexion.commit()
    conexion.close()

    return jsonify({"mensaje": "Notificación marcada como leída"})




@app.route('/mensajes/<int:usuario1>/<int:usuario2>', methods=['GET'])
def ver_conversacion(usuario1, usuario2):

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT mensaje, fecha, id_emisor
        FROM mensajes
        WHERE (id_emisor = %s AND id_receptor = %s)
           OR (id_emisor = %s AND id_receptor = %s)
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
    conexion = get_db()
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
            "id_usuario": s[0],
            "nombre": s[1],
            "correo": s[2],
            "fecha": s[3]
        } for s in datos
    ])

@app.route('/admin/aprobar/<int:id_usuario>', methods=['POST'])
def aprobar_usuario(id_usuario):

    print("🚨 1. ENTRÓ A LA RUTA /admin/aprobar", flush=True)

    try:
        conexion = get_db()
        cursor = conexion.cursor()

        print("🚨 2. CONEXIÓN OK", flush=True)

        cursor.execute("""
            SELECT correo, nombre
            FROM usuarios
            WHERE id_usuario = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()
        print("🚨 3. USUARIO:", usuario, flush=True)

        if not usuario:
            conexion.close()
            return jsonify({"error": "Usuario no encontrado"}), 404

        correo, nombre = usuario

        cursor.execute("""
            UPDATE usuarios
            SET estado = 'aprobado'
            WHERE id_usuario = %s
        """, (id_usuario,))

        cursor.execute("""
            INSERT INTO miembros_grupo (grupo_id, usuario_id)
            VALUES (1, %s)
        """, (id_usuario,))

        conexion.commit()
        conexion.close()

        print("📧 Enviando correo con SendGrid...", flush=True)

        # 🔥 USAR ESTA FUNCIÓN
        resultado = enviar_correo_aprobacion(correo, nombre)

        print("📧 Resultado:", resultado, flush=True)

        return jsonify({"mensaje": "Usuario aprobado y correo enviado"})

    except Exception as e:
        print("💥 ERROR GENERAL:", e, flush=True)
        return jsonify({"error": str(e)}), 500
    
def enviar_correo_aprobacion(correo, nombre):
    import requests, os

    print("📧 ENVIANDO CORREO DE APROBACIÓN", flush=True)

    try:
        data = {
            "personalizations": [
                {
                    "to": [{"email": correo}],
                    "subject": "Cuenta aprobada - ConectaVecinos"
                }
            ],
            "from": {
                "email": os.environ.get("MAIL_DEFAULT_SENDER")
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": f"""
Hola {nombre},

Tu cuenta ha sido APROBADA 🎉
Ya puedes iniciar sesión.

ConectaVecinos
"""
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {os.environ.get('MAIL_PASSWORD')}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=data
        )

        print("📬 STATUS:", response.status_code, flush=True)
        print("📬 RESPUESTA:", response.text, flush=True)

        return response.status_code in (200, 202)

    except Exception as e:
        print("💥 ERROR CORREO:", str(e), flush=True)
        return False




@app.route('/admin/rechazar/<int:id_usuario>', methods=['POST'])
def rechazar_usuario(id_usuario):

    print("🚨 ENTRÓ A /admin/rechazar", flush=True)

    try:
        conexion = get_db()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT correo, nombre
            FROM usuarios
            WHERE id_usuario = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()

        if not usuario:
            conexion.close()
            return jsonify({"error": "Usuario no encontrado"}), 404

        correo, nombre = usuario

        cursor.execute("""
            UPDATE usuarios
            SET estado = 'rechazado'
            WHERE id_usuario = %s
        """, (id_usuario,))

        conexion.commit()
        conexion.close()

        print("📧 Enviando correo de rechazo...", flush=True)

        resultado = enviar_correo_rechazo(correo, nombre)

        print("📧 Resultado:", resultado, flush=True)

        return jsonify({"mensaje": "Usuario rechazado y correo enviado"})

    except Exception as e:
        print("💥 ERROR:", e, flush=True)
        return jsonify({"error": str(e)}), 500


def enviar_correo_rechazo(correo, nombre):
    import requests, os

    print("📧 ENVIANDO CORREO DE RECHAZO", flush=True)

    try:
        data = {
            "personalizations": [
                {
                    "to": [{"email": correo}],
                    "subject": "Solicitud rechazada - ConectaVecinos"
                }
            ],
            "from": {
                "email": os.environ.get("MAIL_DEFAULT_SENDER")
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": f"""
Hola {nombre},

Tu solicitud fue RECHAZADA ❌

Para más información contacta al administrador.

ConectaVecinos
"""
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {os.environ.get('MAIL_PASSWORD')}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=data
        )

        print("📬 STATUS:", response.status_code, flush=True)
        print("📬 RESPUESTA:", response.text, flush=True)

        return response.status_code in (200, 202)

    except Exception as e:
        print("💥 ERROR CORREO:", str(e), flush=True)
        return False
    



def enviar_correo(destinatario, asunto, mensaje):
    print("📤 Preparando correo a:", destinatario)

    try:
        with app.app_context():  # 👈 CLAVE
            msg = Message(
                subject=asunto,
                recipients=[destinatario],
                sender=app.config["MAIL_DEFAULT_SENDER"]
            )

            msg.body = mensaje

            mail.send(msg)

        print("✅ CORREO ENVIADO")

    except Exception as e:
        print("💥 ERROR CORREO:", e)
        raise e

def enviar_correo_async(destinatario, asunto, mensaje):
    def tarea():
        try:
            enviar_correo(destinatario, asunto, mensaje)
        except Exception as e:
            print("💥 ERROR EN HILO:", e)

    threading.Thread(target=tarea).start()

@app.route('/admin/aprobados', methods=['GET'])
def usuarios_aprobados():
    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_usuario, nombre, correo, telefono, direccion, fecha_registro
        FROM usuarios
        WHERE estado = 'aprobado'
          AND rol = 'vecino'
    """)

    datos = cursor.fetchall()
    conexion.close()

    resultado = []

    for u in datos:
        fecha_formateada = u[5].strftime("%d/%m/%Y %H:%M") if u[5] else ""

        resultado.append({
            "id": u[0],
            "nombre": u[1],
            "correo": u[2],
            "telefono": u[3],
            "direccion": u[4],
            "fecha": fecha_formateada
        })

    return jsonify(resultado)

def enviar_correo_eliminacion(correo, nombre):
    import requests, os

    print("📧 ENVIANDO CORREO DE ELIMINACIÓN", flush=True)

    try:
        data = {
            "personalizations": [
                {
                    "to": [{"email": correo}],
                    "subject": "Cuenta eliminada - ConectaVecinos"
                }
            ],
            "from": {
                "email": os.environ.get("MAIL_DEFAULT_SENDER")
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": f"""
Hola {nombre},

Tu cuenta ha sido eliminada por el administrador.

Si consideras que esto fue un error, puedes volver a registrarte o contactar al administrador.

ConectaVecinos
"""
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {os.environ.get('MAIL_PASSWORD')}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=data
        )

        print("📬 STATUS:", response.status_code, flush=True)
        print("📬 RESPUESTA:", response.text, flush=True)

        return response.status_code in (200, 202)

    except Exception as e:
        print("💥 ERROR CORREO:", str(e), flush=True)
        return False
    

@app.route('/admin/eliminar/<int:id_usuario>', methods=['DELETE'])
def eliminar_usuario(id_usuario):

    print("🚨 ELIMINANDO USUARIO:", id_usuario, flush=True)

    try:
        conexion = get_db()
        cursor = conexion.cursor()

        # 🔍 Obtener datos del usuario
        cursor.execute("""
            SELECT correo, nombre
            FROM usuarios
            WHERE id_usuario = %s AND rol = 'vecino'
        """, (id_usuario,))

        usuario = cursor.fetchone()

        if not usuario:
            conexion.close()
            return jsonify({"error": "Usuario no encontrado"}), 404

        correo, nombre = usuario

        print("👤 Usuario:", correo, nombre, flush=True)

        # 🗑️ Eliminar usuario
        cursor.execute("""
            DELETE FROM usuarios
            WHERE id_usuario = %s AND rol = 'vecino'
        """, (id_usuario,))

        conexion.commit()
        conexion.close()

        print("🗑️ Usuario eliminado", flush=True)

        # 📧 Enviar correo (NO rompe si falla)
        try:
            enviar_correo_eliminacion(correo, nombre)
        except Exception as e:
            print("⚠️ Error enviando correo:", e, flush=True)

        return jsonify({"mensaje": "Usuario eliminado correctamente"})

    except Exception as e:
        print("💥 ERROR GENERAL:", e, flush=True)
        return jsonify({"error": str(e)}), 500

@app.route('/admin/dashboard')
def dashboard():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

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

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id_usuario, estado
        FROM usuarios
        WHERE correo = %s
    """, (correo.strip(),))

    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "Correo no registrado"}), 400

    if user["estado"] != "aprobado":
        conn.close()
        return jsonify({"error": "Cuenta no aprobada"}), 403

    codigo = str(random.randint(100000, 999999))

    # ⏱ Expira en 10 minutos
    expira = datetime.now() + timedelta(minutes=10)

    cursor.execute("""
        UPDATE usuarios
        SET reset_code = %s, reset_expira = %s
        WHERE correo = %s
    """, (codigo, expira, correo.strip()))

    conn.commit()
    conn.close()

    print("📧 Enviando código de recuperación...", flush=True)

    # ✅ LLAMADA CORRECTA
    resultado = enviar_correo_codigo(correo, codigo)

    print("📧 Resultado envío:", resultado, flush=True)

    return jsonify({"mensaje": "Código enviado al correo"})

def enviar_correo_codigo(correo, codigo):
    import requests, os

    print("📧 ENVIANDO CÓDIGO DE RECUPERACIÓN", flush=True)

    try:
        data = {
            "personalizations": [
                {
                    "to": [{"email": correo}],
                    "subject": "Recuperar contraseña - ConectaVecinos"
                }
            ],
            "from": {
                "email": os.environ.get("MAIL_DEFAULT_SENDER")
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": f"""
Tu código de recuperación es:

{codigo}

⏱ Este código expira en 10 minutos.
Si no lo solicitaste, ignora este correo.
"""
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {os.environ.get('MAIL_PASSWORD')}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=data
        )

        print("📬 STATUS:", response.status_code, flush=True)
        print("📬 RESPUESTA:", response.text, flush=True)

        return response.status_code in (200, 202)

    except Exception as e:
        print("💥 ERROR CORREO:", str(e), flush=True)
        return False



@app.route('/resetear', methods=['POST'])
def resetear():
    data = request.json

    correo = data.get('correo')
    codigo = data.get('codigo')
    nueva = data.get('password')

    print("📩 DATA RECIBIDA:", data, flush=True)

    if not correo or not codigo or not nueva:
        return jsonify({"error": "Completa todos los campos"}), 400

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)  # ✅ CORREGIDO

    cursor.execute("""
        SELECT reset_code, reset_expira
        FROM usuarios
        WHERE correo = %s
    """, (correo.strip(),))

    user = cursor.fetchone()
    print("🧾 Resultado BD:", user, flush=True)

    # ❌ VALIDAR EXISTENCIA
    if not user or not user["reset_code"]:
        conn.close()
        return jsonify({"error": "Código no válido o ya expirado"}), 400

    codigo_bd = user["reset_code"]
    expira = user["reset_expira"]

    # ⏳ VALIDAR EXPIRACIÓN
    if expira:
        try:
            if datetime.now() > expira:
                conn.close()
                return jsonify({"error": "El código ha expirado, solicita uno nuevo"}), 400
        except Exception as e:
            print("⚠️ Error al validar fecha:", e, flush=True)

    # 🔢 VALIDAR CÓDIGO
    if codigo.strip() != codigo_bd.strip():
        conn.close()
        return jsonify({"error": "Código incorrecto"}), 400

    # 🔐 VALIDAR CONTRASEÑA (CORREGIDA)
    regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$'
    if not re.match(regex, nueva):
        conn.close()
        return jsonify({"error": "Contraseña insegura"}), 400

    hash_pass = generate_password_hash(nueva)

    cursor.execute("""
        UPDATE usuarios
        SET contraseña = %s, reset_code = NULL, reset_expira = NULL
        WHERE correo = %s
    """, (hash_pass, correo.strip()))

    conn.commit()
    conn.close()

    print("✅ CONTRASEÑA ACTUALIZADA", flush=True)

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

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        INSERT INTO reportes (titulo, descripcion, foto, fecha, id_usuario, lat, lng, activo)
        VALUES (%s, %s, %s, NOW(), %s, %s, %s, 1)
    """, (titulo, descripcion, ruta_foto, id_usuario, lat, lng))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Reporte creado correctamente"})




@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)





@app.route('/reportes', methods=['GET'])
def ver_reportes():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

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
            "id": r["id_reporte"],
            "titulo": r["titulo"],
            "descripcion": r["descripcion"],
            "foto": r["foto"],
            "fecha": r["fecha"],
            "autor": r["nombre"],
            "id_usuario": r["id_usuario"],
            "lat": r["lat"],
            "lng": r["lng"]
        } for r in datos
    ])




@app.route('/reportes/<int:id_reporte>', methods=['DELETE'])
def eliminar_reporte(id_reporte):
    id_usuario = request.args.get('id_usuario')
    rol = request.args.get('rol')

    if not id_usuario or not rol:
        return jsonify({"error": "Datos insuficientes"}), 400

    id_usuario = int(id_usuario)

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id_usuario
        FROM reportes
        WHERE id_reporte = %s
    """, (id_reporte,))

    reporte = cursor.fetchone()

    if not reporte:
        conn.close()
        return jsonify({"error": "Reporte no encontrado"}), 404

    dueño = reporte["id_usuario"]

    if rol == "vecino" and id_usuario != dueño:
        conn.close()
        return jsonify({"error": "No autorizado"}), 403

    # ✅ ELIMINADO LÓGICO
    cursor.execute("""
        UPDATE reportes
        SET activo = 0
        WHERE id_reporte = %s
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

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id_usuario, foto
        FROM reportes
        WHERE id_reporte = %s
    """, (id_reporte,))

    reporte = cursor.fetchone()

    if not reporte:
        conn.close()
        return jsonify({"error": "Reporte no encontrado"}), 404

    dueño = reporte["id_usuario"]
    foto_anterior = reporte["foto"]

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
        SET titulo = %s, descripcion = %s, foto = %s
        WHERE id_reporte = %s
    """, (titulo, descripcion, nombre_foto, id_reporte))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Reporte actualizado correctamente"})


#correo incidencias 


def obtener_correos_vecinos():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT correo
        FROM usuarios
        WHERE rol = 'vecino'
        AND estado = 'aprobado'
    """)

    correos = [fila["correo"] for fila in cursor.fetchall()]

    conn.close()
    return correos


def obtener_correos_admin():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT correo
        FROM usuarios
        WHERE rol = 'admin'
        AND estado = 'aprobado'
    """)

    correos = [fila["correo"] for fila in cursor.fetchall()]

    conn.close()
    return correos




from flask import current_app
from flask_mail import Message

def enviar_correo_incidencia(titulo, descripcion, lat, lng, tipo, fecha, usuario):
    import requests, os

    print("📧 FUNCION DE CORREO EJECUTANDOSE", flush=True)

    try:
        print("🔎 Obteniendo correos admin...", flush=True)
        correos = obtener_correos_admin()

        print("📧 Correos admin:", correos, flush=True)

        if tipo == "SOS":
            print("🔎 Obteniendo correos vecinos...", flush=True)
            vecinos = obtener_correos_vecinos()
            print("📧 Correos vecinos:", vecinos, flush=True)
            correos += vecinos

        correos = list(set(correos))

        print("📧 DESTINATARIOS:", correos, flush=True)

        if not correos:
            print("❌ No hay destinatarios", flush=True)
            return False


        data = {
            "personalizations": [
                {
                    "to": [{"email": c} for c in correos],
                    "subject": f"🚨 Nueva incidencia vecinal ({tipo})"
                }
            ],
            "from": {
                "email": os.environ.get("MAIL_DEFAULT_SENDER")
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": f"""
🚨 INCIDENCIA VECINAL

👤 Reportado por: {usuario}

📌 Título: {titulo}

📝 Descripción:
{descripcion}

⚠ Tipo:
{tipo}

📅 Fecha:
{fecha}

📍 Ubicación:
https://www.google.com/maps?q={lat},{lng}
"""
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {os.environ.get('MAIL_PASSWORD')}",
            "Content-Type": "application/json"
        }

        print("📤 Enviando correo con SendGrid...", flush=True)

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
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT nombre, correo, rol, telefono, direccion, foto
        FROM usuarios
        WHERE id_usuario = %s
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

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "UPDATE usuarios SET foto = %s WHERE id_usuario = %s",
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
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            UPDATE usuarios
            SET nombre = %s, telefono = %s, direccion = %s
            WHERE id_usuario = %s
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
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 🔎 Obtener nombre de la foto actual
    cursor.execute("SELECT foto FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    usuario = cursor.fetchone()

    if usuario and usuario[0]:
        nombre_foto = usuario[0]
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto)

        # 🗑 borrar archivo físico si existe
        if os.path.exists(ruta):
            os.remove(ruta)

    # 🧹 poner foto en NULL en la BD
    cursor.execute(
        "UPDATE usuarios SET foto = NULL WHERE id_usuario = %s",
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT descripcion FROM reportes WHERE activo = 1")
    resultados = cursor.fetchall()

    conn.close()

    if not resultados:
        return "📋 Actualmente no hay reportes activos."

    texto = "📋 Reportes activos:\n"
    for r in resultados:
        texto += f"- {r[0]}\n"

    return texto





def preguntar_ia(mensaje_usuario, sid):

    contexto = """
    Eres el asistente virtual de la aplicación vecinal de la Sección 130 
    de San Mateo Tlalchichilpan, municipio de Almoloya de Juárez, Estado de México.

    Habla como un vecino amable y claro.
    Responde de forma breve (máximo 6 líneas).
    No uses títulos ni formato por secciones.
    No escribas textos largos.

    Si preguntan sobre la Sección 130, da información real de San Mateo Tlalchichilpan.
    Si preguntan sobre otras secciones, responde que solo tienes información de la Sección 130.

    Explica solo funciones reales de la app:
    reportes vecinales, incidencias, SOS, chat, perfil, recuperación de contraseña,
    aprobación de cuentas y dashboard de administradores.
    """

    # crear historial si no existe
    if sid not in historial_conversaciones:
        historial_conversaciones[sid] = [
            {"role": "system", "content": contexto}
        ]

    # guardar mensaje del usuario
    historial_conversaciones[sid].append({
        "role": "user",
        "content": mensaje_usuario
    })

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": historial_conversaciones[sid]
    }

    try:

        response = requests.post(url, headers=headers, json=data)
        resultado = response.json()

        print("IA RESPONSE:", resultado)

        if "choices" in resultado:

            respuesta = resultado["choices"][0]["message"]["content"]

            # guardar respuesta de la IA
            historial_conversaciones[sid].append({
                "role": "assistant",
                "content": respuesta
            })

            return respuesta

        if "error" in resultado:
            print("❌ ERROR OPENROUTER:", resultado["error"])
            return "Lo siento, el asistente no está disponible en este momento."

        return "No pude generar una respuesta."

    except Exception as e:
        print("❌ ERROR IA:", e)
        return "Ocurrió un error al consultar el asistente."



@socketio.on("mensaje_ia")
def manejar_mensaje(data):

    print("📩 MENSAJE IA RECIBIDO:", data, flush=True)

    mensaje = data["mensaje"].lower()

    if "reporte" in mensaje or "activo" in mensaje or "pendiente" in mensaje:
        respuesta = obtener_reportes_activos()
    else:
        respuesta = preguntar_ia(mensaje, request.sid)

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        INSERT INTO mensajes_grupo (grupo_id, usuario_id, mensaje)
        VALUES (%s, %s, %s)
    """, (grupo_id, usuario_id, mensaje))
    conn.commit()

    cursor.execute("""
        SELECT nombre FROM usuarios WHERE id_usuario = %s
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        INSERT INTO mensajes_privados (emisor_id, receptor_id, mensaje)
        VALUES (%s, %s, %s)
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
    #conn.row_factory = sqlite3.Row
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT 
          mensajes_grupo.usuario_id,
          usuarios.nombre, 
          mensajes_grupo.mensaje, 
          mensajes_grupo.fecha
        FROM mensajes_grupo
        JOIN usuarios 
            ON mensajes_grupo.usuario_id = usuarios.id_usuario
        WHERE grupo_id = %s
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT nombre FROM usuarios WHERE id_usuario = %s", (usuario_id,))
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