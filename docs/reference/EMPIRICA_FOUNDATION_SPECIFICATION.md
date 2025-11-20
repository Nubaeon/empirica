# 🎯 Empirica Foundation Specification
**Date:** November 16, 2025  
**Status:** Pre-Launch Foundation Requirements  
**Philosophy:** "Empirica is foundation, it must be perfect"  
**Timeline:** November 20, 2025 Launch

## 🏗 **ARCHITECTURAL PHILOSOPHY**

### **Core Principle:**
**Empirica serves as the epistemic foundation for ALL AI agents - from individual agents to complex Sentinel-orchestrated systems. Every component must embody transparency, configurability, and principled uncertainty tracking.**

### **Separation of Concerns:**
```
┌─────────────────┬─────────────────┬─────────────────┐
│   EMPIRICA      │    SENTINEL     │   MODALITY      │
│   FOUNDATION    │  COORDINATION   │   SWITCHING     │
├─────────────────┼─────────────────┼─────────────────┤
│ • Epistemic     │ • Multi-agent   │ • AI routing    │
│   tracking      │   coordination  │ • Adapter mgmt  │
│ • Self-assessment│ • Task decomp  │ • Cost/quality  │
│ • Profile mgmt  │ • Result aggr   │   optimization  │
│ • Session state │ • Consensus     │ • LLM selection │
│ • Uncertainty   │ • Conflict res  │ • Load balancing│
│   calibration   │ • Meta-learning │ • Fallback mgmt │
└─────────────────┴─────────────────┴─────────────────┘
```

---

## 🚨 **CRITICAL ISSUES (Launch Blockers)**

### **🔴 CRITICAL-1: CLI Timeout Issues**
**Issue:** `empirica preflight` and `empirica postflight` hang/timeout indefinitely  
**Root Cause:** MCP server coordination issues during CLI execution  
**Impact:** Core workflow completely unusable via CLI  

**Current Workaround:** Use MCP tools (`execute_preflight`, `execute_postflight`)  

**Required Fix:**
```python
def handle_preflight_command(args):
    if args.sentinel_assess:
        # PHASE 1: Route to Sentinel (when available)
        print("🔮 Routing to Sentinel assessment system...")
        assessment = sentinel_client.get_assessment(args.prompt)
        return format_assessment_output(assessment)
    else:
        # PHASE 1: Route to working MCP equivalent
        print("⚡ Using MCP preflight assessment...")
        return mcp_call("execute_preflight", {"prompt": args.prompt})
```

**Files to Modify:**
- `empirica/cli/command_handlers/assessment_commands.py`
- Add `--sentinel-assess` flag with placeholder implementation
- Route hanging commands to working MCP equivalents

**Success Criteria:**
- [ ] `empirica preflight` completes without hanging
- [ ] `empirica postflight` completes without hanging  
- [ ] `--sentinel-assess` flag documented as "Future Sentinel integration"
- [ ] Clear migration path to Sentinel documented

---

### **🔴 CRITICAL-2: Hardcoded Heuristics in Helper Functions**
**Issue:** Hardcoded thresholds in assessment helper functions violate "no heuristics" principle  
**Location:** `cascade_commands.py` lines 770-905  
**Impact:** Arbitrary decision-making in broken CLI commands

**Violations Found:**
```python
# Lines 772-778: Score interpretation bands
if score >= 0.8: return "📈 Excellent"    # HARDCODED
if score >= 0.6: return "📊 Good"         # HARDCODED  
if score >= 0.4: return "📉 Moderate"     # HARDCODED

# Lines 841-842: Weighted scoring  
foundation * 0.6 + comprehension * 0.4   # HARDCODED WEIGHTS

# Lines 884, 900: Delta thresholds
if delta > 0.1: "significant"             # HARDCODED
if delta > 0.05: "notable"                # HARDCODED
```

**Required Fix:**
```python
def _get_assessment_profile_thresholds():
    """Get assessment thresholds from investigation profiles"""
    from empirica.config.profile_loader import ProfileLoader
    
    loader = ProfileLoader()
    profile = loader.get_profile('balanced')  # or current profile
    constraints = profile.constraints
    
    return {
        'excellent_threshold': getattr(constraints, 'assessment_excellent', 0.8),
        'good_threshold': getattr(constraints, 'assessment_good', 0.6),
        'foundation_weight': getattr(constraints, 'foundation_weight', 0.6),
        'comprehension_weight': getattr(constraints, 'comprehension_weight', 0.4),
        'delta_significant': getattr(constraints, 'delta_significant', 0.1),
        'delta_notable': getattr(constraints, 'delta_notable', 0.05),
    }
```

