# 🔄 EPRE Data Flow & Architecture Clarification

**Date:** 2025-12-20
**Version:** 2.2.0 - Data Flow & Privacy Architecture
**Status:** Critical Architecture Clarification

---

## Your Questions 🎯

### Question 1: "Do we collect demographic patterns then strip when used?"

**Answer:** NO! We strip BEFORE collection, not after.

**Why:** Can't have bias from what you never see.

### Question 2: "Do I see an embeddings service here?"

**Answer:** YES! Embeddings are central to the architecture.

**Why:** Semantic search in Qdrant requires vector embeddings.

---

## Architecture: Data Flow & Privacy

### The Two Pipelines

```
┌─────────────────────────────────────────────────────────────┐
│                 ANALYSIS PIPELINE (Real-Time)               │
│                 NO demographic data allowed                 │
└─────────────────────────────────────────────────────────────┘

Content → Sanitization → Analysis → Response
  │            │             │          │
  │            │             │          └─ User sees result
  │            │             │
  │            │             └─ LLM epistemic assessment
  │            │                 (13 vectors + adaptive)
  │            │
  │            └─ Strip demographics BEFORE analysis
  │               (age, race, gender, name, location, etc)
  │
  └─ Raw content from platform


┌─────────────────────────────────────────────────────────────┐
│              LEARNING PIPELINE (Background)                 │
│              Stores anonymized patterns only                │
└─────────────────────────────────────────────────────────────┘

Analysis → Embeddings → Qdrant → Future Retrieval
   │           │           │          │
   │           │           │          └─ Semantic search
   │           │           │             for similar patterns
   │           │           │
   │           │           └─ Store vector + metadata
   │           │               (NO demographics!)
   │           │
   │           └─ Generate embedding from
   │               anonymized content
   │
   └─ Epistemic assessment (already anonymized)
```

---

## Detailed Data Flow

### Phase 1: Ingestion & Sanitization

```python
class IngestionPipeline:
    """
    First stage: Strip demographics BEFORE anything else
    
    Principle: Can't leak what we never collect
    """
    
    async def ingest_content(
        self,
        raw_content: RawContentStream
    ) -> SanitizedContent:
        """
        Step 1: Receive raw content from platform
        Step 2: IMMEDIATELY sanitize (strip demographics)
        Step 3: Pass sanitized content to analysis
        
        Demographics NEVER enter the analysis pipeline!
        """
        
        # 1. Receive raw content
        # At this point, may contain:
        # - Author name, profile pic, location
        # - Demographic signals in text
        # - Platform metadata with personal info
        
        # 2. IMMEDIATE sanitization (first thing we do!)
        sanitized = await self.sanitizer.sanitize(raw_content)
        # Now contains ONLY:
        # - Content text (with demographic markers removed)
        # - Platform type (twitter/discord/etc)
        # - Domain (detected from content, not user)
        # - Timestamp
        # - Anonymous session ID (not linkable to user)
        
        # 3. Verify sanitization (double-check!)
        if not await self.verify_sanitized(sanitized):
            raise PrivacyViolation("Demographic data detected after sanitization!")
        
        # 4. Pass to analysis pipeline
        return sanitized


class ContentSanitizer:
    """
    Strip ALL demographic signals
    
    Multiple layers of protection
    """
    
    async def sanitize(
        self,
        raw: RawContentStream
    ) -> SanitizedContent:
        """
        Remove demographics at multiple levels
        """
        
        # Layer 1: Metadata stripping
        clean_metadata = {
            "platform": raw.platform,  # Keep: platform type
            "timestamp": raw.timestamp,  # Keep: when
            "content_type": raw.content_type,  # Keep: text/audio/video
            # REMOVE: author_name, author_id, location, profile, etc
        }
        
        # Layer 2: Text anonymization
        clean_text = await self._anonymize_text(raw.text)
        # Removes: "As a 65-year-old..." → "As someone with experience..."
        
        # Layer 3: Generate anonymous session ID
        session_id = self._generate_anonymous_id(
            # Hash of content + timestamp, NOT user ID!
            content=raw.text,
            timestamp=raw.timestamp
        )
        
        # Layer 4: Detect domain FROM CONTENT (not user profile!)
        domain = await self._detect_domain_from_content(clean_text)
        
        return SanitizedContent(
            content_id=session_id,  # Anonymous!
            text=clean_text,  # Demographics removed
            platform=clean_metadata["platform"],
            domain=domain,  # From content, not user
            timestamp=clean_metadata["timestamp"],
            # NO author info, NO location, NO demographics
        )
    
    async def _anonymize_text(self, text: str) -> str:
        """
        Remove demographic markers from text
        
        Uses LLM to rewrite while preserving meaning
        """
        
        prompt = f"""
Rewrite this text to remove demographic markers while preserving meaning.

Original: "{text}"

Remove mentions of:
- Age ("I'm 65" → "I have experience")
- Race/ethnicity ("As a Black person" → "From my perspective")
- Gender ("As a woman in tech" → "As someone in tech")
- Location ("In Silicon Valley" → "In a tech hub")
- Socioeconomic status ("I went to Harvard" → "I studied at a university")
- Religion, nationality, disability, etc.

Preserve:
- Domain expertise
- Experience level
- Argument content
- Evidence

Return JSON: {{"anonymized_text": "...", "markers_removed": [...]}}
"""
        
        result = await self.llm.complete(prompt)
        return result['anonymized_text']
```

