# Inventario App - Quick Start Guide

## One-time Setup Commands

### Linux (VPS/Ubuntu/Debian)
```bash
# Install dos2unix
sudo apt update && sudo apt install dos2unix

# Fix and run
cd /path/to/your/Inventario_app
dos2unix dev-launcher.sh
chmod +x dev-launcher.sh
./dev-launcher.sh
```

### Linux (CentOS/RHEL/Amazon Linux)
```bash
# Install dos2unix
sudo yum install dos2unix
# OR: sudo dnf install dos2unix

# Fix and run
cd /path/to/your/Inventario_app
dos2unix dev-launcher.sh
chmod +x dev-launcher.sh
./dev-launcher.sh
```

### macOS
```bash
# Install dos2unix
brew install dos2unix

# Fix and run
cd /path/to/your/Inventario_app
dos2unix dev-launcher.sh
chmod +x dev-launcher.sh
./dev-launcher.sh
```

### Windows - Git Bash (Recommended)
```bash
# Install dos2unix (if not included with Git Bash)
# Download from: https://sourceforge.net/projects/dos2unix/

# Fix and run
cd /c/Users/Mau/Documents/Repos/laboratorioCelular/Inventario_app
dos2unix dev-launcher.sh
chmod +x dev-launcher.sh
./dev-launcher.sh
```

### Windows - WSL
```bash
# Install dos2unix in WSL
sudo apt update && sudo apt install dos2unix

# Fix and run
cd /mnt/c/Users/Mau/Documents/Repos/laboratorioCelular/Inventario_app
dos2unix dev-launcher.sh
chmod +x dev-launcher.sh
./dev-launcher.sh
```

### Windows - PowerShell/CMD
```powershell
# Install dos2unix via Chocolatey
choco install dos2unix

# OR via Scoop
scoop install dos2unix

# Fix and run
cd C:\Users\Mau\Documents\Repos\laboratorioCelular\Inventario_app
dos2unix dev-launcher.sh
bash dev-launcher.sh
```

## Daily Usage (After One-time Setup)

### Linux & macOS
```bash
cd /path/to/your/Inventario_app
./dev-launcher.sh
```

### Windows (Git Bash/WSL)
```bash
cd /path/to/your/project
./dev-launcher.sh
```

### Windows (PowerShell/CMD)
```powershell
cd C:\path\to\your\project
bash dev-launcher.sh
```

## Cross-Platform Alternative (No dos2unix needed)

Use the enhanced cross-platform version that handles line endings automatically:

```bash
# Any OS - after making it executable once
./dev-launcher-cross-platform.sh

# Or if not executable
bash dev-launcher-cross-platform.sh
```

## Troubleshooting

### "Permission denied" error:
```bash
chmod +x dev-launcher.sh
```

### "command not found" error:
```bash
dos2unix dev-launcher.sh
```

### "No such file" error:
```bash
# Check you're in the right directory
ls -la dev-launcher.sh
pwd
```

### Docker not found:
- Make sure Docker is installed and running
- On Windows: Start Docker Desktop
- On Linux: `sudo systemctl start docker`
- On macOS: Start Docker Desktop app