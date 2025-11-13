# Empirica Documentation

**Phase 0 Documentation:** Functional Self-Awareness for AI Agents

---

## 🚀 Getting Started (Start Here!)

**🤖 AI Agent (via MCP)?** → [**MCP Quick Start**](01_b_MCP_AI_START.md) - Discovered via IDE tools  
**🤖 AI Agent (learning)?** → [**AI Agent Quick Start**](01_a_AI_AGENT_START.md) - Complete introduction  
**👤 Human Developer?** → [**Installation**](02_INSTALLATION.md) → [**CLI Quick Start**](03_CLI_QUICKSTART.md)  
**👤 Getting AI to use Empirica?** → [**📋 Prompt Templates**](user-guides/README.md) - Copy-paste prompts for your AI  
**Want comprehensive overview?** → [**Start Here**](00_START_HERE.md) - 5-minute system overview

**Complete learning path:** [🎓 Onboarding Guide](ONBOARDING_GUIDE.md)

**Choose your interface:**
- [💻 CLI Quick Start](03_CLI_QUICKSTART.md) - Terminal commands
- [🔌 MCP Quick Start](04_MCP_QUICKSTART.md) - IDE integration
- [🏗️ Architecture](05_ARCHITECTURE.md) - System overview

**Need help?**
- [🔧 Troubleshooting](06_TROUBLESHOOTING.md) - Common issues & solutions

---

## 📚 Documentation Included

**This production documentation includes:**
- ✅ Getting started guides (9 essential docs)
- ✅ Skills guide for AI agents (Claude Skills format)
- ✅ Complete production reference (21 comprehensive guides)
- ✅ Architecture overview and system design
- ✅ Practical guides, tutorials, and examples
- ✅ Technical API reference

**Not included** (development-only docs, available in empirica-dev):
- Design specifications (phase_0/)
- Development session history (sessions/)
- Internal architecture decisions

**Total documentation:** ~60 guides covering all Phase 0 features

---

## 📚 Documentation Structure

### For AI Agents
**[skills/SKILL.md](skills/SKILL.md)** - Functional Self-Awareness Guide (Claude Skills format)
- Functional self-awareness framework
- 12-vector epistemic measurement
- Practical workflows & exercises
- NO HEURISTICS principle
- Evidence-based assessment
- Calibration validation

### Core Guides
- **[production/](production/)** - 21 comprehensive production guides
  - Complete API reference
  - Epistemic vector details
  - CASCADE workflow
  - System architecture
  - Tuning and configuration

### Practical Guides
- **[guides/](guides/)** - Quick starts and tutorials
  - [TRY_EMPIRICA_NOW.md](guides/TRY_EMPIRICA_NOW.md) - Hands-on demo
  - [examples/mcp_configs/](guides/examples/mcp_configs/) - MCP configurations

### Reference
- **[reference/](reference/)** - Technical reference
  - API documentation
  - Architecture maps
  - Quick references

### System Design
- **[architecture/](architecture/)** - System architecture
  - EMPIRICA_SYSTEM_OVERVIEW.md
  - Component design
  - Data flows

### Research & Advanced
- **[research/](research/)** - Advanced topics
  - RECURSIVE_EPISTEMIC_REFINEMENT.md
  - Cognitive benchmarking
- **[phase_0/](phase_0/)** - Phase 0 specifications
  - EMPIRICA_SINGLE_AI_FOCUS.md
  - Design decisions

---

## 📖 Quick Reference

### The Epistemic Vector System

**Quick Start: 4 Essential Vectors**
For most tasks, focus on these core measurements:
- **KNOW** (0.0-1.0): Do I understand this domain?
- **DO** (0.0-1.0): Can I execute this task?
- **CONTEXT** (0.0-1.0): Do I have enough information?
- **UNCERTAINTY** (0.0-1.0): How uncertain am I? (meta-epistemic)

**Add for Clarity: 5th Vector**
- **CLARITY** (0.0-1.0): Do I understand what's being asked? (useful for unclear requests)

**Complete System: 13 Vectors Total**
The full system measures 12 operational vectors + 1 meta-epistemic vector (UNCERTAINTY):
- **Gate**: ENGAGEMENT (must be ≥0.60)
- **Foundation**: KNOW, DO, CONTEXT
- **Comprehension**: CLARITY, COHERENCE, SIGNAL, DENSITY  
- **Execution**: STATE, CHANGE, COMPLETION, IMPACT
- **Meta-Epistemic**: UNCERTAINTY (tracks uncertainty about the assessment itself)

