#!/usr/bin/env python3
import time
import json
import urllib.request
import urllib.error
import sys

API_KEY = "FhCo3G2ppuBti5BQAZ2b7fo6ZUfMvrya"
BASE_URL = "https://api.dune.com/api/v1"

EXECUTIONS = {
    "q1":         "01KT4DDDS79A243CJ0KSVKT6V1",
    "q2":         "01KT4DDER4BN8WHBVJVAQSQZQS",
    "q2b":        "01KT4DDG76R46240NVHCC19S3R",
    "q3":         "01KT4DD1NJ6V3SPW70WB4VK91K",
    "q4":         "01KT4DDH6BC53S6YC6DGM7MV3F",
    "q5":         "01KT4DDJ5088NNKBCRHE60SEJD",
    "q5a":        "01KT4CV2KRDF6NDC0H919V2ZC5",
    "q5b":        "01KT4CV3H2V40N13MGZNE3ZKHD",
    "q1_summary": "01KT4CV4H5X8TYQ88R403H8KZK",
}

TIMEOUT_SECS = 900  # 15 minutes

def dune_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"X-Dune-API-Key": API_KEY})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

statuses = {k: "pending" for k in EXECUTIONS}
results = {}
start_times = {k: time.time() for k in EXECUTIONS}

print("Starting poll loop...", flush=True)

while True:
    pending_keys = [k for k, v in statuses.items() if v == "pending"]
    if not pending_keys:
        break

    for key in list(pending_keys):
        exec_id = EXECUTIONS[key]
        elapsed = time.time() - start_times[key]
        if elapsed > TIMEOUT_SECS:
            statuses[key] = "timed_out"
            print(f"  TIMEOUT: {key}", flush=True)
            continue
        try:
            data = dune_get(f"/execution/{exec_id}/status")
            state = data.get("state", "unknown")
            print(f"  {key}: {state} ({elapsed:.0f}s)", flush=True)
            if state == "QUERY_STATE_COMPLETED":
                statuses[key] = "completed"
            elif state == "QUERY_STATE_FAILED":
                statuses[key] = "failed"
                print(f"  FAILED detail: {data}", flush=True)
        except Exception as e:
            print(f"  ERROR polling {key}: {e}", flush=True)

    still_pending = [k for k, v in statuses.items() if v == "pending"]
    if still_pending:
        print(f"Still pending: {still_pending} — sleeping 15s...", flush=True)
        time.sleep(15)
    else:
        break

print("All queries settled. Fetching results...", flush=True)

for key, status in statuses.items():
    if status == "completed":
        exec_id = EXECUTIONS[key]
        try:
            data = dune_get(f"/execution/{exec_id}/results")
            rows = data.get("result", {}).get("rows", [])
            results[key] = rows
            print(f"  Fetched {key}: {len(rows)} rows", flush=True)
        except Exception as e:
            print(f"  ERROR fetching {key}: {e}", flush=True)
            results[key] = []
            statuses[key] = "failed"
    else:
        results[key] = []

output = {
    "statuses": statuses,
    "results": results,
}

with open("/home/user/Stablecoin-dune-weekly/dune_results.json", "w") as f:
    json.dump(output, f)

print("Done. Results written to dune_results.json", flush=True)
