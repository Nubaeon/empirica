# Epistemic Project Management - Wide View Proposal

**Date:** 2025-12-22  
**Status:** Proposal for v1.0.5  
**Purpose:** Enable users and AIs to see the full epistemic landscape across all projects

---

## 🎯 Problem Statement

Currently, Empirica tracks epistemic state **per-session** and **per-project**, but there's no way to:
1. See all projects at once with their epistemic health
2. Compare knowledge gaps across projects
3. Decide intelligently where to focus effort next
4. Understand the overall learning trajectory

**User need:** "Step back and see the full picture to decide more intelligently where things go"

---

## 📊 Proposed Solution: `empirica workspace-overview`

### Command Structure

```bash
# Show all projects with epistemic metrics
empirica workspace-overview [OPTIONS]

Options:
  --format <json|table|dashboard>  Output format (default: dashboard)
  --sort-by <activity|knowledge|uncertainty|value>  
  --filter <active|stalled|complete>
  --depth <summary|detailed>
```

### Output Example (Dashboard Mode)

```
╔════════════════════════════════════════════════════════════════╗
║  Empirica Workspace Overview - Epistemic Project Management    ║
╚════════════════════════════════════════════════════════════════╝

📊 Workspace Summary
   Total Projects:    12
   Active Sessions:   3
   Total Sessions:    247
   Collective Know:   0.72 (↑ 0.08 this week)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Projects by Epistemic Health

🟢 HIGH KNOWLEDGE (know ≥ 0.7)
   1. empirica-core │ Know: 0.85 │ Sessions: 47 │ ⏰ 2 days ago
      Findings: 234  Unknowns: 12  Dead Ends: 8
      → Ready for: Production release, Documentation cleanup

   2. customer-dashboard │ Know: 0.78 │ Sessions: 23 │ ⏰ 5 days ago
      Findings: 89  Unknowns: 18  Dead Ends: 5
      → Ready for: Feature expansion, Performance tuning

🟡 MEDIUM KNOWLEDGE (0.5 ≤ know < 0.7)
   3. auth-service │ Know: 0.64 │ Sessions: 15 │ ⏰ 1 day ago
      Findings: 56  Unknowns: 31  Dead Ends: 12
      ⚠️  High uncertainty in: OAuth2 token refresh
      → Recommend: Investigation session on token lifecycle

   4. payment-gateway │ Know: 0.58 │ Sessions: 8 │ ⏰ 3 weeks ago
      Findings: 23  Unknowns: 45  Dead Ends: 7
      ⚠️  Stalled - Last active 3 weeks ago
      → Recommend: Context refresh, handoff review

🔴 LOW KNOWLEDGE (know < 0.5)
   5. ml-pipeline │ Know: 0.42 │ Sessions: 12 │ ⏰ 2 days ago
      Findings: 34  Unknowns: 67  Dead Ends: 15
      🚨 High dead end ratio (31%) - many failed approaches
      → Recommend: Architecture review, external consultation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Recommended Next Actions

   1. 🔴 ml-pipeline needs strategic intervention
      - Schedule architecture review with senior engineer
      - Consider external consultation on ML infrastructure
      - Review and categorize unknowns for systematic resolution

   2. 🟡 payment-gateway has gone stale
      - Run context refresh: empirica project-bootstrap --project-id payment-gateway
      - Review last handoff: empirica handoff-query --project-id payment-gateway
      - Assign to available session or mark inactive

   3. 🟢 empirica-core ready for milestone
      - High knowledge (0.85), low unknowns (12)
      - Perfect timing for v1.1.0 release
      - Consider: Create release checklist, final QA pass

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Cross-Project Insights

   Common Unknowns (appearing in multiple projects):
   • OAuth2 token refresh patterns (3 projects)
   • Database connection pooling (2 projects)
   • Error handling best practices (4 projects)
   → Consider: Create shared knowledge base or wiki page

   Successful Patterns (high confidence findings):
   • API versioning strategy (from customer-dashboard)
   • Testing pyramid approach (from empirica-core)
   → Consider: Document as organization standards

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run 'empirica project-bootstrap --project-id <ID>' for detailed context
Run 'empirica goals-ready --project-id <ID>' to find available work
```

