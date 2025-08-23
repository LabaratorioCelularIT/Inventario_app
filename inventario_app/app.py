from flask import Flask, render_template, request, redirect, session, send_file, flash, abort, jsonify
import sqlite3, os, csv
from io import StringIO
from datetime import datetime, timedelta
import uuid
from PIL import Image
import shutil
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from urllib.parse import urlencode
import time

CAJA_URL_BASE = "http://89.117.145.73:5003"
SSO_SHARED_SECRET = "cambia_esta_clave_32+caracteres"
app = Flask(__name__)
app.secret_key = "inventario_secret_key"
DB_PATH = os.path.join(os.path.dirname(__file__), "inventario.sqlite3")

REDES_LOCALES = [
    '138.84.61.202',  # Villas
    '138.84.61.41',  # Reservas
    '138.84.61.36',  # Colinas
    '138.84.61.11',  # Colinas1
    '187.189.164.174',  # Colinas2
    '138.84.61.25', # Hidalgo
    '187.190.158.152', # VOL1
    '187.189.68.44', # Reservas2
]

DISPOSITIVOS_ESPECIALES = [
    '189.145.88.123',  # Celular Jesús
    '189.150.77.88',   # Laptop Victoria
    '192.168.1.139',  # Laptop David
    '187.189.68.44',
]

USUARIOS_CONSULTA = {
    "Litzy": "1234", "Lorena": "1234", "Abigail": "1234", "Fátima": "1234",
    "Alejandrina C": "1234", "Carolina": "1234", "Monserrath": "1234",
    "Brayan": "1234", "Evelin": "1234", "Angela": "1234", "Leslie": "1234",
    "Lizeth": "1234", "Briseida": "1234", "Daniel": "1234"
}

USUARIOS_ADMIN = {
    "David": "262293", "Victoria": "262293", "Vanessa": "262293",
    "Blanca": "262293", "Jesús": "262293", "Alejandrina": "Labcel2578"
}

SUCURSALES = ["Hidalgo", "Colinas", "Voluntad 1", "Reservas", "Villas", "Jose", "Daniel", "Mauricio", "Mundocel"]


NOMBRES_REALES = {
    "admin_ajnd_7204": "Alejandrina",
    "admin_blcn_8532": "Blanca",
    "admin_vnss_3189": "Vanessa",
    "admin_dvcd_6497": "David",
    "admin_vctr_9051": "Victoria",
    "consulta_abav_5921": "Abigail Avila",
    "consulta_ftrr_8350": "Fátima Reyes",
    "consulta_cndz_1043": "Carolina Díaz",
    "consulta_abcr_6619": "Abigail Corona",
    "consulta_lzrz_1284": "Lizeth Ruiz",
    "consulta_lsrv_2390": "Leslie Reservas",
    "consulta_alnd_7452": "Alondra",
    "consulta_lrbn_3017": "Lorena",
    "consulta_brsd_5126": "Briseida",
    "consulta_evln_6029": "Evelin",
    "consulta_mnsr_1045": "Monserrath",
    "consulta_angl_7238": "Angeles",
    "consulta_dnlv_2096": "Daniel",
    "consulta_ltzb_8431": "Litzy",
    "consulta_bryn_9327": "Brayan",
    "consulta_arln_6235": "Arlen",
    "consulta_angl_0187": "Angela",
    "reparto_jsss_7493": "Jesús",
    "consulta_ajnd_7204": "Alejandrina (consulta)",
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS tipos_producto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        stock_minimo INTEGER DEFAULT 0
    );""")
    c.execute("""CREATE TABLE IF NOT EXISTS articulos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_id INTEGER,
        memoria TEXT,
        color TEXT,
        proveedor TEXT,
        precio TEXT,
        factura_id TEXT,
        fecha_compra TEXT,
        sucursal TEXT,
        estado TEXT,
        imei TEXT UNIQUE,
        imei2 TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")
    c.execute("""CREATE TABLE IF NOT EXISTS log_actividad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        tipo TEXT,
        descripcion TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")
    c.execute("""CREATE TABLE IF NOT EXISTS transferencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        articulo_id INTEGER,
        sucursal_origen TEXT,
        sucursal_destino TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        usuario TEXT
    );""")
    conn.commit()
    conn.close()

def registrar_log(usuario, tipo, descripcion):
    conn = sqlite3.connect(DB_PATH)
    ahora_local = (datetime.utcnow() - timedelta(hours=5)).strftime("%d-%m-%Y %H:%M:%S")
    conn.execute("INSERT INTO log_actividad (usuario, tipo, descripcion, fecha) VALUES (?, ?, ?, ?)",
                 (usuario, tipo, descripcion, ahora_local))
    conn.commit()
    conn.close()

def sso_serializer():
    return URLSafeTimedSerializer(SSO_SHARED_SECRET, salt="sso-inv-5001")

def _destino_valido():
    try:
        return url_for("listado_articulos")
    except Exception:
        return "/"

@app.route('/')
def index():
    if 'usuario' in session:
        return redirect('/dashboard')
    return render_template("login.html", sucursales=SUCURSALES)

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('usuario', '').strip()
    password = request.form.get('password', '').strip()
    sucursal = request.form.get('sucursal', '').strip()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT nombre, tipo FROM usuarios WHERE nombre = ? AND contraseña = ?", (usuario, password))
    row = cur.fetchone()
    conn.close()

    if row:
        nombre, tipo = row

        
        session['usuario'] = nombre
        session['tipo'] = tipo

        if tipo == 'consulta':
            session['sucursal'] = sucursal
            registrar_log(nombre, "Inicio de sesión", f"Entró como usuario de consulta en {sucursal}")
        elif tipo == 'reparto':
            registrar_log(nombre, "Inicio de sesión", f"Entró como usuario tipo reparto")
        else:
            registrar_log(nombre, "Inicio de sesión", f"Entró como administrador")

        return redirect('/dashboard')
    else:
        return "❌ Usuario o contraseña incorrectos"

@app.route('/login', methods=['GET'])
def login_get():
    if 'usuario' in session:
        return redirect('/dashboard')
    return render_template("login.html", sucursales=SUCURSALES)

@app.route("/sso-login")
def sso_login():
    token = request.args.get("token", "")
    destino = request.args.get("next") or "/dashboard"
    if not token:
        return redirect("/login")
    try:
        data = sso_serializer().loads(token, max_age=300)  # 5 min
    except (SignatureExpired, BadSignature):
        return redirect("/login")

    usuario = data.get("usuario") or ""
    if not usuario:
        return redirect("/login")

    session["usuario"] = usuario
    session["tipo"] = data.get("tipo", "")
    session["sucursal"] = data.get("sucursal", "")

    return redirect(destino)

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect('/')

    tipo = session.get('tipo')

    if tipo == 'admin':
        return render_template("dashboard_admin.html", usuario=session['usuario'])

    elif tipo == 'consulta':
        return render_template("dashboard_consulta.html", usuario=session['usuario'], sucursal=session.get('sucursal', ''))

    elif tipo == 'reparto':
        return render_template("dashboard_reparto.html", usuario=session['usuario'])

    else:
        return f"❌ Tipo de usuario no reconocido: {tipo}", 403

@app.route('/logout')
def logout():
    if 'usuario' in session:
        registrar_log(session['usuario'], "Cierre de sesión", "Cerró sesión")
    session.clear()
    return redirect('/')

@app.route("/ir-caja")
def ir_caja():
    if "usuario" not in session:
        return redirect("/login")

    payload = {
        "usuario": session.get("usuario",""),
        "tipo": session.get("tipo",""),
        "sucursal": session.get("sucursal",""),
        "ts": int(time.time())
    }
    token = sso_serializer().dumps(payload)

    next_map = {"admin": "/panel-admin", "consulta": "/panel-consulta", "reparto": "/panel-reparto"}
    next_path = next_map.get(session.get("tipo",""), "/dashboard")

    q = urlencode({"token": token, "next": next_path})
    target = f"{CAJA_URL_BASE}/sso-login-caja?{q}"
    print("REDIRIGIENDO A:", target)
    return redirect(target)

@app.route("/chat")
def chat():
    if "usuario" not in session:
        return redirect("/")

    usuario_actual = session["usuario"]

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        
        cur.execute("SELECT nombre, tipo FROM usuarios WHERE nombre != ?", (usuario_actual,))
        usuarios = cur.fetchall()

        
        cur.execute("""
            SELECT DISTINCT 
                CASE 
                    WHEN remitente = ? THEN destinatario 
                    ELSE remitente 
                END AS otro_usuario
            FROM mensajes_chat
            WHERE remitente = ? OR destinatario = ?
        """, (usuario_actual, usuario_actual, usuario_actual))
        historial = cur.fetchall()

        
        cur.execute("SELECT archivo FROM stickers_usuarios WHERE usuario = ?", (usuario_actual,))
        stickers_propios = cur.fetchall()

    lista_usuarios = []
    historial_usuarios = []

    for u in usuarios:
        user_id = u["nombre"]
        nombre_mostrar = NOMBRES_REALES.get(user_id, user_id)
        lista_usuarios.append({
            "usuario": user_id,
            "nombre": nombre_mostrar,
            "tipo": u["tipo"]
        })

    for h in historial:
        user_id = h["otro_usuario"]
        if user_id != usuario_actual:
            nombre_mostrar = NOMBRES_REALES.get(user_id, user_id)
            historial_usuarios.append({
                "usuario": user_id,
                "nombre": nombre_mostrar
            })

    return render_template("chat.html",
        usuario=usuario_actual,
        tipo=session.get("tipo", ""),
        sucursal=session.get("sucursal", ""),
        usuarios=lista_usuarios,
        historial_usuarios=historial_usuarios,
        stickers_propios=stickers_propios
    )

@app.route("/chat/crear_grupo", methods=["POST"])
def crear_grupo():
    if "usuario" not in session:
        return redirect("/")

    data = request.get_json()
    nombre_grupo = data.get("nombre", "").strip()
    miembros = data.get("miembros", [])
    creado_por = session["usuario"]
    fecha = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    if not nombre_grupo or not miembros:
        return jsonify({"ok": False, "error": "Faltan datos"})

    try:
        miembros_json = json.dumps(miembros)

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO grupos_chat (nombre, miembros, creado_por, fecha)
                VALUES (?, ?, ?, ?)
            """, (nombre_grupo, miembros_json, creado_por, fecha))
            conn.commit()

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/chat/enviar_usuario", methods=["POST"])
def enviar_usuario():
    if "usuario" not in session:
        return jsonify({"ok": False, "error": "No autorizado"})

    remitente = session["usuario"]
    tipo_destinatario = "usuario"
    fecha = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    mensaje = request.form.get("mensaje", "").strip()
    destinatario = request.form.get("destinatario", "")
    archivo = None

    if 'archivo' in request.files:
        archivo_file = request.files['archivo']
        if archivo_file and archivo_file.filename:
            archivo = secure_filename(archivo_file.filename)
            ruta_destino = os.path.join("static", "chat", archivo)
            archivo_file.save(ruta_destino)

    elif 'archivo_nombre' in request.form:
        archivo_nombre = request.form.get("archivo_nombre")
        ruta_origen = os.path.join("static", "stickers", archivo_nombre)
        ruta_destino = os.path.join("static", "chat", archivo_nombre)
        if os.path.exists(ruta_origen):
            shutil.copyfile(ruta_origen, ruta_destino)
            archivo = archivo_nombre

    if not destinatario or (not mensaje and not archivo):
        return jsonify({"ok": False, "error": "Mensaje vacío o sin destinatario"})

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO mensajes_chat (remitente, destinatario, tipo_destinatario, mensaje, archivo, fecha)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (remitente, destinatario, tipo_destinatario, mensaje, archivo, fecha))
        conn.commit()

    return jsonify({"ok": True})

