#!/bin/bash

# Variables
VNC_PASS="votre_mot_de_passe"  # À personnaliser !
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/x11vnc.desktop"

# 1. Installer x11vnc si absent
if ! command -v x11vnc >/dev/null 2>&1; then
    echo "Installation de x11vnc..."
    sudo apt update
    sudo apt install -y x11vnc
fi

# 2. Créer le dossier .vnc si besoin
mkdir -p "$HOME/.vnc"

# 3. Enregistrer le mot de passe VNC
echo "$VNC_PASS" | x11vnc -storepasswd - "$HOME/.vnc/passwd"

# 4. Créer le dossier d'autostart KDE si besoin
mkdir -p "$AUTOSTART_DIR"

# 5. Créer le fichier .desktop pour lancement auto au login
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Exec=x11vnc -rfbauth $HOME/.vnc/passwd -forever -shared -display :0
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Serveur VNC (x11vnc)
Comment=Permet l'accès distant à la session graphique via VNC
EOF

echo "Installation et configuration terminées !"
echo "Le serveur VNC se lancera automatiquement à chaque ouverture de session."
echo "Adresse IP de ce poste :"
hostname -I | awk '{print $1}'
