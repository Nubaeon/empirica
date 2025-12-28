# Skill Extractor Implementation Guide
# For local Claude/AI to build the extraction tool

## What This Does

Converts verbose skill `references/` files into concise YAML config for epistemic bootstrap cards.

**Example:**
- Input: `~/.claude/skills/astro-islands/references/patterns.md` (5kb)
- Output: `meta-agent-config.yaml` entry for astro-islands domain (0.6kb)
- Reduction: 88% fewer tokens

## Why This Matters

Per Anthropic's skill-creator, skills use progressive disclosure:
1. Metadata (always loaded)
2. SKILL.md (when triggered)
3. `references/` (loaded as needed)

**Problem:** Loading full `references/` is expensive (5-10kb per domain).

**Solution:** Extract decision frameworks once → store in `meta-agent-config.yaml` → load via bootstrap cards (0.5-1kb per domain).

## What to Extract

From skill `references/` files, extract:

### 1. Decision Frameworks
```markdown
## When to Use Islands
- Component needs interactivity
- Requires state management
```
→ Extract to:
```yaml
decision_frameworks:
  when_to_use:
    - "Component needs interactivity"
    - "Requires state management"
```

### 2. Anti-Patterns
```markdown
## Common Mistakes
- Islands for forms: 40kb vs 6kb progressive enhancement
```
→ Extract to:
```yaml
anti_patterns:
  - id: "islands-forms"
    cost: "40kb vs 6kb"
    alternative: "Progressive enhancement"
```

### 3. Cost Models
```markdown
## Performance
- Typical island: 30-50kb
- Rule: 5x value over cost
```
→ Extract to:
```yaml
cost_models:
  typical_island: "30-50kb"
  decision_rule: "5x value over cost"
```

### 4. Doc References
```markdown
See docs/astro/islands.md#hydration
```
→ Extract to:
```yaml
references:
  primary: "docs/astro/islands.md"
  sections: ["hydration"]
```

## Implementation Steps

### Step 1: Setup

```bash
# Create project structure
mkdir skill-extractor
cd skill-extractor

# Create Python script
touch skill_extractor.py
chmod +x skill_extractor.py

# Install dependencies
pip install PyYAML --break-system-packages
```

### Step 2: Core Extraction Logic

