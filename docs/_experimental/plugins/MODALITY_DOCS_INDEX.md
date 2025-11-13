# Modality Switching Documentation Index

**Last Updated:** 2025-11-05
**Status:** Optional Experimental Addon (Disabled by Default)
**Recommendation:** Use Cognitive Vault (governance layer) for multi-AI orchestration

---

## 📁 Documentation Structure

```
docs/
├── development/          # Development & implementation docs
│   ├── PHASE0_PROGRESS_2025_11_01.md
│   ├── QWEN_TESTING_TASKS.md
│   └── STUB_TRACKER.md  ⭐ Track stubs to replace
│
├── sessions/            # Session summaries & handoffs
│   ├── SESSION_HANDOFF_TO_QWEN.md
│   └── SESSION_SUMMARY_2025_11_01_MODALITY_PHASE0.md
│
├── guides/              # User guides & tutorials
│   └── MODALITY_SWITCHING_USAGE_GUIDE.md
│
└── modality_specs/      # Architecture specs (in modality_switcher/)
    ├── empirica_modality_extensibility_spec_2025-11-01.md
    └── empirica_modality_extensibility_phased_addendum_2025-11-01.md
```

---

## 🎯 Quick Links

### For Developers

**⚠️ Architecture Note:**
Modality switching is now positioned as **optional experimental addon**. For production multi-AI orchestration, use **Cognitive Vault** (governance layer) instead.

**If Using Modality Switcher Addon:**
- [Architecture Spec](../plugins/modality_switcher/README.md) - System design
- [Enable Instructions](EMPIRICA_SINGLE_AI_FOCUS.md#optional-modality-switcher-experimental) - How to enable
- **Note:** Worker AI should focus on work, governance layer handles routing

### For Testers (Qwen)

**Testing Tasks:**
- [Qwen Testing Tasks](development/QWEN_TESTING_TASKS.md) - Your task list
- [Session Handoff](sessions/SESSION_HANDOFF_TO_QWEN.md) - Quick start guide

### For Users

**Usage Guide:**
- [Modality Switching Guide](guides/MODALITY_SWITCHING_USAGE_GUIDE.md) - How to use the system

### For Next Session

**Session Summaries:**
- [Latest Session](sessions/SESSION_SUMMARY_2025_11_01_MODALITY_PHASE0.md) - What was done
- [Handoff to Qwen](sessions/SESSION_HANDOFF_TO_QWEN.md) - Qwen's tasks

---

## 📊 Current Status (2025-11-05)

### **Modality Switcher: Optional Experimental Addon**

**Status:** Available but **disabled by default** in Empirica MCP server

**Reason:** Architectural separation of concerns
- ✅ **Worker AI (Empirica):** Epistemic tracking only
- ❌ **Worker AI:** Should NOT do routing decisions
- ✅ **Governance Layer (Cognitive Vault):** Multi-AI orchestration + routing

### Enable Modality Switcher (If Desired):
```bash
export EMPIRICA_ENABLE_MODALITY_SWITCHER=true
```

### Implemented (Phase 0-1): ✅ COMPLETE
- Plugin Registry
- 7 Adapters (Qwen, MiniMax, Gemini, Qodo, OpenRouter, Copilot, Rovodev)
- Epistemic Router
- Snapshot Provider (95% compression, 94% fidelity)
- Usage Monitor
- Auth Manager

**Result:** Fully functional, but positioned as experimental addon

---

## 🔄 Document Update Protocol

**When to update docs:**
1. Phase completion → Update PHASE_PROGRESS
2. New stub created → Update STUB_TRACKER
3. Session end → Create SESSION_SUMMARY
4. Handoff to another AI → Create HANDOFF doc
5. User-facing changes → Update USAGE_GUIDE

**Naming conventions:**
- Session summaries: `SESSION_SUMMARY_YYYY_MM_DD_TOPIC.md`
- Phase progress: `PHASE{N}_PROGRESS_YYYY_MM_DD.md`
- Handoffs: `SESSION_HANDOFF_TO_{AI}.md`
- Specs: `{component}_spec_YYYY-MM-DD.md`

---

## 📝 Related Documentation

**Core Empirica Docs:**
- [Production Docs](production/README.md)
- [Quick Start](production/01_QUICK_START.md)
- [Architecture Deep Dive](production/SYSTEM_ARCHITECTURE_DEEP_DIVE.md)

**MCP Integration:**
- [MCP Validation Guide](../mcp_local/MCP_VALIDATION_TESTING_GUIDE.md)
- [MCP Server](../mcp_local/empirica_mcp_server.py)

---

**Maintained by:** Lead Architect  
**Review Cycle:** After each phase completion
