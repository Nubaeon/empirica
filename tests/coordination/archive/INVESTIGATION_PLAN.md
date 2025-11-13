# Structural Integrity Investigation Plan

**Following Empirica Methodology:**
1. ✅ PREFLIGHT - Assessed current knowledge (low, need investigation)
2. 🔄 INVESTIGATE - Gather actual evidence from codebase
3. ⏳ CHECK - Validate findings before recommendations
4. ⏳ ACT - Make evidence-based recommendations

---

## Investigation Areas

### Area 1: SessionDB Actual Schema
**Questions:**
- What does the ACTUAL schema look like?
- What fields exist TODAY?
- Are my assumptions correct?

**Method:** Read session_database.py, check CREATE TABLE statements

### Area 2: Reflex Frame Actual Structure  
**Questions:**
- What does EpistemicAssessment ACTUALLY contain?
- What fields are there NOW?
- What about ReflexLogger implementation?

**Method:** Read reflex_frame.py, reflex_logger.py

### Area 3: CASCADE Integration Points
**Questions:**
- How does CASCADE ACTUALLY use SessionDB?
- What data is logged WHERE?
- Are calibration results stored?

**Method:** Read metacognitive_cascade.py, trace data flow

### Area 4: Existing Test Coverage
**Questions:**
- What do Qwen's 89 tests ACTUALLY test?
- What's covered vs assumptions?

**Method:** Review test files Qwen created

### Area 5: MCP Integration Reality
**Questions:**
- How does MCP server ACTUALLY store data?
- What about the recent fix?

**Method:** Read empirica_mcp_server.py after fix

---

**Starting systematic investigation...**