---

## Phase 2: Embeddings Generation

```python
class EmbeddingService:
    """
    Generate embeddings for semantic search
    
    Critical: Embeddings generated from SANITIZED content only
    """
    
    def __init__(self, model: str = "voyage-large-2"):
        # Use state-of-art embedding model
        self.model = VoyageEmbeddings(model_name=model)
        
        # Alternatives:
        # - OpenAI text-embedding-3-large
        # - Cohere embed-english-v3.0
        # - sentence-transformers (open source)
    
    async def embed_content(
        self,
        sanitized_content: SanitizedContent
    ) -> ContentEmbedding:
        """
        Generate embedding from sanitized content
        
        Input: Already anonymized text
        Output: Vector representation (1024-4096 dims)
        
        Embeddings capture SEMANTIC meaning, not identity
        """
        
        # 1. Prepare text for embedding
        embed_text = self._prepare_for_embedding(sanitized_content)
        
        # 2. Generate embedding
        vector = await self.model.embed(embed_text)
        
        # 3. Verify no demographic leakage
        # (paranoid check: embeddings shouldn't encode demographics)
        if await self._check_demographic_leakage(vector):
            # This should never happen, but if it does...
            raise PrivacyViolation("Demographic signal detected in embedding!")
        
        return ContentEmbedding(
            content_id=sanitized_content.content_id,
            vector=vector,  # Dense vector (e.g., 1536 dims)
            model=self.model.name,
            generated_at=datetime.now()
        )
    
    def _prepare_for_embedding(
        self,
        content: SanitizedContent
    ) -> str:
        """
        Prepare text for embedding
        
        Include context that matters for semantic similarity
        """
        
        return f"""
Platform: {content.platform}
Domain: {content.domain}

Content: {content.text}

Context: This is {content.domain} content from {content.platform}.
"""
        
        # This gives embedding model context for better semantic matching
        # E.g., medical content similarity vs creative content similarity
```

---

## Phase 3: Analysis (LLM-Based)