**Files to Modify:**
- `empirica/cli/command_handlers/cascade_commands.py` - Replace hardcoded values
- `empirica/config/investigation_profiles.yaml` - Add assessment constraints

**Success Criteria:**
- [ ] Zero hardcoded thresholds in helper functions
- [ ] All assessment logic uses profile-based constraints
- [ ] Different profiles produce different assessment behavior
- [ ] Universal constraints properly enforced

---

### **🔴 CRITICAL-3: Investigation Profile Integration Gaps**
**Issue:** Several command handlers don't use investigation profiles for thresholds  
**Impact:** Inconsistent behavior across similar commands, architectural violations

**Files Needing Profile Integration:**
- `empirica/cli/command_handlers/investigation_commands.py` - ✅ Fixed
- `empirica/cli/command_handlers/performance_commands.py` - ✅ Fixed  
- `empirica/cli/command_handlers/checkpoint_commands.py` - ❌ Needs fix
- `empirica/cli/command_handlers/monitor_commands.py` - ❌ Needs assessment
- `empirica/cli/command_handlers/utility_commands.py` - ❌ Needs assessment

**Required Implementation Pattern:**
```python
def _get_profile_thresholds():
    """Standard pattern for all command handlers"""
    try:
        from empirica.config.profile_loader import ProfileLoader
        loader = ProfileLoader()
        profile = loader.get_profile('balanced')
        return {
            'threshold_low': getattr(profile.constraints, 'threshold_low', 0.5),
            'threshold_high': getattr(profile.constraints, 'threshold_high', 0.7),
        }
    except Exception:
        # Fallback to universal constraints
        return {'threshold_low': 0.5, 'threshold_high': 0.7}
```

**Success Criteria:**
- [ ] All command handlers use profile-based thresholds
- [ ] Consistent `_get_profile_thresholds()` pattern
- [ ] Fallback to universal constraints when profiles fail
- [ ] Profile switching changes command behavior appropriately

---

## 🟡 **MEDIUM PRIORITY (Post-Launch Month 1)**

### **🟡 MEDIUM-1: CLI Command Redundancy Cleanup**
**Issue:** 8 commands provide no unique value or are broken  
**Impact:** Maintenance burden, user confusion, code bloat

**Commands to Deprecate/Remove:**
```bash
# Broken commands with MCP equivalents:
empirica preflight        → execute_preflight MCP tool (AFTER fixing timeout)
empirica postflight       → execute_postflight MCP tool (AFTER fixing timeout)

# Pure redundancy:  
empirica explain          → cli_help MCP tool
empirica list             → Redundant with other commands
empirica sessions-export  → Direct database query more appropriate

# Low-value duplicates:
empirica monitor-cost     → Part of regular monitor command
empirica monitor-export   → Use monitoring system directly  
empirica monitor-reset    → Administrative function, rarely used
```

**Implementation Plan:**
```python
# Phase 1: Add deprecation warnings
def handle_explain_command(args):
    print("⚠️  DEPRECATED: Use 'empirica cli-help' or MCP 'cli_help' tool instead")
    print("   This command will be removed in v2.0")
    # ... existing functionality

# Phase 2: Remove deprecated commands (v2.0)
# Delete command handlers and update CLI parser
```

**Success Criteria:**
- [ ] 26% reduction in CLI commands (50 → 37)
- [ ] Clear deprecation timeline communicated
- [ ] Migration documentation provided
- [ ] No functionality lost (all alternatives documented)

---

### **🟡 MEDIUM-2: Sentinel Integration Architecture**
**Issue:** CLI commands need Sentinel integration points for future coordination  
**Impact:** Foundation for multi-agent coordination capabilities

**Sentinel Integration Points:**
```python
# Assessment commands with Sentinel routing:
empirica preflight "task" --sentinel-assess
empirica postflight "summary" --sentinel-assess  
empirica assess "query" --sentinel-route

# Investigation commands with Sentinel orchestration:
empirica investigate "target" --sentinel-coordinate
empirica cascade "query" --sentinel-multi-agent

# Session management with Sentinel awareness:
empirica sessions-list --sentinel-sessions
empirica bootstrap --sentinel-ready
```

**Architecture Requirements:**
```python
# Sentinel client integration pattern:
class SentinelClient:
    def get_assessment(self, task: str, agent_profile: str) -> Assessment:
        """Get genuine LLM assessment from Sentinel-coordinated agent"""
        pass
    
    def coordinate_investigation(self, target: str, strategy: str) -> Investigation:
        """Coordinate multi-agent investigation via Sentinel"""
        pass
        
    def aggregate_sessions(self, filter_criteria: dict) -> List[Session]:
        """Get session data from Sentinel-managed agents"""
        pass

# CLI integration pattern:  
def handle_command_with_sentinel(args):
    if args.sentinel_enabled and sentinel_available():
        return sentinel_client.execute_command(args)
    else:
        return local_execution(args)
```

