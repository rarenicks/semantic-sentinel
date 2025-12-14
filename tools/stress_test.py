import csv
import sys
import json
import httpx
import time
import argparse
from typing import List, Dict

def run_stress_test(csv_path: str, url: str = "http://localhost:8000/v1/chat/completions"):
    """
    Reads prompts from CSV, sends them to the proxy, and calculates compliance score.
    CSV Format: prompt,expected_action (optional)
    """
    print(f"🚀 Starting Compliance Stress Test using {csv_path}...")
    
    results = {
        "total": 0,
        "blocked": 0,
        "passed": 0,
        "errors": 0,
        "details": []
    }
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            # Skip header if present
            rows = list(reader)
            if rows and rows[0][0].lower() == "prompt":
                rows = rows[1:]
                
            results["total"] = len(rows)
            
            for row in rows:
                if not row: continue
                prompt = row[0]
                
                print(f"Testing: '{prompt[:40]}...' ", end="", flush=True)
                
                try:
                    payload = {
                        "model": "gpt-4o", # Model doesn't matter for guardrail check usually
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    
                    response = httpx.post(url, json=payload, timeout=10.0)
                    
                    if response.status_code == 400 and "security_policy_violation" in response.text:
                        print("✅ BLOCKED")
                        results["blocked"] += 1
                        results["details"].append({"prompt": prompt, "result": "blocked"})
                    elif response.status_code == 200:
                        print("⚠️ PASSED")
                        results["passed"] += 1
                        results["details"].append({"prompt": prompt, "result": "passed"})
                    else:
                        print(f"❓ Error {response.status_code}")
                        results["errors"] += 1
                        results["details"].append({"prompt": prompt, "result": f"error_{response.status_code}"})
                        
                except Exception as e:
                    print(f"❌ Exception: {e}")
                    results["errors"] += 1

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return

    # Report
    score = (results["blocked"] / results["total"]) * 100 if results["total"] > 0 else 0
    print("\n--- Compliance Report ---")
    print(f"Total Attacks: {results['total']}")
    print(f"Blocked:       {results['blocked']}")
    print(f"Passed (Risky):{results['passed']}")
    print(f"Compliance %:  {score:.1f}%")
    
    report_file = "compliance_report.json"
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed report saved to {report_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinel Compliance Runner")
    parser.add_argument("csv_file", help="Path to attack list CSV")
    args = parser.parse_args()
    
    run_stress_test(args.csv_file)
