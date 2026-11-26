# Lab 01：只有 log 的世界（原始訊號）

> 對應講義：開場故事「9:00 加選變慢」、Golden Signals 之前

## 這一步裝了什麼

```bash
./lab.sh up 01
./lab.sh status
```

你會看到兩個服務：
- `app`：加選系統（查課 → 檢查衝堂 → 寫入）
- `loadgen`：模擬同學每秒 3 個請求在用系統

打開 `modules/01-app/compose.yaml` 看看，注意 `METRICS_ENABLED: "false"`。

## 動手做

1. 瀏覽器打開 `http://<VM-IP>:8000`，再試試：
   ```bash
   curl -X POST "http://localhost:8000/enroll?course=IM1001"
   curl http://localhost:8000/metrics      # 現在還沒有 metrics
   ```
2. 看原始訊號：每個請求一行 log
   ```bash
   docker compose logs --no-log-prefix --tail 5 app
   # 2026-11-26T09:28:46 POST /enroll 200 0.156
   #   時間              方法  路徑    狀態碼 秒數
   ```
3. 模擬 9:00 開放加選（另開一個終端機）：
   ```bash
   ./lab.sh rush
   ```
4. 跑完之後，用 awk 自己算「加選」的平均延遲、中位數、最慢的 1%：
   ```bash
   docker compose logs --no-log-prefix --since 3m app \
     | awk '$3=="/enroll"{print $5}' | sort -n \
     | awk '{a[NR]=$1; s+=$1} END{printf "筆數=%d 平均=%.3f p50=%.3f p99=%.3f 最慢=%.3f\n", NR, s/NR, a[int(NR*.5)], a[int(NR*.99)], a[NR]}'
   ```

## 想一想

- 平均是多少？p99 是多少？如果老闆只看「平均」，他會覺得系統有問題嗎？
- 現在是「事後」才算出來的。如果你想**每 5 秒**知道一次、還想看過去一週的趨勢，用 log 這樣算會遇到什麼問題？（log 量、計算成本、保存多久）
- 你能從 log 看出 VM 的 CPU、記憶體快滿了嗎？

👉 這就是為什麼我們要把 signal 變成 **metric**：事先決定好要看的數字，持續、便宜地收集。
