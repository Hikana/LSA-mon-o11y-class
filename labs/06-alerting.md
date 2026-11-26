# Lab 06：出事了要有人通知（Alerting / SLO）

> 對應講義：Alerting 與 SLO

## 這一步裝了什麼

```bash
./lab.sh up 06
./lab.sh status        # 多了 alertmanager、alert-receiver
```

- `modules/06-alerting/rules.yml`：告警規則，寫的就是我們的 SLO
  - 99% 的加選要在 1 秒內完成
  - 加選失敗率低於 5%
  - 服務抓不到 metrics
- `modules/06-alerting/alertmanager.yml`：告警要送到哪裡（這裡送到一個只會印出來的小服務，
  代替 Email / Slack / Discord）

## 動手做

1. 在 Prometheus 網頁 → Alerts，看三條規則都是 Inactive。
2. 開兩個終端機：
   ```bash
   ./lab.sh logs alert-receiver
   ```
   ```bash
   ./lab.sh rush
   ```
3. 觀察告警狀態：Inactive → Pending（條件成立但還沒滿 30 秒）→ Firing，
   然後 alert-receiver 印出 `[FIRING] 加選太慢 ...`。rush 結束後會收到 `[RESOLVED]`。
4. 打開 `http://<VM-IP>:9093` 看 Alertmanager。
5. 把 app 停掉，看「服務抓不到」：
   ```bash
   docker compose stop app      # 記得之後 docker compose start app
   ```

## 想一想

- 規則裡的 `for: 30s` 拿掉會怎樣？設成 10 分鐘又會怎樣？
- 為什麼告警寫「p99 > 1 秒」，而不是「CPU > 80%」？（症狀 vs 原因）
- 告警響了，你知道是加選的哪一步慢嗎？→ 這就是下半堂 Observability 要回答的問題。