---

## 🔧 Implementation Plan

### Phase 1: Data Aggregation (30 minutes)

```python
# empirica/data/session_database.py

def get_workspace_overview(self):
    """Get epistemic overview of all projects"""
    cursor = self.conn.cursor()
    
    # Get all projects with their latest epistemic state
    cursor.execute("""
        SELECT 
            p.id,
            p.name,
            p.description,
            p.status,
            p.total_sessions,
            p.last_activity_timestamp,
            -- Latest epistemic vectors from most recent session
            (SELECT vectors_json FROM reflexes 
             WHERE session_id IN (SELECT session_id FROM sessions WHERE project_id = p.id)
             ORDER BY logged_at DESC LIMIT 1) as latest_vectors,
            -- Counts
            (SELECT COUNT(*) FROM findings WHERE project_id = p.id) as findings_count,
            (SELECT COUNT(*) FROM unknowns WHERE project_id = p.id AND is_resolved = 0) as unknowns_count,
            (SELECT COUNT(*) FROM dead_ends WHERE project_id = p.id) as dead_ends_count,
            (SELECT COUNT(*) FROM mistakes WHERE project_id = p.id) as mistakes_count
        FROM projects p
        ORDER BY last_activity_timestamp DESC
    """)
    
    projects = []
    for row in cursor.fetchall():
        project = dict(row)
        
        # Parse latest vectors
        if project['latest_vectors']:
            vectors = json.loads(project['latest_vectors'])
            project['epistemic_state'] = {
                'know': vectors.get('foundation', {}).get('know', 0.5),
                'do': vectors.get('foundation', {}).get('do', 0.5),
                'context': vectors.get('foundation', {}).get('context', 0.5),
                'uncertainty': vectors.get('uncertainty', 0.5)
            }
        else:
            project['epistemic_state'] = None
        
        # Calculate health metrics
        if project['total_sessions'] > 0:
            dead_end_ratio = project['dead_ends_count'] / project['total_sessions']
            project['dead_end_ratio'] = dead_end_ratio
            
            # Health score (0-1)
            if project['epistemic_state']:
                know = project['epistemic_state']['know']
                uncertainty = project['epistemic_state']['uncertainty']
                health = (know * 0.6) + ((1 - uncertainty) * 0.4) - (dead_end_ratio * 0.2)
                project['health_score'] = max(0, min(1, health))
            else:
                project['health_score'] = 0.5
        
        projects.append(project)
    
    return {
        'total_projects': len(projects),
        'projects': projects,
        'workspace_stats': self._get_workspace_stats()
    }

def _get_workspace_stats(self):
    """Get workspace-level aggregated stats"""
    cursor = self.conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT p.id) as total_projects,
            COUNT(DISTINCT s.session_id) as total_sessions,
            COUNT(DISTINCT CASE WHEN s.end_time IS NULL THEN s.session_id END) as active_sessions,
            AVG(CASE WHEN r.vectors_json IS NOT NULL 
                THEN json_extract(r.vectors_json, '$.foundation.know') END) as avg_know
        FROM projects p
        LEFT JOIN sessions s ON s.project_id = p.id
        LEFT JOIN reflexes r ON r.session_id = s.session_id
    """)
    
    return dict(cursor.fetchone())
```

### Phase 2: CLI Command (20 minutes)

