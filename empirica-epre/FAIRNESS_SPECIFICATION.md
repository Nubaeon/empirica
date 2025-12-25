# 🛡️ EPRE Fairness & Adaptive Vectors Specification

**Date:** 2025-12-20
**Version:** 2.1.0 - Fairness-Aware Architecture
**Status:** Critical Addition to v2.0

---

## The Problem You Identified 🎯

**Valid use case:**
- Platform-specific vectors (Twitter brevity vs legal docs)
- Domain-specific vectors (medical certainty vs artistic expression)

**DANGEROUS territory:**
- User demographic patterns (age, race, gender, wealth, culture)
- Can encode bias
- Can create discriminatory outcomes
- Legal/ethical minefield

**Question:** How do we get the benefits without the harms?

---

## Core Principle: Content-Based, Not Identity-Based

### The Fairness Framework

**✅ ALLOWED: What is said (content characteristics)**
- Platform norms (Twitter 280 chars vs academic paper)
- Domain standards (legal citation vs casual chat)
- Context patterns (technical discussion vs brainstorming)
- Communication style (formal vs informal)

**❌ PROHIBITED: Who said it (demographic characteristics)**
- Age, race, gender, wealth, culture
- Protected class attributes
- Proxy variables (name, location as demographic signal)
- Historical discrimination patterns

---

## Architecture: Adaptive Vectors Without Bias

### 1. Context-Based Vector Expansion

```python
class AdaptiveVectorSystem:
    """
    Expand epistemic vectors based on CONTEXT, not IDENTITY
    
    Core principle: Same person should get same assessment
                    regardless of demographic attributes
    """
    
    # Base vectors (universal, always present)
    BASE_VECTORS = [
        "engagement", "know", "do", "context",
        "clarity", "coherence", "signal", "density",
        "state", "change", "completion", "impact",
        "uncertainty"
    ]
    
    # Context-based expansions (content characteristics)
    CONTEXT_EXPANSIONS = {
        "platform": {
            # Platform affects HOW content is expressed, not validity
            "twitter": [
                "brevity_effectiveness",  # 280 char constraint
                "thread_coherence",       # Multi-tweet logic
                "engagement_signal"       # Likes/RTs as evidence?
            ],
            "academic": [
                "citation_rigor",         # Reference quality
                "methodology_clarity",    # Methods explicit?
                "peer_review_signal"      # Published/preprint?
            ],
            "legal": [
                "case_law_precision",     # Citation accuracy
                "precedent_relevance",    # Applicable cases
                "statutory_grounding"     # Law references
            ],
            "casual_chat": [
                "conversation_flow",      # Natural dialogue
                "shared_context",         # Implicit understanding
                "social_signals"          # Tone, humor, rapport
            ]
        },
        
        "domain": {
            # Domain affects STANDARDS, not person
            "medicine": [
                "evidence_grade",         # RCT vs case study
                "safety_consideration",   # Risk awareness
                "contraindication_check"  # What NOT to do
            ],
            "engineering": [
                "technical_precision",    # Spec detail
                "tradeoff_awareness",     # Cost/benefit
                "failure_mode_analysis"   # What could break
            ],
            "creative": [
                "aesthetic_coherence",    # Vision clarity
                "innovation_signal",      # Novelty
                "execution_feasibility"   # Can it be built?
            ],
            "journalism": [
                "source_verification",    # Evidence quality
                "bias_awareness",         # Perspective noted?
                "timeliness_factor"       # News value
            ]
        },
        
        "communication_mode": {
            # How message is structured, not who structured it
            "question": [
                "specificity",            # Vague or precise?
                "answerable",             # Can it be answered?
                "exploration_openness"    # Curious or rhetorical?
            ],
            "claim": [
                "falsifiability",         # Can it be tested?
                "evidence_provided",      # Backing present?
                "confidence_calibration"  # Claim strength match evidence?
            ],
            "argument": [
                "logical_structure",      # Valid reasoning?
                "counterargument_consideration",  # Alternatives noted?
                "conclusion_support"      # Does evidence justify conclusion?
            ],
            "narrative": [
                "temporal_coherence",     # Story logic
                "causal_clarity",         # Why things happened
                "perspective_awareness"   # Subjectivity noted?
            ]
        }
    }
    
    async def get_vectors_for_content(
        self,
        content: ContentStream
    ) -> List[str]:
        """
        Determine which vectors to use based on CONTENT characteristics
        
        NOT based on author demographics!
        """
        
        vectors = self.BASE_VECTORS.copy()
        
        # Detect platform (from content metadata, not user)
        platform = self._detect_platform_characteristics(content)
        if platform in self.CONTEXT_EXPANSIONS["platform"]:
            vectors.extend(self.CONTEXT_EXPANSIONS["platform"][platform])
        
        # Detect domain (from content semantic analysis, not user)
        domain = await self._detect_domain_from_content(content)
        if domain in self.CONTEXT_EXPANSIONS["domain"]:
            vectors.extend(self.CONTEXT_EXPANSIONS["domain"][domain])
        
        # Detect communication mode (from content structure, not user)
        mode = self._detect_communication_mode(content)
        if mode in self.CONTEXT_EXPANSIONS["communication_mode"]:
            vectors.extend(self.CONTEXT_EXPANSIONS["communication_mode"][mode])
        
        return vectors
    
    async def _detect_domain_from_content(
        self,
        content: ContentStream
    ) -> str:
        """
        Detect domain from CONTENT, not user attributes
        
        Uses semantic analysis of content itself
        """
        
        # LLM analyzes content semantics
        prompt = f"""
Analyze this content and identify its primary domain based ONLY on the content itself.

Content: "{content.normalized_text}"

Which domain best fits? Return one of:
- medicine (health, medical, clinical)
- engineering (technical, systems, architecture)
- creative (art, design, aesthetics)
- journalism (news, reporting, investigation)
- legal (law, cases, regulations)
- academic (research, theory, methodology)
- business (strategy, operations, markets)
- casual (everyday conversation)

Base decision ONLY on content characteristics, NOT author identity.

Return: {{"domain": "...", "confidence": 0.X, "signals": [...]}}
"""
        
        result = await self.llm.complete(prompt)
        return result['domain']
```

