"""
Lens Command Handlers — Rich TUI for Epistemic Lens commands.

Handles:
- lens-profile: Display human epistemic profile
- lens-ingest: Extract + chunk + embed
- lens-delta: Delta scoring with Rich TUI
- lens-status: Collection stats
"""

import json
import logging
import time

logger = logging.getLogger(__name__)


def _resolve_project_id(parsed_args):
    """Resolve project_id from args or CWD."""
    project_id = getattr(parsed_args, 'project_id', None)
    if project_id:
        return project_id

    try:
        from empirica.config.path_resolver import PathResolver
        resolver = PathResolver()
        project_yaml = resolver.find_project_yaml()
        if project_yaml:
            import yaml
            with open(project_yaml) as f:
                data = yaml.safe_load(f)
            return data.get("project_id", "")
    except Exception:
        pass

    return ""


def handle_lens_profile_command(parsed_args):
    """Handle lens-profile command."""
    project_id = _resolve_project_id(parsed_args)
    output_fmt = getattr(parsed_args, 'output', 'human')
    for_ai = getattr(parsed_args, 'for_ai', False)

    if for_ai:
        from empirica.core.lens.profile import profile_for_ai
        summary = profile_for_ai(project_id)
        if output_fmt == 'json':
            return {"ok": True, "summary": summary}
        print(summary)
        return

    from empirica.core.lens.profile import build_profile
    profile = build_profile(project_id)

    if output_fmt == 'json':
        return {"ok": True, "profile": profile.to_dict()}

    # Rich TUI display
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        console = Console()

        # Header panel
        header = Text()
        header.append(f"Human Epistemic Profile", style="bold cyan")
        if profile.project_name:
            header.append(f"\nProject: {profile.project_name}", style="dim")
        header.append(f"\nFindings: {profile.total_findings} | Eidetic: {profile.total_eidetic_facts} | Docs: {profile.total_docs} | Episodes: {profile.total_episodes}", style="dim")

        console.print(Panel(header, title="[bold]Epistemic Lens[/bold]", border_style="cyan"))

        # Domain strengths
        if profile.domain_strengths:
            table = Table(title="Domain Strengths", show_header=True, header_style="bold green")
            table.add_column("Domain", style="cyan")
            table.add_column("Strength", justify="right")
            table.add_column("Bar", min_width=20)
            table.add_column("Findings", justify="right")

            sorted_domains = sorted(profile.domain_strengths.items(), key=lambda x: x[1], reverse=True)
            for domain, strength in sorted_domains[:10]:
                count = profile.domain_exposure_counts.get(domain, 0)
                bar_len = int(strength * 20)
                bar = "\u2588" * bar_len + "\u2591" * (20 - bar_len)
                table.add_row(domain, f"{strength:.2f}", bar, str(count))

            console.print(table)

        # Knowledge gaps
        if profile.open_unknowns:
            table = Table(title=f"Knowledge Gaps ({len(profile.open_unknowns)} open unknowns)", show_header=True, header_style="bold yellow")
            table.add_column("Unknown", style="yellow", max_width=60)
            table.add_column("Age", justify="right")

            now = time.time()
            for u in profile.open_unknowns[:10]:
                age_days = int((now - u.created_at) / 86400) if u.created_at else 0
                table.add_row(u.text[:60], f"{age_days}d")

            console.print(table)

        # Stale assumptions
        if profile.stale_assumptions:
            table = Table(title=f"Stale Assumptions (urgency > 0.3)", show_header=True, header_style="bold red")
            table.add_column("Assumption", max_width=50)
            table.add_column("Conf", justify="right")
            table.add_column("Urgency", justify="right", style="red")

            for a in profile.stale_assumptions[:5]:
                table.add_row(a.text[:50], f"{a.confidence:.2f}", f"{a.urgency:.2f}")

            console.print(table)

        # Calibration biases
        if profile.calibration_biases:
            biases = {k: v for k, v in profile.calibration_biases.items() if abs(v) > 0.05}
            if biases:
                table = Table(title="Calibration Biases", show_header=True, header_style="bold magenta")
                table.add_column("Vector")
                table.add_column("Bias", justify="right")
                table.add_column("Direction")

                for vec, bias in sorted(biases.items(), key=lambda x: abs(x[1]), reverse=True):
                    direction = "overestimate" if bias > 0 else "underestimate"
                    style = "red" if bias > 0 else "blue"
                    table.add_row(vec, f"{'+' if bias > 0 else ''}{bias:.2f}", Text(direction, style=style))

                console.print(table)

        # Active goals
        if profile.active_goals:
            table = Table(title=f"Active Goals ({len(profile.active_goals)})", show_header=True, header_style="bold blue")
            table.add_column("Objective", max_width=60)
            table.add_column("Status")

            for g in profile.active_goals[:5]:
                table.add_row(g.objective[:60], g.status)

            console.print(table)

        # HESM baseline
        hesm = profile.baseline_hesm
        hesm_dict = hesm.to_dict()
        table = Table(title="Baseline HESM", show_header=True, header_style="bold white")
        table.add_column("Vector", style="cyan")
        table.add_column("Value", justify="right")
        table.add_column("Bar", min_width=15)

        for vec_name, val in hesm_dict.items():
            bar_len = int(val * 15)
            bar = "\u2588" * bar_len + "\u2591" * (15 - bar_len)
            table.add_row(vec_name, f"{val:.3f}", bar)

        console.print(table)

    except ImportError:
        # Fallback: plain text
        print(f"Profile: {profile.project_name or project_id}")
        print(f"  Findings: {profile.total_findings} | Eidetic: {profile.total_eidetic_facts}")
        if profile.domain_strengths:
            for d, s in sorted(profile.domain_strengths.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {d}: {s:.2f}")
        if profile.open_unknowns:
            print(f"  Open unknowns: {len(profile.open_unknowns)}")


def handle_lens_ingest_command(parsed_args):
    """Handle lens-ingest command."""
    source = parsed_args.source
    project_id = _resolve_project_id(parsed_args)
    chunk_size = getattr(parsed_args, 'chunk_size', 512)
    overlap = getattr(parsed_args, 'overlap', 64)
    dry_run = getattr(parsed_args, 'dry_run', False)
    output_fmt = getattr(parsed_args, 'output', 'human')

    # Extract
    from empirica.core.lens.extractors import extract_text
    doc = extract_text(source)

    if doc.error:
        result = {"ok": False, "error": doc.error}
        if output_fmt == 'json':
            return result
        print(f"Error: {doc.error}")
        return 1

    # Chunk
    from empirica.core.lens.chunker import chunk_text
    chunks = chunk_text(doc.text, chunk_size=chunk_size, overlap=overlap)

    if dry_run:
        result = {
            "ok": True,
            "source": source,
            "source_type": doc.source_type,
            "title": doc.title,
            "word_count": doc.word_count,
            "chunks": len(chunks),
            "dry_run": True,
            "chunk_previews": [
                {"index": c.index, "tokens": c.token_count, "preview": c.text[:80]}
                for c in chunks[:5]
            ],
        }
        if output_fmt == 'json':
            return result
        print(f"Source: {source}")
        print(f"Type: {doc.source_type} | Title: {doc.title}")
        print(f"Words: {doc.word_count} | Chunks: {len(chunks)}")
        print()
        for c in chunks[:5]:
            print(f"  [{c.index}] ({c.token_count} tokens) {c.text[:80]}...")
        if len(chunks) > 5:
            print(f"  ... and {len(chunks) - 5} more chunks")
        return

    # Embed and store
    stored = 0
    try:
        from empirica.core.qdrant.connection import _check_qdrant_available
        if not _check_qdrant_available():
            result = {"ok": False, "error": "Qdrant not available"}
            if output_fmt == 'json':
                return result
            print("Error: Qdrant not available for embedding")
            return 1

        from empirica.core.qdrant.memory import upsert_docs
        import uuid as _uuid

        for chunk in chunks:
            try:
                upsert_docs(
                    project_id=project_id,
                    doc_id=f"lens-{_uuid.uuid4().hex[:12]}",
                    text=chunk.text,
                    metadata={
                        "source": source,
                        "source_type": doc.source_type,
                        "title": doc.title,
                        "chunk_index": chunk.index,
                        "ingested_by": "lens",
                    },
                )
                stored += 1
            except Exception as e:
                logger.debug(f"Failed to embed chunk {chunk.index}: {e}")

    except ImportError:
        result = {"ok": False, "error": "Qdrant dependencies not available"}
        if output_fmt == 'json':
            return result
        print("Error: Qdrant dependencies not available")
        return 1

    result = {
        "ok": True,
        "source": source,
        "title": doc.title,
        "chunks_total": len(chunks),
        "chunks_stored": stored,
    }

    if output_fmt == 'json':
        return result

    print(f"Ingested: {source}")
    print(f"  Title: {doc.title}")
    print(f"  Chunks: {stored}/{len(chunks)} stored")


def handle_lens_delta_command(parsed_args):
    """Handle lens-delta command."""
    source = parsed_args.source
    project_id = _resolve_project_id(parsed_args)
    learn = getattr(parsed_args, 'learn', False)
    verbose = getattr(parsed_args, 'verbose', False)
    gaps_only = getattr(parsed_args, 'gaps_only', False)
    chunk_size = getattr(parsed_args, 'chunk_size', 512)
    output_fmt = getattr(parsed_args, 'output', 'human')

    # Extract
    from empirica.core.lens.extractors import extract_text
    doc = extract_text(source)

    if doc.error:
        result = {"ok": False, "error": doc.error}
        if output_fmt == 'json':
            return result
        print(f"Error: {doc.error}")
        return 1

    # Chunk
    from empirica.core.lens.chunker import chunk_text
    chunks = chunk_text(doc.text, chunk_size=chunk_size)

    # Compute delta
    from empirica.core.lens.delta import compute_delta
    delta = compute_delta(
        project_id=project_id,
        chunks=chunks,
        source=source,
        source_type=doc.source_type,
        title=doc.title,
        gaps_only=gaps_only,
    )

    # Learn mode
    learn_result = None
    if learn:
        from empirica.core.lens.learn import learn_from_delta
        learn_result = learn_from_delta(
            project_id=project_id,
            delta_result=delta,
        )

    if output_fmt == 'json':
        result = {"ok": True, "delta": delta.to_dict()}
        if learn_result:
            result["learn"] = learn_result.to_dict()
        return result

    # Rich TUI display
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        console = Console()

        # Header panel
        header = Text()
        header.append(f"Epistemic Delta: ", style="bold")
        header.append(f"{source}\n", style="cyan")
        header.append(f"Against: profile ({project_id[:20]})\n", style="dim")
        header.append(f"Novelty: {delta.novelty_pct:.0f}% novel", style="bold green" if delta.novelty_pct > 50 else "bold yellow")
        if delta.gaps_matched:
            header.append(f" | Gaps matched: {delta.gaps_matched}", style="bold red")
        header.append(f"\nChunks: {delta.chunks_total}", style="dim")
        header.append(f" | Novel: {delta.chunks_novel}", style="green")
        header.append(f" | Partial: {delta.chunks_partial}", style="yellow")
        header.append(f" | Known: {delta.chunks_known}", style="dim")
        if delta.chunks_gap_closing:
            header.append(f" | Gap-closing: {delta.chunks_gap_closing}", style="bold red")
        header.append(f"\nTime: {delta.elapsed_ms}ms", style="dim")

        console.print(Panel(header, title="[bold]Epistemic Lens[/bold]", border_style="cyan"))

        # Chunk results table
        if delta.chunk_results:
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", justify="right", width=4)
            table.add_column("Score", justify="right", width=6)
            table.add_column("Class", width=12)
            table.add_column("Preview", max_width=50)
            table.add_column("Match", max_width=25)

            if verbose:
                for vec in ["exposure", "comprehension", "retention", "fluency", "integration", "uncertainty", "interest"]:
                    table.add_column(vec[:4], justify="right", width=5)

            for cr in delta.chunk_results:
                # Style based on classification
                if cr.classification == "gap_closing":
                    class_style = "bold red"
                    score_text = "GAP!"
                elif cr.classification == "novel":
                    class_style = "green"
                    score_text = f"{(1.0 - cr.composite) * 100:.0f}%"
                elif cr.classification == "partial":
                    class_style = "yellow"
                    score_text = f"{(1.0 - cr.composite) * 100:.0f}%"
                else:
                    class_style = "dim"
                    score_text = f"{(1.0 - cr.composite) * 100:.0f}%"

                match_text = ""
                if cr.matched_unknown_text:
                    match_text = f"unknown:{cr.matched_unknown_text[:20]}"
                elif cr.best_match_collection:
                    match_text = cr.best_match_collection

                row = [
                    str(cr.index),
                    score_text,
                    Text(cr.classification, style=class_style),
                    cr.text_preview[:50],
                    match_text,
                ]

                if verbose:
                    hesm = cr.hesm.to_dict()
                    for vec in ["exposure", "comprehension", "retention", "fluency", "integration", "uncertainty", "interest"]:
                        row.append(f"{hesm.get(vec, 0):.2f}")

                table.add_row(*row)

            console.print(table)

        # Learn results
        if learn_result:
            console.print()
            learn_text = Text()
            learn_text.append("Learn results: ", style="bold")
            learn_text.append(f"Findings: {learn_result.findings_logged}", style="green")
            learn_text.append(f" | Unknowns logged: {learn_result.unknowns_logged}", style="yellow")
            learn_text.append(f" | Unknowns resolved: {learn_result.unknowns_resolved}", style="red")
            learn_text.append(f" | Beliefs stored: {learn_result.beliefs_stored}", style="cyan")
            console.print(Panel(learn_text, border_style="green"))

        # Hint
        if not learn and delta.chunks_gap_closing > 0:
            console.print(f"\n[bold yellow]Hint:[/bold yellow] {delta.chunks_gap_closing} chunks match your open unknowns — use --learn to resolve them")

    except ImportError:
        # Fallback: plain text
        print(f"Delta: {source}")
        print(f"  Novelty: {delta.novelty_pct:.0f}% | Chunks: {delta.chunks_total}")
        print(f"  Novel: {delta.chunks_novel} | Partial: {delta.chunks_partial} | Known: {delta.chunks_known}")
        if delta.chunks_gap_closing:
            print(f"  Gap-closing: {delta.chunks_gap_closing}")
        for cr in delta.chunk_results[:10]:
            print(f"  [{cr.index}] {cr.classification:12s} {cr.text_preview[:60]}")


def handle_lens_status_command(parsed_args):
    """Handle lens-status command."""
    project_id = _resolve_project_id(parsed_args)
    output_fmt = getattr(parsed_args, 'output', 'human')

    from empirica.core.lens.profile import build_profile
    profile = build_profile(project_id)

    status = {
        "ok": True,
        "project_id": profile.project_id,
        "project_name": profile.project_name,
        "collections": {
            "findings": profile.total_findings,
            "eidetic_facts": profile.total_eidetic_facts,
            "docs": profile.total_docs,
            "episodes": profile.total_episodes,
        },
        "profile": {
            "domain_count": len(profile.domain_strengths),
            "open_unknowns": len(profile.open_unknowns),
            "stale_assumptions": len(profile.stale_assumptions),
            "active_goals": len(profile.active_goals),
            "calibration_vectors": len(profile.calibration_biases),
        },
        "baseline_hesm": profile.baseline_hesm.to_dict(),
    }

    if output_fmt == 'json':
        return status

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        # Collections
        table = Table(title="Collection Stats", show_header=True, header_style="bold cyan")
        table.add_column("Collection")
        table.add_column("Count", justify="right")

        for name, count in status["collections"].items():
            table.add_row(name, str(count))

        console.print(table)

        # Profile summary
        table = Table(title="Profile Summary", show_header=True, header_style="bold green")
        table.add_column("Metric")
        table.add_column("Value", justify="right")

        for name, val in status["profile"].items():
            table.add_row(name.replace("_", " ").title(), str(val))

        console.print(table)

    except ImportError:
        print(f"Lens Status: {profile.project_name or project_id}")
        for name, count in status["collections"].items():
            print(f"  {name}: {count}")