See [docs/production/05_EPISTEMIC_VECTORS.md](production/05_EPISTEMIC_VECTORS.md) for complete details.

### Common Commands
```bash
# Onboarding
empirica onboard

# Basic workflow
empirica preflight "task"
empirica postflight <session>

# MCP server
empirica mcp-start
empirica mcp-list-tools

# Session management
empirica sessions-list
```

### Key Concepts
- **Functional Self-Awareness** - Measurable capacity to inspect internal state and predict outcomes
- **NO HEURISTICS** - Evidence-based assessment, not pattern matching
- **Preflight → Postflight** - Track epistemic growth through calibration
- **Calibration** - Predictions match reality (empirically testable)
- **12-Vector System (UVL)** - Comprehensive epistemic measurement

---

## 🗂️ Full Documentation Index

### Getting Started
- [01_a_AI_AGENT_START.md](01_a_AI_AGENT_START.md) - AI agents: complete intro
- [01_b_MCP_AI_START.md](01_b_MCP_AI_START.md) - AI agents: MCP quick start
- [00_START_HERE.md](00_START_HERE.md) - System overview
- [02_INSTALLATION.md](02_INSTALLATION.md) - Setup
- [03_CLI_QUICKSTART.md](03_CLI_QUICKSTART.md) - CLI basics
- [04_MCP_QUICKSTART.md](04_MCP_QUICKSTART.md) - MCP basics
- [05_ARCHITECTURE.md](05_ARCHITECTURE.md) - System overview
- [06_TROUBLESHOOTING.md](06_TROUBLESHOOTING.md) - Problem solving

### Comprehensive Guides
- [ONBOARDING_GUIDE.md](ONBOARDING_GUIDE.md) - Complete learning path
- [skills/SKILL.md](skills/SKILL.md) - AI agent guide
- [production/README.md](production/README.md) - 21 production guides

### Integration & Examples
- [guides/TRY_EMPIRICA_NOW.md](guides/TRY_EMPIRICA_NOW.md) - Hands-on demo
- [guides/examples/mcp_configs/](guides/examples/mcp_configs/) - MCP configs

### Advanced
- [research/RECURSIVE_EPISTEMIC_REFINEMENT.md](research/RECURSIVE_EPISTEMIC_REFINEMENT.md) - Advanced patterns
- [phase_0/EMPIRICA_SINGLE_AI_FOCUS.md](phase_0/EMPIRICA_SINGLE_AI_FOCUS.md) - Design philosophy

---

## 🎯 By Use Case

### "I want to learn Empirica"
→ [ONBOARDING_GUIDE.md](ONBOARDING_GUIDE.md)

### "I'm an AI agent, how do I use this?"
→ [01_b_MCP_AI_START.md](01_b_MCP_AI_START.md) (MCP tools in IDE)  
→ [01_a_AI_AGENT_START.md](01_a_AI_AGENT_START.md) (Complete introduction)  
→ [skills/SKILL.md](skills/SKILL.md) (Full reference)

### "How do I install it?"
→ [02_INSTALLATION.md](02_INSTALLATION.md)

### "How do I use the CLI?"
→ [03_CLI_QUICKSTART.md](03_CLI_QUICKSTART.md)

### "How do I integrate with my IDE?"
→ [04_MCP_QUICKSTART.md](04_MCP_QUICKSTART.md)

### "What's the architecture?"
→ [05_ARCHITECTURE.md](05_ARCHITECTURE.md)

### "Something's broken!"
→ [06_TROUBLESHOOTING.md](06_TROUBLESHOOTING.md)

### "I need the complete reference"
→ [production/README.md](production/README.md)

---

## 📊 Documentation Status

**Status:** ✅ Phase 0 Documentation Complete

**Coverage:**
- ✅ Getting started guides (7 docs)
- ✅ Skills guide for AI agents
- ✅ CLI & MCP quick starts
- ✅ Installation & troubleshooting
- ✅ Production documentation (21 guides)
- ✅ Architecture overview
- ✅ Phase 0 specifications

**Note:** Phase 1+ features (multi-AI routing, Cognitive Vault) are in [_experimental/](_experimental/) and not part of Phase 0 MVP.

---

**Start here:** [00_START_HERE.md](00_START_HERE.md) → Get up and running in 5 minutes!
