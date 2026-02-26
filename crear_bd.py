import sqlite3

# Conectar o crear la base de datos
conexion = sqlite3.connect("vecinal.db")
cursor = conexion.cursor()

# TABLA USUARIOS
cursor.execute("""
CREATE TABLE usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT UNIQUE NOT NULL,
    contraseña TEXT NOT NULL,
    rol TEXT NOT NULL,
    fecha_registro TEXT
)
""")


# TABLA INCIDENCIAS
cursor.execute("""
CREATE TABLE IF NOT EXISTS incidencias (
    id_incidencia INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    descripcion TEXT,
    tipo TEXT,
    estado TEXT,
    fecha TEXT,
    id_usuario INTEGER,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
)
""")

# TABLA GEOLOCALIZACION
cursor.execute("""
CREATE TABLE IF NOT EXISTS geolocalizacion (
    id_geolocalizacion INTEGER PRIMARY KEY AUTOINCREMENT,
    latitud REAL,
    longitud REAL,
    id_incidencia INTEGER,
    FOREIGN KEY (id_incidencia) REFERENCES incidencias(id_incidencia)
)
""")

# TABLA MENSAJES
cursor.execute("""
CREATE TABLE IF NOT EXISTS mensajes (
    id_mensaje INTEGER PRIMARY KEY AUTOINCREMENT,
    mensaje TEXT,
    fecha TEXT,
    id_emisor INTEGER,
    id_receptor INTEGER,
    FOREIGN KEY (id_emisor) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_receptor) REFERENCES usuarios(id_usuario)
)
""")

# TABLA NOTIFICACIONES
cursor.execute("""
CREATE TABLE IF NOT EXISTS notificaciones (
    id_notificacion INTEGER PRIMARY KEY AUTOINCREMENT,
    mensaje TEXT,
    fecha TEXT,
    leida INTEGER,
    id_usuario INTEGER,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
)
""")

# Guardar cambios
conexion.commit()
conexion.close()

print("Base de datos actualizada correctamente")