```python
class EpistemicAnalyzer:
    """
    LLM analyzes sanitized content using Empirica framework
    
    Input: Sanitized content (no demographics)
    Output: Epistemic assessment (13 vectors + adaptive)
    """
    
    async def analyze(
        self,
        sanitized_content: SanitizedContent,
        similar_patterns: List[SimilarPattern] = None
    ) -> EpistemicAnalysis:
        """
        Main analysis using LLM + Empirica framework
        """
        
        # 1. Build epistemic prompt
        prompt = self._build_epistemic_prompt(
            content=sanitized_content,
            similar_patterns=similar_patterns
        )
        
        # 2. LLM analyzes
        llm_response = await self.llm.complete(
            prompt=prompt,
            response_format="json",
            temperature=0.1
        )
        
        # 3. Parse vectors
        vectors = self._parse_vectors(llm_response)
        
        # 4. Adaptive vectors (based on domain/platform, NOT user!)
        adaptive = await self.adaptive_system.get_vectors_for_content(
            sanitized_content
        )
        
        # 5. Assess adaptive vectors
        adaptive_scores = await self._assess_adaptive_vectors(
            content=sanitized_content,
            adaptive_vectors=adaptive
        )
        
        return EpistemicAnalysis(
            content_id=sanitized_content.content_id,
            base_vectors=vectors,  # 13 core Empirica vectors
            adaptive_vectors=adaptive_scores,  # Domain/platform specific
            confidence=self._calculate_confidence(vectors),
            uncertainty=vectors['uncertainty'],
            should_investigate=self._check_investigation_triggers(vectors),
            reasoning=llm_response.reasoning
        )
```

---

## Phase 4: Storage in Qdrant

```python
class QdrantLearningStorage:
    """
    Store epistemic patterns for future learning
    
    Critical: Store embeddings + analysis, NO demographics
    """
    
    async def store_analysis(
        self,
        sanitized_content: SanitizedContent,
        embedding: ContentEmbedding,
        analysis: EpistemicAnalysis
    ) -> str:
        """
        Store in Qdrant for semantic search
        
        What we store:
        ✅ Content embedding (vector)
        ✅ Epistemic vectors (scores)
        ✅ Domain, platform, timestamp
        ✅ Anonymous content preview (first 500 chars)
        ✅ Outcome (if known later)
        
        What we DO NOT store:
        ❌ Author demographics
        ❌ Author identity
        ❌ Linkable personal info
        """
        
        point_id = str(uuid.uuid4())
        
        # Prepare payload (metadata)
        payload = {
            # Content characteristics (not identity!)
            "domain": sanitized_content.domain,
            "platform": sanitized_content.platform,
            "content_preview": sanitized_content.text[:500],  # Truncated
            
            # Epistemic assessment
            "base_vectors": analysis.base_vectors,
            "adaptive_vectors": analysis.adaptive_vectors,
            "confidence": analysis.confidence,
            "uncertainty": analysis.uncertainty,
            "should_investigate": analysis.should_investigate,
            
            # Temporal
            "timestamp": sanitized_content.timestamp.isoformat(),
            
            # Outcome (added later when known)
            "outcome": None,  # Will be updated if outcome learned
            
            # NO DEMOGRAPHICS!
            # ❌ author_id
            # ❌ author_name
            # ❌ author_demographics
            # ❌ location
            # ❌ etc.
        }
        
        # Store in Qdrant
        await self.qdrant.upsert(
            collection_name="epistemic_patterns",
            points=[{
                "id": point_id,
                "vector": embedding.vector,  # Dense embedding
                "payload": payload
            }]
        )
        
        return point_id
```

---

## Phase 5: Retrieval (Semantic Search)

