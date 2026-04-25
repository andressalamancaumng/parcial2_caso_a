#!/bin/bash
# Script de configuración sg-frontend
set -e

apt update && apt install -y nginx certbot python3-certbot-nginx nodejs npm

# Angular CLI
npm install -g @angular/cli

# Let's Encrypt — reemplazar con el dominio real
# certbot --nginx -d clinica-grupoN.lab.umng.edu.co

# Fail2ban
apt install -y fail2ban
systemctl enable fail2ban && systemctl start fail2ban

# UFW
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "sg-frontend configurado"
