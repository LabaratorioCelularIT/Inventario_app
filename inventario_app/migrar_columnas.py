import sqlite3

DB_PATH = "inventario.sqlite3"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Verificar si la columna ya existe antes de intentar agregarla
try:
    cur.execute("ALTER TABLE tipos_producto ADD COLUMN stock_minimo INTEGER DEFAULT 0")
    print("✅ Columna 'stock_minimo' agregada correctamente.")
except sqlite3.OperationalError as e:
    print("⚠️ Ya existe la columna o hay otro error:", e)

conn.commit()
conn.close()
