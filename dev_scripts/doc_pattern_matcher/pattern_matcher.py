#!/usr/bin/env python3
"""
Pattern Matcher - Match code, docs, and database patterns

Recursively matches at 4 levels:
1. Surface: Name matching (exact/fuzzy)
2. Structural: Call chains, workflows
3. Semantic: Concepts, purpose
4. Dependency: Import/topic graphs

Output: alignment_matrix.json, gaps.json
"""

import json
import difflib
from pathlib import Path
from typing import Dict, List, Set, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Match:
    code_entity: str
    doc_reference: str
    match_type: str  # exact, fuzzy, semantic, structural
    confidence: float  # 0.0-1.0


@dataclass
class Gap:
    entity: str
    gap_type: str  # code_orphan, doc_orphan, stale_example, missing_workflow, db_mismatch
    details: str
    severity: str  # critical, high, medium, low


class PatternMatcher:
    def __init__(self, code_patterns: Dict, doc_patterns: Dict, db_patterns: Dict):
        self.code = code_patterns
        self.docs = doc_patterns
        self.db = db_patterns
        
        self.matches: List[Match] = []
        self.gaps: List[Gap] = []
        
    def match_all(self) -> Dict[str, Any]:
        """Perform all matching levels"""
        print("🔗 Matching patterns...")
        
        # Level 1: Surface matching
        print("  Level 1: Surface patterns (names)...")
        self._match_surface()
        
        # Level 2: Structural matching
        print("  Level 2: Structural patterns (workflows)...")
        self._match_structural()
        
        # Level 3: Semantic matching
        print("  Level 3: Semantic patterns (concepts)...")
        self._match_semantic()
        
        # Level 4: Database matching
        print("  Level 4: Database patterns (schema)...")
        self._match_database()
        
        # Detect gaps
        print("  Detecting gaps...")
        self._detect_gaps()
        
        print(f"✅ Found {len(self.matches)} matches, {len(self.gaps)} gaps")
        
        return {
            "matches": [asdict(m) for m in self.matches],
            "gaps": [asdict(g) for g in self.gaps],
            "summary": self._generate_summary()
        }
    
    def _match_surface(self):
        """Level 1: Match function/class names with doc mentions"""
        # Build doc mention index
        doc_mentions = {}
        for mention in self.docs.get("function_mentions", []):
            name = mention["name"]
            if name not in doc_mentions:
                doc_mentions[name] = []
            doc_mentions[name].append(mention)
        
        # Match functions
        for func_key, func in self.code.get("functions", {}).items():
            func_name = func["name"]
            
            # Exact match
            if func_name in doc_mentions:
                for mention in doc_mentions[func_name]:
                    self.matches.append(Match(
                        code_entity=func_key,
                        doc_reference=f"{mention['doc_path']}:{mention['line_number']}",
                        match_type="exact",
                        confidence=1.0
                    ))
            else:
                # Try fuzzy match
                close_matches = difflib.get_close_matches(
                    func_name, doc_mentions.keys(), n=1, cutoff=0.8
                )
                if close_matches:
                    for mention in doc_mentions[close_matches[0]]:
                        self.matches.append(Match(
                            code_entity=func_key,
                            doc_reference=f"{mention['doc_path']}:{mention['line_number']}",
                            match_type="fuzzy",
                            confidence=0.8
                        ))
        
        # Match classes (same logic)
        for class_key, cls in self.code.get("classes", {}).items():
            class_name = cls["name"]
            
            if class_name in doc_mentions:
                for mention in doc_mentions[class_name]:
                    self.matches.append(Match(
                        code_entity=class_key,
                        doc_reference=f"{mention['doc_path']}:{mention['line_number']}",
                        match_type="exact",
                        confidence=1.0
                    ))
    
    def _match_structural(self):
        """Level 2: Match call chains with workflow steps"""
        # Build workflow index
        workflow_steps = {}
        for workflow in self.docs.get("workflows", []):
            for step in workflow["steps"]:
                step_lower = step.lower()
                if step_lower not in workflow_steps:
                    workflow_steps[step_lower] = []
                workflow_steps[step_lower].append(workflow)
        
        # Check if function call chains match workflow sequences
        call_graph = self.code.get("call_graph", {})
        
        for func_key, calls in call_graph.items():
            # For each function, see if its calls match workflow steps
            for call in calls:
                call_lower = call.lower()
                if call_lower in workflow_steps:
                    for workflow in workflow_steps[call_lower]:
                        self.matches.append(Match(
                            code_entity=func_key,
                            doc_reference=f"{workflow['doc_path']} (workflow: {workflow['name']})",
                            match_type="structural",
                            confidence=0.7
                        ))
    
    def _match_semantic(self):
        """Level 3: Match concepts (CASCADE, goals, etc.)"""
        # Common Empirica concepts
        concepts = {
            "cascade": ["preflight", "check", "act", "postflight"],
            "goals": ["objective", "subtask", "scope", "completion"],
            "epistemic": ["vectors", "uncertainty", "confidence", "calibration"],
            "continuity": ["checkpoint", "handoff", "resume", "breadcrumbs"],
        }
        
        # Check if code modules implement concepts mentioned in docs
        for concept, keywords in concepts.items():
            # Find code with concept keywords
            code_entities = set()
            for func_key, func in self.code.get("functions", {}).items():
                module_lower = func["module"].lower()
                name_lower = func["name"].lower()
                doc_lower = func["docstring"].lower()
                
                if any(kw in module_lower or kw in name_lower or kw in doc_lower 
                       for kw in keywords):
                    code_entities.add(func_key)
            
            # Find docs with concept keywords
            doc_refs = set()
            for heading in self.docs.get("headings", []):
                text_lower = heading["text"].lower()
                if any(kw in text_lower for kw in keywords):
                    doc_refs.add(f"{heading['doc_path']}:{heading['line_number']}")
            
            # Create matches
            if code_entities and doc_refs:
                for code_entity in code_entities:
                    for doc_ref in doc_refs:
                        self.matches.append(Match(
                            code_entity=code_entity,
                            doc_reference=doc_ref,
                            match_type="semantic",
                            confidence=0.6
                        ))
    
    def _match_database(self):
        """Level 4: Match code DB models with actual DB schema"""
        code_tables = self.code.get("db_tables", {})
        db_tables = self.db.get("tables", {})
        
        for table_name, code_table in code_tables.items():
            if table_name in db_tables:
                db_table = db_tables[table_name]
                
                # Compare columns
                code_cols = {col["name"] for col in code_table["columns"]}
                db_cols = {col["name"] for col in db_table["columns"]}
                
                if code_cols == db_cols:
                    self.matches.append(Match(
                        code_entity=f"table:{table_name}",
                        doc_reference=f"db:{table_name}",
                        match_type="exact",
                        confidence=1.0
                    ))
                else:
                    # Mismatch
                    missing_in_db = code_cols - db_cols
                    missing_in_code = db_cols - code_cols
                    
                    if missing_in_db or missing_in_code:
                        self.gaps.append(Gap(
                            entity=f"table:{table_name}",
                            gap_type="db_mismatch",
                            details=f"Missing in DB: {missing_in_db}, Missing in code: {missing_in_code}",
                            severity="high"
                        ))
    
    def _detect_gaps(self):
        """Detect orphaned code, docs, and stale examples"""
        # Find code orphans (code with no doc matches)
        matched_code = {m.code_entity for m in self.matches}
        
        all_code = set()
        all_code.update(self.code.get("functions", {}).keys())
        all_code.update(self.code.get("classes", {}).keys())
        
        code_orphans = all_code - matched_code
        
        for orphan in code_orphans:
            # Skip private/internal functions
            if orphan.split(".")[-1].startswith("_"):
                continue
            
            # Skip test functions
            if "test" in orphan.lower():
                continue
            
            self.gaps.append(Gap(
                entity=orphan,
                gap_type="code_orphan",
                details="No documentation found",
                severity="medium"
            ))
        
        # Find doc orphans (doc mentions with no code)
        all_functions = set(self.code.get("functions", {}).keys())
        all_classes = set(self.code.get("classes", {}).keys())
        
        for mention in self.docs.get("function_mentions", []):
            name = mention["name"]
            # Check if this name exists in code
            found = any(name in key for key in all_functions | all_classes)
            
            if not found:
                # Skip common words
                if name.lower() in {"if", "for", "while", "def", "class", "return"}:
                    continue
                
                self.gaps.append(Gap(
                    entity=f"{mention['doc_path']}:{mention['line_number']}",
                    gap_type="doc_orphan",
                    details=f"Mentions '{name}' which doesn't exist in code",
                    severity="low"
                ))
        
        # Check stale CLI commands
        code_commands = set(self.code.get("cli_commands", {}).keys())
        
        for cmd in self.docs.get("commands", []):
            # Extract command name from "empirica command-name ..."
            parts = cmd["command"].split()
            if len(parts) >= 2 and parts[0] == "empirica":
                cmd_name = parts[1].replace("-", "_")
                
                if cmd_name not in code_commands:
                    self.gaps.append(Gap(
                        entity=f"{cmd['doc_path']}:{cmd['line_number']}",
                        gap_type="stale_example",
                        details=f"CLI command '{cmd['command']}' doesn't exist",
                        severity="high"
                    ))
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        # Count gap types
        gap_counts = defaultdict(int)
        for gap in self.gaps:
            gap_counts[gap.gap_type] += 1
        
        # Count match types
        match_counts = defaultdict(int)
        for match in self.matches:
            match_counts[match.match_type] += 1
        
        return {
            "total_matches": len(self.matches),
            "match_breakdown": dict(match_counts),
            "total_gaps": len(self.gaps),
            "gap_breakdown": dict(gap_counts),
            "code_coverage": len(self.matches) / max(
                len(self.code.get("functions", {})) + len(self.code.get("classes", {})), 1
            )
        }


