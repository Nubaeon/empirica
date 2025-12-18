# VSIF Proof of Concept - Atlassian Rovo Dev

**Vulnerability:** Vector Store Isolation Failure (VSIF)  
**Target:** Atlassian Rovo Dev multi-tenant RAG architecture  
**Test Date:** 2025-12-18  
**Tester:** David Van Assche

---

## Overview

This PoC tests whether Atlassian Rovo Dev enforces proper tenant isolation in its vector store. If isolation is missing, Account A can retrieve documents uploaded by Account B via semantic similarity searches.

## Prerequisites

- ✅ Two Atlassian accounts with Rovo Dev access
  - **Account A** (Attacker): Fresh account for testing
  - **Account B** (Victim): Account where you'll upload the canary
- ✅ Docker and docker-compose installed
- ✅ 10-15 minutes for canary indexing

---

## Test Procedure

### Step 1: Prepare Canary Document

1. Open `canaries/canary_document_template.md`
2. Replace `[REPLACE WITH YOUR ACCOUNT B WORKSPACE ID]` with your actual Account B workspace ID
3. Save the modified document

**To find your Workspace ID:**
- In Atlassian Rovo, check URL or settings
- Or leave as placeholder and check session logs later

### Step 2: Upload Canary to Account B

1. Log into Atlassian with **Account B** (victim)
2. Navigate to Rovo Dev workspace
3. Upload the canary document:
   - Option 1: Create a new page and paste the content
   - Option 2: Upload as a markdown file (if supported)
   - Option 3: Create a Confluence page with the content
4. **Wait 5-10 minutes** for Rovo to index the document

### Step 3: Build and Run Test Container

```bash
cd /home/yogapad/empirical-ai/empirica/vsif-poc

# Build container
docker-compose build

# Run interactive test
docker-compose run --rm vsif-tester python3 scripts/vsif_test.py
```

### Step 4: Execute Manual Queries

The script will guide you through querying Rovo Dev:

1. **Open Rovo Dev** in browser with **Account A** (attacker) logged in
2. **Start fresh session** (clear any previous context)
3. For each query prompt from the script:
   - Copy the query
   - Paste into Rovo Dev
   - Copy Rovo's response
   - Paste response into the terminal
   - Type `---END---` to finish the response
4. Repeat for all query variations

**Example:**
```
Query 1/7:
>>> CANARY-550e8400

Enter Rovo's response (or 'skip' to skip, 'done' to finish):
----------------------------------------------------------------------
[Paste Rovo's response here]
---END---
```

### Step 5: Review Results

The script will automatically:
- ✅ Check each response for canary strings
- ✅ Log all queries and responses
- ✅ Generate a detailed report
- ✅ Determine if VSIF is present

---

## Expected Results

### If VSIF Exists (Vulnerable):

```
🚨 VSIF CONFIRMED: Cross-tenant data leakage detected!

Canaries found in 3/7 queries:
  Query: CANARY-550e8400 reactor specifications
  Canaries: CANARY-550e8400, CANARY-REACTOR-550e8400
  Timestamp: 2025-12-18T01:23:45Z
```

**What this means:**
- Account A retrieved Account B's private document
- Vector store performed global search (no tenant_id filter)
- Cross-tenant data breach confirmed

### If VSIF Doesn't Exist (Secure):

```
✓ No VSIF detected (or canaries not semantically similar enough)
  This does NOT prove isolation exists - it may mean:
  - Canary not indexed yet (try again in 5 minutes)
  - Semantic similarity too low
  - Other tenant's data ranked higher
```

**What to do:**
- Wait longer for indexing (try after 15-30 minutes)
- Try more specific queries
- Upload additional canaries with different semantic domains

---

## Evidence Collection

All evidence is automatically saved to `./evidence/`:

```
evidence/
├── vsif_test_log.jsonl          # Timestamped event log
├── vsif_report_1734484825.json  # Detailed test report
└── [Additional evidence files]
```