```python
class SemanticPatternRetrieval:
    """
    Find similar epistemic patterns using embeddings
    
    This is where embeddings shine!
    """
    
    async def find_similar_patterns(
        self,
        current_content: SanitizedContent,
        current_embedding: ContentEmbedding,
        limit: int = 10
    ) -> List[SimilarPattern]:
        """
        Semantic search: Find similar content + epistemic assessments
        
        Method:
        1. Use current embedding as query vector
        2. Qdrant finds nearest neighbors in vector space
        3. Return similar patterns with their assessments
        
        Result: Learn from similar past situations
        """
        
        # 1. Search Qdrant by vector similarity
        results = await self.qdrant.search(
            collection_name="epistemic_patterns",
            query_vector=current_embedding.vector,
            limit=limit,
            
            # Optional filters (content-based, not identity!)
            query_filter={
                "should": [
                    # Prefer same domain
                    {"key": "domain", "match": {"value": current_content.domain}},
                    # Prefer same platform
                    {"key": "platform", "match": {"value": current_content.platform}},
                    # Prefer completed patterns (have outcome)
                    {"key": "outcome", "match": {"any": ["success", "failure"]}}
                ]
            }
        )
        
        # 2. Convert to SimilarPattern objects
        patterns = []
        for result in results:
            patterns.append(SimilarPattern(
                content_preview=result.payload['content_preview'],
                domain=result.payload['domain'],
                platform=result.payload['platform'],
                base_vectors=result.payload['base_vectors'],
                adaptive_vectors=result.payload['adaptive_vectors'],
                confidence=result.payload['confidence'],
                outcome=result.payload.get('outcome'),
                similarity_score=result.score,  # Cosine similarity (0-1)
                timestamp=datetime.fromisoformat(result.payload['timestamp'])
            ))
        
        return patterns
    
    async def calibrate_with_history(
        self,
        current_analysis: EpistemicAnalysis,
        similar_patterns: List[SimilarPattern]
    ) -> EpistemicAnalysis:
        """
        Use similar patterns to calibrate assessment
        
        Example:
        - Current content: "Definitely going to work" (confidence 0.9)
        - Similar patterns: 5 past cases with same language
          - All had confidence 0.9
          - All had bad outcomes (failures)
        - Calibrated: Adjust down to confidence 0.4
          (Overconfidence pattern detected!)
        """
        
        # Filter to patterns with known outcomes
        with_outcomes = [p for p in similar_patterns if p.outcome]
        
        if not with_outcomes:
            return current_analysis  # No calibration data
        
        # Calculate calibration adjustment
        adjustments = []
        
        for pattern in with_outcomes:
            # Weight by similarity
            weight = pattern.similarity_score
            
            # Was original assessment accurate?
            if pattern.outcome.success:
                # Good outcome
                if pattern.confidence > 0.7:
                    # High confidence, good outcome = well calibrated
                    adjustments.append(("confirm", weight))
                else:
                    # Low confidence, good outcome = underconfident
                    adjustments.append(("increase", weight * 0.1))
            else:
                # Bad outcome
                if pattern.confidence > 0.7:
                    # High confidence, bad outcome = OVERCONFIDENT!
                    adjustments.append(("decrease", weight * 0.2))
                else:
                    # Low confidence, bad outcome = correctly cautious
                    adjustments.append(("confirm", weight))
        
        # Apply weighted adjustment
        net_adjustment = self._calculate_weighted_adjustment(adjustments)
        
        calibrated = dataclasses.replace(current_analysis)
        calibrated.confidence = max(0.0, min(1.0,
            current_analysis.confidence + net_adjustment
        ))
        calibrated.calibration_note = (
            f"Adjusted by {net_adjustment:+.2f} based on "
            f"{len(with_outcomes)} similar patterns"
        )
        
        return calibrated
```

---

## Complete Flow Example

### User tweets: "I think we should rewrite in Rust"

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Ingestion & Sanitization                           │
└─────────────────────────────────────────────────────────────┘

Raw input:
- Author: @john_smith (age 28, location: SF, profile pic...)
- Text: "I think we should rewrite our API in Rust"
- Timestamp: 2025-12-20T14:00:00Z

↓ IMMEDIATE SANITIZATION (before anything else!)

Sanitized output:
- Content ID: anon_abc123 (hash, not linkable)
- Text: "I think we should rewrite our API in Rust"
- Platform: twitter
- Domain: engineering (detected from "API", "Rust")
- Timestamp: 2025-12-20T14:00:00Z
- ❌ NO author info, NO location, NO demographics