def main():
    root_dir = Path("/home/yogapad/empirical-ai/empirica")
    output_dir = root_dir / "dev_scripts/doc_pattern_matcher"
    
    # Load patterns
    print("📂 Loading patterns...")
    with open(output_dir / "code_patterns.json") as f:
        code_patterns = json.load(f)
    
    with open(output_dir / "doc_patterns.json") as f:
        doc_patterns = json.load(f)
    
    with open(output_dir / "db_patterns.json") as f:
        db_patterns = json.load(f)
    
    # Match
    matcher = PatternMatcher(code_patterns, doc_patterns, db_patterns)
    result = matcher.match_all()
    
    # Save results
    with open(output_dir / "alignment_matrix.json", "w") as f:
        json.dump(result["matches"], f, indent=2)
    
    with open(output_dir / "gaps.json", "w") as f:
        json.dump(result["gaps"], f, indent=2)
    
    with open(output_dir / "summary.json", "w") as f:
        json.dump(result["summary"], f, indent=2)
    
    print(f"\n✅ Results saved to: {output_dir}")
    print(f"   Matches: {result['summary']['total_matches']}")
    print(f"   Gaps: {result['summary']['total_gaps']}")
    print(f"   Code Coverage: {result['summary']['code_coverage']:.1%}")


if __name__ == "__main__":
    main()