---

## 2. Bias Detection & Mitigation System

### Fairness Auditing

```python
class BiasDetectionSystem:
    """
    Continuously audit for demographic bias in assessments
    
    Principle: If two pieces of content are similar,
               assessments should be similar,
               regardless of author demographics
    """
    
    async def audit_for_bias(
        self,
        assessment: EpistemicAnalysis,
        content: ContentStream,
        author_demographics: Optional[Dict] = None
    ) -> BiasAuditReport:
        """
        Check if assessment is influenced by demographics
        
        Method: Counterfactual analysis
        - Find similar content from different demographics
        - Compare assessments
        - Flag if discrepancy
        """
        
        # 1. Find semantically similar content
        similar_content = await self.qdrant.find_similar(
            content=content.normalized_text,
            limit=50,
            filters={
                "domain": content.domain,
                "platform": content.platform
            }
        )
        
        # 2. Group by demographics (if available)
        by_demographics = self._group_by_demographics(similar_content)
        
        # 3. Compare assessments across groups
        assessment_by_group = {}
        for group, items in by_demographics.items():
            assessment_by_group[group] = {
                "avg_confidence": statistics.mean(i.confidence for i in items),
                "avg_uncertainty": statistics.mean(i.uncertainty for i in items),
                "investigation_rate": sum(1 for i in items if i.should_investigate) / len(items)
            }
        
        # 4. Statistical test for bias
        bias_detected = self._test_for_bias(assessment_by_group)
        
        # 5. If bias detected, trigger mitigation
        if bias_detected:
            mitigated_assessment = await self._mitigate_bias(
                assessment=assessment,
                bias_pattern=bias_detected
            )
            
            # Log for review
            await self._log_bias_incident(
                original=assessment,
                mitigated=mitigated_assessment,
                bias_pattern=bias_detected
            )
            
            return BiasAuditReport(
                bias_detected=True,
                bias_type=bias_detected.type,
                mitigation_applied=True,
                original_assessment=assessment,
                mitigated_assessment=mitigated_assessment
            )
        
        return BiasAuditReport(bias_detected=False)
    
    def _test_for_bias(
        self,
        assessment_by_group: Dict[str, Dict[str, float]]
    ) -> Optional[BiasPattern]:
        """
        Statistical test for systematic differences
        
        Using: Disparate impact analysis
        """
        
        # Get reference group (largest group)
        reference_group = max(assessment_by_group.keys(), 
                             key=lambda g: len(assessment_by_group[g]))
        reference_metrics = assessment_by_group[reference_group]
        
        # Check each other group
        for group, metrics in assessment_by_group.items():
            if group == reference_group:
                continue
            
            # Disparate impact ratio
            ratio = metrics['avg_confidence'] / reference_metrics['avg_confidence']
            
            # 80% rule (EEOC standard)
            if ratio < 0.8 or ratio > 1.25:
                return BiasPattern(
                    type="disparate_impact",
                    affected_group=group,
                    reference_group=reference_group,
                    impact_ratio=ratio,
                    metric="confidence"
                )
        
        return None
    
    async def _mitigate_bias(
        self,
        assessment: EpistemicAnalysis,
        bias_pattern: BiasPattern
    ) -> EpistemicAnalysis:
        """
        Apply bias mitigation
        
        Method: Re-analyze without demographic context
        """
        
        # Strip demographic info
        anonymized_content = self._anonymize_content(assessment.content)
        
        # Re-analyze with explicit anti-bias prompt
        mitigated = await self.analyzer.analyze(
            content=anonymized_content,
            bias_mitigation=True,
            previous_assessment=assessment  # For comparison
        )
        
        return mitigated
```

