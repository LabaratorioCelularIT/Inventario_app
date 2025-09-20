# Data migration script from SQLite to MongoDB
import sqlite3
import pymongo
import json
from datetime import datetime
from bson import ObjectId
import os
import sys

class DataMigrator:
    def __init__(self, sqlite_path, mongo_uri):
        self.sqlite_path = sqlite_path
        self.mongo_client = pymongo.MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client.inventario_new
        
    def connect_sqlite(self):
        """Connect to SQLite database"""
        if not os.path.exists(self.sqlite_path):
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")
        return sqlite3.connect(self.sqlite_path)
    
    def migrate_users(self):
        """Migrate users table"""
        print("🔄 Migrating users...")
        conn = self.connect_sqlite()
        cursor = conn.cursor()
        
        # Get users from SQLite
        cursor.execute("""
            SELECT nombre, tipo, contraseña, correo, telefono, 
                   aprobado, recibe_todos_pendientes, sucursal
            FROM usuarios
        """)
        
        users_data = []
        for row in cursor.fetchall():
            user_doc = {
                'nombre': row[0],
                'tipo': row[1],
                'contraseña': row[2],  # Will hash in API
                'correo': row[3],
                'telefono': row[4],
                'aprobado': bool(row[5]),
                'recibe_todos_pendientes': bool(row[6]),
                'sucursal': row[7],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'permissions': self._get_user_permissions(row[1])
            }
            users_data.append(user_doc)
        
        # Insert into MongoDB
        if users_data:
            result = self.mongo_db.users.insert_many(users_data)
            print(f"✅ Migrated {len(result.inserted_ids)} users")
        
        conn.close()
    
    def migrate_inventory(self):
        """Migrate inventory (articulos + tipos_producto)"""
        print("🔄 Migrating inventory...")
        conn = self.connect_sqlite()
        cursor = conn.cursor()
        
        # Get inventory with product types
        cursor.execute("""
            SELECT a.id, a.imei, a.marca, a.modelo, a.estado, a.sucursal,
                   a.fecha_registro, a.memoria, a.color, a.proveedor, a.precio,
                   a.factura_id, a.fecha_compra, a.imei2, a.estatus, a.imei1,
                   tp.nombre as tipo_producto, tp.stock_minimo
            FROM articulos a
            LEFT JOIN tipos_producto tp ON a.tipo_id = tp.id
        """)
        
        inventory_data = []
        for row in cursor.fetchall():
            # Create inventory document
            item_doc = {
                'legacy_id': row[0],
                'imei': row[1],
                'marca': row[2],
                'modelo': row[3],
                'estado': row[4],
                'sucursal': row[5],
                'fecha_registro': self._parse_date(row[6]),
                'memoria': row[7],
                'color': row[8],
                'proveedor': row[9],
                'precio': row[10],
                'factura_id': row[11],
                'fecha_compra': self._parse_date(row[12]),
                'imei2': row[13],
                'estatus': row[14] or 'Nuevo',
                'imei1': row[15],
                'tipo_producto': {
                    'nombre': row[16],
                    'stock_minimo': row[17] or 0
                } if row[16] else None,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'history': []
            }
            inventory_data.append(item_doc)
        
        # Insert into MongoDB
        if inventory_data:
            result = self.mongo_db.inventory.insert_many(inventory_data)
            print(f"✅ Migrated {len(result.inserted_ids)} inventory items")
        
        conn.close()
        
    def migrate_sales(self):
        """Migrate sales data"""
        print("🔄 Migrating sales...")
        conn = self.connect_sqlite()
        cursor = conn.cursor()
        
        # Get sales data
        cursor.execute("""
            SELECT id, descripcion, concepto, tipo, referencia, precio,
                   pagado, cambio, dolar, fecha, sucursal, eliminado,
                   efectivo, tarjeta, dolares, tipo_pago
            FROM ventas
            WHERE eliminado IS NULL OR eliminado = 0
        """)
        
        sales_data = []
        for row in cursor.fetchall():
            # Generate folio
            fecha_obj = self._parse_date(row[9])
            folio = f"V-{fecha_obj.strftime('%Y%m%d')}-{row[0]:06d}" if fecha_obj else f"V-{row[0]:06d}"
            
            sale_doc = {
                'legacy_id': row[0],
                'folio': folio,
                'items': [{
                    'descripcion': row[1],
                    'concepto': row[2],
                    'tipo': row[3],
                    'referencia': row[4],
                    'precio': row[5]
                }],
                'total': row[5],
                'payment': {
                    'total_pagado': row[6],
                    'cambio': row[7],
                    'efectivo': row[12] or 0,
                    'tarjeta': row[13] or 0,
                    'dolares': row[14] or 0,
                    'tipo_pago': row[15]
                },
                'fecha': fecha_obj,
                'sucursal': row[10],
                'created_at': datetime.utcnow(),
                'status': 'completed'
            }
            sales_data.append(sale_doc)
        
        # Insert into MongoDB
        if sales_data:
            result = self.mongo_db.sales.insert_many(sales_data)
            print(f"✅ Migrated {len(result.inserted_ids)} sales")
        
        conn.close()
    
    def migrate_transfers(self):
        """Migrate transfers"""
        print("🔄 Migrating transfers...")
        conn = self.connect_sqlite()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, t.articulo_id, t.sucursal_origen, t.sucursal_destino,
                   t.fecha, t.usuario, t.estatus, t.imei, t.id_lote,
                   a.marca, a.modelo
            FROM transferencias t
            LEFT JOIN articulos a ON t.articulo_id = a.id
        """)
        
        transfers_data = []
        for row in cursor.fetchall():
            transfer_doc = {
                'legacy_id': row[0],
                'articulo': {
                    'legacy_articulo_id': row[1],
                    'imei': row[7],
                    'marca': row[9],
                    'modelo': row[10]
                },
                'sucursal_origen': row[2],
                'sucursal_destino': row[3],
                'fecha': self._parse_date(row[4]),
                'usuario': row[5],
                'estatus': row[6] or 'pendiente-envío',
                'id_lote': row[8],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            transfers_data.append(transfer_doc)
        
        if transfers_data:
            result = self.mongo_db.transfers.insert_many(transfers_data)
            print(f"✅ Migrated {len(result.inserted_ids)} transfers")
        
        conn.close()
    
    def migrate_chat(self):
        """Migrate chat messages"""
        print("🔄 Migrating chat...")
        conn = self.connect_sqlite()
        cursor = conn.cursor()
        
        # Check if chat table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat'")
        if not cursor.fetchone():
            print("⚠️ Chat table not found, skipping...")
            conn.close()
            return
        
        cursor.execute("""
            SELECT fecha, remitente, destinatario, mensaje, modulo, leido, archivo
            FROM chat
        """)
        
        messages_data = []
        for row in cursor.fetchall():
            message_doc = {
                'fecha': self._parse_date_string(row[0]),
                'remitente': row[1],
                'destinatario': row[2],
                'mensaje': row[3],
                'modulo': row[4],
                'leido': bool(row[5]),
                'archivo': row[6],
                'created_at': datetime.utcnow()
            }
            messages_data.append(message_doc)
        
        if messages_data:
            result = self.mongo_db.chat.insert_many(messages_data)
            print(f"✅ Migrated {len(result.inserted_ids)} chat messages")
        
        conn.close()
    
    def _get_user_permissions(self, user_type):
        """Get permissions based on user type"""
        permissions_map = {
            'admin': ['inventory', 'sales', 'reports', 'users', 'transfers', 'cash'],
            'consulta': ['inventory', 'sales', 'reports', 'transfers'],
            'reparto': ['transfers']
        }
        return permissions_map.get(user_type, [])
    
    def _parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%d-%m-%Y %H:%M:%S',
                '%Y-%m-%d',
                '%d-%m-%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def _parse_date_string(self, date_str):
        """Parse date string specifically for chat messages"""
        if not date_str:
            return datetime.utcnow()
        
        try:
            return datetime.strptime(date_str, '%d-%m-%Y %H:%M:%S')
        except ValueError:
            return datetime.utcnow()
    
    def run_migration(self):
        """Run complete migration"""
        print("🚀 Starting data migration from SQLite to MongoDB...")
        print(f"Source: {self.sqlite_path}")
        print(f"Target: {self.mongo_client.address}")
        
        try:
            # Create indexes
            self.create_indexes()
            
            # Run migrations
            self.migrate_users()
            self.migrate_inventory()
            self.migrate_sales()
            self.migrate_transfers()
            self.migrate_chat()
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {str(e)}")
            raise
        
        finally:
            self.mongo_client.close()
    
    def create_indexes(self):
        """Create indexes for better performance"""
        print("📊 Creating database indexes...")
        
        # Users indexes
        self.mongo_db.users.create_index("nombre", unique=True)
        self.mongo_db.users.create_index("correo")
        
        # Inventory indexes
        self.mongo_db.inventory.create_index("imei", unique=True)
        self.mongo_db.inventory.create_index("sucursal")
        self.mongo_db.inventory.create_index("estado")
        self.mongo_db.inventory.create_index([("marca", 1), ("modelo", 1)])
        
        # Sales indexes
        self.mongo_db.sales.create_index("folio", unique=True)
        self.mongo_db.sales.create_index("fecha")
        self.mongo_db.sales.create_index("sucursal")
        self.mongo_db.sales.create_index([("fecha", -1), ("sucursal", 1)])
        
        # Transfers indexes
        self.mongo_db.transfers.create_index("sucursal_origen")
        self.mongo_db.transfers.create_index("sucursal_destino")
        self.mongo_db.transfers.create_index("estatus")
        
        print("✅ Indexes created")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python migrate_data.py <sqlite_path> <mongo_uri>")
        print("Example: python migrate_data.py /shared/databases/inventario.sqlite3 mongodb://localhost:27017/inventario_new")
        sys.exit(1)
    
    sqlite_path = sys.argv[1]
    mongo_uri = sys.argv[2]
    
    migrator = DataMigrator(sqlite_path, mongo_uri)
    migrator.run_migration()