┌─────────────────────────────────────────────────────────────┐
│ Step 2: Embedding Generation                               │
└─────────────────────────────────────────────────────────────┘

Input: Sanitized content
Model: voyage-large-2

Output: Vector embedding [1536 dims]
Example: [0.123, -0.456, 0.789, ...]

This captures SEMANTIC meaning:
- Technical discussion
- Programming language migration
- Engineering domain
- NOT: who said it!


┌─────────────────────────────────────────────────────────────┐
│ Step 3: Semantic Search (Qdrant)                           │
└─────────────────────────────────────────────────────────────┘

Query: Current embedding
Qdrant finds 10 most similar past patterns

Results:
1. "Thinking about moving to Go" (similarity: 0.92)
   - Domain: engineering, Platform: discord
   - Confidence: 0.85, Outcome: failure (scope creep)
   
2. "Should we switch to microservices?" (similarity: 0.88)
   - Domain: engineering, Platform: slack
   - Confidence: 0.9, Outcome: failure (complexity)
   
3. "Considering Kotlin" (similarity: 0.85)
   - Domain: engineering, Platform: twitter
   - Confidence: 0.7, Outcome: success (small scope)

Learning: Similar language → mixed outcomes
Pattern: High confidence without evidence → bad outcomes


┌─────────────────────────────────────────────────────────────┐
│ Step 4: LLM Analysis (Empirica Framework)                  │
└─────────────────────────────────────────────────────────────┘

Prompt to LLM:
"Analyze this content using Empirica's 13 epistemic vectors...
Context from similar patterns: [...]"

LLM Response:
{
  "base_vectors": {
    "engagement": 0.7,
    "foundation": {"know": 0.6, "do": 0.7, "context": 0.4},
    "comprehension": {"clarity": 0.5, "coherence": 0.6, ...},
    "execution": {"state": 0.3, "change": 0.4, ...},
    "uncertainty": 0.7  # "I think" = high uncertainty
  },
  "adaptive_vectors": {
    // Engineering-specific
    "technical_precision": 0.3,  # Vague ("rewrite")
    "tradeoff_awareness": 0.2,   # No cost/benefit
    "failure_mode_analysis": 0.1 # What could go wrong?
  },
  "reasoning": "High uncertainty with sparse technical detail.
                Similar patterns suggest overconfidence risk.
                Missing: current pain points, migration plan, team skills."
}


┌─────────────────────────────────────────────────────────────┐
│ Step 5: Calibration with History                           │
└─────────────────────────────────────────────────────────────┘

Initial confidence: 0.6
Similar patterns: 2 failures (high conf), 1 success (low conf)

Calibration: -0.25 (adjust down)
Final confidence: 0.35

Reasoning: "Similar confident statements about rewrites
           had poor outcomes. Recommend investigation first."


┌─────────────────────────────────────────────────────────────┐
│ Step 6: Storage (Qdrant)                                   │
└─────────────────────────────────────────────────────────────┘

Store:
- Embedding vector
- Epistemic assessment
- Domain: engineering
- Platform: twitter
- Outcome: TBD (will update when known)

❌ NOT stored: Author identity, demographics


┌─────────────────────────────────────────────────────────────┐
│ Step 7: Response to User                                   │
└─────────────────────────────────────────────────────────────┘

Bot reply:
"📊 Low confidence (35%)

Uncertainty detected: 'I think'

Missing context:
- What problems exist with current API?
- What are migration costs?
- Does team have Rust experience?

Similar patterns suggest investigating first.
Run /preflight before committing?"
```

---

## Embeddings Architecture

### Why Embeddings are Central

```
Traditional Keyword Search (Bad):
Query: "rewrite in Rust"
Matches: Only exact keyword "Rust"
Misses: "migrate to Go", "switch to Kotlin"