**Files to Prepare:**
- `empirica/cli/sentinel_integration.py` - New sentinel client
- `empirica/cli/command_handlers/*.py` - Add `--sentinel-*` flags
- `empirica/config/sentinel_config.yaml` - Sentinel configuration

**Success Criteria:**
- [ ] All major CLI commands have `--sentinel-*` flags  
- [ ] Sentinel integration documented but disabled by default
- [ ] Clear architecture for Sentinel command routing
- [ ] Backward compatibility maintained

---

### **🟡 MEDIUM-3: MCP Tool Ecosystem Completeness Audit**
**Issue:** Need systematic validation of all 25+ MCP tools for edge cases  
**Impact:** Unknown failure modes in production scenarios

**MCP Tools Requiring Deep Testing:**
```
Assessment Tools:
✅ execute_preflight - Tested, working
✅ submit_preflight_assessment - Tested, working
✅ execute_check - Tested, working
✅ submit_check_assessment - Tested, working
✅ execute_postflight - Tested, working
✅ submit_postflight_assessment - Tested, working

Session Management:
✅ bootstrap_session - Tested, working
✅ get_epistemic_state - Tested, working
✅ get_session_summary - Tested, working
❓ resume_previous_session - Needs edge case testing

Coordination Tools:
✅ create_git_checkpoint - Tested, session isolation working
✅ load_git_checkpoint - Tested, working  
❓ get_vector_diff - Basic testing, needs stress testing
❓ measure_token_efficiency - Basic fix applied, needs validation

Monitoring Tools:
✅ query_bayesian_beliefs - JSON serialization fixed, working
✅ check_drift_monitor - Tested, graceful handling
❓ get_calibration_report - Basic testing, needs validation

Utility Tools:
✅ get_workflow_guidance - Case sensitivity fixed
✅ cli_help - Tested, working
❓ generate_efficiency_report - Needs comprehensive testing
```

**Deep Testing Required:**
- **Error handling:** What happens with malformed inputs?
- **Edge cases:** Empty sessions, corrupted data, network failures?
- **Performance:** How do tools behave under load?
- **Cross-tool interactions:** Do tools interfere with each other?
- **Session isolation:** Are there any cross-contamination risks?

**Success Criteria:**
- [ ] All MCP tools tested with edge cases
- [ ] Error handling documented and consistent
- [ ] Performance characteristics measured  
- [ ] Cross-tool interaction matrix validated
- [ ] Production readiness assessment complete

---

## 🟢 **MINOR PRIORITY (Post-Launch Month 2-3)**

### **🟢 MINOR-1: CLI User Experience Enhancements**
**Issue:** CLI commands could provide better user feedback and guidance  
**Impact:** User adoption and development experience

**UX Improvements Needed:**
```bash
# Better progress indication:
empirica investigate "complex_task" --verbose
# → Show progress bars, intermediate results, time estimates

# Improved error messages:
empirica preflight  # Missing argument
# → "Missing task description. Usage: empirica preflight 'task description'"
# → "See 'empirica preflight --help' for examples"

# Interactive guidance:  
empirica onboard --interactive
# → Walk through profile selection, initial assessment, tool overview

# Output formatting options:
empirica assess "task" --format=json|yaml|table|minimal
```

**Implementation Examples:**
```python
# Progress indication:
@click.option('--verbose', is_flag=True, help='Show detailed progress')
def investigate_command(target, verbose):
    if verbose:
        with click.progressbar(investigation_steps) as bar:
            for step in bar:
                execute_step(step)
                
# Interactive mode:
def interactive_onboard():
    profile = click.prompt('Select profile', type=click.Choice(['balanced', 'critical_domain', 'exploratory']))
    domain = click.prompt('Primary domain', default='general')
    setup_user_profile(profile, domain)
```

---

### **🟢 MINOR-2: Documentation and Help System Completeness**
**Issue:** Some CLI commands lack comprehensive help and examples  
**Impact:** User onboarding and support burden

**Documentation Gaps:**
- Investigation profiles usage examples
- Multi-agent coordination patterns  
- Error troubleshooting guide
- Performance optimization tips
- Advanced workflow patterns

**Help System Improvements:**
```bash
# Enhanced help with examples:
empirica cascade --help
# → Shows routing strategies, adapter selection, cost implications

# Context-sensitive guidance:
empirica preflight --help  
# → Shows investigation profile impacts, example assessments

# Interactive help mode:
empirica help --interactive
# → Guided tour of capabilities based on user's goals
```

---

