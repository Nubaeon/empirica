# Empirica Website Visual Assets

**Purpose:** Central directory for SVG icons, diagrams, screenshots, videos, podcasts, and other media used on the website.

**Status:** Directory structure created, assets ready to be added.

---

## Directory Structure

```
assets/
├── icons/             # SVG icons (7 icons needed)
├── diagrams/          # SVG flowcharts and visualizations (5 diagrams needed)
├── screenshots/       # PNG screenshots of CLI/MCP tools in action (5+ needed)
├── videos/            # MP4 screencasts (4 videos needed)
├── podcasts/          # MP3 audio (NotebookLM recordings, 3 podcasts needed)
└── videocasts/        # MP4 talking head + screen (3 videocasts needed)
```

---

## Icons Needed (7 total)

**Location:** `/icons/`
**Format:** SVG (preferred) or high-res PNG (2x retina)
**Status:** Not started

### Core Icons (3 - Used on Homepage)

1. **brain-vectors.svg** - Brain with measurement lines/vectors
   - Location: Homepage "Genuine Self-Assessment" card
   - Concept: Epistemic measurement visualization
   - Source: Create custom or use heroicons.com brain icon + modify

2. **git-memory.svg** - Git branch with epistemic state nodes
   - Location: Homepage "Multi-Session Memory" card
   - Concept: Making Git sexy - version control of epistemic states
   - Source: Create custom - git branch shape with circular nodes

3. **ecosystem.svg** - Network/ecosystem with multiple provider nodes
   - Location: Homepage "Provider Agnostic" card + Provider section
   - Concept: Multiple AI providers, IDEs, models interconnected
   - Source: Create custom or adapt from Unsplash networks

### Cognitive Vault Icons (4 - Used in Teaser Section)

4. **bayesian-guardian.svg** - Shield with probability distribution
   - Location: Cognitive Vault teaser section
   - Concept: Evidence-based belief tracking
   - Source: Create custom shield + Gaussian curve overlay

5. **sentinel.svg** - Eye with monitoring waves
   - Location: Cognitive Vault teaser section
   - Concept: Behavioral monitoring and drift detection
   - Source: Create custom eye + wave patterns

6. **augie.svg** - Connected nodes (collaboration)
   - Location: Cognitive Vault teaser section
   - Concept: AUGIE - Adaptive Uncertainty Grounded Intelligence Engine
   - Source: Create custom multi-node network graph

7. **meta-mcp.svg** - Router with epistemic states
   - Location: Cognitive Vault teaser section
   - Concept: Meta-MCP routing based on epistemic state
   - Source: Create custom router icon + state indicators

---

## Diagrams Needed (5 total)

**Location:** `/diagrams/`
**Format:** SVG (preferred) or high-res PNG
**Status:** Not started

1. **cascade-workflow.svg** (PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT)
   - Location: Homepage "CASCADE Workflow" section + Features page
   - Size: Horizontal flowchart, ~800x300px
   - Style: 7 boxes with arrows, gradient blue→purple→green
   - Detail: Include phase names + brief descriptions
   - Source: Create custom in Figma/Draw.io

2. **13-vectors-radial.svg** (Epistemic vector visualization)
   - Location: Homepage "13 Epistemic Vectors" section + Epistemics page
   - Size: Radial diagram or grouped bars, ~600x600px
   - Style: Color-coded by tier, size represents weight
   - Detail: Gate (ENGAGEMENT), Foundation (35%), Comprehension (25%), Execution (25%), Meta (UNCERTAINTY, CALIBRATION)
   - Source: Create custom - consider Figma or D3.js

3. **delta-learning.svg** (PREFLIGHT vs POSTFLIGHT comparison)
   - Location: Homepage "Delta Learning Measurement" section
   - Size: Before/After comparison, ~800x300px
   - Style: Progress bars with gradient, green for positive, blue for reduction
   - Detail: Show KNOW and UNCERTAINTY deltas
   - Source: Create custom, could animate for video

4. **architecture-overview.svg** (System architecture 3-layer)
   - Location: Developers architecture page + Homepage overview
   - Size: Vertical stack, ~700x600px
   - Style: 4 stacked boxes (Integration Layer, CASCADE Engine, Persistence, Continuity)
   - Detail: Show data flow between layers
   - Source: Create custom in Draw.io or Figma