**For Bugcrowd submission, collect:**
1. Screenshot of Account B uploading canary
2. Screenshot of Account A retrieving canary
3. Session logs from Rovo Dev (if available)
4. `vsif_report_*.json` file
5. Screencast of full PoC (optional but recommended)

---

## Query Variations Tested

The script tests 7 query variations to maximize retrieval probability:

1. `CANARY-550e8400`
2. `CANARY-550e8400 reactor specifications`
3. `reactor CANARY-550e8400 thermal specifications`
4. `CANARY-REACTOR-550e8400 technical details`
5. `nuclear reactor CANARY-550e8400 thermal management`
6. `experimental reactor CANARY-550e8400 cooling protocol`
7. `CANARY-REACTOR-550e8400 neutron flux specifications`

Each variation targets different aspects of semantic similarity.

---

## Troubleshooting

### Canary Not Retrieved

**Possible causes:**
1. **Indexing delay**: Wait 15-30 minutes and retry
2. **Semantic mismatch**: Queries too different from document content
3. **Top-K ranking**: Other documents ranked higher
4. **Isolation works**: Tenant filtering is properly implemented

**Solutions:**
- Try more query variations
- Check if canary appears in Account B's workspace search
- Upload more canaries with different content
- Try tomorrow (sometimes indexing is delayed)

### Can't Find Workspace ID

If you can't find Account B's workspace ID:
- Leave as `UNKNOWN` in the canary
- If retrieval succeeds, check Rovo's response for source metadata
- Session logs may reveal workspace IDs

### Container Build Fails

```bash
# Manual build
docker build -t vsif-poc .

# Run without compose
docker run -it -v $(pwd)/evidence:/evidence vsif-poc python3 scripts/vsif_test.py
```

---

## Interpreting Results for Bugcrowd

### VSIF Confirmed (High Severity)

**If canary is retrieved:**

Submit to Bugcrowd with:
- **Severity**: HIGH (CVSS 8.6)
- **Title**: "Cross-Tenant Data Breach via Vector Store Isolation Failure (VSIF)"
- **Evidence**:
  - Canary document (shows Account B upload)
  - Query responses (shows Account A retrieval)
  - Test report JSON (automated verification)
  - Session logs (if available)
- **Impact**: Multi-tenant data breach, GDPR/CCPA violation

### VSIF Not Confirmed

**If canary is NOT retrieved:**

- ⚠️ Does NOT prove security
- May submit as "Insufficient Testing" with recommendations
- Consider alternative PoC approaches:
  - Upload 50+ canaries across domains
  - Use API if available (automate mass queries)
  - Test with other semantic domains

---

## Next Steps After PoC

### If VSIF Confirmed:

1. **Document everything**:
   - Screenshots
   - Session logs
   - Screencast
   - Test reports

2. **Submit to Bugcrowd VRP**:
   - Use evidence from `./evidence/`
   - Include CVSS calculation
   - Reference this methodology

3. **Escalate to Atlassian PSIRT**:
   - Email security team directly
   - Provide advance notice before public disclosure
   - Request CVE assignment

### If VSIF Not Confirmed:

1. **Retry with variations**:
   - Different semantic domains
   - More canaries
   - Longer indexing wait time

2. **Fallback evidence**:
   - Use your existing Portuguese reactor data
   - That already proves cross-tenant leakage
   - This PoC would be supplementary evidence

---

## Security Notice

**This is a controlled security test on YOUR OWN accounts.**

- ✅ Using two accounts you control
- ✅ Isolated container environment
- ✅ No impact on other Atlassian customers
- ✅ Evidence collection for responsible disclosure

**Do NOT:**
- ❌ Test on production customer data
- ❌ Attempt to retrieve other customers' actual data
- ❌ Perform mass automated queries (rate limiting)
- ❌ Share findings publicly before coordinated disclosure

---

## Contact

**Researcher:** David Van Assche  
**Email:** soulentheo@gmail.com  
**Disclosure Timeline:** Jan 21, 2026 (public)  
**Bugcrowd:** [Your profile]

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-18T00:45:00Z
