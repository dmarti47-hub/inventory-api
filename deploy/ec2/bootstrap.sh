#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-ubuntu}"
APP_DIR="${APP_DIR:-/opt/inventory-api}"
REPOSITORY_URL="${REPOSITORY_URL:-https://github.com/dmarti47-hub/inventory-api.git}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  ca-certificates \
  docker.io \
  docker-compose-v2 \
  git \
  openssl

systemctl enable --now docker
usermod -aG docker "${APP_USER}"

if ! swapon --show=NAME --noheadings | grep -qx '/swapfile'; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

if [[ ! -d "${APP_DIR}/.git" ]]; then
  install -d -o "${APP_USER}" -g "${APP_USER}" "${APP_DIR}"
  sudo -u "${APP_USER}" git clone "${REPOSITORY_URL}" "${APP_DIR}"
fi

echo
echo "EC2 host bootstrap complete."
echo "Sign out and reconnect so the Docker group membership takes effect."
echo "Then create ${APP_DIR}/.env.production and run deploy/ec2/deploy.sh."