5. **ecosystem.svg** (Provider/IDE/Model network)
   - Location: Provider Agnostic section + Mcp-integration page
   - Size: Network graph, ~800x400px
   - Style: Central Empirica node with 3 branches (IDEs, CLIs, Models)
   - Detail: List providers under each branch
   - Source: Create custom or adapt GitHub's ecosystem diagrams

---

## Screenshots Needed (5+ total)

**Location:** `/screenshots/`
**Format:** PNG high-res (2x retina, ~1200x800px minimum)
**Status:** Not started

1. **tmux-dashboard.png** - Empirica CASCADE phases in real-time
   - Location: Features page
   - Content: Real tmux session showing PREFLIGHT → INVESTIGATE → CHECK phases
   - Capture: During actual task execution
   - File: 2MB max (optimize with compression)

2. **mcp-cursor.png** - Cursor IDE showing MCP tools
   - Location: MCP integration page
   - Content: Tools dropdown with 23 Empirica tools visible
   - Capture: Clear list view of available MCP tools
   - File: 1.5MB max

3. **mcp-windsurf.png** - Windsurf IDE showing MCP integration
   - Location: MCP integration page
   - Content: Similar to Cursor, showing Windsurf interface
   - File: 1.5MB max

4. **cli-bootstrap.png** - Terminal showing `empirica bootstrap` output
   - Location: Getting started page
   - Content: Real terminal output with formatted ASCII art
   - File: 1MB max

5. **vectors-assessment.png** - 13-vector assessment output
   - Location: Epistemics page
   - Content: Actual vector values from a real assessment
   - File: 1.5MB max

**Additional useful screenshots:**
- `mcp-claude-desktop.png` - Claude Desktop showing MCP tools
- `goal-tracking.png` - Goal creation and subtask management
- `handoff-report.png` - Example handoff report output

---

## Videos Needed (4 total)

**Location:** `/videos/`
**Format:** MP4 H.264 (preferably <5MB)
**Status:** Not started

1. **quickstart-30sec.mp4** (30-second quick start)
   - Location: Homepage (top section)
   - Content: Adding MCP config → restart → tools available
   - Duration: 30 seconds
   - Quality: Clear screen recording + optional voiceover
   - Compression: Optimize for web

2. **cascade-demo.mp4** (Complete CASCADE workflow)
   - Location: Features page
   - Content: Real task from PREFLIGHT → POSTFLIGHT
   - Duration: 2-3 minutes
   - Quality: Screen capture of actual session
   - Detail: Show vector changes, phase transitions

3. **provider-comparison.mp4** (Same task, different models)
   - Location: Homepage Provider section
   - Content: Claude 3.5 vs GPT-4 vs Qwen-3-32B on same task
   - Duration: 90 seconds
   - Quality: Side-by-side comparison view
   - Detail: Show how smaller models benefit from structure

4. **multi-session.mp4** (3-day multi-AI development)
   - Location: Use cases page
   - Content: Day 1 start → Day 2 resume → Day 3 complete
   - Duration: 2 minutes
   - Quality: Show context preservation across sessions
   - Detail: Demonstrate handoff mechanism

---

## Podcasts Needed (3 total - NotebookLM)

**Location:** `/podcasts/`
**Format:** MP3 high-quality (128kbps minimum)
**Status:** Not started

1. **epistemic-intro.mp3** ("What is Epistemic Self-Awareness?")
   - Duration: 5 minutes
   - Topic: Accessibility intro to epistemics for non-technical users
   - Embedding: Homepage or Features page
   - Creation: NotebookLM from epistemics_VALIDATED.md

2. **git-sexy.mp3** ("Making Git Sexy Again")
   - Duration: 7 minutes
   - Topic: Deep dive into why Git as epistemic infrastructure
   - Embedding: Collaboration or Architecture pages
   - Creation: NotebookLM from MAKING_GIT_SEXY_AGAIN.md

3. **provider-agnostic.mp3** ("Provider Agnostic AI Infrastructure")
   - Duration: 6 minutes
   - Topic: Why Empirica works everywhere, shines with small models
   - Embedding: Provider section on homepage
   - Creation: NotebookLM from index.md + features.md

---

## Videocasts Needed (3 total - Talking Head + Screen)

**Location:** `/videocasts/`
**Format:** MP4 H.264 (1280x720 minimum)
**Status:** Not started