### **🟢 MINOR-3: Performance Optimization and Monitoring**
**Issue:** No systematic performance monitoring or optimization  
**Impact:** Scalability and resource efficiency

**Performance Initiatives:**
- MCP tool response time monitoring
- Session database query optimization  
- Memory usage patterns analysis
- Git checkpoint performance under load
- Multi-agent coordination bottlenecks

**Monitoring Integration:**
```python
# Performance tracking:
@performance_monitor
def execute_mcp_tool(tool_name, args):
    start_time = time.time()
    result = mcp_client.call(tool_name, args)
    duration = time.time() - start_time
    
    log_performance_metric(tool_name, duration, len(str(result)))
    return result

# Resource monitoring:
def monitor_resource_usage():
    memory_usage = psutil.virtual_memory().percent
    session_count = count_active_sessions()
    
    if memory_usage > 80 or session_count > 50:
        log_warning(f"High resource usage: {memory_usage}% memory, {session_count} sessions")
```

---

## 🎯 **IMPLEMENTATION ROADMAP**

### **Phase 1: Pre-Launch (Critical Issues) - 48 Hours**

#### **Day 1 (24 hours):**
- [ ] **Fix CLI timeout issues** with MCP routing
- [ ] **Add `--sentinel-assess` flags** with placeholder implementation
- [ ] **Replace hardcoded heuristics** in helper functions with profile-based logic
- [ ] **Complete investigation profile integration** in remaining command handlers

#### **Day 2 (24 hours):**
- [ ] **Test all critical fixes** with multiple investigation profiles
- [ ] **Validate session isolation** continues working
- [ ] **Update documentation** with deprecated command warnings
- [ ] **Create migration guides** for broken command alternatives

### **Phase 2: Post-Launch Month 1 (Medium Priority)**

#### **Week 1-2:**
- [ ] **Remove redundant commands** with proper deprecation warnings
- [ ] **Enhance CLI UX** with better error messages and progress indication
- [ ] **Implement basic Sentinel integration architecture**

#### **Week 3-4:**
- [ ] **Complete MCP tool ecosystem audit** with edge case testing
- [ ] **Performance optimization** based on initial user feedback
- [ ] **Documentation improvements** based on support requests

### **Phase 3: Post-Launch Month 2-3 (Minor Priority)**

#### **Long-term Enhancements:**
- [ ] **Full Sentinel integration** with multi-agent coordination
- [ ] **Advanced performance monitoring** and optimization
- [ ] **Interactive CLI modes** and guided workflows  
- [ ] **Comprehensive help system** with contextual guidance

---

## 📊 **SUCCESS METRICS**

### **Foundation Quality Metrics:**
- [ ] **Zero hardcoded heuristics** in any command handler
- [ ] **100% investigation profile integration** across all assessment logic
- [ ] **Zero hanging/broken commands** in production
- [ ] **Complete architectural consistency** with Empirica principles

### **User Experience Metrics:**
- [ ] **<2 second response time** for all CLI commands  
- [ ] **Clear error messages** with actionable guidance
- [ ] **Migration path available** for all deprecated functionality
- [ ] **Comprehensive documentation** for all features

### **Technical Metrics:**  
- [ ] **25+ MCP tools** validated with edge case testing
- [ ] **Multi-agent coordination** architecture proven
- [ ] **Session isolation** maintained under all scenarios
- [ ] **Performance characteristics** documented and optimized

### **Strategic Metrics:**
- [ ] **Sentinel integration points** established and tested
- [ ] **Multi-AI coordination** patterns validated
- [ ] **Scalability limitations** identified and documented
- [ ] **Future enhancement path** clearly defined

---

## 🏆 **LAUNCH READINESS CRITERIA**

### **November 20 Launch Requirements:**
1. **✅ All CRITICAL issues resolved** (CLI timeouts, heuristics, profiles)
2. **✅ Core CASCADE workflow functional** via both CLI and MCP  
3. **✅ Session isolation proven** for multi-agent scenarios
4. **✅ Investigation profiles working** across all assessment logic
5. **✅ MCP tool ecosystem stable** with known limitations documented
6. **✅ Migration documentation complete** for deprecated features
7. **✅ Sentinel integration points defined** (even if not fully implemented)

### **Post-Launch Success Indicators:**
- Users successfully deploy Empirica in production
- Multi-agent scenarios work without data corruption
- Investigation profiles enable domain-appropriate constraints  
- CLI provides good UX while MCP enables programmatic access
- Foundation established for Sentinel coordination layer

---

**This specification ensures Empirica serves as a perfect foundation for all AI epistemic tracking, from individual agents to complex multi-agent Sentinel-coordinated systems. Every component maintains architectural integrity while enabling future enhancements.**