```python
#!/usr/bin/env python3
"""
Extract decision frameworks from skill references/ to meta-agent-config.yaml
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any

class SkillExtractor:
    def __init__(self, skill_dir: Path):
        self.skill_dir = Path(skill_dir)
        self.references_dir = self.skill_dir / "references"
    
    def extract(self) -> Dict[str, Any]:
        """Extract decision frameworks from all reference files"""
        domain = self.skill_dir.name
        domain_knowledge = {
            'decision_frameworks': {},
            'anti_patterns': [],
            'cost_models': {},
            'references': {}
        }
        
        # Process all markdown files in references/
        for ref_file in self.references_dir.glob("*.md"):
            content = ref_file.read_text()
            
            # Extract decision frameworks
            when_to_use = self._extract_section(content, r"## When to [Uu]se")
            if when_to_use:
                domain_knowledge['decision_frameworks']['when_to_use'] = when_to_use
            
            when_not_to = self._extract_section(content, r"## When NOT to [Uu]se")
            if when_not_to:
                domain_knowledge['decision_frameworks']['when_not_to_use'] = when_not_to
            
            # Extract anti-patterns
            anti_patterns = self._extract_anti_patterns(content)
            domain_knowledge['anti_patterns'].extend(anti_patterns)
            
            # Extract cost models
            costs = self._extract_costs(content)
            domain_knowledge['cost_models'].update(costs)
            
            # Extract doc references
            refs = self._extract_references(content)
            domain_knowledge['references'].update(refs)
        
        return {domain: domain_knowledge}
    
    def _extract_section(self, content: str, header_pattern: str) -> List[str]:
        """Extract bullet points from a section"""
        match = re.search(f"{header_pattern}(.*?)(?=##|$)", content, re.DOTALL)
        if not match:
            return []
        
        section = match.group(1)
        # Extract bullet points
        bullets = re.findall(r"^[-*]\s+(.+)$", section, re.MULTILINE)
        return [b.strip() for b in bullets if b.strip()]
    
    def _extract_anti_patterns(self, content: str) -> List[Dict]:
        """Extract anti-patterns from Common Mistakes, Anti-patterns sections"""
        patterns = []
        
        # Find anti-pattern sections
        for header in [r"## Common [Mm]istakes?", r"## Anti-[Pp]atterns?", r"## [Pp]itfalls?"]:
            match = re.search(f"{header}(.*?)(?=##|$)", content, re.DOTALL)
            if not match:
                continue
            
            section = match.group(1)
            # Extract patterns (format: "X: Y" or "- X (Y)")
            for line in section.split('\n'):
                line = line.strip()
                if not line or not line.startswith(('-', '*')):
                    continue
                
                # Remove bullet
                line = re.sub(r"^[-*]\s+", "", line)
                
                # Try to parse "description: cost/reason"
                if ':' in line:
                    parts = line.split(':', 1)
                    desc = parts[0].strip()
                    detail = parts[1].strip()
                    
                    pattern = {
                        'id': self._make_id(desc),
                        'description': desc
                    }
                    
                    # Check if detail contains cost (kb, ms, etc)
                    if re.search(r'\d+\s*(kb|ms|MB|%)', detail, re.IGNORECASE):
                        pattern['cost'] = detail
                    else:
                        pattern['reason'] = detail
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _extract_costs(self, content: str) -> Dict[str, str]:
        """Extract performance costs"""
        costs = {}
        
        for header in [r"## Performance", r"## Cost", r"## Bundle [Ss]ize"]:
            match = re.search(f"{header}(.*?)(?=##|$)", content, re.DOTALL)
            if not match:
                continue
            
            section = match.group(1)
            # Extract patterns like "X: Nkb" or "X costs Nkb"
            for line in section.split('\n'):
                # Match "typical island: 30-50kb"
                cost_match = re.search(r"(.+?):\s*(\d+[-\d]*\s*kb)", line, re.IGNORECASE)
                if cost_match:
                    key = self._make_id(cost_match.group(1))
                    costs[key] = cost_match.group(2).strip()
                
                # Match "Rule: X" for decision rules
                rule_match = re.search(r"[Rr]ule:\s*(.+)$", line)
                if rule_match:
                    costs['decision_rule'] = rule_match.group(1).strip()
        
        return costs
    
    def _extract_references(self, content: str) -> Dict[str, Any]:
        """Extract doc references"""
        refs = {}
        
        # Find references section
        match = re.search(r"## References?(.*?)(?=##|$)", content, re.DOTALL)
        if not match:
            # Also look for inline references
            doc_matches = re.findall(r"[Ss]ee (docs/[\w/.-]+)(?:#([\w-]+))?", content)
            if doc_matches:
                refs['primary'] = doc_matches[0][0]
                if doc_matches[0][1]:
                    refs['sections'] = [doc_matches[0][1]]
            return refs
        
        section = match.group(1)
        
        # Extract doc paths
        doc_matches = re.findall(r"(docs/[\w/.-]+)(?:#([\w-]+))?", section)
        if doc_matches:
            refs['primary'] = doc_matches[0][0]
            sections = [m[1] for m in doc_matches if m[1]]
            if sections:
                refs['sections'] = sections
        
        return refs
    
    def _make_id(self, text: str) -> str:
        """Convert text to ID (lowercase, hyphens)"""
        return re.sub(r'\s+', '-', text.lower().strip())

def extract_all_skills(skills_dir: Path, output_file: Path):
    """Extract all skills to meta-agent-config.yaml"""
    config = {
        'meta_agent': {
            'epistemic_thresholds': {
                'bootstrap_trigger': [
                    {'condition': 'context < 0.5'},
                    {'condition': 'uncertainty > 0.6'}
                ]
            },
            'domain_knowledge': {}
        }
    }
    
    # Process each skill
    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue
        
        references_dir = skill_path / "references"
        if not references_dir.exists():
            continue
        
        print(f"Extracting {skill_path.name}...")
        extractor = SkillExtractor(skill_path)
        domain_data = extractor.extract()
        config['meta_agent']['domain_knowledge'].update(domain_data)
    
    # Write output
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"\nExtracted to {output_file}")
    
    # Show stats
    total_domains = len(config['meta_agent']['domain_knowledge'])
    print(f"Domains: {total_domains}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: skill_extractor.py <skills-dir> <output-yaml>")
        print("Example: skill_extractor.py ~/.claude/skills meta-agent-config.yaml")
        sys.exit(1)
    
    skills_dir = Path(sys.argv[1]).expanduser()
    output_file = Path(sys.argv[2])
    
    extract_all_skills(skills_dir, output_file)
```

