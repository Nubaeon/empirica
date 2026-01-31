"""
Tool Router - Maps epistemic vectors + task intent to specific tools/agents/skills.

Extends the VectorRouter (which routes to behavioral modes) with concrete
tool recommendations. This is the bridge between "what should I do" (modes)
and "what should I use" (tools).

Architecture:
  VectorRouter:  vectors → mode (investigate, implement, clarify, ...)
  ToolRouter:    vectors + task → mode + tools (agents, skills, MCP tools)

The ToolRouter is consumed by:
  - UserPromptSubmit hook: injects routing advice before Claude reasons
  - skill_suggest MCP tool: vector-aware tool recommendation API
  - EpistemicMiddleware: enriches responses with tool suggestions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .router import VectorRouter


@dataclass
class ToolRecommendation:
    """A recommended tool/agent/skill for a task."""
    tool_type: str          # "agent", "skill", "mcp_tool", "cli"
    name: str               # e.g., "empirica-integration:architecture"
    confidence: float       # 0.0-1.0 routing confidence
    reasoning: str          # Why this tool is recommended
    priority: int = 0       # Higher = more important (for ordering)

    def to_dict(self) -> Dict:
        return {
            "tool_type": self.tool_type,
            "name": self.name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "priority": self.priority,
        }


@dataclass
class RoutingAdvice:
    """Complete routing advice: mode + tools."""
    mode: str                               # From VectorRouter
    mode_confidence: float
    mode_reasoning: str
    tools: List[ToolRecommendation] = field(default_factory=list)
    context_depth: str = "standard"         # minimal, standard, deep

    def to_dict(self) -> Dict:
        return {
            "mode": self.mode,
            "mode_confidence": self.mode_confidence,
            "mode_reasoning": self.mode_reasoning,
            "tools": [t.to_dict() for t in self.tools],
            "context_depth": self.context_depth,
        }

    def format_for_prompt(self) -> str:
        """Format as concise text for injection into Claude's context."""
        if not self.tools:
            return ""

        lines = [f"**Epistemic Routing: {self.mode}** (confidence: {self.mode_confidence:.0%})"]

        for tool in sorted(self.tools, key=lambda t: -t.priority):
            prefix = {
                "agent": "Agent",
                "skill": "Skill",
                "mcp_tool": "Tool",
                "cli": "CLI",
            }.get(tool.tool_type, "Tool")
            lines.append(f"- {prefix}: `{tool.name}` — {tool.reasoning}")

        return "\n".join(lines)


# Domain keyword → agent mapping
# Maps task-relevant keywords to Empirica plugin agents
AGENT_DOMAINS = {
    "empirica-integration:security": {
        "keywords": [
            "security", "auth", "authentication", "authorization",
            "encrypt", "vulnerability", "xss", "csrf", "injection",
            "token", "credential", "permission", "access control",
            "threat", "attack", "sanitiz",
        ],
        "description": "Security analysis and hardening",
    },
    "empirica-integration:architecture": {
        "keywords": [
            "architecture", "design", "pattern", "refactor",
            "modular", "coupling", "cohesion", "abstraction",
            "interface", "dependency", "scalab", "structure",
            "component", "layer", "separation of concerns",
        ],
        "description": "Architecture analysis and system design",
    },
    "empirica-integration:performance": {
        "keywords": [
            "performance", "optimiz", "latency", "throughput",
            "memory", "cpu", "cache", "profil", "slow",
            "bottleneck", "n+1", "query", "index",
        ],
        "description": "Performance analysis and optimization",
    },
    "empirica-integration:ux": {
        "keywords": [
            "usability", "accessibility", "user flow", "ux",
            "error message", "response time", "wcag", "a11y",
            "user experience", "interaction", "visual",
        ],
        "description": "UX and accessibility analysis",
    },
}

# Mode → tool mappings
# For each behavioral mode, which tools are most useful
MODE_TOOLS = {
    "load_context": [
        ToolRecommendation(
            tool_type="mcp_tool",
            name="project_bootstrap",
            confidence=0.95,
            reasoning="Load project context (goals, findings, unknowns)",
            priority=10,
        ),
        ToolRecommendation(
            tool_type="mcp_tool",
            name="blindspot_scan",
            confidence=0.7,
            reasoning="Scan for knowledge gaps before starting work",
            priority=6,
        ),
    ],
    "investigate": [
        ToolRecommendation(
            tool_type="mcp_tool",
            name="investigate",
            confidence=0.85,
            reasoning="Systematic investigation with epistemic tracking",
            priority=8,
        ),
        ToolRecommendation(
            tool_type="mcp_tool",
            name="blindspot_scan",
            confidence=0.8,
            reasoning="Detect unknown unknowns from negative space analysis",
            priority=7,
        ),
        ToolRecommendation(
            tool_type="mcp_tool",
            name="unknown_log",
            confidence=0.7,
            reasoning="Log uncertainties discovered during investigation",
            priority=5,
        ),
    ],
    "clarify": [
        ToolRecommendation(
            tool_type="mcp_tool",
            name="unknown_log",
            confidence=0.8,
            reasoning="Log what's unclear before asking the user",
            priority=7,
        ),
    ],
    "confident_implementation": [
        ToolRecommendation(
            tool_type="mcp_tool",
            name="finding_log",
            confidence=0.7,
            reasoning="Log discoveries as you implement",
            priority=5,
        ),
    ],
    "cautious_implementation": [
        ToolRecommendation(
            tool_type="mcp_tool",
            name="finding_log",
            confidence=0.7,
            reasoning="Log discoveries as you implement",
            priority=5,
        ),
        ToolRecommendation(
            tool_type="mcp_tool",
            name="deadend_log",
            confidence=0.65,
            reasoning="Log failed approaches to prevent re-exploration",
            priority=4,
        ),
        ToolRecommendation(
            tool_type="mcp_tool",
            name="unknown_log",
            confidence=0.6,
            reasoning="Log uncertainties encountered during implementation",
            priority=3,
        ),
    ],
}

