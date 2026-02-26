from fastapi import FastAPI, WebSocket
import sqlite3
import json

app = FastAPI()
clientes = {}

def guardar_mensaje(emisor, receptor, mensaje):
    conn = sqlite3.connect("vecinal.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mensajes (mensaje, fecha, id_emisor, id_receptor)
        VALUES (?, datetime('now'), ?, ?)
    """, (mensaje, emisor, receptor))
    conn.commit()
    conn.close()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    data = json.loads(await ws.receive_text())
    id_usuario = data["id_usuario"]
    clientes[id_usuario] = ws

    while True:
        data = json.loads(await ws.receive_text())

        emisor = data["id_emisor"]
        receptor = data.get("id_receptor")
        mensaje = data["mensaje"]

        # 💾 GUARDAR EN BD
        guardar_mensaje(emisor, receptor, mensaje)

        # 📤 ENVIAR
        if receptor and receptor in clientes:
            await clientes[receptor].send_text(json.dumps(data))
        else:
            for c in clientes.values():
                await c.send_text(json.dumps(data))

@app.get("/historial")
def obtener_historial(usuario1: str, usuario2: str = None):

    conn = sqlite3.connect("vecinal.db")
    cur = conn.cursor()

    # 🔹 Chat privado
    if usuario2:
        cur.execute("""
            SELECT mensaje, id_emisor, id_receptor, fecha
            FROM mensajes
            WHERE (id_emisor=? AND id_receptor=?)
               OR (id_emisor=? AND id_receptor=?)
            ORDER BY fecha
        """, (usuario1, usuario2, usuario2, usuario1))

    # 🔹 Chat grupal
    else:
        cur.execute("""
            SELECT mensaje, id_emisor, id_receptor, fecha
            FROM mensajes
            WHERE id_receptor IS NULL
            ORDER BY fecha
        """)

    mensajes = cur.fetchall()
    conn.close()

    return [
        {
            "mensaje": m[0],
            "id_emisor": m[1],
            "id_receptor": m[2],
            "fecha": m[3]
        }
        for m in mensajes
    ]
