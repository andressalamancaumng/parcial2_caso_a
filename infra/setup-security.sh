#!/bin/bash
set -e
apt update && apt install -y docker.io docker-compose wireguard

# SonarQube con Docker
docker run -d --name sonarqube \
  -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
  sonarqube:community

# OWASP ZAP con Docker
docker pull ghcr.io/zaproxy/zaproxy:stable

# UFW — SonarQube solo via VPN (WireGuard en 10.6.0.0/24)
ufw allow from 10.6.0.0/24 to any port 9000
ufw allow 51820/udp  # WireGuard
ufw allow 22/tcp
ufw --force enable

echo "sg-security configurado"
