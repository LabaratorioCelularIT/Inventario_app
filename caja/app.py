from flask import Flask, render_template, request, redirect, session, send_file, jsonify, flash, url_for
import sqlite3
import os
from datetime import datetime
from pytz import timezone
from openpyxl import load_workbook
from io import BytesIO
import re
import requests
import ast
import json
from datetime import datetime, timedelta
import base64
from flask import request
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from utils import enviar_codigo_verificacion
import random

# Configuración inicial
app = Flask(__name__)
app.secret_key = 'clave-secreta-caja'
DB_PATH = "/app/inventario.sqlite3"

SUCURSALES = ["Hidalgo", "Colinas", "Voluntad 1", "Reservas", "Villas"]

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

# Zona horaria
TZ = timezone("America/Monterrey")

DENOM = [1, 2, 5, 10, 20, 50, 100]

OBJETIVOS_DEFAULT = {
    1: 40,
    2: 40,
    5: 40,
    10: 20,
    20: 20,
    50: 10,
    100: 5
}


# Funciones de utilidad
def fecha_hoy():
    return datetime.now(TZ).strftime("%d-%m-%Y")

def fecha_hora_actual():
    return datetime.now(TZ).strftime("%d-%m-%Y %H:%M:%S")

def validar_contrasena_segura(contrasena):
    return bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$', contrasena))

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE,
                contrasena TEXT,
                tipo TEXT,
                sucursal TEXT
            )
        ''')
        conn.commit()

def registrar_log(usuario, tipo, accion):
    fecha_hora = fecha_hora_actual()
    origen = "Caja"
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO log_actividad (usuario, tipo, accion, fecha, origen)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario, tipo, accion, fecha_hora, origen))
        conn.commit()

def get_caja():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT denom, cantidad FROM caja")
        return dict(cur.fetchall())

def ya_envio_feria(sucursal, fecha):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ciclos WHERE sucursal = ? AND fecha = ?", (sucursal, fecha))
        count = cur.fetchone()[0]
        return count > 0

@app.before_request
def forzar_logout_por_turno():
    usuario = session.get("usuario")
    tipo = session.get("tipo")

    if usuario and tipo in ["consulta", "reparto"]:
        ahora = datetime.now()
        inicio_sesion_str = session.get("inicio_sesion")

        if not inicio_sesion_str:
            session["inicio_sesion"] = ahora.isoformat()
        else:
            inicio_sesion = datetime.fromisoformat(inicio_sesion_str)
            if ahora - inicio_sesion > timedelta(hours=4):
                session.clear()
                flash("🔒 Tu sesión ha expirado después del turno de 4 horas. Por favor inicia sesión de nuevo.")
                return redirect("/login")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        tipo_usuario = request.form["tipo"]
        nombre = request.form["usuario"]
        contraseña = request.form["contrasena"]  
        sucursal = request.form.get("sucursal")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, contraseña, tipo FROM usuarios WHERE nombre = ?", (nombre,))
        usuario = cur.fetchone()
        conn.close()

        if usuario and usuario[1] == contraseña and usuario[2] == tipo_usuario:
            session["usuario"] = nombre
            session["tipo"] = tipo_usuario
            session["sucursal"] = sucursal
            session["inicio_sesion"] = datetime.now().isoformat()

            registrar_log(nombre, tipo_usuario, "Inicio de sesión exitoso")

            if tipo_usuario == "admin":
                return redirect("/panel-admin")
            elif tipo_usuario == "consulta":
                return redirect("/panel-consulta")
            elif tipo_usuario == "reparto":
                return redirect("/panel-reparto")
            else:
                return "Tipo de usuario desconocido", 403
        else:
            return render_template("login.html", error="Credenciales incorrectas", tipo=tipo_usuario)

    return render_template("login.html")

@app.route("/panel-admin")
def panel_admin():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/")

    bloqueos_pendientes = 0
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM bloqueos_feria WHERE autorizado = 0")
        bloqueos_pendientes = cur.fetchone()[0]

    return render_template("panel-admin.html", sucursales=SUCURSALES, bloqueos_pendientes=bloqueos_pendientes)

@app.route("/panel-consulta")
def panel_consulta():
    if "usuario" not in session or session.get("tipo") != "consulta":
        return redirect("/")

    nombre_usuario = session.get("usuario", "")
    nombre_real = NOMBRES_REALES.get(nombre_usuario, nombre_usuario)

    return render_template(
        "panel-consulta.html",
        sucursal=session.get("sucursal", ""),
        tipo=session.get("tipo", ""),
        nombre_real=nombre_real
    )

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        correo = request.form["correo"]
        nombre = request.form["nombre"]
        contrasena = request.form["contrasena"]
        confirmar = request.form["confirmar"]
        telefono = request.form["telefono"]
        tipo = request.form["tipo"]

        if contrasena != confirmar:
            return render_template("registro.html", error="Las contraseñas no coinciden.")

        patron = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+=?<>.,]).{6,}$"
        if not re.match(patron, contrasena):
            return render_template("registro.html", error="La contraseña no cumple con los requisitos.")

        nombre_base = nombre.split()[0].lower()
        codigo = random.randint(1000, 9999)
        usuario_generado = f"{tipo}_{nombre_base}_{codigo}"

        conn = sqlite3.connect("inventario.sqlite3")
        cur = conn.cursor()

        cur.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario_generado,))
        while cur.fetchone():
            codigo = random.randint(1000, 9999)
            usuario_generado = f"{tipo}_{nombre_base}_{codigo}"
            cur.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario_generado,))

        cur.execute("INSERT INTO usuarios (usuario, contrasena, tipo, correo, telefono) VALUES (?, ?, ?, ?, ?)", 
                    (usuario_generado, contrasena, tipo, correo, telefono))
        conn.commit()
        conn.close()

        return render_template("registro.html", success=f"Usuario registrado con éxito: {usuario_generado}")

    return render_template("registro.html")

@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    mensaje = ""
    error = ""
    if request.method == "POST":
        contacto = request.form.get("contacto", "").strip()

        if not contacto:
            error = "Debes ingresar tu correo o número de teléfono."
            return render_template("recuperar.html", error=error)

        codigo = ''.join(random.choices(string.digits, k=6))
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()

            cur.execute("SELECT usuario FROM usuarios WHERE correo = ? OR telefono = ?", (contacto, contacto))
            resultado = cur.fetchone()

            if resultado:
                usuario = resultado[0]

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS codigos_recuperacion (
                        usuario TEXT,
                        codigo TEXT,
                        contacto TEXT,
                        fecha TEXT
                    )
                """)
                cur.execute("DELETE FROM codigos_recuperacion WHERE usuario = ?", (usuario,))
                cur.execute("INSERT INTO codigos_recuperacion (usuario, codigo, contacto, fecha) VALUES (?, ?, ?, ?)",
                            (usuario, codigo, contacto, fecha))
                conn.commit()

                mensaje = f"Tu código de recuperación es: {codigo} (Solo visible para pruebas, luego se enviará por correo o SMS)"
            else:
                error = "No se encontró ninguna cuenta asociada a ese correo o número."

    return render_template("recuperar.html", mensaje=mensaje, error=error)

@app.route("/verificar-codigo", methods=["GET", "POST"])
def verificar_codigo():
    if request.method == "POST":
        usuario = request.form["usuario"]
        codigo_ingresado = request.form["codigo"]
        nueva_contrasena = request.form["nueva_contrasena"]

        conn = sqlite3.connect("inventario.sqlite3")
        cur = conn.cursor()
        cur.execute("SELECT codigo FROM codigos_verificacion WHERE usuario = ?", (usuario,))
        fila = cur.fetchone()
        conn.close()

        if fila and fila[0] == codigo_ingresado:
            # validar nueva contraseña
            if not validar_contrasena_segura(nueva_contrasena):
                return render_template("verificar_codigo.html", usuario=usuario, error="La contraseña no cumple los requisitos de seguridad.")

            conn = sqlite3.connect("inventario.sqlite3")
            cur = conn.cursor()
            cur.execute("UPDATE usuarios SET contrasena = ? WHERE usuario = ?", (nueva_contrasena, usuario))
            cur.execute("DELETE FROM codigos_verificacion WHERE usuario = ?", (usuario,))
            conn.commit()
            conn.close()
            return redirect("/login")
        else:
            return render_template("verificar_codigo.html", usuario=usuario, error="Código incorrecto.")
    
    usuario = request.args.get("usuario", "")
    return render_template("verificar_codigo.html", usuario=usuario)

@app.route('/enviar-codigo', methods=['POST'])
def enviar_codigo():
    dato = request.form.get("dato")
    codigo = str(random.randint(100000, 999999))

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT correo, telefono FROM usuarios WHERE correo = ? OR telefono = ?", (dato, dato))
        usuario = cur.fetchone()

        if not usuario:
            return render_template("enviar_codigo.html", error="❌ No se encontró ninguna cuenta con ese dato.")

        correo, telefono = usuario

        # Guardar código en sesión
        session["codigo_verificacion"] = codigo
        session["dato_verificado"] = dato

        if correo:
            enviado = enviar_codigo_verificacion(correo, codigo)
            if enviado:
                return redirect("/verificar-codigo")
            else:
                return render_template("enviar_codigo.html", error="❌ Falló el envío del correo.")
        else:
            return render_template("enviar_codigo.html", error="❌ Este usuario no tiene correo registrado.")

@app.route('/firmar', methods=['POST'])
def firmar():
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    import base64

    with open("QZ Tray Demo Cert/private-key.pem", "rb") as f:
        key = load_pem_private_key(f.read(), password=None)

    data = request.data
    firma = key.sign(data, padding.PKCS1v15(), hashes.SHA1())
    return base64.b64encode(firma).decode()

@app.route("/logout")
def logout():
    registrar_log(session.get("usuario", "Desconocido"), session.get("tipo", "Desconocido"), "Cerró sesión")
    session.clear()
    return redirect("/")

@app.route("/limpiar-carrito", methods=["POST"])
def limpiar_carrito():
    session.pop("carrito", None)
    session.pop("total", None)
    return '', 204

from datetime import datetime
import pytz

@app.route("/log-actividad", methods=["GET"])
def log_actividad():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/")

    origen = request.args.get("origen", "")
    TZ = pytz.timezone("America/Monterrey")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if origen:
            cur.execute("SELECT usuario, tipo, accion, fecha, origen FROM log_actividad WHERE origen = ? ORDER BY id DESC", (origen,))
        else:
            cur.execute("SELECT usuario, tipo, accion, fecha, origen FROM log_actividad ORDER BY id DESC")
        rows = cur.fetchall()

    logs = []
    for row in rows:
        try:
            fecha = datetime.strptime(row["fecha"], "%d-%m-%Y %H:%M:%S")
            fecha_local = fecha.astimezone(TZ)
            fecha_formateada = fecha_local.strftime("%d-%m-%Y %H:%M:%S")
        except Exception:
            fecha_formateada = row["fecha"]

        logs.append({
            "usuario": row["usuario"],
            "tipo": row["tipo"],
            "accion": row["accion"],
            "fecha": fecha_formateada,
            "origen": row["origen"]
        })

    return render_template("log_actividad.html", logs=logs, origen=origen)

@app.route("/gastos", methods=["GET", "POST"])
def gastos():
    if "usuario" not in session:
        return redirect("/")

    tipo_usuario = session.get("tipo")
    sucursal_sesion = session.get("sucursal")
    fecha_hoy_str = datetime.now(TZ).strftime("%d-%m-%Y")
    sucursales = ["Hidalgo", "Colinas", "Voluntad 1", "Reservas", "Villas"]

    # Obtener filtros (solo los usa el admin)
    sucursal_filtro = request.args.get("sucursal", sucursal_sesion)
    fecha_filtro = request.args.get("fecha", fecha_hoy_str)

    # Si no es admin, forzamos sucursal y fecha
    if tipo_usuario != "admin":
        sucursal_filtro = sucursal_sesion
        fecha_filtro = fecha_hoy_str

        # Guardar gasto
    if request.method == "POST":
        motivo = request.form["motivo"]
        monto = float(request.form["monto"])

        if tipo_usuario == "admin":
            fecha = request.form.get("fecha", fecha_hoy_str)
            try:
                fecha = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
            except:
                pass
            sucursal = request.form.get("sucursal", sucursal_sesion)
        else:
            fecha = fecha_hoy_str
            sucursal = sucursal_sesion

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO gastos (motivo, monto, fecha, sucursal) VALUES (?, ?, ?, ?)",
                        (motivo, monto, fecha, sucursal))
            conn.commit()

        registrar_log(session["usuario"], session["tipo"], f"Registró un gasto en {sucursal} de ${monto:.2f} - {motivo}")
        return redirect(f"/gastos?sucursal={sucursal_filtro}&fecha={fecha_filtro}")

    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, motivo, monto, fecha, sucursal 
            FROM gastos 
            WHERE sucursal = ? AND fecha = ? 
            ORDER BY id DESC
        """, (sucursal_filtro, fecha_filtro))
        gastos = cur.fetchall()

    return render_template("gastos.html",
                           tipo=tipo_usuario,
                           sucursales=sucursales,
                           gastos=gastos,
                           sucursal_filtro=sucursal_filtro,
                           fecha_filtro=fecha_filtro)

@app.route("/eliminar-gasto", methods=["POST"])
def eliminar_gasto():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/")
    gasto_id = request.form["id"]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    conn.commit()
    conn.close()
    return redirect("/gastos")

@app.route("/ventas", methods=["GET", "POST"])
def ventas():
    if "usuario" not in session:
        return redirect("/login")

    if "carrito" not in session:
        session["carrito"] = []

    tipo_usuario = session.get("tipo")
    sucursal_sesion = session.get("sucursal", "")
    fecha_hoy_dt = datetime.now(TZ)
    fecha_hoy_str = fecha_hoy_dt.strftime("%d-%m-%Y")

    
    fecha_input = request.args.get("fecha")
    if fecha_input:
        try:
            fecha_filtro = datetime.strptime(fecha_input, "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            fecha_filtro = fecha_hoy_str
    else:
        fecha_filtro = fecha_hoy_str

    
    sucursal_filtro = request.args.get("sucursal", sucursal_sesion)

    if request.method == "POST":
        descripcion = request.form.get("descripcion", "")
        tipo = request.form.get("tipo", "")
        concepto = request.form.get("concepto", "")
        imei = request.form.get("imei", "")
        referencia = request.form.get("referencia", "")
        tipo_pago = request.form.get("tipo_pago", "")
        precio = float(request.form.get("precio", "0") or 0)

        session["carrito"].append({
            "descripcion": descripcion,
            "tipo": tipo,
            "concepto": concepto,
            "imei": imei,
            "referencia": referencia,
            "tipo_pago": tipo_pago,
            "precio": precio
        })
        session.modified = True
        return redirect("/ventas")

    total = sum(item["precio"] for item in session.get("carrito", []))

    
    ventas_registradas = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if tipo_usuario == "admin":
            cur.execute("SELECT * FROM ventas WHERE fecha LIKE ? AND sucursal = ?",
                        (f"{fecha_filtro}%", sucursal_filtro))
        elif tipo_usuario == "consulta":
            cur.execute("SELECT * FROM ventas WHERE fecha LIKE ? AND sucursal = ?",
                        (f"{fecha_hoy_str}%", sucursal_sesion))
        else:
            cur.execute("SELECT * FROM ventas WHERE 1=0")

        ventas_registradas = cur.fetchall()

    
    fecha_input_str = datetime.strptime(fecha_filtro, "%d-%m-%Y").strftime("%Y-%m-%d")

    return render_template("ventas.html",
                           carrito=session["carrito"],
                           total=total,
                           tipo=tipo_usuario,
                           ventas=ventas_registradas,
                           sucursales=SUCURSALES,
                           sucursal_filtro=sucursal_filtro,
                           fecha=fecha_input_str)


@app.route('/eliminar-venta-admin/<int:id>', methods=['POST'])
def eliminar_venta_admin(id):
    if "usuario" not in session or session.get("tipo") != "admin":
        return jsonify(success=False)

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM ventas WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        print("Error al eliminar venta:", e)
        return jsonify(success=False)

@app.route("/eliminar-item", methods=["POST"])
def eliminar_item():
    if "usuario" not in session or "carrito" not in session:
        return jsonify(success=False), 403

    data = request.get_json()
    index = int(data.get("index"))

    if 0 <= index < len(session["carrito"]):
        session["carrito"].pop(index)
        session.modified = True

    total = sum(item["precio"] for item in session["carrito"])
    return jsonify(success=True, total=total)

from datetime import datetime
import pytz

TZ = pytz.timezone("America/Monterrey")

def fecha_hoy():
    return datetime.now(TZ).strftime("%d-%m-%Y")

from flask import request, session, redirect, render_template, flash
from datetime import datetime
from zoneinfo import ZoneInfo
import sqlite3

@app.route("/cobrar", methods=["POST"])
def cobrar():
    if "usuario" not in session or "carrito" not in session:
        return redirect("/login")

    carrito = session["carrito"]
    usuario = session["usuario"]
    tipo_usuario = session.get("tipo", "")
    sucursal = session.get("sucursal", "")
    fecha = datetime.now(ZoneInfo("America/Monterrey")).strftime("%d-%m-%Y %H:%M:%S")
    fecha_dia = fecha.split(" ")[0]

    efectivo = float(request.form.get("efectivo", 0))
    tarjeta = float(request.form.get("tarjeta", 0))
    dolares = float(request.form.get("dolares", 0))
    tipo_cambio = float(request.form.get("dolar", 0))
    referencia_general = request.form.get("referencia", "")

    total_pago = efectivo + tarjeta + (dolares * tipo_cambio)
    total_venta = sum(item.get("precio", 0) for item in carrito)
    cambio = total_pago - total_venta

    if cambio < 0:
        flash(f"❌ Aún faltan ${abs(cambio):.2f} para completar el pago.")
        return redirect("/ventas")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ventas WHERE fecha LIKE ? AND sucursal = ?", (f"{fecha_dia}%", sucursal))
        ventas_hoy = cur.fetchone()[0]

        if ventas_hoy == 0:
            descripcion_primera = carrito[0].get("descripcion", "").strip().upper()
            if descripcion_primera != "FERIA":
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS bloqueos_feria (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sucursal TEXT,
                        fecha TEXT,
                        motivo TEXT,
                        autorizado INTEGER DEFAULT 0
                    )
                """)
                cur.execute("INSERT INTO bloqueos_feria (sucursal, fecha, motivo, autorizado) VALUES (?, ?, ?, 0)", (sucursal, fecha_dia, "Primera venta no fue FERIA"))
                conn.commit()
                return render_template("venta_bloqueada.html", mensaje="❌ La primera venta del día debe ser FERIA. Espera autorización de un administrador.")

            cur.execute("SELECT autorizado FROM bloqueos_feria WHERE fecha = ? AND sucursal = ?", (fecha_dia, sucursal))
            bloqueo = cur.fetchone()
            if bloqueo and bloqueo[0] == 1:
                pass
            else:
                monto_venta_feria = carrito[0].get("precio", 0)
                ayer = (datetime.now(ZoneInfo("America/Monterrey")) - timedelta(days=1)).strftime("%d-%m-%Y")
                cur.execute("SELECT monto FROM gastos WHERE fecha = ? AND sucursal = ? AND motivo = 'FERIA'", (ayer, sucursal))
                resultado = cur.fetchone()
                if resultado is None or float(resultado[0]) != float(monto_venta_feria):
                    cur.execute("INSERT INTO bloqueos_feria (sucursal, fecha, motivo, autorizado) VALUES (?, ?, ?, 0)", (sucursal, fecha_dia, "Feria no coincide con la salida de ayer"))
                    conn.commit()
                    return render_template("venta_bloqueada.html", mensaje="❌ El monto de la FERIA no coincide con la salida registrada ayer. Espera autorización de un administrador.")

        for item in carrito:
            cur.execute("""
                INSERT INTO ventas (usuario, sucursal, descripcion, tipo, concepto, referencia, precio, tipo_pago, fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario, sucursal,
                item.get("descripcion", ""),
                item.get("tipo", ""),
                item.get("concepto", ""),
                item.get("referencia", referencia_general),
                item.get("precio", 0),
                item.get("tipo_pago", ""),
                fecha
            ))
            imei = item.get("imei", "")
            if imei:
                cur.execute("UPDATE articulos SET estado = 'Vendido' WHERE imei = ?", (imei,))
        conn.commit()

    NOMBRES_USUARIOS = {
        "Litzi": "Litzi",
        "Brayan": "Brayan",
        "Jesús": "Jesús",
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
        "consulta_ajnd_7204": "Alejandrina (consulta)",
        "admin_dvcd_6497": "David",
        "admin_vctr_9051": "Victoria",
        "admin_ajnd_7204": "Alejandrina"
    }

    nombre_usuario = NOMBRES_USUARIOS.get(usuario, usuario)
    productos = carrito.copy()
    session.pop("carrito", None)

    session["ultimo_ticket"] = {
        "sucursal": sucursal,
        "fecha": fecha,
        "nombre_usuario": nombre_usuario,
        "productos": productos,
        "total": total_venta,
        "total_pagado": total_pago,
        "cambio": cambio
    }

    if tipo_usuario == "admin":
        flash("✅ Venta registrada correctamente.")
        return redirect("/ventas")

    return redirect("/abrir-ticket")

@app.route("/autorizar-bloqueo/<int:id>")
def autorizar_bloqueo(id):
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/login")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE bloqueos_feria SET autorizado = 1 WHERE id = ?", (id,))
        conn.commit()

    flash("✅ Bloqueo autorizado correctamente. Ya pueden continuar las ventas.")
    return redirect("/panel-admin")

@app.route("/ver-bloqueos")
def ver_bloqueos():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, sucursal, fecha, motivo, autorizado 
            FROM bloqueos_feria 
            ORDER BY fecha DESC
        """)
        bloqueos = cur.fetchall()

    return render_template("ver_bloqueos.html", bloqueos=bloqueos)

@app.route("/abrir-ticket")
def abrir_ticket():
    return """
    <script>
      window.open('/ultimo-ticket', '_blank', 'width=400,height=600');
      window.location.href = '/ventas';
    </script>
    """

from flask import render_template, session, redirect
from datetime import datetime
from zoneinfo import ZoneInfo  # Requiere Python 3.9+

@app.route("/ticket")
def ticket():
    if "usuario" not in session:
        return redirect("/login")

    
    fecha = datetime.now(ZoneInfo("America/Monterrey")).strftime("%d/%m/%Y %H:%M %S (Hora local)")

    
    NOMBRES_USUARIOS = {
        "Litzi": "Litzi",
        "Brayan": "Brayan",
        "Jesús": "Jesús",
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
        "consulta_ajnd_7204": "Alejandrina (consulta)",
    }

    sucursal = session.get("sucursal", "Sucursal Desconocida")
    usuario = session.get("usuario", "Desconocido")
    nombre_usuario = NOMBRES_USUARIOS.get(usuario, usuario)

    
    productos = [
        {
            "descripcion": "iPhone 13 Pro Max 256GB",
            "concepto": "AT&T",
            "referencia": "1234567890",
            "precio": 19999.99
        }
    ]
    total = sum(item["precio"] for item in productos)
    total_pagado = 20000
    cambio = total_pagado - total

    return render_template("ticket.html",
                           sucursal=sucursal,
                           fecha=fecha,
                           nombre_usuario=nombre_usuario,
                           productos=productos,
                           total=total,
                           total_pagado=total_pagado,
                           cambio=cambio)

@app.route("/ultimo-ticket")
def ultimo_ticket():
    if "ultimo_ticket" not in session:
        return "<h3>No hay ticket reciente para imprimir.</h3>"

    datos = session["ultimo_ticket"]

    return render_template("ticket.html",
        sucursal=datos["sucursal"],
        fecha=datos["fecha"],
        nombre_usuario=datos["nombre_usuario"],
        productos=datos["productos"],
        total=datos["total"],
        total_pagado=datos["total_pagado"],
        cambio=datos["cambio"]
    )

@app.route("/ver-ticket/<int:venta_id>")
def ver_ticket(venta_id):
    if "usuario" not in session:
        return redirect("/")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM ventas WHERE id = ?", (venta_id,))
        venta = cur.fetchone()

    if not venta:
        return "Venta no encontrada", 404

    return render_template("ticket.html",
        sucursal=venta["sucursal"],
        fecha=venta["fecha"],
        producto=venta["descripcion"],
        precio=venta["precio"],
        metodo_pago=venta["tipo_pago"]
    )

@app.route("/fondo")
def ver_fondo_caja():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT fecha, sucursal, cantidad FROM fondo_caja ORDER BY fecha DESC, sucursal ASC")
    registros = c.fetchall()
    conn.close()
    return render_template("fondo_caja.html", registros=registros)

@app.route("/cambio", methods=["GET", "POST"])
def cambio():
    if "usuario" not in session:
        return redirect("/login")

    hoy = get_fecha_hoy()

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
                return redirect("/cambio/confirmar")

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
        return redirect("/cambio/confirmar")

    sucursal = session.get("sucursal", SUCURSALES[0])
    actuales = {d: 0 for d in DENOM}

    return render_template("cambio_index.html",
                           sucursales=SUCURSALES,
                           fecha_actual=hoy,
                           objetivos=OBJETIVOS_DEFAULT,
                           fondo=get_caja(),
                           actuales=actuales)

@app.route("/cambio/confirmar", methods=["GET", "POST"])
def confirmar_cambio():
    if "ciclo" not in session:
        return redirect("/cambio")

    raw_data = session.get("ciclo")
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
    total_repuesto = raw_data.get("total_repuesto", sum(data["repuesto"][d] * d for d in DENOM))

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
            cur.execute("INSERT INTO ciclos (sucursal, fecha, datos) VALUES (?, ?, ?)",
                        (data["sucursal"], data["fecha"], str(data)))
        session.pop("ciclo")
        session.pop("ya_registrado")
        return redirect("/cambio")

    return render_template("cambio_confirmar.html",
                           data=data,
                           denom=DENOM,
                           total_objetivo=total_objetivo,
                           total_actual=total_actual,
                           total_repuesto=total_repuesto,
                           ya_registrado=ya_registrado)

@app.route("/caja-actual", methods=["GET", "POST"])
def caja_actual():
    if "acceso_caja" not in session:
        return redirect("/acceso-caja")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == "POST":
        for denom, cantidad in request.form.items():
            cur.execute("UPDATE caja SET cantidad = ? WHERE denom = ?", (cantidad, denom))
        conn.commit()
        registrar_log(session["usuario"], session["tipo"], "Modificó valores de 'Caja Actual'")

    cur.execute("SELECT denom, cantidad FROM caja ORDER BY CAST(denom AS INTEGER)")
    fondo = cur.fetchall()
    conn.close()

    return render_template("caja_actual.html", fondo=fondo)

@app.route("/acceso-caja", methods=["GET", "POST"])
def acceso_caja():
    if request.method == "POST":
        clave = request.form.get("clave", "")
        if clave == "262293":
            session["acceso_caja"] = True
            return redirect("/caja-actual")
        else:
            return render_template("acceso_caja.html", error="Contraseña incorrecta")
    return render_template("acceso_caja.html")

@app.route("/ciclo-calculo", methods=["POST"])
def ciclo_calculo():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/login")

    datos = []
    for den in [1, 2, 5, 10, 20, 50, 100]:
        objetivo = int(request.form.get(f"objetivo_{den}", 0))
        actual = int(request.form.get(f"actual_{den}", 0))
        repuesto = int(request.form.get(f"repuesto_{den}", 0))
        total = actual + repuesto
        diferencia = total - objetivo

        datos.append({
            "denominacion": den,
            "objetivo": objetivo,
            "actual": actual,
            "repuesto": repuesto,
            "total": total,
            "diferencia": diferencia
        })

    return render_template("cambio_confirmar.html", datos=datos)

@app.route("/guardar-ciclo", methods=["POST"])
def guardar_ciclo():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/login")

    json_datos = request.form["json_datos"]
    datos = ast.literal_eval(json_datos)

    sucursal = session.get("sucursal", "Desconocida")
    fecha = datetime.now(TZ).strftime("%d-%m-%Y")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO ciclos (sucursal, fecha, datos) VALUES (?, ?, ?)", (sucursal, fecha, json_datos))

        for d in datos:
            den = d["denominacion"]
            total = d["actual"] + d["repuesto"]
            diferencia = d["diferencia"]

            cur.execute("UPDATE fondo SET cantidad_actual = ?, cantidad_repuesta = ?, monto_dado = monto_dado + ?, monto_recibido = monto_recibido + ? WHERE denom = ?",
                        (total, d["repuesto"], abs(diferencia) if diferencia < 0 else 0, diferencia if diferencia > 0 else 0, den))

        conn.commit()

    return redirect("/panel-admin")

@app.route("/ver-ciclos")
def ver_ciclos():
    if "usuario" not in session:
        return redirect("/login")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, sucursal, fecha, datos FROM ciclos ORDER BY fecha DESC")
        rows = cur.fetchall()

    ciclos = []
    for row in rows:
        try:
            datos_raw = row["datos"]
            if isinstance(datos_raw, dict):
                datos = datos_raw
            elif datos_raw.strip().startswith("{'"):
                datos = ast.literal_eval(datos_raw)  # Maneja comillas simples
            else:
                datos = json.loads(datos_raw)  # Maneja JSON válido con comillas dobles
        except Exception as e:
            print(f"❌ Error al procesar ciclo ID {row['id']}: {e}")
            continue  # Saltar este ciclo si tiene formato inválido

        desglosado = []
        for denom in datos["objetivos"]:
            obj = datos["objetivos"][denom]
            act = datos["actuales"].get(denom, 0)
            rep = datos["repuesto"].get(denom, 0)
            dif = datos["diferencias"].get(denom, 0)
            total = int(act) * int(denom)
            desglosado.append({
                "denom": denom,
                "objetivo": obj,
                "actual": act,
                "repuesto": rep,
                "total": total,
                "diferencia": dif
            })

        ciclos.append({
            "id": row["id"],
            "sucursal": row["sucursal"],
            "fecha": row["fecha"],
            "total_dado": datos.get("dar", 0),
            "total_recibido": datos.get("recibir", 0),
            "desglosado": desglosado
        })

    return render_template("ver_ciclos.html", ciclos=ciclos)

@app.route("/ver-fondo")
def ver_fondo():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT denom, SUM(cantidad) as total FROM caja GROUP BY denom ORDER BY denom ASC")
    datos = cur.fetchall()
    conn.close()

    denominaciones_validas = [1, 2, 5, 10, 20, 50, 100]

    fondo = []
    total_fondo = 0
    for row in datos:
        denom = row["denom"]
        if denom not in denominaciones_validas:
            continue
        cantidad = row["total"] or 0
        valor = denom * cantidad
        total_fondo += valor
        fondo.append({"denominacion": denom, "cantidad": cantidad, "valor": valor})

    return render_template("ver_fondo.html", fondo=fondo, total_fondo=total_fondo)

@app.route("/modificar-ciclo/<int:ciclo_id>", methods=["GET", "POST"])
def modificar_ciclo(ciclo_id):
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/login")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT sucursal, fecha, datos FROM ciclos WHERE id = ?", (ciclo_id,))
        row = cur.fetchone()

        if not row:
            return "Ciclo no encontrado"

        sucursal, fecha, datos_str = row
        datos = eval(datos_str)

        if request.method == "POST":
            nuevos_datos = {}
            for den in DENOM:
                nuevos_datos[den] = {
                    "objetivo": int(request.form.get(f"objetivo_{den}", 0)),
                    "actual": int(request.form.get(f"actual_{den}", 0)),
                    "repuesto": int(request.form.get(f"repuesto_{den}", 0))
                }

            cur.execute("UPDATE ciclos SET datos = ? WHERE id = ?", (str(nuevos_datos), ciclo_id))
            conn.commit()
            return redirect("/ver-ciclos")

    return render_template("modificar_ciclo.html", ciclo_id=ciclo_id, sucursal=sucursal, fecha=fecha, datos=datos)

@app.route("/faltantes-json")
def faltantes_json():
    import pytz
    from datetime import datetime

    sucursales = ["Hidalgo", "Colinas", "Voluntad 1", "Reservas", "Villas"]
    TZ = pytz.timezone("America/Monterrey")
    hoy = datetime.now(TZ).strftime("%Y-%m-%d")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT sucursal FROM ciclos WHERE fecha = ?", (hoy,))
        registradas = [r[0] for r in cur.fetchall()]

    faltan = [s for s in sucursales if s not in registradas]
    return jsonify({
        "faltan": faltan,
        "todas_registradas": len(faltan) == 0
    })

@app.route("/feria", methods=["GET", "POST"])
def feria():
    if "usuario" not in session or session.get("tipo") not in ["admin", "consulta"]:
        return redirect("/")

    hoy = datetime.now(TZ).strftime("%d-%m-%Y")
    sucursal = session.get("sucursal", "Villas")

    if request.method == "POST":
        actuales = {int(k.split("_")[1]): int(v) for k, v in request.form.items() if k.startswith("actual_")}
        objetivos = OBJETIVOS_DEFAULT.copy()

        reponer = {}
        entregar = {}
        total_objetivo = total_actual = total_reponer = total_entregar = 0

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        for denom in DENOM:
            objetivo = objetivos.get(denom, 0)
            actual = actuales.get(denom, 0)
            valor_objetivo = objetivo * denom
            valor_actual = actual * denom

            total_objetivo += valor_objetivo
            total_actual += valor_actual

            if actual < objetivo:
                cantidad = objetivo - actual
                reponer[denom] = cantidad
                total_reponer += cantidad * denom

                sugerido = min(cantidad, objetivo)  # sugerido a reponer
                cur.execute("UPDATE fondo SET cantidad_actual = cantidad_actual - ? WHERE denominacion = ?", (sugerido, denom))
            elif actual > objetivo:
                cantidad = actual - objetivo
                entregar[denom] = cantidad
                total_entregar += cantidad * denom

                cur.execute("UPDATE fondo SET cantidad_actual = cantidad_actual + ? WHERE denominacion = ?", (cantidad, denom))

        conn.commit()
        conn.close()

        session["feria_datos"] = {
            "sucursal": sucursal,
            "fecha": hoy,
            "actuales": actuales,
            "reponer": reponer,
            "entregar": entregar,
            "total_objetivo": total_objetivo,
            "total_actual": total_actual,
            "total_reponer": total_reponer,
            "total_entregar": total_entregar
        }

        return redirect("/confirmar-feria")

    actuales = {d: 0 for d in DENOM}
    return render_template("feria.html",
                           objetivos=OBJETIVOS_DEFAULT,
                           actuales=actuales,
                           denom=DENOM,
                           sucursal=sucursal,
                           fecha=hoy)

@app.route("/confirmar-feria", methods=["GET", "POST"])
def confirmar_feria():
    if "usuario" not in session or session.get("tipo") not in ["admin", "consulta"]:
        return redirect("/")

    if request.method == "GET":
        return "No puedes acceder directamente a esta página.", 405

    sucursal = session.get("sucursal", "")
    fecha = datetime.now(TZ).strftime("%d-%m-%Y")

    denominaciones = [1, 2, 5, 10, 20, 50, 100]
    cantidades_objetivo = {1: 40, 2: 40, 5: 40, 10: 20, 20: 20, 50: 10, 100: 5}
    cantidades_actual = {}
    cantidades_reponer = {}
    diferencias = {}

    total_objetivo = 0
    total_actual = 0
    total_entregar = 0
    total_reponer = 0
    total_sobrante = 0

    for denom in denominaciones:
        actual = int(request.form.get(f"actual_{denom}", "0") or "0")
        reponer = int(request.form.get(f"reponer_{denom}", "0") or "0")
        objetivo = cantidades_objetivo[denom]
        diferencia = actual - objetivo
        valor_diferencia = diferencia * denom

        if diferencia > 0:
            total_sobrante += valor_diferencia

        cantidades_actual[denom] = actual
        cantidades_reponer[denom] = reponer
        diferencias[denom] = {
            "objetivo": objetivo,
            "actual": actual,
            "diferencia": diferencia,
            "valor_diferencia": valor_diferencia
        }

        total_objetivo += objetivo * denom
        total_actual += actual * denom
        total_entregar += reponer * denom
        
        if actual < objetivo:
            total_reponer += (objetivo - actual) * denom
        
    data = {
        "sucursal": sucursal,
        "fecha": fecha,
        "diferencias": diferencias,
        "repuesto": cantidades_reponer,
        "total_objetivo": total_objetivo,
        "total_actual": total_actual,
        "total_entregar": total_entregar,
        "total_reponer": total_reponer,
        "total_sobrante": total_sobrante
    }

    return render_template("confirmar-feria.html", data=data, denom=denominaciones)

@app.route("/guardar-feria", methods=["POST"])
def guardar_feria():
    if "usuario" not in session:
        return redirect("/login")

    sucursal = session.get("sucursal")
    tipo = session.get("tipo")
    fecha = datetime.now(TZ).strftime("%Y-%m-%d")

    if ya_envio_feria(sucursal, fecha):
        return "Ya se envió la feria hoy."

    objetivos = {1: 40, 2: 40, 5: 40, 10: 20, 20: 20, 50: 10, 100: 5}
    actuales = {}
    diferencias = {}
    repuesto = {}
    total_dar = total_recibir = 0

    for val in objetivos.keys():
        actual_str = request.form.get(f"actual_{val}", "").strip()
        try:
            actual = int(actual_str) if actual_str else 0
        except ValueError:
            actual = 0

        actuales[val] = actual
        dif = actual - objetivos[val]
        diferencias[val] = dif

        if dif < 0:
            rep = abs(dif)
            repuesto[val] = rep
            total_dar += val * rep
        else:
            repuesto[val] = 0
            total_recibir += val * dif

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        for val in objetivos:
            cur.execute("SELECT cantidad FROM caja WHERE denom = ?", (val,))
            row = cur.fetchone()
            actual_caja = row[0] if row else 0

            nuevo_valor = actual_caja
            if diferencias[val] < 0:
                nuevo_valor -= abs(diferencias[val])  # Se dio dinero, se resta
            elif diferencias[val] > 0:
                nuevo_valor += abs(diferencias[val])  # Sobró dinero, se suma

            cur.execute("UPDATE caja SET cantidad = ? WHERE denom = ?", (nuevo_valor, val))

        datos = {
            "sucursal": sucursal,
            "fecha": fecha,
            "actuales": actuales,
            "objetivos": objetivos,
            "diferencias": diferencias,
            "repuesto": repuesto,
            "dar": total_dar,
            "recibir": total_recibir
        }

        cur.execute("INSERT INTO ciclos (sucursal, fecha, datos) VALUES (?, ?, ?)", (sucursal, fecha, json.dumps(datos)))
        conn.commit()

    if tipo == "admin":
        return redirect("/panel-admin")
    else:
        return redirect("/panel-consulta")

@app.route("/eliminar-ciclo", methods=["POST"])
def eliminar_ciclo():
    if "usuario" not in session or session.get("tipo") != "admin":
        return redirect("/")

    ciclo_id = request.form.get("id")
    if not ciclo_id:
        return "ID no válido", 400

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM ciclos WHERE id = ?", (ciclo_id,))
        conn.commit()

    return redirect("/ver-ciclos")

@app.route("/nota", methods=["GET", "POST"])
def nota():
    if "usuario" not in session or session.get("tipo") != "consulta":
        return redirect("/")

    sucursal = session["sucursal"]
    fecha = request.args.get("fecha", datetime.now(TZ).strftime("%d-%m-%Y"))

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if request.method == "POST":
        texto = request.form["texto"]
        cur.execute("INSERT INTO notas (texto, fecha, sucursal) VALUES (?, ?, ?)", (texto, fecha, sucursal))
        conn.commit()
        registrar_log(session["usuario"], "consulta", f"Registró una nota: {texto}")
        return redirect("/nota")

    cur.execute("SELECT id, texto FROM notas WHERE fecha = ? AND sucursal = ?", (fecha, sucursal))
    notas = cur.fetchall()
    conn.close()

    return render_template("notas.html", notas=notas)

@app.route("/eliminar-nota", methods=["POST"])
def eliminar_nota():
    if "usuario" not in session or session.get("tipo") != "consulta":
        return redirect("/")

    nota_id = request.form["id"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM notas WHERE id = ?", (nota_id,))
    conn.commit()
    conn.close()

    registrar_log(session["usuario"], "consulta", f"Eliminó una nota con ID {nota_id}")
    return redirect("/nota")

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

@app.route("/ver-reporte-excel", methods=["GET", "POST"])
def ver_reporte_excel():
    if "usuario" not in session:
        return redirect("/")

    sucursal = request.args.get("sucursal", "")
    fecha = request.args.get("fecha", "")
    datos_ventas = []
    total_ventas = total_efectivo = total_tarjeta = total_dolar = total_mixto = 0.0
    total_gastos = total_anticipos = total_dolares = 0.0
    notas = []
    gastos = []

    if sucursal and fecha:
        # ✅ Manejar correctamente fechas en ambos formatos
        try:
            fecha_str = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            fecha_str = fecha  # Si ya viene en %d-%m-%Y lo dejamos igual

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            
            cur.execute("""
                SELECT tipo_pago, precio 
                FROM ventas 
                WHERE fecha LIKE ? AND sucursal = ? AND eliminado = 0
            """, (fecha_str, sucursal))
            datos_ventas = cur.fetchall()

            for v in datos_ventas:
                precio = float(v["precio"])
                total_ventas += precio
                tipo_pago = v["tipo_pago"].strip().lower()
                if tipo_pago == "efectivo":
                    total_efectivo += precio
                elif tipo_pago == "tarjeta":
                    total_tarjeta += precio
                elif tipo_pago in ("dólar", "dolar"):
                    total_dolar += precio
                elif tipo_pago == "mixto":
                    total_mixto += precio

            
            cur.execute("""
                SELECT motivo, monto, fecha 
                FROM gastos 
                WHERE fecha LIKE ? || '%' AND sucursal = ?
            """, (fecha_str, sucursal))
            gastos = cur.fetchall()
            total_gastos = sum(float(g["monto"]) for g in gastos)

            
            cur.execute("""
                SELECT monto 
                FROM anticipos 
                WHERE fecha LIKE ? || '%' AND sucursal = ?
            """, (fecha_str, sucursal))
            anticipos = cur.fetchall()
            total_anticipos = sum(float(a["monto"]) for a in anticipos)

            
            cur.execute("""
                SELECT texto 
                FROM notas 
                WHERE fecha LIKE ? || '%' AND sucursal = ?
            """, (fecha_str, sucursal))
            notas = [n["texto"] for n in cur.fetchall()]

    return render_template("ver_reporte_excel.html",
        sucursal=sucursal,
        fecha=fecha,
        total_ventas=total_ventas,
        total_efectivo=total_efectivo,
        total_tarjeta=total_tarjeta,
        total_dolar=total_dolar,
        total_mixto=total_mixto,
        total_gastos=total_gastos,
        total_anticipos=total_anticipos,
        total_dolares=total_dolar,
        gastos=gastos,
        notas=notas
    )

@app.route("/reporte-excel")
def reporte_excel():
    if "usuario" not in session:
        return redirect("/")

    tipo_usuario = session.get("tipo")
    sucursal = request.args.get("sucursal", session.get("sucursal", ""))
    fecha = request.args.get("fecha", fecha_hoy())  # puede venir como YYYY-MM-DD

    
    try:
        fecha = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
    except:
        pass  # ya está en formato correcto

    
    if tipo_usuario != "admin":
        sucursal = session.get("sucursal", "")
        fecha = fecha_hoy()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT descripcion, concepto, tipo, referencia, precio, pagado, cambio 
        FROM ventas 
        WHERE fecha LIKE ? AND sucursal = ? AND (eliminado IS NULL OR eliminado = 0)
    """, (f"{fecha}%", sucursal))
    ventas = cur.fetchall()

    cur.execute("SELECT motivo, monto FROM gastos WHERE fecha LIKE ? AND sucursal = ?", (f"{fecha}%", sucursal))
    gastos = cur.fetchall()

    cur.execute("SELECT monto FROM fondo_caja WHERE fecha LIKE ? AND sucursal = ? ORDER BY id DESC LIMIT 1", (f"{fecha}%", sucursal))
    fondo = cur.fetchone()

    cur.execute("SELECT tipo, cantidad, monto FROM dolares WHERE fecha LIKE ? AND sucursal = ?", (f"{fecha}%", sucursal))
    dolares = cur.fetchall()

    cur.execute("SELECT monto FROM anticipos WHERE fecha LIKE ? AND sucursal = ?", (f"{fecha}%", sucursal))
    anticipos = cur.fetchall()

    cur.execute("SELECT texto FROM notas WHERE fecha LIKE ? AND sucursal = ?", (f"{fecha}%", sucursal))
    notas_adicionales = cur.fetchall()

    conn.close()

    plantilla_path = "CORTE.xlsx"
    wb = load_workbook(plantilla_path)
    nueva_hoja = wb.copy_worksheet(wb.active)
    nueva_hoja.title = f"{sucursal}_{fecha}"
    ws = nueva_hoja

    fila = 2
    for venta in ventas:
        ws[f"A{fila}"] = fecha
        ws[f"B{fila}"] = venta[0]
        ws[f"C{fila}"] = venta[2]
        ws[f"D{fila}"] = venta[1]
        ws[f"E{fila}"] = venta[3]
        ws[f"F{fila}"] = ""
        ws[f"G{fila}"] = venta[4]
        fila += 1

    ws["K4"] = sucursal

    if fondo:
        ws["I5"] = fondo[0]

    fila_g = 8
    for g in gastos:
        ws[f"K{fila_g}"] = g[0]
        ws[f"M{fila_g}"] = g[1]
        fila_g += 1
    ws["M41"] = "=SUM(M8:M40)"

    fila_a = 7
    for a in anticipos:
        ws[f"W{fila_a}"] = a[0]
        fila_a += 1
    ws["W41"] = "=SUM(W7:W40)"

    fila_d = 7
    for d in dolares:
        ws[f"R{fila_d}"] = d[0]
        ws[f"S{fila_d}"] = d[1]
        ws[f"T{fila_d}"] = d[2]
        fila_d += 1
    ws["T41"] = "=SUM(T7:T40)"

    fila_nota = 7
    total_notas = 0
    for nota in notas_adicionales:
        texto = nota[0]
        ws[f"U{fila_nota}"] = texto
        match = re.search(r"\$\s?(\d+(?:\.\d{1,2})?)", texto)
        if match:
            try:
                total_notas += float(match.group(1))
            except:
                pass
        fila_nota += 1
    ws["X3"] = total_notas

    if "CORTE DIARIO" in wb.sheetnames:
        wb.remove(wb["CORTE DIARIO"])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name=f"corte_{sucursal}_{fecha}.xlsx", as_attachment=True)


@app.route("/corte-del-dia")
def corte_del_dia():
    if "usuario" not in session:
        return redirect("/")

    tipo = session["tipo"]

    if tipo == "admin":
        fecha = request.args.get("fecha", datetime.now(TZ).strftime("%Y-%m-%d"))
        try:
            fecha_str = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
        except:
            fecha_str = fecha
        sucursal = request.args.get("sucursal", session.get("sucursal", ""))
    else:
        fecha_str = datetime.now(TZ).strftime("%d-%m-%Y")
        sucursal = session.get("sucursal", "")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT SUM(precio) FROM ventas 
        WHERE fecha LIKE ? AND sucursal = ? AND tipo_pago = 'Efectivo'
    """, (f"{fecha_str}%", sucursal))
    ventas_efectivo = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT SUM(precio) FROM ventas 
        WHERE fecha LIKE ? AND sucursal = ? AND tipo_pago = 'Tarjeta'
    """, (f"{fecha_str}%", sucursal))
    ventas_tarjeta = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(monto) FROM gastos WHERE fecha = ? AND sucursal = ?", (fecha_str, sucursal))
    gastos = cur.fetchone()[0] or 0

    cur.execute("SELECT monto FROM fondo_caja WHERE fecha = ? AND sucursal = ? ORDER BY id DESC LIMIT 1", (fecha_str, sucursal))
    fondo = cur.fetchone()
    fondo_inicial = fondo[0] if fondo else 0

    total_caja = fondo_inicial + ventas_efectivo - gastos

    registrar_log(session["usuario"], tipo, f"Consultó corte del día ({sucursal} - {fecha_str})")

    return render_template("corte-del-dia.html",
        fecha=fecha_str,
        sucursal=sucursal,
        ventas_efectivo=ventas_efectivo,
        ventas_tarjeta=ventas_tarjeta,
        gastos=gastos,
        fondo_inicial=fondo_inicial,
        total_caja=total_caja,
        tipo=tipo,
        sucursales=SUCURSALES  # para el select de sucursales si es admin
    )

if not os.path.exists(DB_PATH):
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
