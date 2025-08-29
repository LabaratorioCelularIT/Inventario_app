#!/bin/bash
set -euo pipefail

BACKUP="inventario.sqlite3.bak-2025-08-28-1943"
TARGET="inventario.sqlite3"

echo "Backup: $BACKUP"
echo "Target: $TARGET"

# lista de tablas de usuario presentes en BACKUP (evita sqlite_*):
mapfile -t TABLES < <(sqlite3 "$BACKUP" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")

# función para obtener columnas por tabla en una DB
get_cols(){ sqlite3 "$1" "PRAGMA table_info('$2');" | awk -F'|' '{print $2}'; }

# intersección de columnas (orden = TARGET)
common_cols_csv(){
  local T="$1"
  mapfile -t tgt < <(get_cols "$TARGET" "$T" || true)
  mapfile -t bak < <(get_cols "$BACKUP" "$T" || true)
  [[ ${#tgt[@]} -eq 0 || ${#bak[@]} -eq 0 ]] && { echo ""; return; }
  local bakset="|"; for c in "${bak[@]}"; do bakset+="${c}|"; done
  local out=""
  for c in "${tgt[@]}"; do [[ "$bakset" == *"|${c}|"* ]] && out+="${out:+,}\"${c}\""; done
  echo "$out"
}

# snapshot por si acaso
cp -a "$TARGET" "${TARGET}.premerge.$(date +%F-%H%M)"

for T in "${TABLES[@]}"; do
  # salta si la tabla no existe en TARGET
  sqlite3 "$TARGET" "SELECT 1 FROM sqlite_master WHERE type='table' AND name='$T';" | grep -q 1 || { echo "[SKIP] $T no existe en TARGET"; continue; }
  cols=$(common_cols_csv "$T")
  if [[ -z "$cols" ]]; then
    echo "[SKIP] $T sin columnas comunes (schemas incompatibles)"; continue
  fi
  echo "Fusionando $T con columnas: $cols"
  sqlite3 "$TARGET" "
    PRAGMA foreign_keys=OFF;
    ATTACH '$BACKUP' AS b;
    BEGIN;
    INSERT OR IGNORE INTO \"$T\" ($cols)
    SELECT $cols FROM b.\"$T\";
    COMMIT;
    DETACH b;
  "
done

echo "Reindexando y validando..."
sqlite3 "$TARGET" "REINDEX; ANALYZE; PRAGMA integrity_check;"