1. **empirica-5min.mp4** ("Empirica in 5 Minutes")
   - Location: Homepage
   - Duration: 5 minutes
   - Content: Problem overview → CASCADE intro → quick demo
   - Style: Talking head + screen sharing
   - Detail: Keep punchy, focus on aha moment

2. **cascade-explained.mp4** ("The CASCADE Workflow Explained")
   - Location: Architecture page
   - Duration: 10 minutes
   - Content: Deep dive into each of 7 phases
   - Style: Screen recording + annotations
   - Detail: Show real output from each phase

3. **smaller-models.mp4** ("Building with Smaller Models")
   - Location: Use cases page
   - Duration: 8 minutes
   - Content: Qwen-3-32B, Phi-4, Mistral with Empirica
   - Style: Live demos + comparison to GPT-4
   - Detail: Prove smaller models can compete with guidance

---

## Creative Commons Image Sources

**For free images/icons, use:**

1. **unDraw.co** - Open source illustrations (MIT license)
   - Search: "thinking", "mirror", "network", "structure"
   - Good for: Hero images, abstract concepts

2. **Heroicons** - MIT licensed icon set
   - npm install @heroicons/react
   - Good for: Simple SVG icons

3. **Unsplash** - Free photos (Unsplash License)
   - Search: "technology", "network", "abstract"
   - Good for: Backgrounds, section dividers

4. **Pexels** - Free photos (Pexels License)
   - Similar to Unsplash, more tech content
   - Good for: Tech-specific imagery

5. **Pixabay** - Free (Pixabay License)
   - Search: "AI", "technology", "network"

---

## Design Guidelines

### Color Scheme
- **Primary Gradient:** Indigo → Purple → Blue (CASCADE workflow)
- **Accent:** Green (positive, completion), Red (error, risk)
- **Backgrounds:** Indigo with subtle gradients
- **Text:** High contrast (white on indigo, dark on light)

### Typography
- **Headers:** Sans-serif (use website's primary font)
- **Body:** Same sans-serif, 16px+ for readability
- **Code:** Monospace (if showing terminal output)

### Dark Mode
- All diagrams should work in dark mode
- SVGs preferred over PNGs for better dark mode rendering
- Test with CSS filters if needed

### Accessibility
- All images must have alt text
- Color should not be only way to distinguish elements
- Icons should be clearly labeled
- Videos should have captions

---

## Implementation Priority

### Phase 1 (Critical for launch - November 2025)
- [ ] brain-vectors.svg (Homepage)
- [ ] git-memory.svg (Homepage)
- [ ] ecosystem.svg (Homepage + Provider section)
- [ ] cascade-workflow.svg (Homepage + Features)
- [ ] quickstart-30sec.mp4 (Homepage)
- [ ] mcp-cursor.png (MCP integration)
- [ ] mcp-windsurf.png (MCP integration)

### Phase 2 (Enhance understanding - Early Q1 2026)
- [ ] 13-vectors-radial.svg (Epistemics page)
- [ ] delta-learning.svg (Homepage)
- [ ] architecture-overview.svg (Developers page)
- [ ] tmux-dashboard.png (Features)
- [ ] epistemic-intro.mp3 (Homepage)
- [ ] git-sexy.mp3 (Collaboration)
- [ ] cascade-explained.mp4 (Architecture)

### Phase 3 (Complete experience - Q1 2026)
- [ ] provider-comparison.mp4
- [ ] smaller-models.mp4
- [ ] Cognitive Vault icons (4x)
- [ ] Additional screenshots
- [ ] NotebookLM podcasts (complete set)
- [ ] Videocasts (complete set)

---

## Notes for Asset Creator

- **SVGs preferred** - They scale infinitely, smaller file size, work in dark mode
- **Consistency** - Use same color scheme, font, icon style across all assets
- **Performance** - Optimize images (ImageOptim, TinyPNG)
- **Retina-ready** - Screenshots should be 2x resolution
- **Testing** - Check rendering on light AND dark mode
- **Attribution** - If using Creative Commons sources, include attribution in comments
- **Version control** - Consider storing as SVG text (diffs show what changed)

---

**Status:** ✅ Directory structure ready, visual content plan complete
**Next step:** Create assets according to priority phases
**Contact:** See website contact.md for questions