@app.route("/chat/recibir_usuario")
def recibir_chat_usuario():
    if "usuario" not in session:
        return jsonify([])

    remitente = session["usuario"]
    contacto = request.args.get("usuario")

    if not contacto:
        return jsonify([])

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT remitente, destinatario, mensaje, archivo, fecha
            FROM mensajes_chat
            WHERE 
                tipo_destinatario = 'usuario' AND
                ((remitente = ? AND destinatario = ?) OR (remitente = ? AND destinatario = ?))
            ORDER BY datetime(fecha) ASC
        """, (remitente, contacto, contacto, remitente))

        mensajes = []
        for row in cur.fetchall():
            archivo = row["archivo"]
            ruta = ""
            if archivo:
                if archivo.startswith("sticker_"):
                    ruta = f"stickers/{archivo}"
                else:
                    ruta = f"chat/{archivo}"
            mensajes.append({
                "remitente": row["remitente"],
                "mensaje": row["mensaje"],
                "archivo": archivo,
                "ruta": ruta,
                "fecha": row["fecha"]
            })

    return jsonify(mensajes)

@app.route("/chat/recibidos")
def mensajes_personales():
    if "usuario" not in session:
        return redirect("/login")

    usuario = session["usuario"]

    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM mensajes_chat
            WHERE tipo_destinatario = 'usuario' AND destinatario = ?
            ORDER BY fecha DESC
        """, (usuario,))
        mensajes = cur.fetchall()

    return render_template("mensajes_recibidos.html", mensajes=mensajes)


@app.route("/chat/notificaciones")
def notificaciones_chat():
    if "usuario" not in session:
        return jsonify({"nuevos": 0})

    usuario = session["usuario"]
    tipo = session.get("tipo", "")
    sucursal = session.get("sucursal", "")
    modulo = request.args.get("modulo", "")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM mensajes_chat
            WHERE tipo_destinatario = 'usuario' AND
                  destinatario IN (?, ?, ?, 'Todos') AND
                  leido = 0 AND
                  modulo IN (?, 'General', '')
        """, (usuario, sucursal, tipo, modulo))
        total = cur.fetchone()[0]

    return jsonify({"nuevos": total})

@app.route("/subir_archivo_chat", methods=["POST"])
def subir_archivo_chat():
    archivo = request.files.get("archivo")
    if not archivo:
        return jsonify({"ok": False, "error": "No hay archivo"})

    carpeta = os.path.join("static", "chat")
    os.makedirs(carpeta, exist_ok=True)

    nombre = datetime.now().strftime("%d%m%Y%H%M%S") + "_" + archivo.filename
    ruta = os.path.join(carpeta, nombre)
    archivo.save(ruta)

    return jsonify({"ok": True, "nombre": nombre})

@app.route("/favorito-sticker", methods=["POST"])
def favorito_sticker():
    if "usuario" not in session:
        return redirect("/")

    sticker = request.form.get("sticker")
    usuario = session["usuario"]

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM stickers_favoritos WHERE usuario = ? AND sticker = ?", (usuario, sticker))
        existe = cur.fetchone()
        if not existe:
            cur.execute("INSERT INTO stickers_favoritos (usuario, sticker) VALUES (?, ?)", (usuario, sticker))
            conn.commit()

    return redirect("/chat")

@app.route("/enviar-sticker-favorito", methods=["POST"])
def enviar_sticker_favorito():
    if "usuario" not in session:
        return redirect("/")

    sticker = request.form.get("sticker")
    remitente = session["usuario"]
    destinatario = session.get("chat_destinatario")  # Debes guardar en sesión al seleccionar el chat
    tipo_destino = session.get("tipo_destino")
    modulo = "chat"
    fecha = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO mensajes_chat (remitente, destinatario, tipo_destinatario, mensaje, archivo, fecha, modulo)
            VALUES (?, ?, ?, '', ?, ?, ?)
        """, (remitente, destinatario, tipo_destino, sticker, fecha, modulo))
        conn.commit()

    return redirect("/chat")

