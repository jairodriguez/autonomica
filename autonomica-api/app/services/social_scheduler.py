"""
Social Media Scheduling Algorithm Service
Implements intelligent scheduling algorithms for optimal content posting across platforms
"""

import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import pytz

from app.models.schema import ContentPiece, ContentStatus

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Content type classification for optimization"""
    BLOG_POST = "blog_post"
    TWEET = "tweet"
    LINKEDIN_ARTICLE = "linkedin_article"
    FACEBOOK_POST = "facebook_post"
    INSTAGRAM_POST = "instagram_post"
    AD_COPY = "ad_copy"
    NEWSLETTER = "newsletter"
    VIDEO = "video"
    IMAGE = "image"

class PlatformType(Enum):
    """Social media platforms"""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"

@dataclass
class OptimalTimeSlot:
    """Represents an optimal posting time slot"""
    platform: PlatformType
    day_of_week: int  # 0=Monday, 6=Sunday
    hour: int  # 0-23
    engagement_score: float  # 0.0-1.0
    content_types: List[ContentType]
    timezone: str

@dataclass
class SchedulingRequest:
    """Request for content scheduling"""
    content_id: int
    content_type: ContentType
    platforms: List[PlatformType]
    priority: int  # 1=highest, 5=lowest
    target_date: Optional[datetime] = None
    avoid_cannibalization: bool = True
    timezone: str = "UTC"

@dataclass
class SchedulingResult:
    """Result of scheduling optimization"""
    content_id: int
    platform: PlatformType
    scheduled_time: datetime
    engagement_score: float
    reason: str
    conflicts: List[str] = None

class SocialMediaScheduler:
    """
    Intelligent scheduling algorithm for social media content
    
    Implements:
    - Platform-specific optimal timing
    - Content type optimization
    - Cannibalization avoidance
    - Time zone handling
    - Priority-based scheduling
    """
    
    def __init__(self):
        self.timezone = pytz.UTC
        self.optimal_times = self._initialize_optimal_times()
        self.content_type_weights = self._initialize_content_weights()
        self.platform_weights = self._initialize_platform_weights()
        
        # Scheduling constraints
        self.min_interval_minutes = 30  # Minimum time between posts on same platform
        self.max_daily_posts = {
            PlatformType.TWITTER: 8,
            PlatformType.FACEBOOK: 3,
            PlatformType.LINKEDIN: 2,
            PlatformType.INSTAGRAM: 2
        }
    
    def _initialize_optimal_times(self) -> List[OptimalTimeSlot]:
        """Initialize platform-specific optimal posting times based on research"""
        optimal_times = []
        
        # Twitter optimal times (based on engagement research)
        twitter_times = [
            (1, 9, 0.85),   # Monday 9 AM
            (1, 12, 0.82),  # Monday 12 PM
            (1, 15, 0.79),  # Monday 3 PM
            (2, 9, 0.87),   # Tuesday 9 AM
            (2, 12, 0.84),  # Tuesday 12 PM
            (2, 15, 0.81),  # Tuesday 3 PM
            (3, 9, 0.89),   # Wednesday 9 AM
            (3, 12, 0.86),  # Wednesday 12 PM
            (3, 15, 0.83),  # Wednesday 3 PM
            (4, 9, 0.91),   # Thursday 9 AM
            (4, 12, 0.88),  # Thursday 12 PM
            (4, 15, 0.85),  # Thursday 3 PM
            (5, 9, 0.93),   # Friday 9 AM
            (5, 12, 0.90),  # Friday 12 PM
            (5, 15, 0.87),  # Friday 3 PM
            (6, 10, 0.78),  # Saturday 10 AM
            (6, 14, 0.75),  # Saturday 2 PM
            (0, 10, 0.76),  # Sunday 10 AM
            (0, 14, 0.73),  # Sunday 2 PM
        ]
        
        for day, hour, score in twitter_times:
            optimal_times.append(OptimalTimeSlot(
                platform=PlatformType.TWITTER,
                day_of_week=day,
                hour=hour,
                engagement_score=score,
                content_types=[ContentType.TWEET, ContentType.BLOG_POST, ContentType.AD_COPY],
                timezone="UTC"
            ))
        
        # Facebook optimal times
        facebook_times = [
            (1, 9, 0.82),   # Monday 9 AM
            (1, 15, 0.79),  # Monday 3 PM
            (2, 9, 0.84),   # Tuesday 9 AM
            (2, 15, 0.81),  # Tuesday 3 PM
            (3, 9, 0.86),   # Wednesday 9 AM
            (3, 15, 0.83),  # Wednesday 3 PM
            (4, 9, 0.88),   # Thursday 9 AM
            (4, 15, 0.85),  # Thursday 3 PM
            (5, 9, 0.90),   # Friday 9 AM
            (5, 15, 0.87),  # Friday 3 PM
            (6, 10, 0.76),  # Saturday 10 AM
            (0, 10, 0.74),  # Sunday 10 AM
        ]
        
        for day, hour, score in facebook_times:
            optimal_times.append(OptimalTimeSlot(
                platform=PlatformType.FACEBOOK,
                day_of_week=day,
                hour=hour,
                engagement_score=score,
                content_types=[ContentType.FACEBOOK_POST, ContentType.BLOG_POST, ContentType.VIDEO],
                timezone="UTC"
            ))
        
        # LinkedIn optimal times
        linkedin_times = [
            (1, 8, 0.85),   # Monday 8 AM
            (1, 12, 0.82),  # Monday 12 PM
            (2, 8, 0.87),   # Tuesday 8 AM
            (2, 12, 0.84),  # Tuesday 12 PM
            (3, 8, 0.89),   # Wednesday 8 AM
            (3, 12, 0.86),  # Wednesday 12 PM
            (4, 8, 0.91),   # Thursday 8 AM
            (4, 12, 0.88),  # Thursday 12 PM
            (5, 8, 0.93),   # Friday 8 AM
            (5, 12, 0.90),  # Friday 12 PM
        ]
        
        for day, hour, score in linkedin_times:
            optimal_times.append(OptimalTimeSlot(
                platform=PlatformType.LINKEDIN,
                day_of_week=day,
                hour=hour,
                engagement_score=score,
                content_types=[ContentType.LINKEDIN_ARTICLE, ContentType.BLOG_POST, ContentType.AD_COPY],
                timezone="UTC"
            ))
        
        # Instagram optimal times
        instagram_times = [
            (1, 11, 0.83),  # Monday 11 AM
            (1, 15, 0.80),  # Monday 3 PM
            (2, 11, 0.85),  # Tuesday 11 AM
            (2, 15, 0.82),  # Tuesday 3 PM
            (3, 11, 0.87),  # Wednesday 11 AM
            (3, 15, 0.84),  # Wednesday 3 PM
            (4, 11, 0.89),  # Thursday 11 AM
            (4, 15, 0.86),  # Thursday 3 PM
            (5, 11, 0.91),  # Friday 11 AM
            (5, 15, 0.88),  # Friday 3 PM
            (6, 10, 0.77),  # Saturday 10 AM
            (6, 14, 0.74),  # Saturday 2 PM
            (0, 10, 0.75),  # Sunday 10 AM
            (0, 14, 0.72),  # Sunday 2 PM
        ]
        
        for day, hour, score in instagram_times:
            optimal_times.append(OptimalTimeSlot(
                platform=PlatformType.INSTAGRAM,
                day_of_week=day,
                hour=hour,
                engagement_score=score,
                content_types=[ContentType.INSTAGRAM_POST, ContentType.IMAGE, ContentType.VIDEO],
                timezone="UTC"
            ))
        
        return optimal_times
    
    def _initialize_content_weights(self) -> Dict[ContentType, float]:
        """Initialize content type engagement weights"""
        return {
            ContentType.BLOG_POST: 1.0,
            ContentType.TWEET: 0.8,
            ContentType.LINKEDIN_ARTICLE: 0.9,
            ContentType.FACEBOOK_POST: 0.85,
            ContentType.INSTAGRAM_POST: 0.9,
            ContentType.AD_COPY: 0.7,
            ContentType.NEWSLETTER: 0.75,
            ContentType.VIDEO: 1.1,  # Videos typically get higher engagement
            ContentType.IMAGE: 0.95
        }
    
    def _initialize_platform_weights(self) -> Dict[PlatformType, float]:
        """Initialize platform engagement weights"""
        return {
            PlatformType.TWITTER: 1.0,
            PlatformType.FACEBOOK: 0.9,
            PlatformType.LINKEDIN: 0.85,
            PlatformType.INSTAGRAM: 0.95
        }
    
    async def optimize_schedule(
        self,
        request: SchedulingRequest,
        existing_schedule: List[Dict[str, Any]] = None
    ) -> List[SchedulingResult]:
        """
        Optimize content scheduling across platforms
        
        Args:
            request: Scheduling request with content and platform details
            existing_schedule: Current scheduled posts to avoid conflicts
            
        Returns:
            List of optimized scheduling results
        """
        try:
            results = []
            existing_schedule = existing_schedule or []
            
            for platform in request.platforms:
                # Find optimal time slots for this platform and content type
                optimal_slots = self._find_optimal_slots(
                    platform, request.content_type, request.timezone
                )
                
                # Filter out conflicting times
                available_slots = self._filter_conflicting_slots(
                    optimal_slots, existing_schedule, platform, request.avoid_cannibalization
                )
                
                if not available_slots:
                    # No optimal slots available, find best alternative
                    alternative_slot = self._find_alternative_slot(
                        platform, request.content_type, existing_schedule, request.timezone
                    )
                    if alternative_slot:
                        results.append(SchedulingResult(
                            content_id=request.content_id,
                            platform=platform,
                            scheduled_time=alternative_slot.scheduled_time,
                            engagement_score=alternative_slot.engagement_score * 0.7,  # Penalty for non-optimal
                            reason="Alternative slot used - optimal slots unavailable",
                            conflicts=["No optimal slots available"]
                        ))
                    continue
                
                # Select best available slot
                best_slot = self._select_best_slot(available_slots, request.priority)
                
                # Calculate final engagement score
                final_score = self._calculate_engagement_score(
                    best_slot, request.content_type, request.priority
                )
                
                results.append(SchedulingResult(
                    content_id=request.content_id,
                    platform=platform,
                    scheduled_time=best_slot.scheduled_time,
                    engagement_score=final_score,
                    reason=f"Optimal slot selected - {best_slot.reason}",
                    conflicts=best_slot.conflicts or []
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to optimize schedule: {e}")
            return []
    
    def _find_optimal_slots(
        self,
        platform: PlatformType,
        content_type: ContentType,
        timezone: str
    ) -> List[OptimalTimeSlot]:
        """Find optimal time slots for a platform and content type"""
        slots = []
        
        for slot in self.optimal_times:
            if (slot.platform == platform and 
                content_type in slot.content_types):
                
                # Convert to target timezone
                slot_copy = OptimalTimeSlot(
                    platform=slot.platform,
                    day_of_week=slot.day_of_week,
                    hour=slot.hour,
                    engagement_score=slot.engagement_score,
                    content_types=slot.content_types,
                    timezone=timezone
                )
                slots.append(slot_copy)
        
        # Sort by engagement score (highest first)
        slots.sort(key=lambda x: x.engagement_score, reverse=True)
        return slots
    
    def _filter_conflicting_slots(
        self,
        slots: List[OptimalTimeSlot],
        existing_schedule: List[Dict[str, Any]],
        platform: PlatformType,
        avoid_cannibalization: bool
    ) -> List[OptimalTimeSlot]:
        """Filter out slots that conflict with existing schedule"""
        if not existing_schedule:
            return slots
        
        available_slots = []
        
        for slot in slots:
            # Calculate next occurrence of this time slot
            next_occurrence = self._get_next_occurrence(slot)
            
            # Check for conflicts
            has_conflict = False
            conflicts = []
            
            for scheduled_post in existing_schedule:
                if scheduled_post.get("platform") == platform.value:
                    scheduled_time = scheduled_post.get("scheduled_time")
                    if scheduled_time:
                        if isinstance(scheduled_time, str):
                            scheduled_time = datetime.fromisoformat(scheduled_time)
                        
                        # Check if too close to existing post
                        time_diff = abs((next_occurrence - scheduled_time).total_seconds() / 60)
                        if time_diff < self.min_interval_minutes:
                            has_conflict = True
                            conflicts.append(f"Too close to existing post (diff: {time_diff:.0f} min)")
                        
                        # Check for cannibalization (same day, similar time)
                        if avoid_cannibalization:
                            same_day = next_occurrence.date() == scheduled_time.date()
                            similar_time = abs(next_occurrence.hour - scheduled_time.hour) <= 2
                            if same_day and similar_time:
                                has_conflict = True
                                conflicts.append("Potential content cannibalization")
            
            if not has_conflict:
                slot_copy = OptimalTimeSlot(
                    platform=slot.platform,
                    day_of_week=slot.day_of_week,
                    hour=slot.hour,
                    engagement_score=slot.engagement_score,
                    content_types=slot.content_types,
                    timezone=slot.timezone
                )
                slot_copy.conflicts = conflicts
                available_slots.append(slot_copy)
        
        return available_slots
    
    def _get_next_occurrence(self, slot: OptimalTimeSlot) -> datetime:
        """Get the next occurrence of a time slot"""
        now = datetime.now(pytz.UTC)
        
        # Find next occurrence of this day/hour combination
        current_day = now.weekday()
        current_hour = now.hour
        
        # Calculate days to add
        days_to_add = (slot.day_of_week - current_day) % 7
        
        # If it's today, check if the hour has passed
        if days_to_add == 0 and current_hour >= slot.hour:
            days_to_add = 7
        
        # Calculate target datetime
        target_date = now.date() + timedelta(days=days_to_add)
        target_datetime = datetime.combine(target_date, time(slot.hour))
        
        # Apply timezone
        target_timezone = pytz.timezone(slot.timezone)
        target_datetime = target_timezone.localize(target_datetime)
        
        return target_datetime
    
    def _find_alternative_slot(
        self,
        platform: PlatformType,
        content_type: ContentType,
        existing_schedule: List[Dict[str, Any]],
        timezone: str
    ) -> Optional[OptimalTimeSlot]:
        """Find an alternative time slot when optimal slots are unavailable"""
        # Look for any available time in the next 7 days
        now = datetime.now(pytz.UTC)
        
        for day_offset in range(7):
            for hour in range(6, 22):  # 6 AM to 10 PM
                test_time = now + timedelta(days=day_offset)
                test_time = test_time.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Check if this time conflicts with existing schedule
                has_conflict = False
                for scheduled_post in existing_schedule:
                    if scheduled_post.get("platform") == platform.value:
                        scheduled_time = scheduled_post.get("scheduled_time")
                        if scheduled_time:
                            if isinstance(scheduled_time, str):
                                scheduled_time = datetime.fromisoformat(scheduled_time)
                            
                            time_diff = abs((test_time - scheduled_time).total_seconds() / 60)
                            if time_diff < self.min_interval_minutes:
                                has_conflict = True
                                break
                
                if not has_conflict:
                    # Create alternative slot
                    alternative_slot = OptimalTimeSlot(
                        platform=platform,
                        day_of_week=test_time.weekday(),
                        hour=test_time.hour,
                        engagement_score=0.5,  # Lower score for non-optimal times
                        content_types=[content_type],
                        timezone=timezone
                    )
                    alternative_slot.scheduled_time = test_time
                    alternative_slot.reason = "Alternative slot - optimal times unavailable"
                    return alternative_slot
        
        return None
    
    def _select_best_slot(
        self,
        available_slots: List[OptimalTimeSlot],
        priority: int
    ) -> OptimalTimeSlot:
        """Select the best available slot based on priority and engagement"""
        if not available_slots:
            raise ValueError("No available slots provided")
        
        # For high priority content, prefer highest engagement
        if priority <= 2:
            return max(available_slots, key=lambda x: x.engagement_score)
        
        # For lower priority, consider some randomization to spread content
        import random
        top_slots = sorted(available_slots, key=lambda x: x.engagement_score, reverse=True)[:3]
        return random.choice(top_slots)
    
    def _calculate_engagement_score(
        self,
        slot: OptimalTimeSlot,
        content_type: ContentType,
        priority: int
    ) -> float:
        """Calculate final engagement score considering all factors"""
        base_score = slot.engagement_score
        
        # Apply content type weight
        content_weight = self.content_type_weights.get(content_type, 1.0)
        weighted_score = base_score * content_weight
        
        # Apply platform weight
        platform_weight = self.platform_weights.get(slot.platform, 1.0)
        weighted_score *= platform_weight
        
        # Apply priority adjustment
        priority_multiplier = 1.0 + (5 - priority) * 0.1  # Higher priority = higher score
        final_score = weighted_score * priority_multiplier
        
        # Normalize to 0.0-1.0 range
        return min(max(final_score, 0.0), 1.0)
    
    def get_scheduling_recommendations(
        self,
        content_type: ContentType,
        platforms: List[PlatformType],
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Get scheduling recommendations for content planning"""
        recommendations = {}
        
        for platform in platforms:
            optimal_slots = self._find_optimal_slots(platform, content_type, timezone)
            
            if optimal_slots:
                best_slots = optimal_slots[:3]  # Top 3 slots
                recommendations[platform.value] = {
                    "best_times": [
                        {
                            "day": self._get_day_name(slot.day_of_week),
                            "hour": slot.hour,
                            "engagement_score": slot.engagement_score,
                            "formatted_time": f"{self._get_day_name(slot.day_of_week)} {slot.hour:02d}:00"
                        }
                        for slot in best_slots
                    ],
                    "total_optimal_slots": len(optimal_slots),
                    "platform_weight": self.platform_weights.get(platform, 1.0)
                }
            else:
                recommendations[platform.value] = {
                    "best_times": [],
                    "total_optimal_slots": 0,
                    "message": f"No optimal times found for {content_type.value} on {platform.value}"
                }
        
        return recommendations
    
    def _get_day_name(self, day_of_week: int) -> str:
        """Convert day of week number to name"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[day_of_week]
    
    def validate_schedule(
        self,
        schedule: List[SchedulingResult]
    ) -> Dict[str, Any]:
        """Validate a proposed schedule for conflicts and issues"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "conflicts": []
        }
        
        # Check for platform-specific daily limits
        platform_counts = {}
        for result in schedule:
            platform = result.platform.value
            date = result.scheduled_time.date()
            key = f"{platform}_{date}"
            
            if key not in platform_counts:
                platform_counts[key] = 0
            platform_counts[key] += 1
            
            # Check daily limit
            max_posts = self.max_daily_posts.get(result.platform, 5)
            if platform_counts[key] > max_posts:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Too many posts scheduled for {platform} on {date}: {platform_counts[key]} > {max_posts}"
                )
        
        # Check for time conflicts
        for i, result1 in enumerate(schedule):
            for j, result2 in enumerate(schedule[i+1:], i+1):
                if result1.platform == result2.platform:
                    time_diff = abs((result1.scheduled_time - result2.scheduled_time).total_seconds() / 60)
                    if time_diff < self.min_interval_minutes:
                        validation_result["warnings"].append(
                            f"Posts scheduled too close on {result1.platform.value}: "
                            f"{time_diff:.0f} minutes apart (min: {self.min_interval_minutes})"
                        )
        
        # Check for content cannibalization
        for i, result1 in enumerate(schedule):
            for j, result2 in enumerate(schedule[i+1:], i+1):
                same_day = result1.scheduled_time.date() == result2.scheduled_time.date()
                similar_time = abs(result1.scheduled_time.hour - result2.scheduled_time.hour) <= 2
                
                if same_day and similar_time:
                    validation_result["warnings"].append(
                        f"Potential content cannibalization: {result1.platform.value} and {result2.platform.value} "
                        f"scheduled on {result1.scheduled_time.date()} at similar times"
                    )
        
        return validation_result




