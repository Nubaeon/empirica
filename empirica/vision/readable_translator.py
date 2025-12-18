"""
Human-Readable Vision Assessment
Translates epistemic vectors to actionable insights for non-technical users
"""

from typing import List, Dict
from pathlib import Path
from dataclasses import dataclass

from empirica.vision.slide_processor import SlideEpistemicAssessment


@dataclass
class ReadableAssessment:
    """Human-readable slide assessment"""
    slide_number: int
    quality_level: str  # Excellent/Good/Fair/Needs Work
    reading_experience: str
    pacing: str
    priority: str
    summary: str
    key_terms: List[str]
    study_time_minutes: int
    suggestions: List[str]


class HumanReadableTranslator:
    """Translate epistemic assessments to plain English"""
    
    def translate_single(self, assessment: SlideEpistemicAssessment) -> ReadableAssessment:
        """Translate one slide assessment"""
        
        # Overall quality
        if assessment.context_value >= 0.7:
            quality = "🌟 Excellent"
            quality_emoji = "🌟"
        elif assessment.context_value >= 0.5:
            quality = "✅ Good"
            quality_emoji = "✅"
        elif assessment.context_value >= 0.3:
            quality = "⚠️ Fair"
            quality_emoji = "⚠️"
        else:
            quality = "⛔ Needs Work"
            quality_emoji = "⛔"
        
        # Reading experience (clarity)
        if assessment.clarity >= 0.7:
            reading = "Easy to understand visually"
        elif assessment.clarity >= 0.5:
            reading = "Moderately clear presentation"
        else:
            reading = "May be visually confusing - take extra time"
        
        # Pacing (density - inverted)
        ease_of_processing = 1.0 - assessment.density
        if ease_of_processing >= 0.7:
            pacing = "Quick read - focused content"
        elif ease_of_processing >= 0.5:
            pacing = "Moderate pace - take your time"
        else:
            pacing = "Information-dense - read slowly, take notes"
        
        # Priority (impact)
        if assessment.impact >= 0.7:
            priority = "⭐ Core Concept - Essential"
        elif assessment.impact >= 0.5:
            priority = "📌 Important - Don't Skip"
        else:
            priority = "📚 Background - Skim if short on time"
        
        # Study time estimate (based on density and word count)
        base_time = 2  # minutes
        if assessment.density > 0.7:
            study_time = base_time + 3
        elif assessment.density > 0.5:
            study_time = base_time + 1
        else:
            study_time = base_time
        
        # Generate suggestions
        suggestions = []
        if assessment.clarity < 0.5:
            suggestions.append("💡 Visual quality low - try zooming in or viewing on larger screen")
        
        if assessment.density > 0.7:
            suggestions.append("⏰ Dense content - budget extra time, consider making notes")
        
        if assessment.has_diagram:
            suggestions.append("📊 Contains diagrams - trace connections visually")
        
        if assessment.has_code:
            suggestions.append("💻 Contains code - try typing it out instead of just reading")
        
        if assessment.impact > 0.7 and assessment.clarity < 0.6:
            suggestions.append("⭐ Core concept with unclear presentation - seek supplementary materials")
        
        if not suggestions:
            suggestions.append("👍 Standard slide - read at normal pace")
        
        return ReadableAssessment(
            slide_number=assessment.slide_number,
            quality_level=quality,
            reading_experience=reading,
            pacing=pacing,
            priority=priority,
            summary=assessment.summary,
            key_terms=assessment.key_concepts[:5],
            study_time_minutes=study_time,
            suggestions=suggestions
        )
    
    def generate_study_guide(self, assessments: List[SlideEpistemicAssessment]) -> str:
        """Generate complete study guide"""
        
        # Categorize slides
        essential = [a for a in assessments if a.impact > 0.7]
        important = [a for a in assessments if 0.5 <= a.impact <= 0.7]
        background = [a for a in assessments if a.impact < 0.5]
        
        dense = [a for a in assessments if a.density > 0.6]
        unclear = [a for a in assessments if a.clarity < 0.5]
        
        # Calculate totals
        total_time = sum(
            5 if a.density > 0.7 else (3 if a.density > 0.5 else 2)
            for a in assessments
        )
        
        guide = []
        guide.append("=" * 70)
        guide.append("📚 YOUR PERSONALIZED STUDY GUIDE")
        guide.append("=" * 70)
        guide.append("")
        
        # Study path
        guide.append("🎯 RECOMMENDED STUDY PATH")
        guide.append("-" * 70)
        guide.append("")
        
        if essential:
            guide.append("⭐ START HERE - Core Concepts (MUST READ):")
            for a in essential[:5]:
                guide.append(f"   • Slide {a.slide_number}: {a.summary[:60]}...")
            guide.append(f"   Estimated time: {len(essential[:5]) * 4} minutes")
            guide.append("")
        
        if important:
            guide.append("📌 NEXT - Supporting Material (Important):")
            for a in important[:5]:
                guide.append(f"   • Slide {a.slide_number}: {a.summary[:60]}...")
            guide.append(f"   Estimated time: {len(important[:5]) * 3} minutes")
            guide.append("")
        
        if background:
            guide.append("📚 OPTIONAL - Background Context:")
            for a in background[:5]:
                guide.append(f"   • Slide {a.slide_number}: {a.summary[:60]}...")
            guide.append(f"   Estimated time: {len(background[:5]) * 2} minutes")
            guide.append("")
        
        # Special attention
        guide.append("⚠️ NEEDS SPECIAL ATTENTION")
        guide.append("-" * 70)
        guide.append("")
        
        if dense:
            guide.append("⏰ INFORMATION-DENSE (Budget Extra Time):")
            for a in dense[:5]:
                guide.append(f"   • Slide {a.slide_number} - Allow 5+ minutes")
            guide.append("")
        
        if unclear:
            guide.append("💡 VISUALLY UNCLEAR (Zoom In / Use Larger Screen):")
            for a in unclear[:5]:
                guide.append(f"   • Slide {a.slide_number}")
            guide.append("")
        
        # Time estimate
        guide.append("⏱️ TIME ESTIMATE")
        guide.append("-" * 70)
        guide.append(f"Complete study: ~{total_time} minutes")
        guide.append(f"Core concepts only: ~{len(essential) * 4} minutes")
        guide.append(f"Speed review: ~{len(assessments) * 1} minutes")
        guide.append("")
        
        # Quality summary
        avg_clarity = sum(a.clarity for a in assessments) / len(assessments)
        avg_density = sum(a.density for a in assessments) / len(assessments)
        
        guide.append("📊 OVERALL QUALITY")
        guide.append("-" * 70)
        guide.append(f"Visual Clarity: {self._score_to_grade(avg_clarity)}")
        guide.append(f"Content Density: {self._density_to_description(avg_density)}")
        guide.append(f"Total Slides: {len(assessments)}")
        guide.append("")
        
        guide.append("=" * 70)
        
        return "\n".join(guide)
    
    def generate_slide_card(self, assessment: SlideEpistemicAssessment) -> str:
        """Generate detailed card for one slide"""
        readable = self.translate_single(assessment)
        
        card = []
        card.append("=" * 70)
        card.append(f"SLIDE {readable.slide_number} - {readable.quality_level}")
        card.append("=" * 70)
        card.append("")
        
        card.append("📖 WHAT TO EXPECT")
        card.append(f"   Reading Experience: {readable.reading_experience}")
        card.append(f"   Pacing: {readable.pacing}")
        card.append(f"   Priority: {readable.priority}")
        card.append(f"   Study Time: ~{readable.study_time_minutes} minutes")
        card.append("")
        
        card.append("📝 CONTENT SUMMARY")
        card.append(f"   {readable.summary}")
        card.append("")
        
        if readable.key_terms:
            card.append("🔑 KEY TERMS")
            card.append("   " + ", ".join(readable.key_terms))
            card.append("")
        
        card.append("💡 STUDY TIPS")
        for suggestion in readable.suggestions:
            card.append(f"   {suggestion}")
        card.append("")
        
        card.append("📊 QUALITY METRICS")
        card.append(f"   Visual Clarity:  {self._score_to_grade(assessment.clarity)} [{assessment.clarity:.2f}]")
        card.append(f"   Content Signal:  {self._score_to_grade(assessment.signal)} [{assessment.signal:.2f}]")
        card.append(f"   Easy to Process: {self._score_to_grade(1.0 - assessment.density)} [{1.0-assessment.density:.2f}]")
        card.append(f"   Learning Impact: {self._score_to_grade(assessment.impact)} [{assessment.impact:.2f}]")
        card.append("")
        
        card.append("=" * 70)
        
        return "\n".join(card)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 0.9: return "A+"
        elif score >= 0.8: return "A "
        elif score >= 0.7: return "B+"
        elif score >= 0.6: return "B "
        elif score >= 0.5: return "C+"
        else: return "C "
    
    def _density_to_description(self, density: float) -> str:
        """Convert density score to description"""
        if density >= 0.7:
            return "Very Dense (Allow extra time)"
        elif density >= 0.5:
            return "Moderate (Normal pace)"
        else:
            return "Light (Quick read)"


