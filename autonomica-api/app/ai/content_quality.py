"""
Content Quality Check System

This module provides comprehensive quality assessment and improvement
capabilities for generated and repurposed content.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from content_types_simple import ContentType, ContentFormat, get_content_registry

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Quality levels for content assessment."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class QualityMetric(str, Enum):
    """Quality metrics for content assessment."""
    READABILITY = "readability"
    GRAMMAR = "grammar"
    SEO_OPTIMIZATION = "seo_optimization"
    BRAND_VOICE_CONSISTENCY = "brand_voice_consistency"
    CONTENT_STRUCTURE = "content_structure"
    ENGAGEMENT_POTENTIAL = "engagement_potential"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"


@dataclass
class QualityScore:
    """Individual quality score for a specific metric."""
    metric: QualityMetric
    score: float  # 0.0 to 1.0
    level: QualityLevel
    details: str
    suggestions: List[str]


@dataclass
class ContentQualityReport:
    """Comprehensive quality report for content."""
    overall_score: float
    overall_level: QualityLevel
    metric_scores: Dict[QualityMetric, QualityScore]
    summary: str
    recommendations: List[str]
    word_count: int
    character_count: int
    estimated_reading_time: float


class ContentQualityChecker:
    """Main class for content quality assessment."""
    
    def __init__(self):
        self.content_registry = get_content_registry()
        
        # Common grammar and style rules
        self.grammar_rules = {
            "passive_voice": r"\b(am|is|are|was|were|be|been|being)\s+\w+ed\b",
            "wordy_phrases": [
                r"\b(at this point in time)\b",
                r"\b(due to the fact that)\b",
                r"\b(in order to)\b",
                r"\b(it is important to note that)\b",
                r"\b(the reason why)\b"
            ],
            "repetitive_words": r"\b(\w+)\s+\1\b",
            "long_sentences": r"[^.!?]{50,}"
        }
        
        # SEO optimization rules
        self.seo_rules = {
            "title_length": (50, 60),
            "meta_description_length": (150, 160),
            "heading_structure": ["h1", "h2", "h3"],
            "keyword_density": (1.0, 3.0),  # percentage
            "internal_links": True,
            "image_alt_text": True
        }
        
        # Brand voice indicators
        self.brand_voice_indicators = {
            "professional": ["strategy", "business", "industry", "expertise", "leadership"],
            "conversational": ["you", "we", "let's", "imagine", "think about"],
            "innovative": ["cutting-edge", "revolutionary", "breakthrough", "next-generation"],
            "authoritative": ["research shows", "studies indicate", "experts agree", "data proves"],
            "friendly": ["welcome", "hello", "great", "awesome", "exciting"]
        }
    
    def assess_content_quality(self, content: str, content_type: ContentType, 
                              target_format: ContentFormat, brand_voice: Optional[str] = None,
                              **kwargs) -> ContentQualityReport:
        """Assess the overall quality of content."""
        
        # Initialize metric scores
        metric_scores = {}
        
        # Assess readability
        readability_score = self._assess_readability(content, content_type)
        metric_scores[QualityMetric.READABILITY] = readability_score
        
        # Assess grammar and style
        grammar_score = self._assess_grammar_and_style(content)
        metric_scores[QualityMetric.GRAMMAR] = grammar_score
        
        # Assess SEO optimization
        seo_score = self._assess_seo_optimization(content, content_type, **kwargs)
        metric_scores[QualityMetric.SEO_OPTIMIZATION] = seo_score
        
        # Assess brand voice consistency
        brand_voice_score = self._assess_brand_voice_consistency(content, brand_voice)
        metric_scores[QualityMetric.BRAND_VOICE_CONSISTENCY] = brand_voice_score
        
        # Assess content structure
        structure_score = self._assess_content_structure(content, content_type)
        metric_scores[QualityMetric.CONTENT_STRUCTURE] = structure_score
        
        # Assess engagement potential
        engagement_score = self._assess_engagement_potential(content, content_type)
        metric_scores[QualityMetric.ENGAGEMENT_POTENTIAL] = engagement_score
        
        # Assess accuracy and completeness
        accuracy_score = self._assess_accuracy_and_completeness(content, content_type)
        metric_scores[QualityMetric.ACCURACY] = accuracy_score
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metric_scores)
        overall_level = self._score_to_level(overall_score)
        
        # Generate summary and recommendations
        summary = self._generate_quality_summary(metric_scores, overall_level)
        recommendations = self._generate_recommendations(metric_scores)
        
        # Calculate content statistics
        word_count = len(content.split())
        character_count = len(content)
        estimated_reading_time = word_count / 200  # Average reading speed
        
        return ContentQualityReport(
            overall_score=overall_score,
            overall_level=overall_level,
            metric_scores=metric_scores,
            summary=summary,
            recommendations=recommendations,
            word_count=word_count,
            character_count=character_count,
            estimated_reading_time=estimated_reading_time
        )
    
    def _assess_readability(self, content: str, content_type: ContentType) -> QualityScore:
        """Assess content readability using various metrics."""
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        
        # Calculate readability metrics
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Flesch Reading Ease approximation
        syllables = self._count_syllables(content)
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * (syllables / len(words))) if words else 0
        
        # Score based on content type requirements
        structure = self.content_registry.get_content_structure(content_type)
        target_word_count = None
        if structure and structure.word_count_range:
            target_word_count = sum(structure.word_count_range) / 2
        
        # Assess readability score
        readability_score = 0.0
        readability_details = []
        readability_suggestions = []
        
        # Sentence length assessment
        if avg_sentence_length <= 20:
            readability_score += 0.3
            readability_details.append("Sentence length is optimal")
        elif avg_sentence_length <= 25:
            readability_score += 0.2
            readability_details.append("Sentence length is good")
        else:
            readability_details.append("Sentences are too long")
            readability_suggestions.append("Break long sentences into shorter ones")
        
        # Word length assessment
        if avg_word_length <= 5:
            readability_score += 0.3
            readability_details.append("Word choice is accessible")
        elif avg_word_length <= 6:
            readability_score += 0.2
            readability_details.append("Word choice is reasonable")
        else:
            readability_details.append("Consider using simpler words")
            readability_suggestions.append("Replace complex words with simpler alternatives")
        
        # Flesch score assessment
        if flesch_score >= 60:
            readability_score += 0.4
            readability_details.append("Overall readability is good")
        elif flesch_score >= 50:
            readability_score += 0.2
            readability_details.append("Overall readability is acceptable")
        else:
            readability_details.append("Content may be difficult to read")
            readability_suggestions.append("Simplify language and sentence structure")
        
        # Word count assessment
        if target_word_count and abs(len(words) - target_word_count) <= target_word_count * 0.2:
            readability_score += 0.1
            readability_details.append("Content length is appropriate")
        elif target_word_count:
            readability_details.append("Content length may not match target")
            readability_suggestions.append("Adjust content length to match requirements")
        
        return QualityScore(
            metric=QualityMetric.READABILITY,
            score=min(readability_score, 1.0),
            level=self._score_to_level(readability_score),
            details="; ".join(readability_details),
            suggestions=readability_suggestions
        )
    
    def _assess_grammar_and_style(self, content: str) -> QualityScore:
        """Assess grammar and style quality."""
        grammar_score = 1.0
        grammar_details = []
        grammar_suggestions = []
        
        # Check for passive voice
        passive_matches = re.findall(self.grammar_rules["passive_voice"], content, re.IGNORECASE)
        if passive_matches:
            grammar_score -= 0.1
            grammar_details.append(f"Found {len(passive_matches)} passive voice constructions")
            grammar_suggestions.append("Consider using active voice for more engaging content")
        
        # Check for wordy phrases
        wordy_count = 0
        for phrase in self.grammar_rules["wordy_phrases"]:
            matches = re.findall(phrase, content, re.IGNORECASE)
            wordy_count += len(matches)
        
        if wordy_count > 0:
            grammar_score -= 0.1
            grammar_details.append(f"Found {wordy_count} wordy phrases")
            grammar_suggestions.append("Replace wordy phrases with concise alternatives")
        
        # Check for repetitive words
        repetitive_matches = re.findall(self.grammar_rules["repetitive_words"], content)
        if repetitive_matches:
            grammar_score -= 0.05
            grammar_details.append(f"Found {len(repetitive_matches)} repetitive word patterns")
            grammar_suggestions.append("Use synonyms to avoid repetition")
        
        # Check for long sentences
        long_sentences = re.findall(self.grammar_rules["long_sentences"], content)
        if long_sentences:
            grammar_score -= 0.1
            grammar_details.append(f"Found {len(long_sentences)} very long sentences")
            grammar_suggestions.append("Break long sentences into shorter, clearer ones")
        
        # Basic grammar checks
        if not grammar_details:
            grammar_details.append("Grammar and style are good")
        
        return QualityScore(
            metric=QualityMetric.GRAMMAR,
            score=max(grammar_score, 0.0),
            level=self._score_to_level(grammar_score),
            details="; ".join(grammar_details),
            suggestions=grammar_suggestions
        )
    
    def _assess_seo_optimization(self, content: str, content_type: ContentType, **kwargs) -> QualityScore:
        """Assess SEO optimization quality."""
        seo_score = 0.0
        seo_details = []
        seo_suggestions = []
        
        # Check title length (if provided)
        title = kwargs.get('title', '')
        if title:
            title_length = len(title)
            if self.seo_rules["title_length"][0] <= title_length <= self.seo_rules["title_length"][1]:
                seo_score += 0.3
                seo_details.append("Title length is optimal for SEO")
            else:
                seo_details.append(f"Title length ({title_length}) should be between {self.seo_rules['title_length'][0]}-{self.seo_rules['title_length'][1]} characters")
                seo_suggestions.append("Adjust title length for better SEO")
        
        # Check meta description (if provided)
        meta_description = kwargs.get('meta_description', '')
        if meta_description:
            meta_length = len(meta_description)
            if self.seo_rules["meta_description_length"][0] <= meta_length <= self.seo_rules["meta_description_length"][1]:
                seo_score += 0.2
                seo_details.append("Meta description length is optimal")
            else:
                seo_details.append(f"Meta description length ({meta_length}) should be between {self.seo_rules['meta_description_length'][0]}-{self.seo_rules['meta_description_length'][1]} characters")
                seo_suggestions.append("Adjust meta description length for better SEO")
        
        # Check heading structure
        headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        if headings:
            heading_levels = [len(h.split()[0]) for h in headings]
            if heading_levels and heading_levels[0] == 1:  # Has H1
                seo_score += 0.2
                seo_details.append("Proper heading hierarchy (H1 present)")
            else:
                seo_details.append("Missing H1 heading")
                seo_suggestions.append("Include a main H1 heading for better SEO")
        
        # Check keyword density (if keywords provided)
        keywords = kwargs.get('keywords', [])
        if keywords:
            content_lower = content.lower()
            keyword_density = {}
            for keyword in keywords:
                count = content_lower.count(keyword.lower())
                density = (count / len(content.split())) * 100
                keyword_density[keyword] = density
                
                if self.seo_rules["keyword_density"][0] <= density <= self.seo_rules["keyword_density"][1]:
                    seo_score += 0.1
                    seo_details.append(f"Keyword '{keyword}' density is optimal ({density:.1f}%)")
                else:
                    seo_details.append(f"Keyword '{keyword}' density ({density:.1f}%) should be between {self.seo_rules['keyword_density'][0]}-{self.seo_rules['keyword_density'][1]}%")
                    if density < self.seo_rules["keyword_density"][0]:
                        seo_suggestions.append(f"Increase usage of keyword '{keyword}'")
                    else:
                        seo_suggestions.append(f"Reduce overuse of keyword '{keyword}'")
        
        # Check for internal links
        internal_links = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
        if internal_links:
            seo_score += 0.1
            seo_details.append(f"Found {len(internal_links)} internal links")
        else:
            seo_details.append("No internal links found")
            seo_suggestions.append("Consider adding internal links for better SEO")
        
        # Check for image alt text
        images = re.findall(r'!\[([^\]]*)\]', content)
        if images:
            seo_score += 0.1
            seo_details.append(f"Found {len(images)} images with alt text")
        else:
            seo_details.append("No images found")
        
        if not seo_details:
            seo_details.append("Basic SEO elements are present")
        
        return QualityScore(
            metric=QualityMetric.SEO_OPTIMIZATION,
            score=min(seo_score, 1.0),
            level=self._score_to_level(seo_score),
            details="; ".join(seo_details),
            suggestions=seo_suggestions
        )
    
    def _assess_brand_voice_consistency(self, content: str, brand_voice: Optional[str]) -> QualityScore:
        """Assess brand voice consistency."""
        if not brand_voice:
            return QualityScore(
                metric=QualityMetric.BRAND_VOICE_CONSISTENCY,
                score=0.5,
                level=QualityLevel.AVERAGE,
                details="No brand voice specified for assessment",
                suggestions=["Specify brand voice for better consistency assessment"]
            )
        
        brand_voice_score = 0.0
        brand_voice_details = []
        brand_voice_suggestions = []
        
        # Get expected indicators for the brand voice
        expected_indicators = self.brand_voice_indicators.get(brand_voice.lower(), [])
        
        if expected_indicators:
            content_lower = content.lower()
            found_indicators = []
            
            for indicator in expected_indicators:
                if indicator.lower() in content_lower:
                    found_indicators.append(indicator)
            
            # Score based on found indicators
            indicator_ratio = len(found_indicators) / len(expected_indicators)
            brand_voice_score = indicator_ratio
            
            if indicator_ratio >= 0.8:
                brand_voice_details.append(f"Brand voice '{brand_voice}' is well represented")
            elif indicator_ratio >= 0.5:
                brand_voice_details.append(f"Brand voice '{brand_voice}' is moderately represented")
            else:
                brand_voice_details.append(f"Brand voice '{brand_voice}' is poorly represented")
                brand_voice_suggestions.append(f"Incorporate more {brand_voice} language and tone")
        else:
            brand_voice_details.append(f"Unknown brand voice: {brand_voice}")
            brand_voice_suggestions.append("Use a recognized brand voice type")
        
        return QualityScore(
            metric=QualityMetric.BRAND_VOICE_CONSISTENCY,
            score=brand_voice_score,
            level=self._score_to_level(brand_voice_score),
            details="; ".join(brand_voice_details),
            suggestions=brand_voice_suggestions
        )
    
    def _assess_content_structure(self, content: str, content_type: ContentType) -> QualityScore:
        """Assess content structure quality."""
        structure_score = 0.0
        structure_details = []
        structure_suggestions = []
        
        # Get expected structure for content type
        structure = self.content_registry.get_content_structure(content_type)
        
        if structure:
            # Check for required sections
            content_lower = content.lower()
            required_sections = structure.required_sections
            found_sections = []
            
            for section in required_sections:
                if section.lower() in content_lower:
                    found_sections.append(section)
            
            # Score based on found sections
            section_ratio = len(found_sections) / len(required_sections)
            structure_score = section_ratio
            
            if section_ratio >= 0.8:
                structure_details.append("Content structure is well organized")
            elif section_ratio >= 0.5:
                structure_details.append("Content structure is moderately organized")
            else:
                structure_details.append("Content structure needs improvement")
                missing_sections = [s for s in required_sections if s not in found_sections]
                structure_suggestions.append(f"Add missing sections: {', '.join(missing_sections)}")
            
            # Check word count compliance
            if structure.word_count_range:
                word_count = len(content.split())
                if structure.word_count_range[0] <= word_count <= structure.word_count_range[1]:
                    structure_score += 0.2
                    structure_details.append("Content length meets requirements")
                else:
                    structure_details.append(f"Content length ({word_count}) should be between {structure.word_count_range[0]}-{structure.word_count_range[1]} words")
                    if word_count < structure.word_count_range[0]:
                        structure_suggestions.append("Expand content to meet minimum word count")
                    else:
                        structure_suggestions.append("Reduce content to meet maximum word count")
        else:
            structure_details.append("No specific structure requirements for this content type")
            structure_score = 0.5
        
        return QualityScore(
            metric=QualityMetric.CONTENT_STRUCTURE,
            score=min(structure_score, 1.0),
            level=self._score_to_level(structure_score),
            details="; ".join(structure_details),
            suggestions=structure_suggestions
        )
    
    def _assess_engagement_potential(self, content: str, content_type: ContentType) -> QualityScore:
        """Assess content engagement potential."""
        engagement_score = 0.0
        engagement_details = []
        engagement_suggestions = []
        
        # Check for engaging elements
        content_lower = content.lower()
        
        # Questions
        questions = re.findall(r'\?', content)
        if questions:
            engagement_score += 0.2
            engagement_details.append(f"Found {len(questions)} questions to engage readers")
        
        # Call-to-action phrases
        cta_phrases = ["click here", "learn more", "get started", "sign up", "download", "subscribe"]
        found_ctas = [phrase for phrase in cta_phrases if phrase in content_lower]
        if found_ctas:
            engagement_score += 0.2
            engagement_details.append(f"Found call-to-action phrases: {', '.join(found_ctas)}")
        else:
            engagement_details.append("No clear call-to-action found")
            engagement_suggestions.append("Add a clear call-to-action to engage readers")
        
        # Personal pronouns
        personal_pronouns = ["you", "your", "we", "our", "us"]
        pronoun_count = sum(content_lower.count(pronoun) for pronoun in personal_pronouns)
        if pronoun_count >= 3:
            engagement_score += 0.2
            engagement_details.append("Good use of personal pronouns for engagement")
        else:
            engagement_details.append("Limited use of personal pronouns")
            engagement_suggestions.append("Use more personal pronouns to connect with readers")
        
        # Storytelling elements
        story_elements = ["imagine", "picture this", "let me tell you", "once upon a time", "here's the thing"]
        found_story_elements = [element for element in story_elements if element in content_lower]
        if found_story_elements:
            engagement_score += 0.2
            engagement_details.append("Found storytelling elements for engagement")
        
        # Emotional words
        emotional_words = ["exciting", "amazing", "incredible", "powerful", "transform", "revolutionary"]
        found_emotional_words = [word for word in emotional_words if word in content_lower]
        if found_emotional_words:
            engagement_score += 0.2
            engagement_details.append("Found emotional words for engagement")
        
        if not engagement_details:
            engagement_details.append("Basic engagement elements present")
        
        return QualityScore(
            metric=QualityMetric.ENGAGEMENT_POTENTIAL,
            score=min(engagement_score, 1.0),
            level=self._score_to_level(engagement_score),
            details="; ".join(engagement_details),
            suggestions=engagement_suggestions
        )
    
    def _assess_accuracy_and_completeness(self, content: str, content_type: ContentType) -> QualityScore:
        """Assess content accuracy and completeness."""
        accuracy_score = 0.5  # Base score
        accuracy_details = []
        accuracy_suggestions = []
        
        # Check for factual indicators
        factual_indicators = ["research shows", "studies indicate", "according to", "data suggests", "evidence"]
        content_lower = content.lower()
        
        factual_count = sum(content_lower.count(indicator) for indicator in factual_indicators)
        if factual_count > 0:
            accuracy_score += 0.2
            accuracy_details.append(f"Found {factual_count} factual indicators")
        else:
            accuracy_details.append("Limited factual support")
            accuracy_suggestions.append("Add research, data, or expert opinions to support claims")
        
        # Check for completeness (basic heuristics)
        word_count = len(content.split())
        if word_count >= 100:
            accuracy_score += 0.1
            accuracy_details.append("Content has sufficient length for completeness")
        else:
            accuracy_details.append("Content may be too brief")
            accuracy_suggestions.append("Expand content to provide more comprehensive coverage")
        
        # Check for balanced perspective
        balanced_indicators = ["however", "on the other hand", "alternatively", "while", "although"]
        balanced_count = sum(content_lower.count(indicator) for indicator in balanced_indicators)
        if balanced_count > 0:
            accuracy_score += 0.1
            accuracy_details.append("Content shows balanced perspective")
        else:
            accuracy_details.append("Content may lack balanced perspective")
            accuracy_suggestions.append("Consider presenting multiple viewpoints")
        
        # Check for specific details
        specific_indicators = ["specifically", "for example", "in particular", "such as", "including"]
        specific_count = sum(content_lower.count(indicator) for indicator in specific_indicators)
        if specific_count > 0:
            accuracy_score += 0.1
            accuracy_details.append("Content includes specific details and examples")
        else:
            accuracy_details.append("Content may lack specific details")
            accuracy_suggestions.append("Add specific examples and details")
        
        if not accuracy_details:
            accuracy_details.append("Basic accuracy and completeness elements present")
        
        return QualityScore(
            metric=QualityMetric.ACCURACY,
            score=min(accuracy_score, 1.0),
            level=self._score_to_level(accuracy_score),
            details="; ".join(accuracy_details),
            suggestions=accuracy_suggestions
        )
    
    def _calculate_overall_score(self, metric_scores: Dict[QualityMetric, QualityScore]) -> float:
        """Calculate overall quality score from individual metrics."""
        if not metric_scores:
            return 0.0
        
        # Weighted average of all metrics
        total_score = 0.0
        total_weight = 0.0
        
        # Define weights for different metrics
        weights = {
            QualityMetric.READABILITY: 0.2,
            QualityMetric.GRAMMAR: 0.2,
            QualityMetric.SEO_OPTIMIZATION: 0.15,
            QualityMetric.BRAND_VOICE_CONSISTENCY: 0.15,
            QualityMetric.CONTENT_STRUCTURE: 0.15,
            QualityMetric.ENGAGEMENT_POTENTIAL: 0.1,
            QualityMetric.ACCURACY: 0.05
        }
        
        for metric, score in metric_scores.items():
            weight = weights.get(metric, 0.1)
            total_score += score.score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _score_to_level(self, score: float) -> QualityLevel:
        """Convert numerical score to quality level."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.8:
            return QualityLevel.GOOD
        elif score >= 0.6:
            return QualityLevel.AVERAGE
        elif score >= 0.4:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE
    
    def _generate_quality_summary(self, metric_scores: Dict[QualityMetric, QualityScore], 
                                overall_level: QualityLevel) -> str:
        """Generate a summary of content quality."""
        excellent_count = sum(1 for score in metric_scores.values() if score.level == QualityLevel.EXCELLENT)
        good_count = sum(1 for score in metric_scores.values() if score.level == QualityLevel.GOOD)
        poor_count = sum(1 for score in metric_scores.values() if score.level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE])
        
        summary_parts = [f"Content quality is {overall_level.value}"]
        
        if excellent_count > 0:
            summary_parts.append(f"with {excellent_count} excellent metrics")
        if good_count > 0:
            summary_parts.append(f"{good_count} good metrics")
        if poor_count > 0:
            summary_parts.append(f"and {poor_count} areas for improvement")
        
        return " ".join(summary_parts) + "."
    
    def _generate_recommendations(self, metric_scores: Dict[QualityMetric, QualityScore]) -> List[str]:
        """Generate actionable recommendations for improvement."""
        recommendations = []
        
        # Get suggestions from all metrics
        for metric, score in metric_scores.items():
            if score.level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]:
                recommendations.extend(score.suggestions)
            elif score.level == QualityLevel.AVERAGE and score.suggestions:
                recommendations.extend(score.suggestions[:1])  # Limit suggestions for average scores
        
        # Remove duplicates and limit total recommendations
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:5]  # Limit to top 5 recommendations
    
    def _count_syllables(self, text: str) -> int:
        """Simple syllable counting for readability calculation."""
        text = text.lower()
        count = 0
        vowels = "aeiouy"
        on_vowel = False
        
        for char in text:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel
        
        return count


# Global quality checker instance
quality_checker = ContentQualityChecker()


def get_quality_checker() -> ContentQualityChecker:
    """Get the global quality checker instance."""
    return quality_checker