@app.route("/subir-sticker", methods=["POST"])
def subir_sticker():
    if "usuario" not in session:
        return redirect("/")

    archivo = request.files.get("sticker")
    if not archivo or archivo.filename == "":
        return "No se subió ningún archivo", 400

    nombre_archivo = f"{session['usuario']}_{int(time.time())}_{secure_filename(archivo.filename)}"
    ruta = os.path.join("static", "stickers_usuarios", nombre_archivo)
    archivo.save(ruta)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO stickers_usuarios (usuario, archivo) VALUES (?, ?)", (session["usuario"], nombre_archivo))
        conn.commit()

    return redirect("/chat")

@app.route("/chat/convertir_sticker", methods=["POST"])
def convertir_sticker():
    archivo = request.files.get("archivo")
    if not archivo:
        return jsonify({"ok": False, "error": "No se recibió archivo"})

    nombre_base = secure_filename(archivo.filename.rsplit('.', 1)[0])
    ruta_original = f"static/chat/{nombre_base}.png"
    ruta_sticker = f"static/chat/{nombre_base}.webp"
    archivo.save(ruta_original)

    try:
        img = Image.open(ruta_original).convert("RGBA")
        img = img.resize((512, 512), Image.LANCZOS)
        img.save(ruta_sticker, format="WEBP")
        os.remove(ruta_original)
        return jsonify({"ok": True, "nombre": os.path.basename(ruta_sticker)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/chat/guardar_como_sticker", methods=["POST"])
def guardar_como_sticker():
    data = request.get_json()
    nombre_archivo = data.get("archivo")
    usuario = session.get("usuario", "desconocido")

    if not nombre_archivo:
        return jsonify({"ok": False, "error": "Nombre de archivo no proporcionado"})

    ruta_origen = os.path.join("static", "chat", nombre_archivo)

    if not os.path.exists(ruta_origen):
        return jsonify({"ok": False, "error": "El archivo no existe"})

    
    nuevo_nombre = nombre_archivo if nombre_archivo.startswith("sticker_") else f"sticker_{nombre_archivo}"
    ruta_destino = os.path.join("static", "stickers", nuevo_nombre)

    try:
        import shutil
        shutil.copy(ruta_origen, ruta_destino)  # Usamos copia, no mover
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/chat/stickers_usuario")
def stickers_usuario():
    usuario = session.get("usuario")
    ruta = os.path.join("static", "stickers")
    stickers = []
    for archivo in os.listdir(ruta):
        if archivo.startswith(usuario):
            stickers.append(archivo)
    stickers.sort(key=lambda f: os.path.getmtime(os.path.join(ruta, f)), reverse=True)
    return jsonify({"stickers": stickers})

@app.route("/mis-stickers")
def mis_stickers():
    usuario = request.args.get("usuario", "")
    ruta = os.path.join("static", "stickers")
    stickers = []

    for nombre in os.listdir(ruta):
        if nombre.endswith(".webp") and nombre.startswith(usuario):
            stickers.append(nombre)

    return jsonify(stickers)

@app.route('/transferencias', methods=['GET', 'POST'])
def transferencias():
    if 'usuario' not in session or session.get('tipo') not in ['admin', 'reparto', 'consulta']:
        return redirect('/')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    mensaje = ""

    if session.get('tipo') == 'admin':
        if request.method == 'POST':
            imei = request.form.get('imei', '').strip()
            destino = request.form.get('destino', '').strip()

            articulo = cur.execute("SELECT id, sucursal FROM articulos WHERE imei = ?", (imei,)).fetchone()
            if articulo:
                articulo_id, origen = articulo
                if origen != destino and destino in SUCURSALES:
                    cur.execute("UPDATE articulos SET sucursal = ? WHERE id = ?", (destino, articulo_id))
                    cur.execute("""INSERT INTO transferencias 
                        (articulo_id, sucursal_origen, sucursal_destino, usuario, estatus)
                        VALUES (?, ?, ?, ?, 'pendiente-envío')""",
                        (articulo_id, origen, destino, session['usuario']))
                    conn.commit()
                    registrar_log(session['usuario'], "Transferencia", f"Artículo IMEI {imei} de {origen} a {destino} (pendiente de envío)")
                    mensaje = f"✅ Transferencia registrada de {origen} a {destino}"

        imeis = cur.execute("SELECT imei FROM articulos").fetchall()
        conn.close()
        return render_template("transferencias.html", imeis=[x[0] for x in imeis], sucursales=SUCURSALES, usuario=session['usuario'], mensaje=mensaje)

    elif session.get('tipo') == 'consulta':
        sucursal_actual = session.get('sucursal')
        usuario = session['usuario']

        if request.method == 'POST':
            transferencia_id = request.form.get('transferencia_id')
            if transferencia_id:
                cur.execute("""UPDATE transferencias 
                               SET estatus = 'recibido', fecha = datetime('now', '-5 hours'), usuario = ?
                               WHERE id = ?""",
                            (usuario + " (recibido)", transferencia_id))
                registrar_log(usuario, "Confirmación", f"Confirmó recepción del artículo en sucursal {sucursal_actual}")
                conn.commit()

        transferencias = cur.execute("""
            SELECT t.id, a.imei, t.sucursal_origen, t.sucursal_destino, t.estatus, t.fecha
            FROM transferencias t
            JOIN articulos a ON t.articulo_id = a.id
            WHERE t.sucursal_destino = ? AND t.estatus = 'en camino'
            ORDER BY t.fecha DESC
        """, (sucursal_actual,)).fetchall()

        conn.close()
        return render_template("transferencias_confirmar.html", transferencias=transferencias, usuario=usuario)

    elif session.get('tipo') == 'reparto':
        usuario = session['usuario']

        
        transferencias = cur.execute("""
            SELECT t.id, tp.nombre, a.color, a.imei, t.sucursal_origen, t.sucursal_destino, t.fecha, t.estatus
            FROM transferencias t
            JOIN articulos a ON t.articulo_id = a.id
            JOIN tipos_producto tp ON a.tipo_id = tp.id
            ORDER BY t.fecha DESC
        """).fetchall()

        
        resumen = {
            "total": len(transferencias),
            "en_camino": sum(1 for t in transferencias if t[7] == "en camino"),
            "pendientes": sum(1 for t in transferencias if t[7] == "pendiente-envío"),
            "recibidas": sum(1 for t in transferencias if t[7] == "recibido"),
        }

        conn.close()
        return render_template("transferencias_reparto.html", transferencias=transferencias, resumen=resumen, usuario=usuario)

    return redirect('/')


from collections import defaultdict

@app.route("/reportes-transferencias", methods=["GET", "POST"])
def reportes_transferencias():
    if "usuario" not in session:
        return redirect("/login")

    conn = sqlite3.connect("inventario.sqlite3")
    cursor = conn.cursor()

    if request.method == "POST":
        id_transferencia = request.form.get("confirmar_envio")
        if id_transferencia:
            cursor.execute("UPDATE transferencias SET estatus = 'en camino' WHERE id = ?", (id_transferencia,))
            conn.commit()
        return redirect("/reportes-transferencias")

    
    filtro_sucursal = request.args.get("sucursal")
    filtro_fecha = request.args.get("fecha")

    
    query = """
        SELECT t.id, p.nombre, a.color, a.imei,
               t.sucursal_origen, t.sucursal_destino,
               t.fecha, t.estatus
        FROM transferencias t
        LEFT JOIN articulos a ON t.articulo_id = a.id
        LEFT JOIN tipos_producto p ON a.tipo_id = p.id
    """

    condiciones = []
    valores = []

    if filtro_sucursal:
        condiciones.append("t.sucursal_destino = ?")
        valores.append(filtro_sucursal)

    if filtro_fecha:
        condiciones.append("DATE(t.fecha) = ?")
        valores.append(filtro_fecha)

    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)

    
    query += """
        ORDER BY 
            CASE 
                WHEN t.estatus = 'pendiente-envío' THEN 1
                WHEN t.estatus = 'en camino' THEN 2
                WHEN t.estatus = 'recibido' THEN 3
                ELSE 4
            END,
            t.fecha DESC
    """

    cursor.execute(query, valores)
    transferencias = cursor.fetchall()

    
    cursor.execute("SELECT DISTINCT sucursal_destino FROM transferencias ORDER BY sucursal_destino ASC")
    tiendas = [row[0] for row in cursor.fetchall()]

    conn.close()

    return render_template("reportes_transferencias.html",
                           transferencias=transferencias,
                           tiendas=tiendas,
                           filtro_sucursal=filtro_sucursal,
                           filtro_fecha=filtro_fecha)

@app.route('/confirmar-transferencias', methods=['GET', 'POST'])
def confirmar_transferencias():
    if 'usuario' not in session or session.get('tipo') != 'consulta':
        return redirect('/')

    sucursal_usuario = session.get('sucursal')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if request.method == 'POST':
        id_transfer = request.form.get('confirmar')
        if id_transfer:
            cur.execute("""
                UPDATE transferencias 
                SET estatus = 'recibido', usuario = ?, fecha = datetime('now', '-5 hours')
                WHERE id = ? AND sucursal_destino = ? AND estatus = 'en camino'
            """, (session['usuario'] + " (recibido)", id_transfer, sucursal_usuario))
            conn.commit()
            registrar_log(session['usuario'], "Recepción", f"Confirmó recepción de transferencia ID {id_transfer}")

    transferencias = cur.execute("""
    SELECT t.id, p.nombre AS tipo, a.color, a.imei,
           t.sucursal_origen, t.sucursal_destino,
           t.usuario, t.fecha, t.estatus
    FROM transferencias t
    JOIN articulos a ON t.articulo_id = a.id
    LEFT JOIN tipos_producto p ON a.tipo_id = p.id
    WHERE t.sucursal_destino = ? AND t.estatus = 'en camino'
    ORDER BY t.fecha DESC
""", (sucursal_usuario,)).fetchall()

    conn.close()
    return render_template("confirmar_transferencias.html", transferencias=transferencias)

@app.route("/confirmar-envio-lote", methods=["POST"])
def confirmar_envio_lote():
    if session.get("tipo") not in ["admin", "reparto"]:
        return redirect("/login")

    id_lote = request.form.get("id_lote")
    if not id_lote:
        return "ID de lote no proporcionado.", 400

    conn = sqlite3.connect("inventario.sqlite3")
    cursor = conn.cursor()

    
    cursor.execute("SELECT imei FROM transferencias WHERE id = ?", (id_lote,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return "Lote no encontrado.", 404

    
    cursor.execute("SELECT articulo_id FROM transferencias WHERE id = ?", (id_lote,))
    articulo_id = cursor.fetchone()[0]

    
    cursor.execute("""
        UPDATE transferencias
        SET estatus = 'en camino'
        WHERE articulo_id = ? AND estatus = 'pendiente-envío'
    """, (articulo_id,))

    
    cursor.execute("""
        INSERT INTO log_actividad (usuario, tipo, descripcion)
        VALUES (?, 'Transferencia', ?)
    """, (session["usuario"], f"Confirmó envío de lote del artículo ID {articulo_id}"))

    conn.commit()
    conn.close()

    return redirect("/reportes-transferencias")

@app.route('/eliminar-transferencia/<int:transferencia_id>', methods=['POST'])
def eliminar_transferencia(transferencia_id):
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM transferencias WHERE id = ?", (transferencia_id,))
    conn.commit()
    registrar_log(session['usuario'], "Eliminación", f"Transferencia eliminada ID {transferencia_id}")
    conn.close()
    return redirect('/reportes-transferencias')

@app.route("/transferencias-masivas", methods=["POST"])
def transferencias_masivas():
    if session.get("tipo") != "admin":
        return redirect("/login")

    ids = request.form.getlist("ids")
    destino = request.form.get("destino_masivo")

    if not ids or not destino:
        return "Error: Faltan datos.", 400

    fecha_actual = (datetime.utcnow() - timedelta(hours=5)).strftime('%d-%m-%Y %H:%M:%S')
    
    id_lote = f"lote_{datetime.now().strftime('%d%m%Y_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    conn = sqlite3.connect("inventario.sqlite3")
    cursor = conn.cursor()

    for art_id in ids:
        cursor.execute("SELECT sucursal FROM articulos WHERE id = ?", (art_id,))
        row = cursor.fetchone()
        if row:
            origen = row[0]
            cursor.execute("""
                INSERT INTO transferencias (articulo_id, sucursal_origen, sucursal_destino, fecha, usuario, estatus, id_lote)
                VALUES (?, ?, ?, ?, ?, 'pendiente-envío', ?)
            """, (art_id, origen, destino, fecha_actual, session['usuario'], id_lote))
            cursor.execute("UPDATE articulos SET sucursal = ? WHERE id = ?", (destino, art_id))

    conn.commit()
    conn.close()

    return redirect("/listado_articulos")

@app.route("/resumen_general")
def resumen_general():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    
    cur.execute("""
        SELECT t.nombre AS tipo, a.sucursal, COUNT(*) as total
        FROM articulos a
        JOIN tipos_producto t ON a.tipo_id = t.id
        WHERE a.estado NOT IN ('Vendido', 'Perdido')
        GROUP BY t.nombre, a.sucursal
        ORDER BY t.nombre, a.sucursal
    """)
    datos = cur.fetchall()

    
    from collections import defaultdict
    resumen_por_tipo = defaultdict(list)
    totales_modelo = defaultdict(int)

    for tipo, sucursal, total in datos:
        resumen_por_tipo[tipo].append((tipo, sucursal, total))
        totales_modelo[tipo] += total

    
    cur.execute("""
        SELECT sucursal, COUNT(*) FROM articulos
        WHERE estado NOT IN ('Vendido', 'Perdido')
        GROUP BY sucursal
    """)
    totales_raw = cur.fetchall()
    totales_sucursales = {fila[0]: fila[1] for fila in totales_raw}

    
    total_general = sum(totales_sucursales.values())

          
    cur.execute("""
        SELECT a.sucursal, t.nombre AS tipo, a.estado, COUNT(*) 
        FROM articulos a
        JOIN tipos_producto t ON a.tipo_id = t.id
        WHERE a.estado NOT IN ('Vendido', 'Perdido')
        GROUP BY a.sucursal, t.nombre, a.estado
        ORDER BY a.sucursal, t.nombre, a.estado
    """)
    detalle_estados_raw = cur.fetchall()

    
    desglose_estados = defaultdict(list)
    for sucursal, tipo, estado, cantidad in detalle_estados_raw:
        desglose_estados[sucursal].append((tipo, estado, cantidad))

    conn.close()
    return render_template("resumen_general.html",
                           resumen_por_tipo=resumen_por_tipo,
                           totales_modelo=totales_modelo,
                           totales_sucursales=totales_sucursales,
                           total_general=total_general,
                           desglose_estados=desglose_estados)

@app.route('/listado_articulos')
def listado_articulos():
    if 'usuario' not in session or session.get('tipo') not in ['admin', 'reparto']:
        return redirect('/')

    sucursal = request.args.get("sucursal", "Todas")
    modelo = request.args.get("modelo", "Todos")
    estado = request.args.get("estado", "Todos")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT t.nombre AS tipo, a.sucursal, COUNT(*) as total
        FROM articulos a
        JOIN tipos_producto t ON a.tipo_id = t.id
        GROUP BY t.nombre, a.sucursal
        ORDER BY t.nombre, a.sucursal
    """)
    resumen = cur.fetchall()

    query = """
        SELECT a.id,
               COALESCE(t.nombre, 'Tipo eliminado o inválido') AS tipo,
               a.imei, a.sucursal, a.memoria, a.color, a.proveedor,
               a.precio, a.factura_id, a.fecha_compra, a.estado
        FROM articulos a
        LEFT JOIN tipos_producto t ON a.tipo_id = t.id
        WHERE 1=1
    """
    params = []

    if sucursal != "Todas":
        query += " AND a.sucursal = ?"
        params.append(sucursal)

    if modelo != "Todos":
        query += " AND t.nombre = ?"
        params.append(modelo)

    if estado != "Todos":
        query += " AND a.estado = ?"
        params.append(estado)

    query += " ORDER BY a.fecha_registro DESC"

    cur.execute(query, params)
    articulos = cur.fetchall()

    cur.execute("SELECT DISTINCT nombre FROM tipos_producto ORDER BY nombre ASC")
    modelos = [row[0] for row in cur.fetchall()]

    conn.close()

    return render_template(
        "listado_articulos.html",
        resumen=resumen,
        articulos=articulos,
        modelos=modelos,
        sucursales=SUCURSALES,
        sucursal_actual=sucursal,
        modelo_actual=modelo,
        estado_actual=estado
    )

@app.route('/actualizar-estado', methods=['POST'])
def actualizar_estado():
    if "usuario" not in session:
        return redirect('/')

    ids = request.form.getlist('ids')
    nuevo_estado = request.form.get('nuevo_estado')

    if ids and nuevo_estado:
        conn = sqlite3.connect('inventario.sqlite3')
        cur = conn.cursor()

        for id_articulo in ids:
            # Obtener IMEI del artículo
            cur.execute("SELECT imei FROM articulos WHERE id = ?", (id_articulo,))
            resultado = cur.fetchone()
            imei = resultado[0] if resultado else "IMEI desconocido"

            
            cur.execute("UPDATE articulos SET estado = ? WHERE id = ?", (nuevo_estado, id_articulo))

            
            cur.execute("""
                INSERT INTO log_actividad (usuario, tipo, descripcion, fecha, accion, origen)
                VALUES (?, ?, ?, datetime('now', 'localtime'), ?, ?)
            """, (
                session["usuario"],
                session["tipo"],
                f"Cambio de estado de artículo {id_articulo} a '{nuevo_estado}'",
                f"Modificó el estado del artículo {id_articulo} (IMEI: {imei}) a '{nuevo_estado}'",
                "Inventario"
            ))

        conn.commit()
        conn.close()
        flash("Estado actualizado correctamente.", "success")
    else:
        flash("Faltan datos para actualizar el estado.", "danger")

    return redirect('/listado_articulos')

@app.route('/inventario-sucursal')
def inventario_sucursal():
    if 'usuario' not in session or session.get('tipo') != 'consulta':
        return redirect('/')

    sucursal = session.get('sucursal')
    tipo_filtro = request.args.get('tipo', '')
    color_filtro = request.args.get('color', '')
    memoria_filtro = request.args.get('memoria', '')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Verificar si hay inventario pendiente
    cur.execute("SELECT COUNT(*) FROM inventarios_pendientes WHERE sucursal = ?", (sucursal,))
    tiene_inventario = cur.fetchone()[0] > 0

    # Base de la consulta
    query = """
        SELECT a.id, t.nombre, a.memoria, a.color, a.imei, a.estado
        FROM articulos a
        JOIN tipos_producto t ON a.tipo_id = t.id
        WHERE a.sucursal = ?
        AND (a.estado IS NULL OR a.estado != 'Vendido')
    """
    params = [sucursal]

    # Aplicar filtros dinámicamente
    if tipo_filtro:
        query += " AND t.nombre = ?"
        params.append(tipo_filtro)
    if color_filtro:
        query += " AND a.color = ?"
        params.append(color_filtro)
    if memoria_filtro:
        query += " AND a.memoria = ?"
        params.append(memoria_filtro)

    cur.execute(query, params)
    articulos = cur.fetchall()

    # Obtener opciones únicas para filtros
    cur.execute("SELECT DISTINCT t.nombre FROM articulos a JOIN tipos_producto t ON a.tipo_id = t.id WHERE a.sucursal = ?", (sucursal,))
    tipos = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT a.memoria FROM articulos a WHERE a.sucursal = ?", (sucursal,))
    memorias = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT a.color FROM articulos a WHERE a.sucursal = ?", (sucursal,))
    colores = [row[0] for row in cur.fetchall()]

    conn.close()

    return render_template("inventario_sucursal.html",
                           articulos=articulos,
                           sucursal=sucursal,
                           tipos=tipos,
                           memorias=memorias,
                           colores=colores,
                           tiene_inventario=tiene_inventario)

@app.route('/agregar-articulo', methods=['GET', 'POST'])
def agregar_articulo():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    mensaje = ""

    if request.method == 'POST':
        tipo_id = request.form.get('tipo_id')
        memoria = request.form.get('memoria', '').strip()
        color = request.form.get('color', '').strip()
        proveedor = request.form.get('proveedor', '').strip()
        precio = request.form.get('precio', '').strip()
        factura_id = request.form.get('factura_id', '').strip()
        fecha_compra = request.form.get('fecha_compra', '').strip()
        sucursal = request.form.get('sucursal')
        estado = request.form.get('estado')
        imei1 = request.form.get('imei', '').strip()
        imei2 = request.form.get('imei2', '').strip()
        imeis_detectados = request.form.get('imeis_detectados', '').strip().replace("\n", ",")

        total_agregados = 0
        errores = []

        def guardar_imei(imei):
            nonlocal total_agregados
            if imei:
                try:
                    cur.execute("""INSERT INTO articulos (
                        tipo_id, memoria, color, proveedor, precio,
                        factura_id, fecha_compra, sucursal, estado, imei, imei2
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (tipo_id, memoria, color, proveedor, precio,
                     factura_id, fecha_compra, sucursal, estado, imei, imei2 if imei == imei1 else ''))
                    conn.commit()
                    registrar_log(session['usuario'], "Registro", f"Artículo IMEI {imei} agregado a {sucursal}")
                    total_agregados += 1
                except sqlite3.IntegrityError:
                    errores.append(f"❌ IMEI duplicado o inválido: {imei}")

        
        if imei1:
            guardar_imei(imei1)

        
        if imeis_detectados:
            for i in imeis_detectados.split(","):
                guardar_imei(i.strip())

        if total_agregados:
            mensaje = f"✅ {total_agregados} artículo(s) agregado(s) correctamente."
        if errores:
            mensaje += " " + " ".join(errores)

    cur.execute("SELECT id, nombre FROM tipos_producto")
    tipos = cur.fetchall()
    conn.close()
    return render_template("agregar_articulo.html", tipos=tipos, sucursales=SUCURSALES, mensaje=mensaje)

@app.route('/ver-log')
def ver_log():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = "SELECT * FROM log_actividad WHERE 1=1"
    params = []

    usuario = request.args.get('usuario')
    accion = request.args.get('accion')
    desde = request.args.get('desde')
    hasta = request.args.get('hasta')
    origen = request.args.get('origen')

    if usuario:
        query += " AND usuario = ?"
        params.append(usuario)
    if accion:
        query += " AND tipo = ?"
        params.append(accion)
    if desde:
        query += " AND fecha >= ?"
        params.append(desde)
    if hasta:
        query += " AND fecha <= ?"
        params.append(hasta + " 23:59:59")
    if origen:
        query += " AND origen = ?"
        params.append(origen)

    cur.execute(query, params)
    registros = cur.fetchall()

    cur.execute("SELECT DISTINCT usuario FROM log_actividad")
    usuarios = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT origen FROM log_actividad")
    origenes = [row[0] for row in cur.fetchall()]

    conn.close()

    return render_template("log_actividad.html", registros=registros, usuarios=usuarios, origenes=origenes, origen_actual=origen)

@app.route('/eliminar-log/<int:log_id>', methods=['POST'])
def eliminar_log(log_id):
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM log_actividad WHERE id = ?", (log_id,))
    log = cur.fetchone()
    if log:
        cur.execute("DELETE FROM log_actividad WHERE id = ?", (log_id,))
        conn.commit()
        # Evitar registrar eliminación si es un log de eliminación de log
        if not (log[2] == "Eliminación" and "registro del log" in log[3]):
            registrar_log(session['usuario'], "Eliminación", f"Eliminó registro del log ID {log_id}")
    conn.close()
    return redirect('/ver-log')

@app.route('/descargar-log')
def descargar_log():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM log_actividad")
    registros = cur.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Usuario", "Tipo", "Descripción", "Fecha"])
    writer.writerows(registros)

    output.seek(0)
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name="log_actividad.csv"
    )

@app.route('/backup')
def backup():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')
    
    fecha = datetime.now().strftime("%d%m%Y_%H%M%S")
    backup_name = f"backup_inventario_{fecha}.sqlite3"
    return send_file(DB_PATH, as_attachment=True, download_name=backup_name)

@app.route('/restaurar', methods=['GET', 'POST'])
def restaurar():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')
    
    if request.method == 'POST':
        archivo = request.files.get('archivo')
        if archivo and archivo.filename.endswith(".sqlite3"):
            archivo.save(DB_PATH)
            registrar_log(session['usuario'], "Restauración", "Base de datos restaurada desde archivo")
            return redirect('/dashboard')
        return "❌ Archivo inválido. Debe ser .sqlite3"

    return render_template("restaurar.html", usuario=session['usuario'])

from flask import Response
from datetime import datetime
import sqlite3

@app.route('/reporte-inventario', methods=['GET', 'POST'])
def reporte_inventario():
    conn = sqlite3.connect('inventario.sqlite3')
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT sucursal 
        FROM articulos 
        WHERE LOWER(TRIM(estado)) NOT IN ('vendido', 'perdido')
    """)
    tiendas = sorted([row[0] for row in cur.fetchall()])

    cur.execute("""
        SELECT DISTINCT tp.nombre
        FROM articulos a
        JOIN tipos_producto tp ON a.tipo_id = tp.id
        WHERE LOWER(TRIM(a.estado)) NOT IN ('vendido', 'perdido')
    """)
    productos = sorted([row[0] for row in cur.fetchall()])

    texto = ''
    tipo_reporte = 'general'
    tienda_seleccionada = ''
    producto_seleccionado = ''
    campos = []
    orden_general = 'modelo'
    solo_reparacion = False

    if request.method == 'POST':
        tipo_reporte = request.form.get("tipo_reporte", "general")
        tienda_seleccionada = request.form.get("tienda", "")
        producto_seleccionado = request.form.get("producto", "")
        campos = request.form.getlist("campos")
        orden_general = request.form.get("orden_general", "modelo")
        solo_reparacion = True if request.form.get("solo_reparacion") else False

        base_query = """
            SELECT a.imei, tp.nombre AS producto, a.memoria, a.color, a.sucursal, a.estado, a.precio
            FROM articulos a
            JOIN tipos_producto tp ON a.tipo_id = tp.id
            WHERE LOWER(TRIM(a.estado)) NOT IN ('vendido', 'perdido')
        """
        params = []

        if solo_reparacion:
            base_query += " AND LOWER(TRIM(a.estado)) = 'reparación'"

        if tipo_reporte == "tienda" and tienda_seleccionada and tienda_seleccionada != "Todos":
            base_query += " AND a.sucursal = ?"
            params.append(tienda_seleccionada)

        elif tipo_reporte == "producto" and producto_seleccionado:
            base_query += " AND tp.nombre = ?"
            params.append(producto_seleccionado)
            if tienda_seleccionada and tienda_seleccionada != "Todos":
                base_query += " AND a.sucursal = ?"
                params.append(tienda_seleccionada)

        base_query += " ORDER BY tp.nombre, a.sucursal"

        cur.execute(base_query, params)
        rows = cur.fetchall()

        if not rows:
            texto = "⚠️ No se encontraron resultados para el filtro aplicado."
        else:
            now = (datetime.utcnow() - timedelta(hours=5)).strftime('%d-%m-%Y %H:%M:%S')
            texto += "*REPORTE DE INVENTARIO ACTIVO*\n"
            texto += f"Generado: {now}\n"
            texto += f"Total Artículos en Reporte (Activo): {len(rows)}\n"

            if tipo_reporte == "general":
                conteo_por_tienda = {}
                for r in rows:
                    suc = r[4]
                    conteo_por_tienda[suc] = conteo_por_tienda.get(suc, 0) + 1
                for suc, cant in conteo_por_tienda.items():
                    texto += f"  {suc}: {cant} art.\n"
                texto += "\n"

                agrupado = {}
                for r in rows:
                    imei, producto, memoria, color, sucursal, estado, precio = r
                    clave = sucursal if orden_general == "sucursal" else producto

                    if clave not in agrupado:
                        agrupado[clave] = {}

                    if orden_general == "sucursal":
                        subclave = producto
                    else:
                        subclave = sucursal

                    if subclave not in agrupado[clave]:
                        agrupado[clave][subclave] = []

                    detalles = ""
                    if "imei" in campos:
                        detalles += f"IMEI: {imei} | "
                    if "memoria" in campos:
                        detalles += f"Memoria: {memoria} | "
                    if "color" in campos:
                        detalles += f"Color: {color} | "
                    if "tienda" in campos:
                        detalles += f"Tienda: {sucursal} | "
                    if "estado" in campos:
                        detalles += f"Est: {estado} | "
                    if "precio" in campos:
                        if precio not in (None, '', ' '):
                            try:
                                detalles += f"Precio: ${float(precio):.2f} | "
                            except:
                                detalles += "Precio: N/A | "
                        else:
                            detalles += "Precio: N/A | "

                    agrupado[clave][subclave].append(detalles.strip(" | "))

                for grupo, subgrupos in agrupado.items():
                    texto += f"\n{ 'TIENDA: ' if orden_general == 'sucursal' else 'Producto: ' }{grupo.upper()}\n"
                    texto += "-" * 20 + "\n"
                    for sub, items in subgrupos.items():
                        if orden_general == 'sucursal':
                            texto += f"Producto: {sub}\n"
                        else:
                            texto += f"Tienda: {sub}\n"
                        for i, item in enumerate(items, 1):
                            texto += f"{i}. {item}\n"
                        texto += "\n"

            else:
                agrupado = {}
                for r in rows:
                    imei, producto, memoria, color, sucursal, estado, precio = r
                    clave = f"{producto} - {sucursal}" if tipo_reporte == "producto" and tienda_seleccionada == "Todos" else producto
                    if clave not in agrupado:
                        agrupado[clave] = []

                    detalles = ""
                    if "imei" in campos:
                        detalles += f"IMEI: {imei} | "
                    if "memoria" in campos:
                        detalles += f"Memoria: {memoria} | "
                    if "color" in campos:
                        detalles += f"Color: {color} | "
                    if "tienda" in campos:
                        detalles += f"Tienda: {sucursal} | "
                    if "estado" in campos:
                        detalles += f"Estatus: {estado} | "
                    if "precio" in campos:
                        if precio not in (None, '', ' '):
                            try:
                                detalles += f"Precio: ${float(precio):.2f} | "
                            except:
                                detalles += "Precio: N/A | "
                        else:
                            detalles += "Precio: N/A | "

                    agrupado[clave].append(detalles.strip(" | "))

                for grupo, items in agrupado.items():
                    texto += f"\nProducto: {grupo}\n"
                    for i, item in enumerate(items, 1):
                        texto += f"{i}. {item}\n"
                    texto += "\n"

    conn.close()
    return render_template("reporte_inventario.html",
                           texto=texto,
                           tipo_reporte=tipo_reporte,
                           tiendas=["Todos"] + tiendas,
                           tienda_seleccionada=tienda_seleccionada,
                           productos=productos,
                           producto_seleccionado=producto_seleccionado,
                           campos=campos,
                           orden_general=orden_general,
                           solo_reparacion=solo_reparacion)

@app.route('/recibir-garantia', methods=['GET', 'POST'])
def recibir_garantia():
    if 'usuario' not in session:
        return redirect('/login')

    if request.method == 'POST':
        cliente = request.form['cliente']
        recibido_por = request.form['recibido_por']
        imei = request.form['imei']
        modelo = request.form['modelo']
        fecha_venta = request.form['fecha_venta']
        condiciones = request.form['condiciones']
        accesorios = request.form['accesorios']
        faltante = request.form['faltante']
        daños = request.form['daños']
        problema = request.form['problema']
        tipo_recepcion = request.form['tipo_recepcion']
        pagos = request.form['pagos']

        fotos = request.files.getlist('fotos')
        captura_grupo = request.files.get('captura_grupo')

        
        folder = f"static/garantias/{imei}_{datetime.now().strftime('%d%m%Y%H%M%S')}"
        os.makedirs(folder, exist_ok=True)
        fotos_guardadas = []

        for i, foto in enumerate(fotos):
            if foto.filename:
                path = os.path.join(folder, f'foto{i+1}.jpg')
                foto.save(path)
                fotos_guardadas.append(path)

        
        captura_path = ''
        if captura_grupo and captura_grupo.filename:
            captura_path = os.path.join(folder, 'grupo.jpg')
            captura_grupo.save(captura_path)

        
        conn = sqlite3.connect("inventario.sqlite3")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO garantias_recibidas 
            (cliente, recibido_por, imei, modelo, fecha_venta, condiciones, accesorios, faltante, daños, 
            problema, tipo_recepcion, pagos, fotos, captura_grupo, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente, recibido_por, imei, modelo, fecha_venta, condiciones, accesorios, faltante, daños,
            problema, tipo_recepcion, pagos, ','.join(fotos_guardadas), captura_path, datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        ))
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template("recibir_garantia.html")

@app.route('/tipos-producto', methods=['GET', 'POST'])
def tipos_producto():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    mensaje = ""

    if request.method == 'POST':
        accion = request.form.get('accion')
        tipo_id = request.form.get('tipo_id')
        marca = request.form.get('marca', '').strip()
        modelo = request.form.get('modelo', '').strip()
        stock_minimo = request.form.get('stock_minimo', '').strip()

        if accion == "añadir":
            if marca and modelo:
                nombre = f"{marca} {modelo}"
                try:
                    cur.execute("INSERT INTO tipos_producto (nombre, stock_minimo) VALUES (?, ?)", (nombre, stock_minimo or 0))
                    conn.commit()
                    registrar_log(session['usuario'], "Registro", f"Tipo de producto agregado: {nombre}")
                    mensaje = f"✅ Tipo '{nombre}' añadido correctamente."
                except sqlite3.IntegrityError:
                    mensaje = f"❌ Ya existe el tipo: {nombre}"

        elif accion == "editar" and tipo_id:
            if marca and modelo:
                nuevo_nombre = f"{marca} {modelo}"
                cur.execute("UPDATE tipos_producto SET nombre = ?, stock_minimo = ? WHERE id = ?", (nuevo_nombre, stock_minimo or 0, tipo_id))
                conn.commit()
                registrar_log(session['usuario'], "Edición", f"Tipo de producto ID {tipo_id} actualizado a {nuevo_nombre}")
                mensaje = f"✅ Tipo actualizado."

        elif accion == "eliminar" and tipo_id:
            cur.execute("SELECT nombre FROM tipos_producto WHERE id = ?", (tipo_id,))
            tipo = cur.fetchone()
            if tipo:
                cur.execute("DELETE FROM tipos_producto WHERE id = ?", (tipo_id,))
                conn.commit()
                registrar_log(session['usuario'], "Eliminación", f"Tipo de producto eliminado: {tipo[0]}")
                mensaje = f"✅ Tipo eliminado."

    cur.execute("SELECT id, nombre, stock_minimo FROM tipos_producto ORDER BY id ASC")
    tipos = cur.fetchall()
    conn.close()
    return render_template("tipos_producto.html", tipos=tipos, mensaje=mensaje)

@app.route('/eliminar-tipo/<int:tipo_id>', methods=['POST'])
def eliminar_tipo(tipo_id):
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect('/')
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM tipos_producto WHERE id = ?", (tipo_id,))
    tipo = cur.fetchone()
    if tipo:
        cur.execute("DELETE FROM tipos_producto WHERE id = ?", (tipo_id,))
        conn.commit()
        registrar_log(session['usuario'], "Eliminación", f"Tipo de producto eliminado: {tipo[0]}")
    conn.close()
    return redirect('/tipos-producto')

@app.route("/eliminar-articulos", methods=["POST"])
def eliminar_articulos():
    if session.get("tipo") != "admin":
        return redirect("/login")

    ids = request.form.getlist("ids")
    if not ids:
        return "Error: No se seleccionaron artículos.", 400

    conn = sqlite3.connect("inventario.sqlite3")
    cursor = conn.cursor()
    cursor.executemany("DELETE FROM articulos WHERE id = ?", [(art_id,) for art_id in ids])
    conn.commit()
    conn.close()

    return redirect("/resumen_general")

@app.route("/actualizar-color", methods=["POST"])
def actualizar_color():
    if "usuario" not in session or session["tipo"] != "admin":
        return jsonify(success=False)

    data = request.get_json()
    articulo_id = data.get("id")
    nuevo_color = data.get("color")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE articulos SET color = ? WHERE id = ?", (nuevo_color, articulo_id))
        conn.commit()

    return jsonify(success=True)

@app.route("/historial-estados-imei/<imei>")
def historial_estados_imei(imei):
    if "usuario" not in session:
        return jsonify({"success": False, "mensaje": "No autorizado"})

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT accion, fecha 
            FROM log_actividad 
            WHERE accion LIKE ? OR descripcion LIKE ?
            ORDER BY id DESC
        """, (f'%{imei}%', f'%{imei}%'))
        rows = cur.fetchall()

    historial = []
    for row in rows:
        try:
            # Parsear la fecha original (guardada en UTC o zona del servidor)
            fecha_original = datetime.strptime(row["fecha"], "%d-%m-%Y %H:%M:%S")
            # Ajustar a hora de Tamaulipas (UTC-5 en horario de verano)
            fecha_local = fecha_original - timedelta(hours=5)
            fecha_formateada = fecha_local.strftime("%d-%m-%Y %H:%M:%S")
        except Exception:
            fecha_formateada = row["fecha"]

        historial.append({
            "accion": row["accion"],
            "fecha": fecha_formateada
        })

    return jsonify({"success": True, "historial": historial})

@app.route("/generar-inventario", methods=["POST"])
def generar_inventario():
    if "usuario" not in session or session["tipo"] != "admin":
        return redirect("/")

    sucursal = request.form["sucursal"]
    fecha = datetime.now().strftime("%d-%m-%Y")
    generado_por = session.get("nombre_real", session.get("usuario", "Admin"))

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT a.imei
        FROM articulos a
        WHERE a.sucursal = ? AND (a.estado IS NULL OR a.estado NOT IN ('Vendido', 'Perdido'))
    """, (sucursal,))
    imeis = cur.fetchall()

    for (imei,) in imeis:
        cur.execute("""
            INSERT INTO inventarios_pendientes (sucursal, fecha, generado_por, imei)
            VALUES (?, ?, ?, ?)
        """, (sucursal, fecha, generado_por, imei))

    conn.commit()
    conn.close()

    return f"Inventario generado correctamente para {sucursal}."

@app.route("/generar-inventario-panel")
def generar_inventario_panel():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT sucursal FROM articulos")
    sucursales = [row[0] for row in cur.fetchall()]
    conn.close()

    return render_template("generar_inventario_form.html", sucursales=sucursales)

@app.route("/hacer-inventario")
def hacer_inventario():
    if "usuario" not in session or session.get("tipo") != "consulta":
        return redirect("/")

    sucursal = session.get("sucursal")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Traer todos los IMEIs pendientes de esa sucursal
    cur.execute("""
        SELECT ip.imei, tp.nombre AS tipo, a.memoria, a.color, a.estado
        FROM inventarios_pendientes ip
        JOIN articulos a ON ip.imei = a.imei
        JOIN tipos_producto tp ON a.tipo_id = tp.id
        WHERE ip.sucursal = ?
    """, (sucursal,))
    equipos = cur.fetchall()
    conn.close()

    return render_template("hacer_inventario.html", equipos=equipos, sucursal=sucursal)

@app.route("/finalizar-inventario", methods=["POST"])
def finalizar_inventario():
    if "usuario" not in session or session.get("tipo") != "consulta":
        return redirect("/")

    sucursal = request.form.get("sucursal")
    confirmado_por = session.get("nombre_real")
    fecha = datetime.now().strftime("%d-%m-%Y")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Traer los imeis pendientes de esa sucursal
    cur.execute("""
        SELECT ip.imei, tp.nombre, a.memoria, a.color, a.estado
        FROM inventarios_pendientes ip
        JOIN articulos a ON ip.imei = a.imei
        JOIN tipos_producto tp ON a.tipo_id = tp.id
        WHERE ip.sucursal = ?
    """, (sucursal,))
    pendientes = cur.fetchall()

    for imei, tipo, memoria, color, estado in pendientes:
        key = f"imei_{imei}"
        encontrado = request.form.get(key)
        if encontrado:
            cur.execute("""
                INSERT INTO inventario_respuesta
                (sucursal, fecha, imei, tipo, memoria, color, estado_actual, encontrado, confirmado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sucursal, fecha, imei, tipo, memoria, color, estado or '', encontrado, confirmado_por))

    # Limpiar los pendientes de esa sucursal
    cur.execute("DELETE FROM inventarios_pendientes WHERE sucursal = ?", (sucursal,))
    conn.commit()
    conn.close()

    return render_template("inventario_confirmado.html", sucursal=sucursal)

