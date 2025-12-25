#!/usr/bin/env python3
"""
Documentation Pattern Extractor - Parse markdown to extract patterns

Extracts:
- Headings (topics, hierarchy)
- Code blocks (examples, syntax)
- CLI commands (usage examples)
- Function/class mentions (references to code)
- Configuration examples
- Workflows (step sequences)

Output: doc_patterns.json
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class HeadingPattern:
    text: str
    level: int
    doc_path: str
    line_number: int
    section_content: str  # First 200 chars of section


@dataclass
class CodeBlockPattern:
    language: str
    content: str
    doc_path: str
    line_number: int
    context: str  # Heading above this code block


@dataclass
class CommandPattern:
    command: str
    doc_path: str
    line_number: int
    context: str


@dataclass
class FunctionMentionPattern:
    name: str
    doc_path: str
    line_number: int
    context: str


@dataclass
class WorkflowPattern:
    name: str
    steps: List[str]
    doc_path: str


class DocPatternExtractor:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.headings: List[HeadingPattern] = []
        self.code_blocks: List[CodeBlockPattern] = []
        self.commands: List[CommandPattern] = []
        self.function_mentions: List[FunctionMentionPattern] = []
        self.workflows: List[WorkflowPattern] = []
        self.topic_graph: Dict[str, List[str]] = defaultdict(list)
        
    def extract_all(self) -> Dict[str, Any]:
        """Extract patterns from all markdown files"""
        print("📚 Extracting documentation patterns...")
        
        md_files = list(self.root_dir.glob("docs/**/*.md"))
        md_files += list(self.root_dir.glob("*.md"))
        
        for i, md_file in enumerate(md_files, 1):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(md_files)} docs...")
            self._extract_from_file(md_file)
        
        print(f"✅ Extracted {len(self.headings)} headings, {len(self.code_blocks)} code blocks")
        
        return {
            "headings": [asdict(h) for h in self.headings],
            "code_blocks": [asdict(c) for c in self.code_blocks],
            "commands": [asdict(c) for c in self.commands],
            "function_mentions": [asdict(f) for f in self.function_mentions],
            "workflows": [asdict(w) for w in self.workflows],
            "topic_graph": {k: list(v) for k, v in self.topic_graph.items()},
        }
    
    def _extract_from_file(self, filepath: Path):
        """Extract patterns from single markdown file"""
        try:
            content = filepath.read_text()
            lines = content.split("\n")
            
            doc_path = str(filepath.relative_to(self.root_dir))
            current_heading = "Root"
            current_section = []
            in_code_block = False
            code_block_lang = ""
            code_block_content = []
            code_block_start = 0
            
            for i, line in enumerate(lines, 1):
                # Extract headings
                heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
                if heading_match and not in_code_block:
                    level = len(heading_match.group(1))
                    text = heading_match.group(2).strip()
                    
                    # Save previous section
                    if current_section:
                        section_content = "\n".join(current_section[:10])  # First 10 lines
                        if self.headings:
                            self.headings[-1].section_content = section_content[:200]
                    
                    self.headings.append(HeadingPattern(
                        text=text,
                        level=level,
                        doc_path=doc_path,
                        line_number=i,
                        section_content=""
                    ))
                    
                    # Build topic graph
                    self.topic_graph[doc_path].append(text)
                    
                    current_heading = text
                    current_section = []
                    continue
                
                # Track code blocks
                if line.strip().startswith("```"):
                    if not in_code_block:
                        in_code_block = True
                        code_block_start = i
                        code_block_lang = line.strip()[3:].strip()
                        code_block_content = []
                    else:
                        in_code_block = False
                        self.code_blocks.append(CodeBlockPattern(
                            language=code_block_lang,
                            content="\n".join(code_block_content),
                            doc_path=doc_path,
                            line_number=code_block_start,
                            context=current_heading
                        ))
                        
                        # Extract commands from code blocks
                        if code_block_lang in ("bash", "sh", "shell", ""):
                            for cmd_line in code_block_content:
                                if cmd_line.strip().startswith("empirica "):
                                    self.commands.append(CommandPattern(
                                        command=cmd_line.strip(),
                                        doc_path=doc_path,
                                        line_number=code_block_start,
                                        context=current_heading
                                    ))
                    continue
                
                if in_code_block:
                    code_block_content.append(line)
                else:
                    current_section.append(line)
                    
                    # Extract function mentions (CamelCase or snake_case followed by parentheses)
                    func_mentions = re.findall(r'\b([A-Z][a-zA-Z0-9_]*|[a-z_][a-z0-9_]*)\s*\(', line)
                    for func in func_mentions:
                        self.function_mentions.append(FunctionMentionPattern(
                            name=func,
                            doc_path=doc_path,
                            line_number=i,
                            context=current_heading
                        ))
                    
                    # Extract CLI commands from inline code
                    cmd_matches = re.findall(r'`empirica ([^`]+)`', line)
                    for cmd in cmd_matches:
                        self.commands.append(CommandPattern(
                            command=f"empirica {cmd}",
                            doc_path=doc_path,
                            line_number=i,
                            context=current_heading
                        ))
            
            # Detect workflows (numbered lists with → or ->)
            self._extract_workflows(content, doc_path)
            
        except Exception as e:
            print(f"⚠️  Error parsing {filepath}: {e}")
    
    def _extract_workflows(self, content: str, doc_path: str):
        """Extract workflow patterns from numbered steps"""
        # Look for sequences like:
        # 1. Step one → Step two
        # 2. Another step
        workflow_pattern = re.compile(
            r'(?:^|\n)((?:\d+\.\s+.+(?:→|->).+\n?)+)',
            re.MULTILINE
        )
        
        for match in workflow_pattern.finditer(content):
            workflow_text = match.group(1)
            steps = []
            
            for line in workflow_text.split("\n"):
                if line.strip():
                    # Remove numbering and extract steps
                    cleaned = re.sub(r'^\d+\.\s+', '', line)
                    # Split on arrows
                    step_parts = re.split(r'\s*(?:→|->)\s*', cleaned)
                    steps.extend([s.strip() for s in step_parts if s.strip()])
            
            if len(steps) >= 2:
                # Name workflow after first step
                name = steps[0][:50]
                self.workflows.append(WorkflowPattern(
                    name=name,
                    steps=steps,
                    doc_path=doc_path
                ))


def main():
    root_dir = Path("/home/yogapad/empirical-ai/empirica")
    extractor = DocPatternExtractor(root_dir)
    patterns = extractor.extract_all()
    
    output_file = root_dir / "dev_scripts/doc_pattern_matcher/doc_patterns.json"
    output_file.write_text(json.dumps(patterns, indent=2))
    
    print(f"\n✅ Doc patterns saved to: {output_file}")
    print(f"   Headings: {len(patterns['headings'])}")
    print(f"   Code Blocks: {len(patterns['code_blocks'])}")
    print(f"   Commands: {len(patterns['commands'])}")
    print(f"   Function Mentions: {len(patterns['function_mentions'])}")
    print(f"   Workflows: {len(patterns['workflows'])}")


if __name__ == "__main__":
    main()
