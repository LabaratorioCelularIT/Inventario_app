import sqlite3

DB_PATH = "inventario.sqlite3"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Crear tabla tipos_producto
cursor.execute("""
CREATE TABLE IF NOT EXISTS tipos_producto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    stock_minimo INTEGER DEFAULT 0
)
""")

# Crear tabla articulos
cursor.execute("""
CREATE TABLE IF NOT EXISTS articulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_id INTEGER,
    marca TEXT,
    modelo TEXT,
    imei TEXT UNIQUE,
    estado TEXT,
    sucursal TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Crear tabla log_actividad
cursor.execute("""
CREATE TABLE IF NOT EXISTS log_actividad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    tipo TEXT,
    descripcion TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Crear tabla transferencias
cursor.execute("""
CREATE TABLE IF NOT EXISTS transferencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articulo_id INTEGER,
    sucursal_origen TEXT,
    sucursal_destino TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario TEXT
)
""")

conn.commit()
conn.close()

print("✅ Base de datos creada y verificada con éxito.")
