"""
Parallel Orchestrator - Plan, regulate, and aggregate parallel epistemic agents.

Coordinates multiple epistemic agents working in parallel on a task:
1. plan() — Analyze task, allocate attention budget, assign agent domains
2. regulate() — After each round, decide: continue/spawn_more/stop_early
3. aggregate() — Combine findings with confidence-weighted synthesis

Uses match_or_decompose for persona selection and AttentionBudgetCalculator
for resource allocation.

Usage:
    from empirica.core.parallel_orchestrator import ParallelOrchestrator

    orch = ParallelOrchestrator(session_id="abc123")
    plan = orch.plan(task="Investigate the attention budget architecture", max_agents=3)
    # plan.agents: [AgentAllocation(...), ...]
    # plan.budget: AttentionBudget(...)

    # After agents complete:
    decision = orch.regulate(rollup_results)
    # decision.action: "stop" | "continue" | "spawn_more"

    synthesis = orch.aggregate(all_results)
    # synthesis.findings, synthesis.confidence_weighted_vectors, etc.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from empirica.core.attention_budget import (
    AttentionBudget,
    AttentionBudgetCalculator,
    persist_budget,
)
from empirica.core.information_gain import (
    estimate_information_gain,
    should_spawn_more,
)
from empirica.core.epistemic_rollup import RollupResult

logger = logging.getLogger(__name__)


@dataclass
class AgentAllocation:
    """Allocation for a single parallel agent."""
    agent_name: str
    domain: str
    persona_id: str
    budget: int  # Max findings this agent should produce
    priority: float  # 0.0-1.0
    expected_gain: float
    priors: Dict[str, float] = field(default_factory=dict)
    task_focus: str = ""  # Specific task aspect for this agent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "domain": self.domain,
            "persona_id": self.persona_id,
            "budget": self.budget,
            "priority": self.priority,
            "expected_gain": self.expected_gain,
            "priors": self.priors,
            "task_focus": self.task_focus,
        }


@dataclass
class OrchestrationPlan:
    """Plan for parallel agent execution."""
    task: str
    session_id: str
    agents: List[AgentAllocation]
    budget: AttentionBudget
    strategy: str = "information_gain"
    max_rounds: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "session_id": self.session_id,
            "agents": [a.to_dict() for a in self.agents],
            "budget": self.budget.to_dict(),
            "strategy": self.strategy,
            "max_rounds": self.max_rounds,
        }


@dataclass
class RegulationDecision:
    """Decision from the regulate step."""
    action: str  # "stop", "continue", "spawn_more"
    reason: str
    round_number: int
    findings_this_round: int
    novel_findings_this_round: int
    budget_remaining: int
    gain_estimate: float
    rounds_without_novel: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "round_number": self.round_number,
            "findings_this_round": self.findings_this_round,
            "novel_findings_this_round": self.novel_findings_this_round,
            "budget_remaining": self.budget_remaining,
            "gain_estimate": self.gain_estimate,
            "rounds_without_novel": self.rounds_without_novel,
        }


@dataclass
class AggregatedSynthesis:
    """Result of aggregating all parallel agent results."""
    findings: List[str]
    unknowns: List[str]
    confidence_weighted_vectors: Dict[str, float]
    total_findings: int
    total_accepted: int
    total_rejected: int
    agent_summaries: List[Dict[str, Any]]
    consensus_domains: List[str]  # Domains where agents agree
    conflict_domains: List[str]  # Domains where agents disagree

    def to_dict(self) -> Dict[str, Any]:
        return {
            "findings": self.findings,
            "unknowns": self.unknowns,
            "confidence_weighted_vectors": self.confidence_weighted_vectors,
            "total_findings": self.total_findings,
            "total_accepted": self.total_accepted,
            "total_rejected": self.total_rejected,
            "agent_summaries": self.agent_summaries,
            "consensus_domains": self.consensus_domains,
            "conflict_domains": self.conflict_domains,
        }


class ParallelOrchestrator:
    """
    Orchestrate parallel epistemic agents with attention budget management.
    """

    def __init__(
        self,
        session_id: str,
        max_agents: int = 5,
        total_budget: int = 20,
        strategy: str = "information_gain",
    ):
        self.session_id = session_id
        self.max_agents = max_agents
        self.total_budget = total_budget
        self.strategy = strategy
        self._rounds_without_novel = 0

    def plan(
        self,
        task: str,
        domains: Optional[List[str]] = None,
        max_agents: Optional[int] = None,
        current_vectors: Optional[Dict[str, float]] = None,
    ) -> OrchestrationPlan:
        """
        Plan parallel agent execution for a task.

        1. Analyze task for domain signals
        2. Match or decompose personas for each domain
        3. Allocate attention budget across domains
        4. Return agent allocations

        Args:
            task: Investigation task description
            domains: Override domains (auto-detected if None)
            max_agents: Override max agents
            current_vectors: Current epistemic state

        Returns:
            OrchestrationPlan with agent allocations and budget
        """
        max_agents = max_agents or self.max_agents
        vectors = current_vectors or {}

        # Detect domains from task if not provided
        if not domains:
            domains = self._detect_domains(task)

        # Limit to max_agents
        domains = domains[:max_agents]

        # Get prior findings count per domain
        prior_findings = self._get_prior_findings_by_domain(domains)
        dead_ends = self._get_dead_ends_by_domain(domains)

        # Create attention budget
        calculator = AttentionBudgetCalculator(
            session_id=self.session_id,
            default_total=self.total_budget,
        )
        budget = calculator.create_budget(
            domains=domains,
            current_vectors=vectors,
            prior_findings_by_domain=prior_findings,
            dead_ends_by_domain=dead_ends,
            total_budget=self.total_budget,
        )

        # Persist budget
        persist_budget(budget)

        # Create agent allocations
        agents = []
        for alloc in budget.allocations:
            persona_id = self._select_persona(task, alloc.domain)
            agent_name = f"empirica-integration:{alloc.domain}"

            agents.append(AgentAllocation(
                agent_name=agent_name,
                domain=alloc.domain,
                persona_id=persona_id,
                budget=alloc.budget,
                priority=alloc.priority,
                expected_gain=alloc.expected_gain,
                priors=self._get_domain_priors(persona_id),
                task_focus=self._generate_focus(task, alloc.domain),
            ))

        plan = OrchestrationPlan(
            task=task,
            session_id=self.session_id,
            agents=agents,
            budget=budget,
            strategy=self.strategy,
        )

        logger.info(
            f"Orchestration plan: {len(agents)} agents, "
            f"budget={self.total_budget}, "
            f"domains={[a.domain for a in agents]}"
        )

        return plan

    def regulate(
        self,
        rollup_result: RollupResult,
        round_number: int,
        current_vectors: Optional[Dict[str, float]] = None,
    ) -> RegulationDecision:
        """
        After a round of agent execution, decide next action.

        Checks:
        - Budget remaining
        - Novel findings produced
        - Information gain estimate
        - Rounds without novelty

        Returns:
            RegulationDecision with action and reasoning
        """
        novel_count = sum(
            1 for f in rollup_result.accepted if f.novelty > 0.3
        )

        if novel_count == 0:
            self._rounds_without_novel += 1
        else:
            self._rounds_without_novel = 0

        # Estimate continued gain
        vectors = current_vectors or {}
        gain = estimate_information_gain(
            domain="aggregate",
            current_vectors=vectors,
            prior_findings=[f.finding for f in rollup_result.accepted],
            dead_ends=0,
        )

        spawn_more = should_spawn_more(
            budget_remaining=rollup_result.budget_remaining,
            gain_estimate=gain,
            rounds_without_novel=self._rounds_without_novel,
        )

        if not spawn_more:
            if rollup_result.budget_remaining <= 0:
                reason = "Budget exhausted"
            elif self._rounds_without_novel >= 2:
                reason = f"No novel findings for {self._rounds_without_novel} rounds"
            else:
                reason = f"Expected gain ({gain:.3f}) below threshold"
            action = "stop"
        elif novel_count > 3:
            action = "spawn_more"
            reason = f"High novelty ({novel_count} novel findings) suggests more investigation is valuable"
        else:
            action = "continue"
            reason = f"Moderate gain ({gain:.3f}), {novel_count} novel findings"

        decision = RegulationDecision(
            action=action,
            reason=reason,
            round_number=round_number,
            findings_this_round=len(rollup_result.accepted),
            novel_findings_this_round=novel_count,
            budget_remaining=rollup_result.budget_remaining,
            gain_estimate=gain,
            rounds_without_novel=self._rounds_without_novel,
        )

        logger.info(
            f"Regulation round {round_number}: action={action}, "
            f"reason={reason}"
        )

        return decision

    def aggregate(
        self,
        agent_results: List[Dict[str, Any]],
        agent_confidences: Optional[Dict[str, float]] = None,
    ) -> AggregatedSynthesis:
        """
        Aggregate results from all parallel agents.

        Uses confidence-weighted synthesis:
        - Higher confidence agents contribute more to vector aggregation
        - Findings are deduplicated and ranked
        - Consensus/conflict domains are identified

        Args:
            agent_results: List of agent result dicts with:
                - agent_name, domain, findings, unknowns, vectors
            agent_confidences: Override confidence per agent_name

        Returns:
            AggregatedSynthesis
        """
        confidences = agent_confidences or {}
        all_findings = []
        all_unknowns = []
        agent_summaries = []
        domain_findings: Dict[str, List[str]] = {}
        weighted_vectors: Dict[str, float] = {}
        total_weight = 0.0

        for result in agent_results:
            name = result.get("agent_name", "unknown")
            domain = result.get("domain", "general")
            findings = result.get("findings", [])
            unknowns = result.get("unknowns", [])
            vectors = result.get("vectors", {})
            confidence = confidences.get(name, result.get("confidence", 0.7))

            all_findings.extend(findings)
            all_unknowns.extend(unknowns)

            # Track domain findings for consensus detection
            if domain not in domain_findings:
                domain_findings[domain] = []
            domain_findings[domain].extend(findings)

            # Confidence-weighted vector aggregation
            conf = float(confidence or 0.7)
            for key, value in vectors.items():
                if key not in weighted_vectors:
                    weighted_vectors[key] = 0.0
                weighted_vectors[key] += float(value or 0.0) * conf
            total_weight += confidence or 0.0

            agent_summaries.append({
                "agent_name": name,
                "domain": domain,
                "findings_count": len(findings),
                "unknowns_count": len(unknowns),
                "confidence": confidence,
            })

        # Normalize weighted vectors
        if total_weight > 0:
            for key in weighted_vectors:
                weighted_vectors[key] /= total_weight

        # Deduplicate findings
        unique_findings = []
        seen = set()
        for f in all_findings:
            if f not in seen:
                unique_findings.append(f)
                seen.add(f)

        # Identify consensus/conflict domains
        consensus = []
        conflict = []
        for domain, findings in domain_findings.items():
            if len(findings) >= 2:
                # If multiple agents found similar things = consensus
                consensus.append(domain)
            elif len(findings) == 0:
                conflict.append(domain)

        return AggregatedSynthesis(
            findings=unique_findings,
            unknowns=list(set(all_unknowns)),
            confidence_weighted_vectors=weighted_vectors,
            total_findings=len(all_findings),
            total_accepted=len(unique_findings),
            total_rejected=len(all_findings) - len(unique_findings),
            agent_summaries=agent_summaries,
            consensus_domains=consensus,
            conflict_domains=conflict,
        )

    def _detect_domains(self, task: str) -> List[str]:
        """Detect investigation domains from task description."""
        try:
            from empirica.core.sentinel.decision_logic import DecisionLogic
            logic = DecisionLogic()
            signals = logic.analyze_task(task)
            return [s.domain for s in signals[:self.max_agents]]
        except Exception:
            return ["general"]

    def _get_prior_findings_by_domain(self, domains: List[str]) -> Dict[str, int]:
        """Count existing findings per domain."""
        counts = {}
        try:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            cursor = db.conn.cursor()
            for domain in domains:
                cursor.execute("""
                    SELECT COUNT(*) FROM project_findings
                    WHERE session_id = ? AND finding LIKE ?
                """, (self.session_id, f"%[%{domain}%]%"))
                counts[domain] = cursor.fetchone()[0]
            db.close()
        except Exception:
            for domain in domains:
                counts[domain] = 0
        return counts

    def _get_dead_ends_by_domain(self, domains: List[str]) -> Dict[str, int]:
        """Count dead ends per domain."""
        counts = {}
        try:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            cursor = db.conn.cursor()
            for domain in domains:
                cursor.execute("""
                    SELECT COUNT(*) FROM project_dead_ends
                    WHERE session_id = ? AND approach LIKE ?
                """, (self.session_id, f"%{domain}%"))
                counts[domain] = cursor.fetchone()[0]
            db.close()
        except Exception:
            for domain in domains:
                counts[domain] = 0
        return counts

    def _select_persona(self, task: str, domain: str) -> str:
        """Select best persona for a domain."""
        try:
            from empirica.core.emerged_personas import sentinel_match_persona
            persona = sentinel_match_persona(
                task=f"{task} (focus: {domain})",
                min_reputation=0.3,
            )
            if persona:
                return persona.persona_id
        except Exception:
            pass
        return f"{domain}_expert"

    def _get_domain_priors(self, persona_id: str) -> Dict[str, float]:
        """Get epistemic priors for a persona."""
        try:
            from empirica.core.persona import PersonaManager
            manager = PersonaManager()
            persona = manager.load_persona(persona_id)
            return persona.epistemic_config.priors
        except Exception:
            return {"know": 0.5, "uncertainty": 0.5}

    def _generate_focus(self, task: str, domain: str) -> str:
        """Generate domain-specific task focus."""
        return f"Investigate the {domain} aspects of: {task}"
