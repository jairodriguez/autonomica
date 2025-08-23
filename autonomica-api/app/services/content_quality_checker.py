import logging
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .content_types import (
    ContentType, ContentFormat, Platform, ContentStructure,
    get_content_structure, get_platform_requirements
)

logger = logging.getLogger(__name__)

class QualityCheckStatus(str, Enum):
    """Status of quality checks."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class QualityIssueSeverity(str, Enum):
    """Severity levels for quality issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class QualityIssue:
    """Represents a quality issue found in content."""
    issue_type: str
    severity: QualityIssueSeverity
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None
    line_number: Optional[int] = None
    character_position: Optional[int] = None

@dataclass
class QualityCheckResult:
    """Result of a quality check."""
    content_id: str
    content_type: ContentType
    overall_score: float
    status: QualityCheckStatus
    issues: List[QualityIssue]
    checks_performed: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None

class ContentQualityChecker:
    """Service for checking content quality across multiple dimensions."""
    
    def __init__(self):
        self.grammar_rules = self._initialize_grammar_rules()
        self.style_rules = self._initialize_style_rules()
        self.tone_rules = self._initialize_tone_rules()
        self.relevance_rules = self._initialize_relevance_rules()
        self.quality_thresholds = self._initialize_quality_thresholds()
    
    async def check_content_quality(
        self,
        content: str,
        content_type: ContentType,
        target_platforms: List[Platform],
        brand_voice: str = "Professional and engaging",
        **kwargs
    ) -> QualityCheckResult:
        """Perform comprehensive quality check on content."""
        
        logger.info(f"Starting quality check for content type: {content_type}")
        
        # Initialize result
        result = QualityCheckResult(
            content_id=kwargs.get("content_id", "unknown"),
            content_type=content_type,
            overall_score=0.0,
            status=QualityCheckStatus.PENDING,
            issues=[],
            checks_performed=[],
            metadata={},
            timestamp=datetime.utcnow()
        )
        
        try:
            # Perform various quality checks
            grammar_issues = await self._check_grammar(content, content_type)
            style_issues = await self._check_style(content, content_type, brand_voice)
            tone_issues = await self._check_tone(content, content_type, brand_voice)
            relevance_issues = await self._check_relevance(content, content_type, target_platforms)
            
            # Combine all issues
            all_issues = grammar_issues + style_issues + tone_issues + relevance_issues
            result.issues = all_issues
            
            # Calculate overall score
            result.overall_score = self._calculate_overall_score(all_issues, content_type)
            
            # Determine status
            result.status = self._determine_status(result.overall_score, all_issues)
            
            # Record checks performed
            result.checks_performed = [
                "grammar", "style", "tone", "relevance", "platform_optimization"
            ]
            
            # Add metadata
            result.metadata = {
                "content_length": len(content),
                "word_count": len(content.split()),
                "sentence_count": len(content.split('.')),
                "paragraph_count": len(content.split('\n\n')),
                "brand_voice": brand_voice,
                "target_platforms": [p.value for p in target_platforms]
            }
            
            logger.info(f"Quality check completed. Score: {result.overall_score}, Status: {result.status}")
            
        except Exception as e:
            logger.error(f"Error during quality check: {e}")
            result.status = QualityCheckStatus.FAILED
            result.issues.append(QualityIssue(
                issue_type="system_error",
                severity=QualityIssueSeverity.CRITICAL,
                description=f"System error during quality check: {str(e)}"
            ))
        
        return result
    
    async def _check_grammar(self, content: str, content_type: ContentType) -> List[QualityIssue]:
        """Check grammar and basic language rules."""
        issues = []
        
        # Check for common grammar issues
        grammar_patterns = [
            (r'\b(you|your|you\'re)\b', "Second person usage"),
            (r'\b(we|our|us)\b', "First person plural usage"),
            (r'\b(i|me|my)\b', "First person singular usage"),
            (r'\b(they|their|them)\b', "Third person plural usage"),
        ]
        
        for pattern, description in grammar_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Determine if this is appropriate for the content type
                if not self._is_grammar_appropriate(content_type, match.group(), description):
                    issues.append(QualityIssue(
                        issue_type="grammar",
                        severity=QualityIssueSeverity.MEDIUM,
                        description=f"Inappropriate {description.lower()} usage",
                        location=match.group(),
                        suggestion="Consider using more appropriate language for this content type",
                        character_position=match.start()
                    ))
        
        # Check for basic punctuation
        if content.count('.') < content.count('!') + content.count('?'):
            issues.append(QualityIssue(
                issue_type="grammar",
                severity=QualityIssueSeverity.LOW,
                description="Overuse of exclamation marks or question marks",
                suggestion="Balance sentence endings with periods"
            ))
        
        return issues
    
    async def _check_style(self, content: str, content_type: ContentType, brand_voice: str) -> List[QualityIssue]:
        """Check content style and formatting."""
        issues = []
        
        # Get content structure requirements
        structure = get_content_structure(content_type)
        if not structure:
            return issues
        
        # Check content length
        if structure.max_length and len(content) > structure.max_length:
            issues.append(QualityIssue(
                issue_type="style",
                severity=QualityIssueSeverity.MEDIUM,
                description=f"Content exceeds maximum length ({len(content)} > {structure.max_length})",
                suggestion=f"Reduce content length to {structure.max_length} characters or less"
            ))
        
        if structure.min_length and len(content) < structure.min_length:
            issues.append(QualityIssue(
                issue_type="style",
                severity=QualityIssueSeverity.MEDIUM,
                description=f"Content below minimum length ({len(content)} < {structure.min_length})",
                suggestion=f"Increase content length to {structure.min_length} characters or more"
            ))
        
        # Check paragraph structure
        paragraphs = content.split('\n\n')
        if len(paragraphs) < 2:
            issues.append(QualityIssue(
                issue_type="style",
                severity=QualityIssueSeverity.LOW,
                description="Content lacks proper paragraph structure",
                suggestion="Break content into logical paragraphs"
            ))
        
        # Check for repetitive language
        words = content.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only check words longer than 3 characters
                word_freq[word] = word_freq.get(word, 0) + 1
        
        repetitive_words = [word for word, count in word_freq.items() if count > 5]
        if repetitive_words:
            issues.append(QualityIssue(
                issue_type="style",
                severity=QualityIssueSeverity.MEDIUM,
                description=f"Repetitive language detected: {', '.join(repetitive_words[:3])}",
                suggestion="Use synonyms and varied language to improve readability"
            ))
        
        return issues
    
    async def _check_tone(self, content: str, content_type: ContentType, brand_voice: str) -> List[QualityIssue]:
        """Check content tone and brand voice consistency."""
        issues = []
        
        # Analyze brand voice keywords
        brand_voice_lower = brand_voice.lower()
        
        if "professional" in brand_voice_lower:
            # Check for unprofessional language
            casual_words = ['hey', 'hi there', 'awesome', 'cool', 'gonna', 'wanna']
            for word in casual_words:
                if word in content.lower():
                    issues.append(QualityIssue(
                        issue_type="tone",
                        severity=QualityIssueSeverity.MEDIUM,
                        description=f"Casual language '{word}' inconsistent with professional brand voice",
                        suggestion="Use more formal language appropriate for professional content"
                    ))
        
        elif "casual" in brand_voice_lower:
            # Check for overly formal language
            formal_words = ['nevertheless', 'furthermore', 'consequently', 'thus']
            for word in formal_words:
                if word in content.lower():
                    issues.append(QualityIssue(
                        issue_type="tone",
                        severity=QualityIssueSeverity.LOW,
                        description=f"Formal language '{word}' inconsistent with casual brand voice",
                        suggestion="Use more conversational language"
                    ))
        
        # Check for consistent tone throughout
        sentences = content.split('.')
        tone_indicators = {
            'question': sum(1 for s in sentences if '?' in s),
            'exclamation': sum(1 for s in sentences if '!' in s),
            'statement': sum(1 for s in sentences if not any(p in s for p in '?!'))
        }
        
        # Ensure tone is balanced
        total_sentences = len(sentences)
        if tone_indicators['exclamation'] > total_sentences * 0.3:
            issues.append(QualityIssue(
                issue_type="tone",
                severity=QualityIssueSeverity.MEDIUM,
                description="Overuse of exclamation marks creates overly enthusiastic tone",
                suggestion="Reduce exclamation marks for more balanced tone"
            ))
        
        return issues
    
    async def _check_relevance(self, content: str, content_type: ContentType, target_platforms: List[Platform]) -> List[QualityIssue]:
        """Check content relevance and platform optimization."""
        issues = []
        
        # Check platform-specific requirements
        for platform in target_platforms:
            platform_req = get_platform_requirements(platform)
            if not platform_req:
                continue
            
            # Check character limits
            if platform == Platform.TWITTER:
                char_limit = platform_req.character_limits.get("post", 280)
                if len(content) > char_limit:
                    issues.append(QualityIssue(
                        issue_type="relevance",
                        severity=QualityIssueSeverity.HIGH,
                        description=f"Content exceeds Twitter character limit ({len(content)} > {char_limit})",
                        suggestion=f"Truncate content to {char_limit} characters for Twitter"
                    ))
            
            # Check for platform-specific elements
            if platform == Platform.INSTAGRAM and '#' not in content:
                issues.append(QualityIssue(
                    issue_type="relevance",
                    severity=QualityIssueSeverity.LOW,
                    description="Instagram content lacks hashtags",
                    suggestion="Add relevant hashtags to improve discoverability"
                ))
        
        # Check for content type relevance
        if content_type == ContentType.SOCIAL_MEDIA_POST:
            # Social media should be engaging
            engagement_words = ['you', 'your', 'how', 'what', 'why', 'when', 'where']
            if not any(word in content.lower() for word in engagement_words):
                issues.append(QualityIssue(
                    issue_type="relevance",
                    severity=QualityIssueSeverity.MEDIUM,
                    description="Social media content lacks engagement elements",
                    suggestion="Include questions, calls-to-action, or direct audience references"
                ))
        
        return issues
    
    def _is_grammar_appropriate(self, content_type: ContentType, word: str, description: str) -> bool:
        """Determine if grammar usage is appropriate for content type."""
        # Blog posts and articles can use various perspectives
        if content_type in [ContentType.BLOG_POST, ContentType.ARTICLE]:
            return True
        
        # Social media should be engaging (use 'you', 'your')
        if content_type == ContentType.SOCIAL_MEDIA_POST:
            return 'you' in word.lower()
        
        # Video scripts can be conversational
        if content_type == ContentType.VIDEO_SCRIPT:
            return True
        
        # Default to conservative approach
        return False
    
    def _calculate_overall_score(self, issues: List[QualityIssue], content_type: ContentType) -> float:
        """Calculate overall quality score based on issues."""
        if not issues:
            return 1.0
        
        # Weight issues by severity
        severity_weights = {
            QualityIssueSeverity.LOW: 0.1,
            QualityIssueSeverity.MEDIUM: 0.3,
            QualityIssueSeverity.HIGH: 0.6,
            QualityIssueSeverity.CRITICAL: 1.0
        }
        
        total_weight = 0
        for issue in issues:
            total_weight += severity_weights.get(issue.severity, 0.3)
        
        # Normalize score (0 = worst, 1 = best)
        max_possible_weight = len(issues) * 1.0
        score = 1.0 - (total_weight / max_possible_weight)
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _determine_status(self, score: float, issues: List[QualityIssue]) -> QualityCheckStatus:
        """Determine quality check status based on score and issues."""
        if score >= 0.9:
            return QualityCheckStatus.PASSED
        elif score >= 0.7:
            return QualityCheckStatus.NEEDS_REVIEW
        else:
            return QualityCheckStatus.FAILED
    
    def _initialize_grammar_rules(self) -> Dict[str, Any]:
        """Initialize grammar checking rules."""
        return {
            "common_mistakes": [
                "their vs they're vs there",
                "your vs you're",
                "its vs it's",
                "affect vs effect"
            ],
            "punctuation_rules": [
                "proper sentence endings",
                "comma usage",
                "quotation marks"
            ]
        }
    
    def _initialize_style_rules(self) -> Dict[str, Any]:
        """Initialize style checking rules."""
        return {
            "length_guidelines": {
                "twitter": {"min": 50, "max": 280, "optimal": 200},
                "linkedin": {"min": 100, "max": 1300, "optimal": 800},
                "blog": {"min": 300, "max": 2000, "optimal": 1000}
            },
            "formatting": [
                "paragraph breaks",
                "consistent spacing",
                "proper headings"
            ]
        }
    
    def _initialize_tone_rules(self) -> Dict[str, Any]:
        """Initialize tone checking rules."""
        return {
            "professional": {
                "avoid": ["casual slang", "excessive exclamations", "first person singular"],
                "prefer": ["formal language", "third person", "data-driven content"]
            },
            "casual": {
                "avoid": ["overly formal language", "jargon", "passive voice"],
                "prefer": ["conversational tone", "questions", "direct address"]
            }
        }
    
    def _initialize_relevance_rules(self) -> Dict[str, Any]:
        """Initialize relevance checking rules."""
        return {
            "platform_requirements": {
                "twitter": ["hashtags", "engagement", "character_limit"],
                "linkedin": ["professional_tone", "industry_insights", "networking"],
                "instagram": ["visual_descriptions", "hashtags", "storytelling"]
            }
        }
    
    def _initialize_quality_thresholds(self) -> Dict[str, float]:
        """Initialize quality thresholds for different content types."""
        return {
            "blog_post": 0.8,
            "social_media_post": 0.7,
            "video_script": 0.75,
            "email_newsletter": 0.8,
            "article": 0.85
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the quality checker service."""
        return {
            "status": "healthy",
            "service": "ContentQualityChecker",
            "timestamp": datetime.utcnow().isoformat(),
            "checks_available": [
                "grammar", "style", "tone", "relevance", "platform_optimization"
            ],
            "rules_loaded": {
                "grammar": len(self.grammar_rules),
                "style": len(self.style_rules),
                "tone": len(self.tone_rules),
                "relevance": len(self.relevance_rules)
            }
        }




