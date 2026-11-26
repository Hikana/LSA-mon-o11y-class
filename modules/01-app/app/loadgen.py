"""流量產生器：模擬學生在加選系統上的行為。

  python loadgen.py --rate 3                  # 平常：每秒 3 個請求，一直跑
  python loadgen.py --rate 20 --spike 150 --duration 120
                                              # 9:00 開放加選：每秒 20 個，
                                              # 外加每 20 秒一波「150 人同時按下加選」

每個請求：80% 加選、20% 查課。不等回應就發下一個（開放式負載），
所以系統一慢，同時在處理的請求就會越堆越多。
"""

import argparse
import asyncio
import random
import time

import httpx

COURSES = ["IM1001", "IM2002", "IM3003", "IM4004"]


async def one_request(client: httpx.AsyncClient, stats: dict) -> None:
    try:
        if random.random() < 0.8:
            r = await client.post("/enroll", params={"course": random.choice(COURSES)})
        else:
            r = await client.get("/courses")
        stats[r.status_code] = stats.get(r.status_code, 0) + 1
    except httpx.HTTPError:
        stats["conn_err"] = stats.get("conn_err", 0) + 1


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target", default="http://app:8000")
    p.add_argument("--rate", type=float, default=3, help="每秒請求數")
    p.add_argument("--duration", type=float, default=0, help="秒；0 = 一直跑")
    p.add_argument("--spike", type=int, default=0, help="每波同時湧入的加選請求數；0 = 不要")
    p.add_argument("--spike-every", type=float, default=20, help="每幾秒一波")
    args = p.parse_args()

    stats: dict = {}
    tasks: set = set()
    start = time.monotonic()
    last_report = start
    next_spike = start
    limits = httpx.Limits(max_connections=500, max_keepalive_connections=100)
    async with httpx.AsyncClient(base_url=args.target, timeout=10, limits=limits) as client:
        print(f"loadgen: {args.rate} req/s -> {args.target}", flush=True)
        while args.duration == 0 or time.monotonic() - start < args.duration:
            if args.spike and time.monotonic() >= next_spike:
                # 時間一到，大家同時按下「加選」
                for _ in range(args.spike):
                    t = asyncio.create_task(one_request(client, stats))
                    tasks.add(t)
                    t.add_done_callback(tasks.discard)
                next_spike += args.spike_every
            t = asyncio.create_task(one_request(client, stats))
            tasks.add(t)
            t.add_done_callback(tasks.discard)
            # 用指數分佈的間隔，比固定間隔更像真人
            await asyncio.sleep(random.expovariate(args.rate))
            if time.monotonic() - last_report >= 10:
                print(f"loadgen: {dict(sorted(stats.items(), key=str))}", flush=True)
                last_report = time.monotonic()
        await asyncio.gather(*tasks, return_exceptions=True)
    print(f"loadgen done: {stats}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
