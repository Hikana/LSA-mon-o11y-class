# LSA-mon-o11y-class

教會資管學生什麼是 monitoring / o11y。

故事：選課系統每天 9:00 開放加選，系統變慢了，但「平均延遲」看起來還好。
這個 Lab 帶你從最原始的 log 開始，一步一步把訊號變成 metric、存進 Prometheus、
畫成 Grafana dashboard，最後用 SLO 告警，親眼看到 monitoring 是怎麼演變出來的，
也看到它的極限（知道「慢了」，但不知道「慢在哪」）。

## 快速開始（Ubuntu 24.04）

```bash
git clone https://github.com/Hikana/LSA-mon-o11y-class.git
cd LSA-mon-o11y-class
sudo ./scripts/setup-ubuntu.sh     # 安裝 Docker
newgrp docker
./lab.sh up 01                     # 從第一個模組開始
```

講師在 Proxmox 上準備 VM：見 [docs/pve-setup.md](docs/pve-setup.md)。

## 模組

每個模組是一個獨立的 `modules/NN-*/compose.yaml`。`./lab.sh up NN` 會把 01 到 NN
疊起來（寫進 `.env` 的 `COMPOSE_FILE`），所以隨時可以用 `./lab.sh status` 或
`docker compose config --services` 看到「我現在裝了哪些東西」。

| 模組 | 加入的東西 | 學到什麼 | Lab |
|---|---|---|---|
| 01-app | 加選系統 + 流量產生器 | 只有 log 的世界；平均會騙人 | [labs/01](labs/01-raw-signals.md) |
| 02-node-exporter | node_exporter | exporter、metric 格式、counter vs gauge、USE | [labs/02](labs/02-node-exporter.md) |
| 03-instrument | （覆寫 app 設定，打開 `/metrics`） | instrumentation、RED / Golden Signals、histogram | [labs/03](labs/03-instrument.md) |
| 04-prometheus | Prometheus | pull、時間序列、PromQL：`rate`、`histogram_quantile` | [labs/04](labs/04-prometheus.md) |
| 05-grafana | Grafana + 預建 dashboard | dashboard、provisioning | [labs/05](labs/05-grafana.md) |
| 06-alerting | Alertmanager + SLO 告警規則 | 告警、SLO、症狀 vs 原因 | [labs/06](labs/06-alerting.md) |

下半堂 Observability（Loki / Tempo / OpenTelemetry）之後可以用同樣方式加 07、08 模組。

## lab.sh 指令

```
./lab.sh up 03        開啟模組 01 到 03
./lab.sh status       目前開了哪些模組、哪些容器在跑
./lab.sh rush         模擬 9:00 開放加選的尖峰流量
./lab.sh logs [服務]   看 log（預設 app）
./lab.sh down         全部停掉（保留資料）
./lab.sh reset        全部停掉並刪掉資料
```

## 加選系統怎麼「變慢」的

`POST /enroll` = 查課程 → 檢查衝堂 → 寫入。「檢查衝堂」要跟只有 3 條連線的資料庫連線池借連線。
平常很快；9:00 一大群人同時按下加選，就開始排隊，延遲出現長尾，排超過 3 秒回 503。
CPU 不會滿，所以只看機器的 metrics 找不到原因。

建議 VM 規格：2 vCPU / 4 GB RAM / 20 GB 磁碟。
