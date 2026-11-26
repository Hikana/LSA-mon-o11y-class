#!/usr/bin/env bash
# 加選系統 o11y Lab 小幫手
#
#   ./lab.sh up 03        開啟模組 01 到 03（會寫進 .env 的 COMPOSE_FILE）
#   ./lab.sh status       目前開了哪些模組、哪些容器在跑
#   ./lab.sh rush [rate] [spike] [秒]  模擬 9:00 開放加選（預設每秒 12 個 + 每 20 秒 80 人同時湧入，跑 120 秒）
#   ./lab.sh logs [服務]   看 log（預設 app）
#   ./lab.sh down         全部停掉（保留資料）
#   ./lab.sh reset        全部停掉並刪掉 Prometheus / Grafana 資料
set -euo pipefail
cd "$(dirname "$0")"

modules() { ls -d modules/[0-9][0-9]-*/ | sed 's#/$##'; }

write_env() {
  local upto=$1 files="compose.yaml"
  for m in $(modules); do
    n=$(basename "$m" | cut -d- -f1)
    if [ "$((10#$n))" -le "$((10#$upto))" ]; then
      files="$files:$m/compose.yaml"
    fi
  done
  printf '# 由 ./lab.sh 產生：目前疊上去的模組\nCOMPOSE_FILE=%s\n' "$files" > .env
}

current() {
  [ -f .env ] && grep '^COMPOSE_FILE=' .env | cut -d= -f2 | tr ':' '\n' | grep '^modules' | xargs -r -n1 dirname
}

case "${1:-help}" in
  up)
    upto=${2:?用法：./lab.sh up 03}
    write_env "$upto"
    echo "已開啟的模組："; current | sed 's/^/  /'
    docker compose up -d --build --remove-orphans
    ;;
  status)
    echo "已開啟的模組："; current | sed 's/^/  /' || echo "  (還沒開，請先 ./lab.sh up 01)"
    echo; echo "compose 看到的服務："; docker compose config --services | sed 's/^/  /'
    echo; docker compose ps
    ;;
  rush)
    rate=${2:-12}; spike=${3:-80}; dur=${4:-120}
    echo "9:00 開放加選！每秒 $rate 個請求，每 20 秒 $spike 人同時按下加選，持續 $dur 秒 ..."
    docker compose run --rm --no-deps loadgen \
      python loadgen.py --rate "$rate" --spike "$spike" --duration "$dur"
    ;;
  logs)
    docker compose logs -f --tail 50 "${2:-app}"
    ;;
  down)
    docker compose down --remove-orphans
    ;;
  reset)
    docker compose down --remove-orphans -v
    rm -f .env
    ;;
  *)
    sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
    ;;
esac
