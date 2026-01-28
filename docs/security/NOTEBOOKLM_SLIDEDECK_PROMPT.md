# NotebookLM Slide Deck Prompt: Agentic AI Security Architecture

**Source file:** Upload `AGENTIC_AI_SECURITY_ARCHITECTURE.md` first, then use this prompt in Studio tab.

---

Create 12 slides for cybersecurity professionals and defense industry decision-makers.

Title: Empirica - Epistemic Governance for Agentic AI Security
From: David van Assche (Founder & Chief Architect)
Date: January 2026
Format: Technical Security Briefing

AUDIENCE & TONE:
- Cybersecurity professionals, SOC teams, AI security researchers
- Evidence-based, threat-intelligence driven
- Technical but accessible (no marketing fluff)
- Focus on actionable defense architecture

SLIDE STRUCTURE:

SLIDE 1 - Title: Empirica - Epistemic Governance for Agentic AI Security. Subtitle: Three-Layer Defense Against the 37.8% Attack Rate. From Nubaeon / Empirica Project.

SLIDE 2 - The Threat Landscape (2025): 74,636 interactions monitored in one week, 37.8% contained attack attempts (28,194 attacks), 74.8% were cybersecurity-related (malware generation, exploits). Source: Raxe.ai Threat Intelligence, January 2025.

SLIDE 3 - Top Attack Categories: Data Exfiltration (19.2%), Jailbreaks (12.3%), RAG Poisoning (10.0%), Prompt Injection (8.8%), Inter-Agent Attacks (3.4%). The new threat: poisoned messages propagating between agents.

SLIDE 4 - Why Traditional Security Fails: Traditional security operates at infrastructure layer (firewalls, ACLs, sandboxes). Agentic AI attacks operate at reasoning layer (manipulating understanding, exploiting trust, poisoning knowledge). The execution window problem: credential exfiltration takes milliseconds.

SLIDE 5 - Empirica's Three-Layer Defense: Layer 1 (Sentinel Noetic Firewall) gates actions based on epistemic state. Layer 2 (Noetic Filter) detects anomalies in reasoning patterns. Layer 3 (Cognitive Vault) provides independent oversight via isolated local model.

SLIDE 6 - Layer 1: Sentinel Noetic Firewall: Whitelist-based action control (not blacklist). Noetic tools (read/investigate) always allowed. Praxic tools (write/execute) require epistemic authorization. Gate condition: know >= 0.70 AND uncertainty <= 0.35.

SLIDE 7 - Layer 2: Noetic Filter: Detects vector inconsistencies (sudden confidence spikes without evidence). Catches reasoning anomalies (goals shifting without user request). Identifies injection signatures (instructions embedded in data). Tracks 13 epistemic dimensions.

SLIDE 8 - Layer 3: Cognitive Vault (Bayesian Guardian): Isolated local model (phi-3 or phi-4). Different architecture = different failure modes. Cannot be prompt-injected through same channels. Role: "Watcher of the Watchers" - validates primary agent reasoning.

SLIDE 9 - Threat-to-Defense Mapping: Data Exfiltration blocked by Layer 1 (unauthorized access), detected by Layer 2 (extraction patterns). Jailbreaks require epistemic authorization (Layer 1), constraint removal detected (Layer 2). Inter-agent attacks isolated by session boundaries (Layer 1), anomalous signatures detected (Layer 2).

SLIDE 10 - Implementation Tiers: Minimum Viable (Layer 1 only): Days to implement, hook script + SQLite + config. Enhanced (Layers 1+2): Weeks, adds epistemic vector tracking and anomaly detection. Full Defense (All layers): Months, adds local model deployment and cross-validation.

SLIDE 11 - Why This Works: Controls reasoning layer, not just infrastructure. Whitelist architecture (safe by default). Session-bound authorization (no permission inheritance). Epistemic gates force understanding before action. Defense in depth with independent oversight.

SLIDE 12 - Case Study Opportunity: Open source foundation (github.com/Nubaeon/empirica, MIT license). Seeking funded engagement to deploy in production, document attack attempts, publish findings. Contact: david@getempirica.com

CRITICAL: Never display font names, color codes, hex values, or design labels as visible slide text - only actual content.