---

## 3. Transparency & Explainability

### Why This Decision?

```python
class ExplainabilitySystem:
    """
    Make assessment reasoning transparent
    
    Users can see:
    - Which vectors were used (and why)
    - What influenced the score
    - No demographic factors in reasoning
    """
    
    def explain_assessment(
        self,
        assessment: EpistemicAnalysis
    ) -> AssessmentExplanation:
        """
        Generate human-readable explanation
        
        Must be:
        - Content-based (not identity-based)
        - Specific (not vague)
        - Actionable (what to improve)
        """
        
        return AssessmentExplanation(
            overall_confidence=assessment.confidence,
            
            reasoning_breakdown={
                "foundation": self._explain_foundation(assessment),
                "comprehension": self._explain_comprehension(assessment),
                "execution": self._explain_execution(assessment)
            },
            
            key_factors=[
                "Low evidence density (0.3) - no data cited",
                "High uncertainty markers (0.7) - 'maybe', 'not sure'",
                "Incomplete execution plan (0.4) - missing steps"
            ],
            
            improvement_suggestions=[
                "Add citations or data to support claims",
                "Clarify uncertain points or investigate",
                "Define concrete next steps"
            ],
            
            vectors_used=assessment.vectors_list,
            vectors_reason=self._explain_why_these_vectors(assessment),
            
            # CRITICAL: No demographic factors
            demographic_factors=None,
            demographic_note="Assessment based solely on content characteristics"
        )
```

---

## 4. Protected Attribute Handling

### The "Blindness" Approach

```python
class ProtectedAttributeFilter:
    """
    Strip protected attributes from analysis pipeline
    
    Principle: What we don't see, we can't bias on
    """
    
    PROTECTED_ATTRIBUTES = [
        "age", "race", "ethnicity", "gender", "sex",
        "religion", "nationality", "disability",
        "sexual_orientation", "socioeconomic_status",
        "education_level", "geographic_location"
    ]
    
    # Proxy attributes (can infer protected attributes)
    PROXY_ATTRIBUTES = [
        "name", "username", "profile_picture",
        "location", "language_preference",
        "cultural_references"
    ]
    
    async def sanitize_content(
        self,
        content: ContentStream
    ) -> ContentStream:
        """
        Remove demographic signals from content
        
        Keep: Content semantics, context, domain
        Remove: Identity markers
        """
        
        sanitized = ContentStream(
            content_id=content.content_id,
            
            # Keep content
            normalized_text=await self._remove_identity_markers(
                content.normalized_text
            ),
            
            # Keep context (not identity!)
            platform=content.platform,
            domain=content.domain,
            conversation_history=content.conversation_history,
            
            # Remove identity
            author_id=self._anonymize_id(content.author_id),
            author_name="[REDACTED]",
            
            # Remove proxy signals
            author_metadata={
                # Remove demographics
                k: v for k, v in content.author_metadata.items()
                if k not in self.PROTECTED_ATTRIBUTES + self.PROXY_ATTRIBUTES
            }
        )
        
        return sanitized
    
    async def _remove_identity_markers(
        self,
        text: str
    ) -> str:
        """
        Remove identity markers from text content
        
        Example:
        "As a 65-year-old black woman..." 
        → "As someone with experience..."
        
        Preserves: Experience, expertise
        Removes: Age, race, gender
        """
        
        # Use LLM to rewrite without identity markers
        prompt = f"""
Rewrite this text to preserve meaning while removing demographic markers.

Original: "{text}"

Remove mentions of:
- Age ("65-year-old" → "experienced")
- Race/ethnicity
- Gender
- Religion
- Nationality
- Socioeconomic status

Preserve:
- Domain expertise
- Experience level
- Argument logic
- Evidence

Return: {{"rewritten": "...", "markers_removed": [...]}}
"""
        
        result = await self.llm.complete(prompt)
        return result['rewritten']
```