# Skill triggers — when to recommend the empirica-framework skill
SKILL_TRIGGERS = [
    "preflight", "postflight", "check", "cascade",
    "epistemic", "vector", "calibrat", "drift",
    "assessment", "knowledge state",
]


class ToolRouter:
    """
    Routes tasks to specific tools/agents/skills based on epistemic vectors.

    Usage:
        router = ToolRouter()
        advice = router.route(
            vectors={"know": 0.4, "uncertainty": 0.7, ...},
            task="Investigate the architecture of the hook system"
        )
        # advice.tools → [ToolRecommendation(agent, "empirica-integration:architecture", ...)]
    """

    def __init__(self, personality: Optional[Dict] = None):
        self.vector_router = VectorRouter(personality)

    def route(self, vectors: Dict[str, float], task: str) -> RoutingAdvice:
        """
        Full routing: vectors + task → mode + tools.

        1. VectorRouter determines behavioral mode
        2. Task keywords determine domain-specific agents
        3. Mode determines supporting MCP tools
        4. Skill triggers check for skill recommendations
        """
        # Step 1: Get behavioral mode from VectorRouter
        decision = self.vector_router.route(vectors, task)

        # Step 2: Build tool recommendations
        tools: List[ToolRecommendation] = []

        # 2a: Domain-specific agents from task keywords
        agent_recs = self._match_agents(task, vectors)
        tools.extend(agent_recs)

        # 2b: Mode-specific MCP tools
        mode_tools = MODE_TOOLS.get(decision.mode, [])
        tools.extend(mode_tools)

        # 2c: Skill recommendations
        skill_recs = self._match_skills(task)
        tools.extend(skill_recs)

        # Deduplicate by name, keeping highest priority
        tools = self._deduplicate(tools)

        return RoutingAdvice(
            mode=decision.mode,
            mode_confidence=decision.confidence,
            mode_reasoning=decision.reasoning,
            tools=tools,
            context_depth=decision.context_depth,
        )

    def _match_agents(
        self, task: str, vectors: Dict[str, float]
    ) -> List[ToolRecommendation]:
        """Match task keywords to domain-specific agents."""
        task_lower = task.lower()
        recommendations = []

        for agent_name, config in AGENT_DOMAINS.items():
            matches = sum(
                1 for kw in config["keywords"]
                if kw in task_lower
            )
            if matches == 0:
                continue

            # Confidence scales with keyword matches (1 match = 0.6, 3+ = 0.9)
            confidence = min(0.95, 0.5 + matches * 0.15)

            # Boost confidence in investigation mode (agents are most useful there)
            uncertainty = vectors.get("uncertainty", 0.5)
            if uncertainty > 0.5:
                confidence = min(0.95, confidence + 0.1)

            recommendations.append(ToolRecommendation(
                tool_type="agent",
                name=agent_name,
                confidence=confidence,
                reasoning=str(config["description"]),
                priority=7 + matches,  # More matches = higher priority
            ))

        return recommendations

    def _match_skills(self, task: str) -> List[ToolRecommendation]:
        """Match task to skill recommendations."""
        task_lower = task.lower()
        recommendations = []

        # Check for empirica-framework skill triggers
        skill_matches = sum(
            1 for trigger in SKILL_TRIGGERS
            if trigger in task_lower
        )
        if skill_matches > 0:
            confidence = min(0.95, 0.6 + skill_matches * 0.1)
            recommendations.append(ToolRecommendation(
                tool_type="skill",
                name="empirica-framework",
                confidence=confidence,
                reasoning="Epistemic workflow guidance (CASCADE, vectors, calibration)",
                priority=6,
            ))

        return recommendations

    def _deduplicate(
        self, tools: List[ToolRecommendation]
    ) -> List[ToolRecommendation]:
        """Deduplicate by name, keeping highest priority."""
        seen: Dict[str, ToolRecommendation] = {}
        for tool in tools:
            key = f"{tool.tool_type}:{tool.name}"
            if key not in seen or tool.priority > seen[key].priority:
                seen[key] = tool
        return list(seen.values())
