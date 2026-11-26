# Lab 03：讓程式自己說話（instrumentation / RED）

> 對應講義：Golden Signals、RED、`http_requests_total{page="加選", status="成功"}`

## 這一步裝了什麼

```bash
./lab.sh up 03
./lab.sh status        # 服務沒有變多！
docker compose config app | grep METRICS
```

`modules/03-instrument/compose.yaml` 沒有新服務，它**覆寫** app 的設定，把
`METRICS_ENABLED` 打開。真實世界裡，這一步就是改程式碼、加上 Prometheus client library。
打開 `modules/01-app/app/main.py`，找 `if METRICS_ENABLED:` 那一段。

## 動手做

1. 看看 app 吐出的 metrics：
   ```bash
   curl -s localhost:8000/metrics | grep -E '^(http_|app_)'
   ```
   找到講義上那一行：`http_requests_total{page="加選",status="成功"} ...`
2. 對照 Golden Signals：

   | Golden Signal | metric | 類型 |
   |---|---|---|
   | Traffic | `http_requests_total` | counter |
   | Errors | `http_requests_total{status="失敗"}` | counter |
   | Latency | `http_request_duration_seconds` | histogram |
   | Saturation | `app_inflight_requests` | gauge |

3. 看 histogram 的 bucket：
   ```bash
   curl -s localhost:8000/metrics | grep 'duration_seconds_bucket{le=.*page="加選"'
   ```
   `le="0.25"` 的意思是「≤ 0.25 秒的請求有幾個」。

## 想一想

- 為什麼延遲要用 histogram，不直接存「平均延遲」一個數字就好？
- 為什麼 `page` 標籤只用固定的「首頁／查課／加選」，而不是把學號或課號放進標籤？
  （提示：每個不同的 label 組合都是一條新的時間序列）
- 現在 metrics 只是「此刻」的數字。要看「9:00 那時候」的數字，還缺什麼？