def main():
    """CLI for human-readable assessments"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description="Generate human-readable study guides from epistemic assessments"
    )
    parser.add_argument(
        "assessment_file",
        help="Path to assessment JSON (e.g., .empirica/slides/assessment_ledger-all.png.json)"
    )
    parser.add_argument(
        "--slide", type=int,
        help="Show detailed card for specific slide number"
    )
    parser.add_argument(
        "--format", choices=["guide", "cards", "both"], default="guide",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    # Load assessment
    with open(args.assessment_file) as f:
        data = json.load(f)
    
    assessments = [
        SlideEpistemicAssessment(**slide_data)
        for slide_data in data["slides"]
    ]
    
    translator = HumanReadableTranslator()
    
    if args.slide:
        # Show specific slide
        slide_assessment = next((a for a in assessments if a.slide_number == args.slide), None)
        if slide_assessment:
            print(translator.generate_slide_card(slide_assessment))
        else:
            print(f"Slide {args.slide} not found")
    else:
        # Show study guide
        if args.format in ["guide", "both"]:
            print(translator.generate_study_guide(assessments))
        
        if args.format in ["cards", "both"]:
            print("\n\n")
            for assessment in assessments:
                print(translator.generate_slide_card(assessment))
                print("\n")


if __name__ == "__main__":
    main()