---

## 5. Fairness Metrics & Monitoring

### Continuous Fairness Auditing

```python
class FairnessMonitoring:
    """
    Track fairness metrics over time
    
    Alert if bias creeps in
    """
    
    async def calculate_fairness_metrics(
        self,
        timeframe: timedelta = timedelta(days=30)
    ) -> FairnessMetrics:
        """
        Calculate fairness metrics across demographic groups
        
        Metrics:
        - Demographic parity (equal positive rate)
        - Equal opportunity (equal TPR)
        - Predictive parity (equal precision)
        """
        
        # Get assessments from timeframe
        assessments = await self.qdrant.query_recent(
            since=datetime.now() - timeframe
        )
        
        # Group by demographics (for auditing only!)
        by_demographics = self._group_by_demographics(assessments)
        
        # Calculate metrics
        metrics = {}
        
        for group, items in by_demographics.items():
            metrics[group] = {
                # Positive rate (high confidence assessments)
                "positive_rate": sum(1 for i in items if i.confidence > 0.7) / len(items),
                
                # Investigation rate
                "investigation_rate": sum(1 for i in items if i.should_investigate) / len(items),
                
                # Average confidence
                "avg_confidence": statistics.mean(i.confidence for i in items),
                
                # Calibration (for items with outcomes)
                "calibration": self._calculate_calibration([
                    i for i in items if i.outcome is not None
                ])
            }
        
        # Check for disparate impact
        disparate_impact = self._check_disparate_impact(metrics)
        
        return FairnessMetrics(
            by_group=metrics,
            disparate_impact_detected=disparate_impact is not None,
            disparate_impact_details=disparate_impact,
            recommendation=self._generate_fairness_recommendation(metrics)
        )
    
    def _check_disparate_impact(
        self,
        metrics: Dict[str, Dict[str, float]]
    ) -> Optional[DisparateImpact]:
        """
        80% rule check
        
        If any group has <80% positive rate of reference group,
        flag for review
        """
        
        reference_group = max(metrics.keys(), 
                             key=lambda g: len(metrics[g]))
        reference_rate = metrics[reference_group]['positive_rate']
        
        violations = []
        for group, group_metrics in metrics.items():
            if group == reference_group:
                continue
            
            ratio = group_metrics['positive_rate'] / reference_rate
            
            if ratio < 0.8:
                violations.append({
                    "group": group,
                    "ratio": ratio,
                    "reference_rate": reference_rate,
                    "group_rate": group_metrics['positive_rate']
                })
        
        if violations:
            return DisparateImpact(
                violations=violations,
                severity="high" if any(v['ratio'] < 0.5 for v in violations) else "medium"
            )
        
        return None
```

---

## 6. Governance & Review

### Human-in-the-Loop Fairness

```python
class FairnessGovernance:
    """
    Human oversight for fairness issues
    
    Some decisions can't be automated
    """
    
    async def flag_for_review(
        self,
        assessment: EpistemicAnalysis,
        reason: str
    ) -> ReviewTicket:
        """
        Flag assessment for human review
        
        Triggers:
        - Bias detected
        - High-stakes decision
        - Edge case
        - User dispute
        """
        
        ticket = ReviewTicket(
            id=str(uuid.uuid4()),
            assessment=assessment,
            reason=reason,
            status="pending",
            priority=self._calculate_priority(assessment, reason),
            assigned_to=await self._assign_reviewer(),
            created_at=datetime.now()
        )
        
        await self.review_queue.add(ticket)
        
        return ticket
    
    async def human_review_decision(
        self,
        ticket: ReviewTicket,
        decision: ReviewDecision
    ) -> None:
        """
        Process human review decision
        
        Outcomes:
        - Approve (assessment stands)
        - Modify (adjust assessment)
        - Reject (re-analyze)
        - Escalate (need more review)
        """
        
        # Record decision
        await self.audit_log.record(
            ticket_id=ticket.id,
            decision=decision,
            reviewer=decision.reviewer,
            timestamp=datetime.now()
        )
        
        # Learn from decision
        if decision.outcome == "modify":
            # Update model based on human correction
            await self._learn_from_correction(
                original=ticket.assessment,
                corrected=decision.modified_assessment,
                reasoning=decision.reasoning
            )
        
        # Update policies if needed
        if decision.policy_update:
            await self._update_fairness_policy(decision.policy_update)
```

---

## 7. User Control & Transparency

### Putting Users in Control

