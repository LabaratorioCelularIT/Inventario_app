import sqlite3

DB_PATH = "inventario.sqlite3"  # asegúrate que esté bien la ruta

sucursales = ["Colinas", "Hidalgo", "Voluntad 1", "Reservas", "Villas"]
denoms = [1, 2, 5, 10, 20, 50, 100]
objetivos = {1: 40, 2: 40, 5: 40, 10: 20, 20: 20, 50: 10, 100: 5}

with sqlite3.connect(DB_PATH) as con:
    cur = con.cursor()
    for suc in sucursales:
        for d in denoms:
            cur.execute("""
                INSERT INTO fondo (sucursal, denominacion, cantidad_objetivo, cantidad_actual, cantidad_repuesta)
                VALUES (?, ?, ?, 0, 0)
            """, (suc, d, objetivos.get(d, 0)))
    con.commit()

print("✅ Registros insertados correctamente.")
