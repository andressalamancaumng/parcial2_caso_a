#!/bin/bash
set -e
apt update && apt install -y python3.11 python3.11-venv python3-pip

# Usuario sin privilegios para correr la app
useradd -m -s /bin/bash clinica_app

cd /home/clinica_app
python3.11 -m venv venv
source venv/bin/activate
pip install -r /opt/clinica/backend/requirements.txt

# UFW — solo permite tráfico desde sg-frontend (10.0.0.10)
ufw allow from 10.0.0.10 to any port 8000
ufw allow 22/tcp
ufw --force enable

echo "sg-backend configurado"
