#!/bin/bash
set -e
apt update && apt install -y postgresql-15

# Configurar PostgreSQL — sin acceso externo
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '10.0.0.12'/" \
  /etc/postgresql/15/main/postgresql.conf

# UFW — solo desde sg-backend
ufw allow from 10.0.0.11 to any port 5432
ufw allow 22/tcp
ufw --force enable

systemctl restart postgresql
echo "sg-db configurado"