@app.route("/resultados-inventario", methods=["GET"])
def resultados_inventario():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Filtros (opcional)
    sucursal = request.args.get("sucursal", "")
    fecha = request.args.get("fecha", "")

    # Obtener sucursales y fechas disponibles
    cur.execute("SELECT DISTINCT sucursal FROM inventario_respuesta")
    sucursales = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT fecha FROM inventario_respuesta ORDER BY fecha DESC")
    fechas = [row[0] for row in cur.fetchall()]

    query = """
        SELECT fecha, sucursal, imei, tipo, memoria, color, estado_actual, encontrado, confirmado_por
        FROM inventario_respuesta
        WHERE 1 = 1
    """
    params = []

    if sucursal:
        query += " AND sucursal = ?"
        params.append(sucursal)

    if fecha:
        query += " AND fecha = ?"
        params.append(fecha)

    query += " ORDER BY fecha DESC, sucursal, encontrado"

    cur.execute(query, params)
    resultados = cur.fetchall()

    conn.close()

    return render_template("resultados_inventario.html", resultados=resultados,
                           sucursales=sucursales, fechas=fechas,
                           sucursal_seleccionada=sucursal, fecha_seleccionada=fecha)

@app.route("/cancelar-inventario", methods=["POST"])
def cancelar_inventario():
    if "usuario" not in session or session["tipo"] != "admin":
        return redirect("/")

    sucursal = request.form["sucursal"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM inventarios_pendientes
        WHERE sucursal = ? AND confirmado IS NULL
    """, (sucursal,))
    conn.commit()
    conn.close()

    return f"Inventario pendiente de {sucursal} cancelado correctamente."

@app.errorhandler(403)
def error_403(e):
    return render_template('error.html', mensaje="Acceso no autorizado (403)"), 403

@app.errorhandler(404)
def error_404(e):
    return render_template('error.html', mensaje="Página no encontrada (404)"), 404

@app.errorhandler(500)
def error_500(e):
    return render_template('error.html', mensaje="Error interno del servidor (500)"), 500

# Inicializar la base de datos
init_db()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)