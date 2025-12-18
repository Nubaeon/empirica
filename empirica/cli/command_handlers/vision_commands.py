"""
Vision Analysis Commands - Simple image/slide analysis for Empirica

Provides basic vision analysis without heavy dependencies:
- Image metadata extraction (size, format, path)
- Basic visual assessment (for epistemic logging)
- Slide deck processing
- Integration with findings/unknowns

Core Empirica: Minimal .png analysis
Future enhancements: Playwright MCP, vision APIs, video analysis
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class BasicImageAssessment:
    """Basic image assessment without OCR"""
    image_path: str
    slide_number: Optional[int]
    
    # Basic metadata
    width: int
    height: int
    format: str
    mode: str
    file_size_kb: float
    
    # Simple visual heuristics
    aspect_ratio: float
    pixel_count: int
    is_presentation_size: bool  # Common slide dimensions
    
    # Epistemic placeholder (for manual annotation)
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class VisionAnalyzer:
    """Simple vision analyzer for core Empirica"""
    
    def __init__(self):
        if not HAS_PIL:
            raise ImportError(
                "PIL/Pillow required for vision analysis. "
                "Install: pip install pillow"
            )
    
    def analyze_image(self, image_path: Path, slide_number: Optional[int] = None) -> BasicImageAssessment:
        """Analyze single image - basic metadata only"""
        img = Image.open(image_path)
        file_size = image_path.stat().st_size / 1024  # KB
        
        width, height = img.size
        aspect_ratio = width / height if height > 0 else 0
        pixel_count = width * height
        
        # Common presentation sizes: 16:9, 4:3, 16:10
        is_presentation_size = (
            0.55 < aspect_ratio < 0.80 or  # 4:3 region
            1.5 < aspect_ratio < 1.85       # 16:9, 16:10 region
        )
        
        return BasicImageAssessment(
            image_path=str(image_path),
            slide_number=slide_number,
            width=width,
            height=height,
            format=img.format or "unknown",
            mode=img.mode,
            file_size_kb=round(file_size, 2),
            aspect_ratio=round(aspect_ratio, 2),
            pixel_count=pixel_count,
            is_presentation_size=is_presentation_size,
        )
    
    def analyze_deck(self, pattern: str) -> List[BasicImageAssessment]:
        """Analyze slide deck matching pattern"""
        slide_files = sorted(Path('.').glob(pattern))
        
        if not slide_files:
            raise FileNotFoundError(f"No images found matching: {pattern}")
        
        assessments = []
        for idx, slide_path in enumerate(slide_files, start=1):
            assessment = self.analyze_image(slide_path, slide_number=idx)
            assessments.append(assessment)
        
        return assessments


def handle_vision_analyze(args):
    """Handle vision-analyze command"""
    from empirica.data.session_database import SessionDatabase
    
    analyzer = VisionAnalyzer()
    
    # Analyze image(s)
    if args.pattern:
        assessments = analyzer.analyze_deck(args.pattern)
    else:
        assessments = [analyzer.analyze_image(Path(args.image))]
    
    # Output format
    output = args.output or "json"
    
    if output == "json":
        result = {
            "ok": True,
            "analyzed": len(assessments),
            "images": [a.to_dict() for a in assessments]
        }
        print(json.dumps(result, indent=2))
    else:
        # Human-readable
        print(f"\n📸 Vision Analysis Results")
        print(f"{'='*60}")
        for a in assessments:
            print(f"\n{Path(a.image_path).name}")
            if a.slide_number:
                print(f"  Slide: #{a.slide_number}")
            print(f"  Size: {a.width}x{a.height} ({a.format})")
            print(f"  Aspect: {a.aspect_ratio} {'(presentation)' if a.is_presentation_size else ''}")
            print(f"  File: {a.file_size_kb} KB")
    
    # Auto-log to session if provided
    if args.session_id:
        db = SessionDatabase()
        try:
            for a in assessments:
                finding = f"Analyzed {Path(a.image_path).name}: {a.width}x{a.height} {a.format}"
                if a.slide_number:
                    finding = f"Slide #{a.slide_number}: {finding}"
                
                db.log_finding(
                    session_id=args.session_id,
                    finding=finding,
                    source="vision-analyze"
                )
            
            if output != "json":
                print(f"\n✓ Logged {len(assessments)} findings to session")
        finally:
            db.close()
    
    return 0


def handle_vision_log(args):
    """Handle vision-log command - manually log visual observation"""
    from empirica.data.session_database import SessionDatabase
    
    db = SessionDatabase()
    try:
        # Log as finding
        db.log_finding(
            session_id=args.session_id,
            finding=args.observation,
            source="vision-log"
        )
        
        if args.output == "json":
            print(json.dumps({"ok": True, "logged": True}))
        else:
            print(f"✓ Visual observation logged to session")
        
        return 0
    finally:
        db.close()


def add_vision_parsers(subparsers):
    """Add vision command parsers"""
    
    # vision-analyze: Analyze image(s) with optional session logging
    vision_analyze = subparsers.add_parser(
        'vision-analyze',
        help='Analyze image(s) and optionally log to session'
    )
    vision_analyze.add_argument('--image', help='Single image path')
    vision_analyze.add_argument('--pattern', help='Image pattern (e.g., slides/*.png)')
    vision_analyze.add_argument('--session-id', help='Session ID to log findings')
    vision_analyze.add_argument('--output', choices=['json', 'human'], default='json',
                               help='Output format')
    vision_analyze.set_defaults(func=handle_vision_analyze)
    
    # vision-log: Manually log visual observation to session
    vision_log = subparsers.add_parser(
        'vision-log',
        help='Log visual observation to session'
    )
    vision_log.add_argument('--session-id', required=True, help='Session ID')
    vision_log.add_argument('--observation', required=True, help='Visual observation text')
    vision_log.add_argument('--output', choices=['json', 'human'], default='json',
                           help='Output format')
    vision_log.set_defaults(func=handle_vision_log)
