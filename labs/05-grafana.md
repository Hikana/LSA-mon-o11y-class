# Lab 05：畫成 dashboard（Grafana）

> 對應講義：Prometheus 收集 + Grafana 呈現

## 這一步裝了什麼

```bash
./lab.sh up 05
./lab.sh status
```

打開 `http://<VM-IP>:3000`（不登入即可瀏覽；要編輯用 admin / admin）。
首頁就是 **加選系統 Golden Signals** dashboard。它是用檔案自動建立的（provisioning）：
- `modules/05-grafana/provisioning/datasources/prometheus.yml`：資料來源
- `modules/05-grafana/dashboards/golden-signals.json`：dashboard 本身

## 動手做

1. 先看平常的樣子，記下四格的數字。
2. 跑 `./lab.sh rush`，看四個 Golden Signals 怎麼變化。
3. 點任一格的標題 → Edit，看看它背後的 PromQL，是不是就是 Lab 04 你打的那些？
4. 自己加一格：「查課」頁的 p99 延遲。

## 想一想

- 四格裡面，哪一格最能代表「同學的感受」？哪一格最早出現異常？
- 你會一直盯著 dashboard 嗎？誰來告訴你「現在該看了」？
