#!/usr/bin/env bash
# 在全新的 Ubuntu 24.04 VM 上準備 Lab 環境：
#   - 安裝 Docker Engine + compose plugin（官方 apt repo）
#   - 把目前使用者加入 docker 群組
#   - （可選）預先拉好 Lab 用到的 image
#
# 用法：
#   git clone https://github.com/Hikana/LSA-mon-o11y-class.git
#   cd LSA-mon-o11y-class
#   sudo ./scripts/setup-ubuntu.sh            # 只裝 Docker
#   sudo ./scripts/setup-ubuntu.sh --pull     # 裝 Docker 並預先 build/pull 所有模組
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "請用 sudo 執行：sudo $0 $*"; exit 1
fi

. /etc/os-release
if [ "${VERSION_ID:-}" != "24.04" ]; then
  echo "警告：這個腳本是為 Ubuntu 24.04 寫的，你的是 ${PRETTY_NAME:-unknown}，繼續執行。"
fi

echo "==> 安裝 Docker Engine"
apt-get update
apt-get install -y ca-certificates curl git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

TARGET_USER="${SUDO_USER:-}"
if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
  usermod -aG docker "$TARGET_USER"
  echo "==> 已把 $TARGET_USER 加入 docker 群組（重新登入後生效，或執行 newgrp docker）"
fi

if [ "${1:-}" = "--pull" ]; then
  echo "==> 預先 build / pull 所有模組的 image"
  cd "$(dirname "$0")/.."
  files="compose.yaml"
  for f in modules/*/compose.yaml; do files="$files:$f"; done
  COMPOSE_FILE="$files" docker compose build
  COMPOSE_FILE="$files" docker compose pull --ignore-buildable
fi

docker --version
docker compose version
echo "==> 完成！下一步：./lab.sh up 01"