```python
# empirica/cli/command_handlers/project_commands.py

def handle_workspace_overview_command(args):
    """Show epistemic overview of all projects"""
    from empirica.data.session_database import SessionDatabase
    import json
    from datetime import datetime, timedelta
    
    db = SessionDatabase()
    overview = db.get_workspace_overview()
    db.close()
    
    format_type = getattr(args, 'format', 'dashboard')
    sort_by = getattr(args, 'sort_by', 'activity')
    filter_status = getattr(args, 'filter', None)
    
    if format_type == 'json':
        print(json.dumps(overview, indent=2))
        return overview
    
    # Dashboard output (as shown above)
    projects = overview['projects']
    stats = overview['workspace_stats']
    
    # Sort projects
    if sort_by == 'knowledge':
        projects.sort(key=lambda p: p.get('health_score', 0), reverse=True)
    elif sort_by == 'uncertainty':
        projects.sort(key=lambda p: p.get('epistemic_state', {}).get('uncertainty', 0.5))
    # ... etc
    
    # Filter projects
    if filter_status:
        projects = [p for p in projects if p['status'] == filter_status]
    
    # Render dashboard
    _render_workspace_dashboard(projects, stats)
    
    return overview
```

### Phase 3: Git Workflow Integration (Optional, 45 minutes)

```python
# empirica/cli/command_handlers/project_commands.py

def handle_workspace_map_command(args):
    """
    Create a visual map of all git repos in parent directory
    with their epistemic health
    """
    import os
    import subprocess
    from pathlib import Path
    
    # Scan parent directory for git repos
    parent = Path.cwd().parent
    git_repos = []
    
    for item in parent.iterdir():
        if item.is_dir() and (item / '.git').exists():
            # Get git remote URL
            try:
                result = subprocess.run(
                    ['git', '-C', str(item), 'remote', 'get-url', 'origin'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    remote_url = result.stdout.strip()
                    
                    # Check if this repo is tracked in Empirica
                    db = SessionDatabase()
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT id, name, status FROM projects 
                        WHERE repos LIKE ?
                    """, (f'%{remote_url}%',))
                    project = cursor.fetchone()
                    db.close()
                    
                    git_repos.append({
                        'path': str(item),
                        'name': item.name,
                        'remote_url': remote_url,
                        'empirica_project': dict(project) if project else None
                    })
            except Exception as e:
                logger.debug(f"Skipping {item.name}: {e}")
    
    # Render map
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  Git Workspace Map - Epistemic Health                     ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    for repo in git_repos:
        if repo['empirica_project']:
            # Tracked in Empirica
            status_icon = "🟢" if repo['empirica_project']['status'] == 'active' else "🟡"
            print(f"{status_icon} {repo['name']}")
            print(f"   Path: {repo['path']}")
            print(f"   Empirica Project: {repo['empirica_project']['name']}")
        else:
            # Not tracked
            print(f"⚪ {repo['name']} (not tracked)")
            print(f"   Path: {repo['path']}")
            print(f"   → Run: empirica project-create --name '{repo['name']}' --repos '[\"{ repo['remote_url']}\"]'")
        print()
    
    return {'git_repos': git_repos}
```

---

## 🎯 Key Benefits

1. **Strategic Decision Making:** See which projects need attention vs. which are ready for milestones
2. **Resource Allocation:** Identify stalled projects, high-uncertainty areas
3. **Knowledge Transfer:** Spot common unknowns across projects → create shared docs
4. **Pattern Recognition:** See successful approaches that can be replicated
5. **Epistemic Health Monitoring:** Track collective knowledge growth over time

---

## 📦 Deliverables for v1.0.5

1. ✅ `workspace-overview` command (epistemic project management)
2. ✅ `workspace-map` command (git repo discovery with epistemic health)
3. ✅ Health scoring algorithm (combines know, uncertainty, dead end ratio)
4. ✅ Cross-project insight detection (common unknowns, shared patterns)
5. ✅ Actionable recommendations (what to work on next)

---

## 🚀 Future Enhancements (v1.1.0+)

- **Epistemic Heatmap:** Visual representation of knowledge density across repos
- **Collaboration Insights:** Which projects benefit from multi-AI coordination
- **Learning Velocity:** Track knowledge growth rate per project
- **Risk Detection:** Projects with high uncertainty + low activity = risk
- **Resource Optimization:** Suggest project combinations for efficient context sharing

---

**Ready to implement!** This gives users and AIs the "step back" view they need for intelligent project management.
