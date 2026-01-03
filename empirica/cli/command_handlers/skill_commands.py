"""
Skill Commands - suggest and fetch skills into project_skills/*.yaml
"""
from __future__ import annotations
import os
import json
import logging
from typing import Dict, List
from ..cli_utils import handle_cli_error

logger = logging.getLogger(__name__)


def _load_skill_sources(root: str) -> List[Dict]:
    import yaml  # type: ignore
    path = os.path.join(root, 'docs', 'skills', 'SKILL_SOURCES.yaml')
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data.get('skills', [])


def handle_skill_suggest_command(args):
    try:
        import yaml  # type: ignore
        root = os.getcwd()
        task = getattr(args, 'task', '')

        # First: check local project_skills/*.yaml
        local_skills = []
        skills_dir = os.path.join(root, 'project_skills')
        if os.path.exists(skills_dir):
            for filename in os.listdir(skills_dir):
                if filename.endswith(('.yaml', '.yml')):
                    try:
                        with open(os.path.join(skills_dir, filename), 'r', encoding='utf-8') as f:
                            skill = yaml.safe_load(f)
                            if skill:
                                local_skills.append({
                                    'name': skill.get('title', skill.get('id', filename)),
                                    'id': skill.get('id', filename.replace('.yaml', '').replace('.yml', '')),
                                    'source': 'local',
                                    'tags': skill.get('tags', []),
                                    'location': 'project_skills'
                                })
                    except Exception:
                        pass

        # Second: get available online sources (candidates to fetch)
        online_sources = _load_skill_sources(root)

        # Combine: local first (already fetched), then online candidates
        result = {
            'ok': True,
            'task': task,
            'suggestions': {
                'local': local_skills,
                'available_to_fetch': online_sources
            },
        }
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        handle_cli_error(e, "Skill suggest", getattr(args, 'verbose', False))
        return None


def handle_skill_fetch_command(args):
    try:
        import requests  # type: ignore
        import yaml  # type: ignore
        import zipfile, io
        from empirica.core.skills.parser import parse_markdown_to_skill

        name = args.name
        url = getattr(args, 'url', None)
        file_path = getattr(args, 'file', None)
        tags = [t.strip() for t in (getattr(args, 'tags', '') or '').split(',') if t.strip()]

        def _save_skill(skill_obj: dict) -> dict:
            slug = skill_obj['id']
            out_dir = os.path.join(os.getcwd(), 'project_skills')
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{slug}.yaml")
            with open(out_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(skill_obj, f, sort_keys=False)
            return {'ok': True, 'saved': out_path, 'skill': skill_obj}

        # Case 1: local file (.skill archive)
        if file_path:
            if not os.path.exists(file_path):
                raise FileNotFoundError(file_path)
            # Try to open as zip archive
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Preference order: skill.yaml, skill.json, skill.md, README.md
                members = zf.namelist()
                candidate = None
                for cand in ['skill.yaml', 'skill.yml', 'skill.json', 'skill.md', 'README.md', 'readme.md']:
                    for m in members:
                        if m.lower().endswith(cand):
                            candidate = m
                            break
                    if candidate:
                        break
                if not candidate:
                    # Fallback: concatenate text files
                    md_text = ''
                    for m in members:
                        if m.lower().endswith(('.md', '.txt')):
                            with zf.open(m) as fh:
                                md_text += fh.read().decode('utf-8', errors='ignore') + "\n\n"
                    skill_obj = parse_markdown_to_skill(md_text, name=name, tags=tags)
                    result = _save_skill(skill_obj)
                    print(json.dumps(result, indent=2))
                    return None  # Success - output already printed
                # Parse candidate
                with zf.open(candidate) as fh:
                    data = fh.read()
                    if candidate.lower().endswith(('.yaml', '.yml')):
                        meta = yaml.safe_load(data) or {}
                        # Normalize keys
                        skill_obj = {
                            'id': meta.get('id') or name.lower().replace(' ', '-'),
                            'title': meta.get('title') or name,
                            'tags': meta.get('tags') or tags,
                            'preconditions': meta.get('preconditions') or [],
                            'steps': meta.get('steps') or [],
                            'gotchas': meta.get('gotchas') or [],
                            'references': meta.get('references') or [],
                            'summary': meta.get('summary') or ''
                        }
                        result = _save_skill(skill_obj)
                        print(json.dumps(result, indent=2))
                        return None  # Success - output already printed
                    elif candidate.lower().endswith('.json'):
                        import json as _json
                        meta = _json.loads(data.decode('utf-8', errors='ignore'))
                        skill_obj = {
                            'id': meta.get('id') or name.lower().replace(' ', '-'),
                            'title': meta.get('title') or name,
                            'tags': meta.get('tags') or tags,
                            'preconditions': meta.get('preconditions') or [],
                            'steps': meta.get('steps') or [],
                            'gotchas': meta.get('gotchas') or [],
                            'references': meta.get('references') or [],
                            'summary': meta.get('summary') or ''
                        }
                        result = _save_skill(skill_obj)
                        print(json.dumps(result, indent=2))
                        return None  # Success - output already printed
                    else:
                        # Markdown
                        md_text = data.decode('utf-8', errors='ignore')
                        skill_obj = parse_markdown_to_skill(md_text, name=name, tags=tags)
                        result = _save_skill(skill_obj)
                        print(json.dumps(result, indent=2))
                        return None  # Success - output already printed

        # Case 2: URL fetch (markdown)
        if not url:
            raise ValueError("--url or --file is required for skill-fetch")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        md_text = resp.text
        skill_obj = parse_markdown_to_skill(md_text, name=name, tags=tags)
        result = _save_skill(skill_obj)
        print(json.dumps(result, indent=2))
        return None  # Success - output already printed
    except Exception as e:
        handle_cli_error(e, "Skill fetch", getattr(args, 'verbose', False))
        return None


def handle_skill_extract_command(args):
    """Extract decision frameworks from skill(s) to meta-agent-config.yaml."""
    try:
        from pathlib import Path
        from empirica.core.skills.extractor import (
            SkillExtractor, extract_all_skills, extract_single_skill
        )

        skill_dir = getattr(args, 'skill_dir', None)
        skills_dir = getattr(args, 'skills_dir', None)
        output_file = getattr(args, 'output_file', 'meta-agent-config.yaml')
        verbose = getattr(args, 'verbose', False)
        output_format = getattr(args, 'output', 'json')

        if not skill_dir and not skills_dir:
            raise ValueError("Either --skill-dir or --skills-dir is required")

        if skills_dir:
            # Extract all skills from directory
            config = extract_all_skills(
                Path(skills_dir),
                Path(output_file),
                verbose=verbose
            )
            result = {
                'ok': True,
                'mode': 'multi',
                'skills_dir': str(skills_dir),
                'output_file': str(output_file),
                'domains': list(config.get('meta_agent', {}).get('domain_knowledge', {}).keys())
            }
        else:
            # Extract single skill
            domain_data = extract_single_skill(Path(skill_dir), verbose=verbose)
            result = {
                'ok': True,
                'mode': 'single',
                'skill_dir': str(skill_dir),
                'extracted': domain_data
            }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            if skills_dir:
                print(f"Extracted {len(result['domains'])} skills to {output_file}")
                for domain in result['domains']:
                    print(f"  - {domain}")
            else:
                domain_name = list(domain_data.keys())[0] if domain_data else 'unknown'
                print(f"Extracted skill: {domain_name}")

        return result
    except Exception as e:
        handle_cli_error(e, "Skill extract", getattr(args, 'verbose', False))
        return None
