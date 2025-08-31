# 2. cámbiate al usuario que tiene docker
su - mauricio

# 3. ve a la carpeta de la app
cd ~/apps/app

# 4. trae los cambios de git
git pull origin main   # o la rama que uses

# 5. reconstruye e inicia los contenedores con el nuevo código
docker compose build --no-cache
docker compose down
docker compose up -d

# 6. confirma que todo funciona
docker compose logs -f inventari

pkill cloudflared || true
cloudflared tunnel run apps