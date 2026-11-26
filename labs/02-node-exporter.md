# Lab 02：機器的 metrics（node_exporter / USE）

> 對應講義：USE（Utilization、Saturation、Errors）、Exporter

## 這一步裝了什麼

```bash
./lab.sh up 02
./lab.sh status        # 多了 node-exporter
```

`modules/02-node-exporter/compose.yaml` 只有一個新服務。它把 Linux 的 `/proc`、`/sys`
翻譯成 Prometheus 看得懂的格式：這就是 **exporter**。

## 動手做

1. 直接看 metrics 長什麼樣子（純文字）：
   ```bash
   curl -s localhost:9100/metrics | grep -E '^node_(load1|memory_MemAvailable_bytes|cpu_seconds_total\{cpu="0")'
   ```
2. 讀懂一行 metric：`名稱{標籤} 值`
   ```
   node_cpu_seconds_total{cpu="0",mode="idle"} 12345.67
   ```
   - 名稱：`node_cpu_seconds_total`
   - 標籤（labels）：`cpu="0"`、`mode="idle"`
   - 值：開機到現在，CPU 0 閒置了幾秒
3. 隔 10 秒再抓一次，值變了多少？用兩次相減除以 10，算出 CPU 0 的閒置比例。

## 想一想

- `node_cpu_seconds_total` 只會一直變大，這種叫 **counter**；`node_memory_MemAvailable_bytes`
  會上上下下，這種叫 **gauge**。各舉一個生活中的例子。
- 這些數字能告訴你「加選很慢」嗎？為什麼不能？（提示：USE 看的是資源，不是使用者體驗）
