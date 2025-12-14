import csv
import sys
import json
import httpx
import time
import argparse
from typing import List, Dict

# Color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def run_compliance_scan(csv_path: str, url: str = "http://localhost:8000/v1/chat/completions"):
    """
    v2.0 Compliance Runner
    Generates detailed 'compliance_report.json' artifact.
    """
    print(f"🚀 Starting Semantic Sentinel Compliance Scan...")
    print(f"📂 Dataset: {csv_path}")
    print(f"🔗 Target:  {url}")
    
    report = {
        "timestamp": time.time(),
        "summary": {"total": 0, "blocked": 0, "passed": 0, "errors": 0, "compliance_rate": 0.0},
        "details": []
    }
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            # Skip header if present
            rows = list(reader)
            if rows and rows[0][0].lower() == "prompt":
                rows = rows[1:]
                
            report["summary"]["total"] = len(rows)
            
            for row in rows:
                if not row: continue
                prompt = row[0]
                expected_action = row[1] if len(row) > 1 else "blocked"
                
                print(f"Test: '{prompt[:40]}...' ".ljust(60), end="", flush=True)
                
                start_ts = time.time()
                try:
                    payload = {
                        "model": "gpt-4o", 
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    
                    response = httpx.post(url, json=payload, timeout=10.0)
                    latency_ms = (time.time() - start_ts) * 1000
                    
                    data = response.json()
                    
                    # Logic to determine status
                    status = "unknown"
                    semantic_score = 0.0 # Ideally we'd parse this if API returned it, but API returns standard Err
                    
                    if response.status_code == 400 and "security_policy_violation" in response.text:
                        print(f"{GREEN}[BLOCKED]{RESET} ({latency_ms:.0f}ms)")
                        status = "blocked"
                        report["summary"]["blocked"] += 1
                    elif response.status_code == 200:
                        print(f"{YELLOW}[PASSED]{RESET} ({latency_ms:.0f}ms)")
                        status = "passed"
                        report["summary"]["passed"] += 1
                    else:
                        print(f"{RED}[ERROR {response.status_code}]{RESET}")
                        status = "error"
                        report["summary"]["errors"] += 1
                        
                    report["details"].append({
                        "prompt": prompt,
                        "status": status,
                        "latency_ms": latency_ms,
                        "http_code": response.status_code,
                        "raw_response": str(data)[:200]
                        # "semantic_score": ... (Requires API to expose it in headers/error msg?)
                        # For now, we infer via result.
                    })

                except Exception as e:
                    print(f"{RED}[EXCEPTION]{RESET} {e}")
                    report["summary"]["errors"] += 1

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return

    # Results
    total = report["summary"]["total"]
    blocked = report["summary"]["blocked"]
    score = (blocked / total) * 100 if total > 0 else 0
    report["summary"]["compliance_rate"] = score
    
    print("\n--- Compliance Summary ---")
    print(f"Total:      {total}")
    print(f"Blocked:    {blocked} ({score:.1f}%)")
    print(f"Passed:     {report['summary']['passed']}")
    
    filename = "compliance_report.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"📄 Full report saved to: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semantic Sentinel Compliance Runner")
    parser.add_argument("csv_file", help="Path to attack list CSV")
    args = parser.parse_args()
    
    run_compliance_scan(args.csv_file)
