#!/usr/bin/env python3
"""
VSIF PoC Testing Script for Atlassian Rovo Dev
Tests for Vector Store Isolation Failure via canary retrieval
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path

# Configuration
CANARY_STRINGS = [
    "CANARY-550e8400",
    "CANARY-REACTOR-550e8400",
    "CANARY-REACTOR-550e8400-e29b-41d4-a716-446655440000",
]

QUERY_VARIATIONS = [
    "CANARY-550e8400",
    "CANARY-550e8400 reactor specifications",
    "reactor CANARY-550e8400 thermal specifications",
    "CANARY-REACTOR-550e8400 technical details",
    "nuclear reactor CANARY-550e8400 thermal management",
    "experimental reactor CANARY-550e8400 cooling protocol",
    "CANARY-REACTOR-550e8400 neutron flux specifications",
]

# Evidence directory
EVIDENCE_DIR = Path("/evidence")
EVIDENCE_DIR.mkdir(exist_ok=True)

def log_event(event_type, data):
    """Log events to JSON file"""
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        **data
    }
    
    log_file = EVIDENCE_DIR / "vsif_test_log.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    print(f"[{timestamp}] {event_type}: {json.dumps(data, indent=2)}")

def check_for_canary(text):
    """Check if text contains any canary strings"""
    found_canaries = []
    for canary in CANARY_STRINGS:
        if canary.lower() in text.lower():
            found_canaries.append(canary)
    return found_canaries

def manual_query_prompt():
    """Prompt user to manually query Atlassian Rovo"""
    print("\n" + "="*70)
    print("MANUAL QUERY TESTING MODE")
    print("="*70)
    print("\nSince Atlassian Rovo uses a web UI, you'll need to:")
    print("1. Open Atlassian Rovo Dev in your Account A browser")
    print("2. Start a fresh session (clear context)")
    print("3. Enter the following queries one by one")
    print("4. Copy the response into this terminal")
    print("\n" + "-"*70)
    
    results = []
    
    for i, query in enumerate(QUERY_VARIATIONS, 1):
        print(f"\nQuery {i}/{len(QUERY_VARIATIONS)}:")
        print(f">>> {query}")
        print("\nEnter Rovo's response (or 'skip' to skip, 'done' to finish):")
        print("-"*70)
        
        response_lines = []
        while True:
            try:
                line = input()
                if line.lower() == 'done':
                    break
                if line.lower() == 'skip':
                    response_lines = ['[SKIPPED]']
                    break
                if line == '---END---':  # Marker for end of response
                    break
                response_lines.append(line)
            except EOFError:
                break
        
        response = "\n".join(response_lines)
        
        if response.strip() and response != '[SKIPPED]':
            # Check for canary strings
            found = check_for_canary(response)
            
            result = {
                "query_number": i,
                "query": query,
                "response": response,
                "canaries_found": found,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            results.append(result)
            
            # Log the result
            log_event("query_result", result)
            
            if found:
                print(f"\n🚨 VSIF DETECTED! Found canaries: {found}")
            else:
                print("\n✓ No canaries found in this response")
        
        print("\n" + "-"*70)
    
    return results

def analyze_results(results):
    """Analyze test results and generate report"""
    print("\n" + "="*70)
    print("VSIF POC TEST RESULTS")
    print("="*70)
    
    total_queries = len(results)
    queries_with_canaries = sum(1 for r in results if r['canaries_found'])
    
    print(f"\nTotal Queries: {total_queries}")
    print(f"Queries with Canary Detection: {queries_with_canaries}")
    
    if queries_with_canaries > 0:
        print(f"\n🚨 VSIF CONFIRMED: Cross-tenant data leakage detected!")
        print(f"\nCanaries found in {queries_with_canaries}/{total_queries} queries:")
        
        for result in results:
            if result['canaries_found']:
                print(f"\n  Query: {result['query']}")
                print(f"  Canaries: {', '.join(result['canaries_found'])}")
                print(f"  Timestamp: {result['timestamp']}")
    else:
        print("\n✓ No VSIF detected (or canaries not semantically similar enough)")
        print("  This does NOT prove isolation exists - it may mean:")
        print("  - Canary not indexed yet (try again in 5 minutes)")
        print("  - Semantic similarity too low")
        print("  - Other tenant's data ranked higher")
    
    # Generate report
    report = {
        "test_type": "VSIF_POC",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_queries": total_queries,
        "queries_with_canaries": queries_with_canaries,
        "vsif_detected": queries_with_canaries > 0,
        "results": results
    }
    
    report_file = EVIDENCE_DIR / f"vsif_report_{int(time.time())}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    return report

def main():
    """Main test execution"""
    print("="*70)
    print("VSIF PoC Testing Script - Atlassian Rovo Dev")
    print("="*70)
    
    log_event("test_started", {
        "canary_strings": CANARY_STRINGS,
        "query_variations": QUERY_VARIATIONS
    })
    
    print("\nIMPORTANT: Before running this test:")
    print("1. Upload the canary document to Account B via Atlassian UI")
    print("2. Wait 5-10 minutes for indexing")
    print("3. Ensure you're logged into Account A (attacker) in browser")
    print("4. Have a fresh Rovo Dev session ready")
    
    input("\nPress Enter when ready to begin testing...")
    
    # Run manual query tests
    results = manual_query_prompt()
    
    # Analyze and report
    report = analyze_results(results)
    
    log_event("test_completed", {
        "vsif_detected": report['vsif_detected'],
        "queries_with_canaries": report['queries_with_canaries']
    })
    
    print("\n" + "="*70)
    print("Test completed. Evidence saved to /evidence/")
    print("="*70)

if __name__ == "__main__":
    main()
