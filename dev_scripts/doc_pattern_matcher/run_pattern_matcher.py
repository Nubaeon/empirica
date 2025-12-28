#!/usr/bin/env python3
"""
Recursive Pattern Matching Doc-Code Alignment Tool

Runs all extractors and matcher in sequence:
1. Extract code patterns (AST parsing)
2. Extract doc patterns (markdown parsing)
3. Extract DB patterns (SQLite inspection)
4. Match patterns recursively (4 levels)
5. Generate gap report and alignment matrix

Usage:
    python run_pattern_matcher.py          # Run all phases
    python run_pattern_matcher.py --quick  # Skip DB extraction (faster)
"""

import sys
import time
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from code_extractor import CodePatternExtractor
from doc_extractor import DocPatternExtractor
from db_extractor import DBPatternExtractor
from pattern_matcher import PatternMatcher
import json


def main():
    root_dir = Path("/home/yogapad/empirical-ai/empirica")
    output_dir = root_dir / "dev_scripts/doc_pattern_matcher"
    
    quick_mode = "--quick" in sys.argv
    
    print("=" * 70)
    print("RECURSIVE PATTERN MATCHING DOC-CODE ALIGNMENT")
    print("=" * 70)
    print()
    
    start_time = time.time()
    
    # Phase 1: Extract code patterns
    print("PHASE 1: Code Pattern Extraction")
    print("-" * 70)
    code_extractor = CodePatternExtractor(root_dir)
    code_patterns = code_extractor.extract_all()
    
    code_file = output_dir / "code_patterns.json"
    code_file.write_text(json.dumps(code_patterns, indent=2))
    print(f"✅ Saved to: {code_file}")
    print()
    
    # Phase 2: Extract doc patterns
    print("PHASE 2: Documentation Pattern Extraction")
    print("-" * 70)
    doc_extractor = DocPatternExtractor(root_dir)
    doc_patterns = doc_extractor.extract_all()
    
    doc_file = output_dir / "doc_patterns.json"
    doc_file.write_text(json.dumps(doc_patterns, indent=2))
    print(f"✅ Saved to: {doc_file}")
    print()
    
    # Phase 3: Extract DB patterns
    if not quick_mode:
        print("PHASE 3: Database Pattern Extraction")
        print("-" * 70)
        db_path = root_dir / ".empirica/empirica_state.db"
        db_extractor = DBPatternExtractor(db_path)
        db_patterns = db_extractor.extract_all()
        
        db_file = output_dir / "db_patterns.json"
        db_file.write_text(json.dumps(db_patterns, indent=2))
        print(f"✅ Saved to: {db_file}")
    else:
        print("PHASE 3: Database Pattern Extraction (SKIPPED - quick mode)")
        print("-" * 70)
        db_patterns = {"tables": {}}
    print()
    
    # Phase 4: Match patterns
    print("PHASE 4: Recursive Pattern Matching")
    print("-" * 70)
    matcher = PatternMatcher(code_patterns, doc_patterns, db_patterns)
    result = matcher.match_all()
    
    # Save results
    alignment_file = output_dir / "alignment_matrix.json"
    gaps_file = output_dir / "gaps.json"
    summary_file = output_dir / "summary.json"
    
    with open(alignment_file, "w") as f:
        json.dump(result["matches"], f, indent=2)
    
    with open(gaps_file, "w") as f:
        json.dump(result["gaps"], f, indent=2)
    
    with open(summary_file, "w") as f:
        json.dump(result["summary"], f, indent=2)
    
    print(f"✅ Saved alignment matrix to: {alignment_file}")
    print(f"✅ Saved gaps report to: {gaps_file}")
    print(f"✅ Saved summary to: {summary_file}")
    print()
    
    # Phase 5: Generate report
    print("=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print()
    
    summary = result["summary"]
    
    print(f"📊 Pattern Extraction:")
    print(f"   Functions:     {len(code_patterns['functions'])}")
    print(f"   Classes:       {len(code_patterns['classes'])}")
    print(f"   DB Tables:     {len(code_patterns['db_tables'])}")
    print(f"   CLI Commands:  {len(code_patterns['cli_commands'])}")
    print(f"   Imports:       {len(code_patterns['imports'])}")
    print()
    print(f"   Doc Headings:  {len(doc_patterns['headings'])}")
    print(f"   Code Blocks:   {len(doc_patterns['code_blocks'])}")
    print(f"   Commands:      {len(doc_patterns['commands'])}")
    print(f"   Workflows:     {len(doc_patterns['workflows'])}")
    print()
    
    print(f"🔗 Pattern Matching:")
    print(f"   Total Matches: {summary['total_matches']}")
    for match_type, count in sorted(summary['match_breakdown'].items()):
        print(f"     {match_type:12s}: {count}")
    print(f"   Code Coverage: {summary['code_coverage']:.1%}")
    print()
    
    print(f"⚠️  Gaps Detected: {summary['total_gaps']}")
    for gap_type, count in sorted(summary['gap_breakdown'].items()):
        severity_emoji = {
            "code_orphan": "📝",
            "doc_orphan": "🗑️ ",
            "stale_example": "⏰",
            "missing_workflow": "🔀",
            "db_mismatch": "⚠️ "
        }.get(gap_type, "❓")
        print(f"     {severity_emoji} {gap_type:20s}: {count}")
    print()
    
    elapsed = time.time() - start_time
    print(f"⏱️  Total time: {elapsed:.1f}s")
    print()
    
    # Show top gaps
    print("=" * 70)
    print("TOP GAPS TO ADDRESS")
    print("=" * 70)
    print()
    
    gaps_by_severity = {"critical": [], "high": [], "medium": [], "low": []}
    for gap in result["gaps"]:
        gaps_by_severity[gap["severity"]].append(gap)
    
    for severity in ["critical", "high", "medium"]:
        gaps = gaps_by_severity[severity][:10]  # Top 10
        if gaps:
            print(f"{severity.upper()} PRIORITY:")
            for gap in gaps:
                entity = gap["entity"]
                if len(entity) > 60:
                    entity = entity[:57] + "..."
                print(f"  • {entity}")
                print(f"    {gap['gap_type']}: {gap['details']}")
            print()
    
    print("=" * 70)
    print(f"✅ Full results in: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
