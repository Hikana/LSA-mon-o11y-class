# Lab 04：把數字存成時間序列（Prometheus / PromQL）

> 對應講義：Prometheus、pull vs push

## 這一步裝了什麼

```bash
./lab.sh up 04
./lab.sh status
cat modules/04-prometheus/prometheus.yml
```

Prometheus 每 5 秒主動去 `node-exporter:9100` 和 `app:8000` 拿 `/metrics`（**pull**），
存成時間序列。打開 `http://<VM-IP>:9090` → Status → Targets，三個都要是 UP。

## 動手做（在 Prometheus 網頁的 Query 輸入）

1. 原始 counter：`http_requests_total` → 切到 Graph，一直往上爬，看不出什麼
2. 變成「每秒幾個」：`sum by (page) (rate(http_requests_total[1m]))`
3. 失敗比例：
   ```
   sum(rate(http_requests_total{status="失敗"}[1m])) / sum(rate(http_requests_total[1m]))
   ```
4. 現在另開終端機跑 `./lab.sh rush`，然後比較這兩條：
   ```
   # 平均延遲
   sum(rate(http_request_duration_seconds_sum{page="加選"}[1m]))
     / sum(rate(http_request_duration_seconds_count{page="加選"}[1m]))

   # p99 延遲
   histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{page="加選"}[1m])))
   ```
5. CPU 使用率：`100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m])))`

## 想一想

- rush 的時候，平均和 p99 差幾倍？跟 Lab 01 你用 awk 算的結果一樣嗎？
- rush 的時候 CPU 有滿嗎？如果 CPU 沒滿，那請求在等什麼？
  （這就是 monitoring 的極限：它告訴你「慢了」，但不告訴你「慢在哪」→ 下半堂 observability）
- 試試更狠的 9:00：`./lab.sh rush 20 150`，失敗比例出現了嗎？