Semantic Search with Embeddings (Good):
Query embedding: [0.123, -0.456, ...]
Finds:
- "rewrite in Rust" (exact match)
- "migrate to Go" (similar concept)
- "switch to microservices" (similar decision pattern)
- "considering Kotlin" (similar uncertainty)

Why? Embeddings capture MEANING, not just words!
```

### Embedding Model Selection

```python
class EmbeddingModelConfig:
    """
    Choose embedding model based on requirements
    """
    
    MODELS = {
        "voyage-large-2": {
            # Best overall (as of 2024)
            "dimensions": 1536,
            "cost": "$0.12 / 1M tokens",
            "performance": "State-of-art",
            "use_case": "Production (recommended)"
        },
        
        "openai-text-embedding-3-large": {
            "dimensions": 3072,
            "cost": "$0.13 / 1M tokens",
            "performance": "Excellent",
            "use_case": "Production (alternative)"
        },
        
        "cohere-embed-english-v3": {
            "dimensions": 1024,
            "cost": "$0.10 / 1M tokens",
            "performance": "Very good",
            "use_case": "Cost-optimized production"
        },
        
        "all-MiniLM-L6-v2": {
            # Open source (sentence-transformers)
            "dimensions": 384,
            "cost": "$0 (self-hosted)",
            "performance": "Good",
            "use_case": "Free tier / development"
        }
    }
```

---

## Privacy Guarantees

### What We Collect

```
✅ Content characteristics:
- Sanitized text (demographics removed)
- Platform type
- Domain (from content, not user)
- Timestamp
- Epistemic assessment

✅ Learning data:
- Embeddings (semantic meaning)
- Epistemic patterns
- Outcomes (if learned)

❌ Never collected:
- Author identity
- Demographics (age, race, gender, etc)
- Personal information
- Linkable user data
```

### Verification

```python
class PrivacyAuditor:
    """
    Verify no demographic data in pipeline
    
    Runs automatically on every analysis
    """
    
    async def audit_pipeline(
        self,
        content: Any,
        stage: str
    ) -> AuditResult:
        """
        Check for demographic leakage at each stage
        """
        
        violations = []
        
        # Check for protected attributes
        for attr in PROTECTED_ATTRIBUTES:
            if self._contains_attribute(content, attr):
                violations.append(f"Found {attr} at stage {stage}")
        
        # Check for proxy attributes
        for proxy in PROXY_ATTRIBUTES:
            if self._contains_proxy(content, proxy):
                violations.append(f"Found proxy {proxy} at stage {stage}")
        
        if violations:
            # CRITICAL: Halt processing!
            raise PrivacyViolation(
                stage=stage,
                violations=violations,
                content_id=content.content_id
            )
        
        return AuditResult(
            stage=stage,
            violations=None,
            timestamp=datetime.now()
        )
```

---

## The Bottom Line

### Your Questions Answered

**Q1: "Do we collect then strip demographics?"**
**A1:** NO! We strip BEFORE collection. Can't leak what we never see.

**Q2: "Do I see an embeddings service?"**
**A2:** YES! Embeddings are central to:
- Semantic search (find similar patterns)
- Learning (store in Qdrant)
- Calibration (adjust based on history)

### Data Flow Summary

```
1. INGESTION: Raw content → IMMEDIATE sanitization
2. EMBEDDINGS: Sanitized text → Vector representation
3. SEARCH: Query Qdrant for similar patterns
4. ANALYSIS: LLM assesses using Empirica framework
5. CALIBRATION: Adjust based on similar outcomes
6. STORAGE: Store embedding + assessment (no demographics!)
7. RESPONSE: Return to user
```

### Privacy by Design

```
Strip demographics → Generate embeddings → Store in Qdrant
       ↑                     ↑                    ↑
   First step!        Semantic meaning       No identity!
```

---

**This is privacy-preserving semantic learning.** 🔒🧠

Ready to implement the embedding pipeline? 🚀

