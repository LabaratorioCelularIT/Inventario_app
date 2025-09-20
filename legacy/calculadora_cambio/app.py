from flask import Flask, render_template, request, redirect, session, jsonify, abort
import sqlite3, os
from datetime import datetime, timedelta
import ast
from pytz import timezone

TZ = timezone("America/Matamoros")

def fecha_hoy():
    return datetime.now(TZ).strftime("%d-%m-%Y")

app = Flask(__name__)
app.secret_key = "cambio_secret_key"

DB_PATH = os.path.join(os.path.dirname(__file__), "inventario.sqlite3")
PASSWORD = "262293"

REDES_LOCALES = [
    '138.84.61.74', '138.84.61.41', '138.84.61.11',
    '187.189.164.174', '138.84.61.99', '138.84.61.25',
    '187.190.158.152'
]

DISPOSITIVOS_ESPECIALES = [
    '189.145.88.123', '189.150.77.88', '192.168.1.139'
]

DENOM = [1, 2, 5, 10, 20, 50, 100]
SUCURSALES = ["Colinas", "Hidalgo", "Voluntad 1", "Reservas", "Villas"]
OBJETIVOS_DEFAULT = {1: 40, 2: 40, 5: 40, 10: 20, 20: 20, 50: 10, 100: 5}

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        # Tabla de ciclos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ciclos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sucursal TEXT,
                fecha TEXT,
                datos TEXT
            )
        """)

        # Insertar registros por sucursal y denominación si no existen
        for suc in SUCURSALES:
            for d in DENOM:
                objetivos = OBJETIVOS_DEFAULT.get(d, 0)
                cur.execute("""
                    INSERT OR IGNORE INTO fondo (
                        sucursal, denominacion, cantidad_objetivo, cantidad_actual, cantidad_repuesta
                    ) VALUES (?, ?, ?, 0, 0)
                """, (suc, d, objetivos))
        con.commit()

@app.route("/", methods=["GET", "POST"])
def index():
    hoy = fecha_hoy()

    if request.method == "POST":
        sucursal = request.form["sucursal"]
        fecha = request.form["fecha"]

        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("SELECT datos FROM ciclos WHERE sucursal = ? AND fecha = ?", (sucursal, fecha))
            registro_existente = cur.fetchone()
            if registro_existente:
                datos = ast.literal_eval(registro_existente[0])
                session["ciclo"] = datos
                session["ya_registrado"] = True
                return redirect("/confirmar")

            cur.execute("SELECT datos FROM cantidad_actual_temp WHERE sucursal = ? AND fecha = ?", (sucursal, fecha))
            sugerencia = cur.fetchone()
            if sugerencia:
                actuales = ast.literal_eval(sugerencia[0])
            else:
                actuales = {d: int(request.form.get(f"actual_{d}", 0)) for d in DENOM}

        objetivos = OBJETIVOS_DEFAULT.copy()
        diferencias = {d: objetivos[d] - actuales[d] for d in DENOM}
        dar = sum(max(0, diferencias[d]) * d for d in DENOM)
        recibir = sum(abs(min(0, diferencias[d])) * d for d in DENOM)

        repuesto = {}
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            for d in DENOM:
                delta = diferencias[d]
                if delta > 0:
                    actual_caja = cur.execute("SELECT cantidad FROM caja WHERE denom = ?", (d,)).fetchone()
                    actual_caja = actual_caja[0] if actual_caja else 0
                    repuesto[d] = min(delta, actual_caja)
                else:
                    repuesto[d] = 0

        total_objetivo = sum(objetivos[d] * d for d in DENOM)
        total_actual = sum(actuales[d] * d for d in DENOM)
        total_repuesto = sum(repuesto[d] * d for d in DENOM)

        session["ciclo"] = {
            "sucursal": sucursal,
            "fecha": fecha,
            "actuales": actuales,
            "objetivos": objetivos,
            "diferencias": diferencias,
            "dar": dar,
            "recibir": recibir,
            "repuesto": repuesto,
            "total_objetivo": total_objetivo,
            "total_actual": total_actual,
            "total_repuesto": total_repuesto
        }
        session["ya_registrado"] = False
        return redirect("/confirmar")

    
    sucursal = session.get("sucursal", SUCURSALES[0])
    fecha = hoy

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT datos FROM cantidad_actual_temp WHERE sucursal = ? AND fecha = ?", (sucursal, fecha))
        sugerencia = cur.fetchone()
        if sugerencia:
            actuales = ast.literal_eval(sugerencia[0])
        else:
            actuales = {d: 0 for d in DENOM}

    return render_template("index.html",
                           sucursales=SUCURSALES,
                           fecha_actual=hoy,
                           objetivos=OBJETIVOS_DEFAULT,
                           fondo=get_caja(),
                           actuales=actuales)

@app.route("/confirmar", methods=["GET", "POST"])
def confirmar():
    raw_data = session.get("ciclo")
    if not raw_data:
        return redirect("/")

    data = {
        "sucursal": raw_data["sucursal"],
        "fecha": raw_data["fecha"],
        "actuales": {int(k): v for k, v in raw_data["actuales"].items()},
        "objetivos": {int(k): v for k, v in raw_data["objetivos"].items()},
        "diferencias": {int(k): v for k, v in raw_data["diferencias"].items()},
        "repuesto": {int(k): v for k, v in raw_data["repuesto"].items()},
        "dar": raw_data["dar"],
        "recibir": raw_data["recibir"]
    }

    total_objetivo = raw_data.get("total_objetivo", sum(data["objetivos"][d] * d for d in DENOM))
    total_actual = raw_data.get("total_actual", sum(data["actuales"][d] * d for d in DENOM))

    total_repuesto = 0
    for d in DENOM:
        if data["diferencias"][d] > 0 and data["repuesto"][d] > 0:
            usado = min(data["diferencias"][d], data["repuesto"][d])
            total_repuesto += usado * d

    ya_registrado = session.get("ya_registrado", False)

    if request.method == "POST" and not ya_registrado:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            for d in DENOM:
                delta = data["diferencias"][d]
                if delta > 0:
                    cur.execute("UPDATE caja SET cantidad = cantidad - ? WHERE denom = ?", (data["repuesto"][d], d))
                elif delta < 0:
                    cur.execute("UPDATE caja SET cantidad = cantidad + ? WHERE denom = ?", (abs(delta), d))
            cur.execute("INSERT INTO ciclos (sucursal, fecha, datos) VALUES (?, ?, ?)", (data["sucursal"], data["fecha"], str(data)))
        session.pop("ciclo")
        session.pop("ya_registrado")
        return redirect("/")

    return render_template("confirmar.html", data=data, denom=DENOM,
                           total_objetivo=total_objetivo,
                           total_actual=total_actual,
                           total_repuesto=total_repuesto,
                           ya_registrado=ya_registrado)

@app.route("/modificar_ciclo/<int:ciclo_id>", methods=["GET", "POST"])
def modificar_ciclo(ciclo_id):
    if not session.get("autorizado"):
        return redirect("/login?next=ver_ciclos")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        row = cur.execute("SELECT datos FROM ciclos WHERE id = ?", (ciclo_id,)).fetchone()
        if not row:
            return "Ciclo no encontrado", 404
        datos = ast.literal_eval(row[0])

    if request.method == "POST":
        actuales = {d: int(request.form.get(f"actual_{d}", 0)) for d in DENOM}
        objetivos = datos["objetivos"]
        diferencias = {d: objetivos[d] - actuales[d] for d in DENOM}
        dar = sum(max(0, diferencias[d]) * d for d in DENOM)
        recibir = sum(abs(min(0, diferencias[d])) * d for d in DENOM)
        repuesto = {d: int(request.form.get(f"repuesto_{d}", 0)) for d in DENOM}

        total_objetivo = sum(objetivos[d] * d for d in DENOM)
        total_actual = sum(actuales[d] * d for d in DENOM)
        total_repuesto = sum(repuesto[d] * d for d in DENOM)

        nuevo = {
            "sucursal": datos["sucursal"],
            "fecha": datos["fecha"],
            "actuales": actuales,
            "objetivos": objetivos,
            "diferencias": diferencias,
            "dar": dar,
            "recibir": recibir,
            "repuesto": repuesto,
            "total_objetivo": total_objetivo,
            "total_actual": total_actual,
            "total_repuesto": total_repuesto
        }

        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("UPDATE ciclos SET datos = ? WHERE id = ?", (str(nuevo), ciclo_id))
        return redirect("/ver_ciclos")

    return render_template("modificar_ciclo.html", datos=datos, denom=DENOM)

@app.route("/fondo", methods=["GET", "POST"])
def fondo():
    if not session.get("autorizado"):
        return redirect("/login?next=fondo")

    if request.method == "POST":
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            for d in DENOM:
                n = request.form.get(f"nuevo_{d}")
                if n and n.isdigit():
                    cur.execute("UPDATE caja SET cantidad = ? WHERE denom = ?", (int(n), d))
        return redirect("/fondo")

    return render_template("fondo.html", fondo=get_caja(), denom=DENOM)

@app.route("/ver_ciclos", methods=["GET", "POST"])
def ver_ciclos():
    if not session.get("autorizado"):
        return redirect("/login?next=ver_ciclos")

    if request.method == "POST":
        eliminar_id = request.form.get("eliminar")
        if eliminar_id:
            with sqlite3.connect(DB_PATH) as con:
                cur = con.cursor()
                cur.execute("SELECT datos FROM ciclos WHERE id = ?", (eliminar_id,))
                row = cur.fetchone()
                if row:
                    datos = ast.literal_eval(row[0])
                    diferencias = datos.get("diferencias", {})
                    repuesto = datos.get("repuesto", {})
                    for d in DENOM:
                        d = int(d)
                        diff = diferencias.get(d, 0)
                        rep = repuesto.get(d, 0)
                        if diff < 0:
                            cur.execute("UPDATE fondo SET cantidad = cantidad - ? WHERE denom = ?", (abs(diff), d))
                        elif diff > 0:
                            cur.execute("UPDATE fondo SET cantidad = cantidad + ? WHERE denom = ?", (min(rep, diff), d))
                cur.execute("DELETE FROM ciclos WHERE id = ?", (eliminar_id,))
        return redirect("/ver_ciclos")

    filtro_sucursal = request.args.get("sucursal", "")
    filtro_fecha = request.args.get("fecha", "")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        query = "SELECT id, sucursal, fecha, datos FROM ciclos WHERE 1=1"
        params = []

        if filtro_sucursal:
            query += " AND sucursal = ?"
            params.append(filtro_sucursal)
        if filtro_fecha:
            query += " AND fecha = ?"
            params.append(filtro_fecha)

        query += " ORDER BY id DESC"
        registros = cur.execute(query, params).fetchall()

        registros = [{
            "id": r[0],
            "sucursal": r[1],
            "fecha": r[2],
            "datos": ast.literal_eval(r[3])
        } for r in registros]

    return render_template("ver_ciclos.html", registros=registros, sucursales=SUCURSALES,
                           filtro_sucursal=filtro_sucursal, filtro_fecha=filtro_fecha)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["pass"] == PASSWORD:
            session["autorizado"] = True
            next_url = request.args.get("next", "/")
            return redirect(f"/{next_url}")
    return render_template("login.html")

@app.route("/chat/enviar", methods=["POST"])
def enviar_mensaje():
    data = request.json
    remitente = session.get("usuario", "anónimo")
    destinatario = data.get("destinatario")
    mensaje = data.get("mensaje")
    modulo = data.get("modulo")
    archivo = data.get("archivo", None)  # Opcional

    if not mensaje or not destinatario:
        return jsonify({"ok": False, "error": "Mensaje o destinatario faltante"})

    fecha = datetime.now(TZ).strftime("%d-%m-%Y %H:%M:%S")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO chat (fecha, remitente, destinatario, mensaje, modulo, leido, archivo)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (fecha, remitente, destinatario, mensaje, modulo, archivo))

    return jsonify({"ok": True})

@app.route("/chat/recibir")
def recibir_mensajes():
    usuario = session.get("usuario", "")
    tipo = session.get("tipo", "")
    modulo = request.args.get("modulo", "")

    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM chat
            WHERE destinatario IN (?, ?, ?, 'Todos')
            AND modulo IN (?, 'General', '')
            ORDER BY id DESC LIMIT 100
        """, (usuario, session.get("sucursal", ""), tipo, modulo))
        mensajes = cur.fetchall()

    return jsonify([dict(row) for row in mensajes])