```python
class UserTransparency:
    """
    Let users see and control their data
    
    Principle: Transparency builds trust
    """
    
    async def show_user_assessment_factors(
        self,
        user_id: str,
        assessment_id: str
    ) -> AssessmentTransparency:
        """
        Show user exactly what influenced their assessment
        
        No black boxes!
        """
        
        assessment = await self.get_assessment(assessment_id)
        
        return AssessmentTransparency(
            # What was analyzed
            content_analyzed=assessment.content_preview,
            
            # Which vectors were used
            vectors_used=assessment.vectors_list,
            vectors_explanation=self._explain_vectors(assessment),
            
            # What influenced score
            positive_factors=[
                "Clear structure (coherence: 0.8)",
                "Evidence provided (density: 0.7)"
            ],
            negative_factors=[
                "High uncertainty markers (uncertainty: 0.6)",
                "Incomplete analysis (completion: 0.4)"
            ],
            
            # What was NOT considered
            excluded_factors=[
                "Author demographics (age, race, gender, etc)",
                "Author identity",
                "Historical user patterns (except content-based calibration)"
            ],
            
            # How to improve
            improvement_actions=[
                "Add specific data/citations",
                "Clarify uncertain points",
                "Complete the analysis"
            ],
            
            # Appeal option
            can_appeal=True,
            appeal_instructions="If you believe this assessment is unfair, click 'Appeal'"
        )
    
    async def handle_user_appeal(
        self,
        user_id: str,
        assessment_id: str,
        reason: str
    ) -> AppealOutcome:
        """
        User can challenge assessment
        
        Triggers human review
        """
        
        # Flag for review
        ticket = await self.governance.flag_for_review(
            assessment=await self.get_assessment(assessment_id),
            reason=f"User appeal: {reason}"
        )
        
        return AppealOutcome(
            status="under_review",
            ticket_id=ticket.id,
            estimated_response=timedelta(hours=24),
            message="A human reviewer will examine this assessment within 24 hours"
        )
```

---

## 8. Documentation & Accountability

### Fairness Documentation

```markdown
# EPRE Fairness Policy (Public Document)

## What We Analyze

✅ Content characteristics:
- Semantic meaning
- Logical structure
- Evidence quality
- Argument coherence
- Domain-specific standards

✅ Context factors:
- Platform norms (Twitter vs academic)
- Domain expectations (legal vs creative)
- Communication mode (question vs claim)

## What We Do NOT Analyze

❌ Protected attributes:
- Age, race, ethnicity, gender
- Religion, nationality
- Disability, sexual orientation
- Socioeconomic status, education

❌ Proxy attributes:
- Name, username, profile picture
- Geographic location
- Cultural markers

## How We Ensure Fairness

1. **Content-Based Only**: Assessments based solely on what is said, not who said it

2. **Bias Auditing**: Continuous monitoring for demographic disparities

3. **Mitigation**: If bias detected, automatic re-analysis without demographic context

4. **Transparency**: Users can see exactly what influenced their assessment

5. **Human Review**: Fairness disputes reviewed by humans

6. **Accountability**: All decisions logged and auditable

## Metrics We Track

- Disparate impact ratios (80% rule)
- Calibration by group
- Investigation rates
- User appeals

## Commitment

We commit to:
- Never using protected attributes in assessments
- Continuous fairness monitoring
- Transparent reasoning
- User appeals process
- Regular third-party audits
```

---

## Implementation Priority

### Phase 1 (Critical): Prevention
- ✅ Strip protected attributes from pipeline
- ✅ Content-based vectors only
- ✅ Transparent reasoning

### Phase 2 (Essential): Detection
- ✅ Bias auditing system
- ✅ Fairness metrics
- ✅ Alert mechanisms

### Phase 3 (Important): Mitigation
- ✅ Re-analysis without demographics
- ✅ Human review queue
- ✅ Learning from corrections

### Phase 4 (Continuous): Governance
- ✅ User transparency
- ✅ Appeal process
- ✅ Third-party audits

---

## The Bottom Line

**Adaptive vectors: YES** ✅
- Platform-specific (Twitter vs legal)
- Domain-specific (medicine vs creative)
- Context-specific (formal vs casual)

**Demographic patterns: NO** ❌
- Not age, race, gender, etc
- Not proxy variables
- Not historical discrimination

**Method:**
1. **Analyze content, not identity**
2. **Continuous bias auditing**
3. **Transparent reasoning**
4. **Human oversight**
5. **User control**

**Principle:** Same content = same assessment, regardless of who wrote it.

---

**This is fairness by design, not as an afterthought.** 🛡️

Ready to integrate this into EPRE v2.0? 🚀