### Step 3: Test

```bash
# Run extraction
python skill_extractor.py ~/.claude/skills meta-agent-config.yaml

# Validate output
python -c "import yaml; yaml.safe_load(open('meta-agent-config.yaml'))"

# Check token reduction
echo "Original: $(find ~/.claude/skills -name '*.md' -exec wc -c {} + | tail -1 | awk '{print $1}') bytes"
echo "Extracted: $(wc -c meta-agent-config.yaml | awk '{print $1}') bytes"
```

### Step 4: Integration with Bootstrap

The extracted `meta-agent-config.yaml` is used by bootstrap to construct reference cards:

```python
# In bootstrap MCP server
def construct_reference_card(domain, tags):
    # Load meta-agent-config.yaml
    config = yaml.safe_load(open('meta-agent-config.yaml'))
    
    # Get domain knowledge
    domain_knowledge = config['meta_agent']['domain_knowledge'].get(domain, {})
    
    # Get noematic objects from Qdrant
    noematic_objects = query_qdrant(tags)
    
    # Construct card
    card = {
        'domain': domain,
        'decision_frameworks': domain_knowledge.get('decision_frameworks', {}),
        'anti_patterns': domain_knowledge.get('anti_patterns', []),
        'past_learnings': noematic_objects,
        'references': domain_knowledge.get('references', {})
    }
    
    return card  # ~1-2kb total
```

## Expected Output Format

```yaml
meta_agent:
  epistemic_thresholds:
    bootstrap_trigger:
      - condition: "context < 0.5"
      - condition: "uncertainty > 0.6"
  
  domain_knowledge:
    astro-islands:
      decision_frameworks:
        when_to_use:
          - "Component needs interactivity"
          - "Requires state management"
        when_not_to_use:
          - "Static content → server-side"
          - "Simple forms → progressive enhancement"
      
      anti_patterns:
        - id: "islands-forms"
          description: "Islands for forms"
          cost: "40kb vs 6kb"
          alternative: "Progressive enhancement"
      
      cost_models:
        typical_island: "30-50kb"
        decision_rule: "5x value over cost"
      
      references:
        primary: "docs/astro/islands.md"
        sections: ["hydration"]
    
    performance:
      decision_frameworks:
        when_to_use:
          - "Every feature justifies bundle cost"
      
      cost_models:
        target_js: "<50kb"
        target_tti: "<3s on 3G"
      
      references:
        primary: "docs/performance/budgets.md"
```

## Token Economics

| Approach | Tokens per Domain | 3 Domains | 10 Domains |
|----------|-------------------|-----------|------------|
| Load full `references/` | 5-10kb | 15-30kb | 50-100kb |
| Load extracted YAML via bootstrap | 0.5-1kb | 1.5-3kb | 5-10kb |
| **Reduction** | **80-90%** | **80-90%** | **80-90%** |

## Next Steps

1. **Build:** Implement `skill_extractor.py` as shown above
2. **Extract:** Run on your `~/.claude/skills` directory
3. **Validate:** Check output YAML structure and token reduction
4. **Integrate:** Update bootstrap MCP server to use extracted config
5. **Test:** Verify bootstrap cards construct properly with extracted knowledge

## Questions to Address During Implementation

1. **What if a skill has no `references/` directory?**
   - Skip it, no extraction needed

2. **What if decision frameworks aren't clearly marked?**
   - Use fuzzy matching for headers, extract bullet points anyway

3. **What about skills with multiple reference files?**
   - Extract from all, merge into single domain entry

4. **How to handle conflicts when merging?**
   - Last-write-wins, or manual review

5. **How often to re-extract?**
   - When skills update, or on-demand via `--force` flag