@app.route("/chat/notificaciones")
def notificaciones_chat():
    usuario = session.get("usuario", "")
    tipo = session.get("tipo", "")
    modulo = request.args.get("modulo", "")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM chat
            WHERE destinatario IN (?, ?, ?, 'Todos') AND leido = 0
            AND modulo IN (?, 'General', '')
        """, (usuario, session.get("sucursal", ""), tipo, modulo))
        total = cur.fetchone()[0]

    return jsonify({"nuevos": total})

@app.route("/subir_archivo_chat", methods=["POST"])
def subir_archivo_chat():
    archivo = request.files.get("archivo")
    if not archivo:
        return jsonify({"ok": False, "error": "No hay archivo"})

    nombre = datetime.now().strftime("%d%m%Y%H%M%S") + "_" + archivo.filename
    ruta = os.path.join("static", "chat", nombre)
    archivo.save(ruta)

    return jsonify({"ok": True, "nombre": nombre})

@app.route("/ver_caja", methods=["GET", "POST"])
def ver_caja():
    if request.method == "POST":
        if request.form.get("pass") == "labcel2578":
            session["ver_caja_autorizado"] = True
            return redirect("/ver_caja")
        else:
            return render_template("ver_caja_login.html", error="Contraseña incorrecta.")
    
    if not session.get("ver_caja_autorizado"):
        return render_template("ver_caja_login.html", error=None)

    caja = get_caja()
    total_caja = sum(cantidad * denom for denom, cantidad in caja.items())
    return render_template("ver_caja.html", fondo=caja, denom=DENOM, total_fondo=total_caja)

@app.route("/faltantes")
def faltantes():
    fecha = request.args.get("fecha")
    if not fecha:
        return jsonify({"faltantes": []})
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        enviadas = cur.execute("SELECT DISTINCT sucursal FROM ciclos WHERE fecha = ?", (fecha,)).fetchall()
        enviadas = [e[0] for e in enviadas]
        faltantes = [s for s in SUCURSALES if s not in enviadas]
    return jsonify({"faltantes": faltantes})

def get_caja():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        return dict(cur.execute("SELECT denom, cantidad FROM caja").fetchall())

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0")
