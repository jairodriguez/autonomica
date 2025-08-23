"""
Vercel KV Service for Analytics Data Storage
Extends Redis service to work with Vercel KV (Redis-compatible) for analytics data storage
with user-scoped namespacing and multi-tenant security.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

try:
    from vercel_kv import kv
    VERCEL_KV_AVAILABLE = True
except ImportError:
    VERCEL_KV_AVAILABLE = False
    logging.warning("Vercel KV not available, falling back to Redis")

from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

class AnalyticsDataType(Enum):
    """Types of analytics data for storage"""
    SOCIAL_MEDIA = "social_media"
    SEO = "seo"
    CONTENT = "content"
    USER_BEHAVIOR = "user_behavior"
    SYSTEM = "system"
    KPI = "kpi"
    GROWTH = "growth"
    REPORTS = "reports"

class DataRetentionPolicy(Enum):
    """Data retention policies for analytics data"""
    REAL_TIME = "real_time"      # 5 minutes
    HOURLY = "hourly"            # 1 hour
    DAILY = "daily"              # 24 hours
    WEEKLY = "weekly"            # 7 days
    MONTHLY = "monthly"          # 30 days
    QUARTERLY = "quarterly"      # 90 days
    YEARLY = "yearly"            # 365 days
    PERMANENT = "permanent"      # No expiration

@dataclass
class AnalyticsDataRecord:
    """Analytics data record for storage"""
    id: str
    user_id: str
    data_type: AnalyticsDataType
    source_id: str
    metric_name: str
    metric_value: Union[int, float, str, Dict[str, Any]]
    timestamp: datetime
    metadata: Dict[str, Any] = None
    platform: Optional[str] = None
    retention_policy: DataRetentionPolicy = DataRetentionPolicy.DAILY

@dataclass
class StorageStats:
    """Storage statistics for analytics data"""
    total_records: int
    total_size_bytes: int
    records_by_type: Dict[str, int]
    records_by_user: Dict[str, int]
    oldest_record: Optional[datetime]
    newest_record: Optional[datetime]
    storage_efficiency: float

class VercelKVService:
    """
    Vercel KV service for analytics data storage
    
    Features:
    - User-scoped namespacing for multi-tenant security
    - Configurable data retention policies
    - Efficient data storage and retrieval
    - Background cleanup and optimization
    - Storage statistics and monitoring
    - Fallback to Redis when Vercel KV unavailable
    """
    
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service
        self.use_vercel_kv = VERCEL_KV_AVAILABLE
        
        # Storage configuration
        self.default_retention_policies = {
            AnalyticsDataType.SOCIAL_MEDIA: DataRetentionPolicy.REAL_TIME,
            AnalyticsDataType.SEO: DataRetentionPolicy.DAILY,
            AnalyticsDataType.CONTENT: DataRetentionPolicy.HOURLY,
            AnalyticsDataType.USER_BEHAVIOR: DataRetentionPolicy.REAL_TIME,
            AnalyticsDataType.SYSTEM: DataRetentionPolicy.HOURLY,
            AnalyticsDataType.KPI: DataRetentionPolicy.DAILY,
            AnalyticsDataType.GROWTH: DataRetentionPolicy.WEEKLY,
            AnalyticsDataType.REPORTS: DataRetentionPolicy.MONTHLY
        }
        
        # TTL mappings for retention policies
        self.retention_ttl = {
            DataRetentionPolicy.REAL_TIME: 300,      # 5 minutes
            DataRetentionPolicy.HOURLY: 3600,        # 1 hour
            DataRetentionPolicy.DAILY: 86400,        # 24 hours
            DataRetentionPolicy.WEEKLY: 604800,      # 7 days
            DataRetentionPolicy.MONTHLY: 2592000,    # 30 days
            DataRetentionPolicy.QUARTERLY: 7776000,  # 90 days
            DataRetentionPolicy.YEARLY: 31536000,    # 365 days
            DataRetentionPolicy.PERMANENT: 0         # No expiration
        }
        
        # Key patterns for different data types
        self.key_patterns = {
            AnalyticsDataType.SOCIAL_MEDIA: "user:{user_id}:social:{platform}:{date}",
            AnalyticsDataType.SEO: "user:{user_id}:seo:{source}:{date}",
            AnalyticsDataType.CONTENT: "user:{user_id}:content:{content_id}:{date}",
            AnalyticsDataType.USER_BEHAVIOR: "user:{user_id}:behavior:{session_id}:{date}",
            AnalyticsDataType.SYSTEM: "user:{user_id}:system:{metric}:{date}",
            AnalyticsDataType.KPI: "user:{user_id}:kpi:{kpi_name}:{period}",
            AnalyticsDataType.GROWTH: "user:{user_id}:growth:{metric}:{period}",
            AnalyticsDataType.REPORTS: "user:{user_id}:reports:{report_type}:{date}"
        }
        
        # Initialize storage
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage service"""
        if self.use_vercel_kv:
            logger.info("Initialized Vercel KV service for analytics data storage")
        else:
            logger.info("Vercel KV not available, using Redis fallback for analytics data storage")
    
    async def store_analytics_data(
        self,
        user_id: str,
        data_type: AnalyticsDataType,
        source_id: str,
        metric_name: str,
        metric_value: Union[int, float, str, Dict[str, Any]],
        platform: Optional[str] = None,
        retention_policy: Optional[DataRetentionPolicy] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store analytics data with user-scoped namespacing
        
        Args:
            user_id: User ID for multi-tenant isolation
            data_type: Type of analytics data
            source_id: Source identifier (content_id, platform, etc.)
            metric_name: Name of the metric
            metric_value: Value of the metric
            platform: Platform identifier (for social media data)
            retention_policy: Data retention policy
            metadata: Additional metadata
            
        Returns:
            Record ID of the stored data
        """
        try:
            # Generate record ID
            record_id = str(uuid.uuid4())
            
            # Determine retention policy
            if retention_policy is None:
                retention_policy = self.default_retention_policies.get(data_type, DataRetentionPolicy.DAILY)
            
            # Create data record
            record = AnalyticsDataRecord(
                id=record_id,
                user_id=user_id,
                data_type=data_type,
                source_id=source_id,
                metric_name=metric_name,
                metric_value=metric_value,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                platform=platform,
                retention_policy=retention_policy
            )
            
            # Generate storage key
            storage_key = self._generate_storage_key(record)
            
            # Store data
            if self.use_vercel_kv:
                await self._store_in_vercel_kv(storage_key, record, retention_policy)
            else:
                await self._store_in_redis(storage_key, record, retention_policy)
            
            # Store record metadata for indexing
            await self._store_record_index(record)
            
            logger.debug(f"Stored analytics data: {storage_key}")
            return record_id
            
        except Exception as e:
            logger.error(f"Error storing analytics data: {e}")
            raise
    
    async def retrieve_analytics_data(
        self,
        user_id: str,
        data_type: AnalyticsDataType,
        source_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        platform: Optional[str] = None,
        limit: int = 100
    ) -> List[AnalyticsDataRecord]:
        """
        Retrieve analytics data with filtering
        
        Args:
            user_id: User ID for multi-tenant isolation
            data_type: Type of analytics data to retrieve
            source_id: Filter by source ID
            metric_name: Filter by metric name
            start_date: Start date for time range filtering
            end_date: End date for time range filtering
            platform: Filter by platform (for social media data)
            limit: Maximum number of records to return
            
        Returns:
            List of analytics data records
        """
        try:
            # Build search pattern
            search_pattern = self._build_search_pattern(
                user_id, data_type, source_id, metric_name, platform
            )
            
            # Get matching keys
            matching_keys = await self._get_matching_keys(search_pattern)
            
            # Filter by date range if specified
            if start_date or end_date:
                matching_keys = await self._filter_keys_by_date(
                    matching_keys, start_date, end_date
                )
            
            # Limit results
            matching_keys = matching_keys[:limit]
            
            # Retrieve data records
            records = []
            for key in matching_keys:
                try:
                    record = await self._retrieve_record(key)
                    if record:
                        records.append(record)
                except Exception as e:
                    logger.warning(f"Error retrieving record from {key}: {e}")
                    continue
            
            # Sort by timestamp (newest first)
            records.sort(key=lambda x: x.timestamp, reverse=True)
            
            logger.debug(f"Retrieved {len(records)} analytics records for user {user_id}")
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving analytics data: {e}")
            raise
    
    async def get_analytics_summary(
        self,
        user_id: str,
        data_type: AnalyticsDataType,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get analytics summary for a specific period
        
        Args:
            user_id: User ID for multi-tenant isolation
            data_type: Type of analytics data
            period: Time period (7d, 30d, 90d, 1y)
            
        Returns:
            Summary statistics for the period
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Retrieve data for the period
            records = await self.retrieve_analytics_data(
                user_id, data_type, start_date=start_date, end_date=end_date
            )
            
            # Calculate summary statistics
            summary = self._calculate_summary_statistics(records, period)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            raise
    
    async def delete_analytics_data(
        self,
        user_id: str,
        data_type: AnalyticsDataType,
        source_id: Optional[str] = None,
        before_date: Optional[datetime] = None
    ) -> int:
        """
        Delete analytics data based on criteria
        
        Args:
            user_id: User ID for multi-tenant isolation
            data_type: Type of analytics data to delete
            source_id: Filter by source ID
            before_date: Delete data before this date
            
        Returns:
            Number of records deleted
        """
        try:
            # Build search pattern
            search_pattern = self._build_search_pattern(user_id, data_type, source_id)
            
            # Get matching keys
            matching_keys = await self._get_matching_keys(search_pattern)
            
            # Filter by date if specified
            if before_date:
                matching_keys = await self._filter_keys_by_date(
                    matching_keys, end_date=before_date
                )
            
            # Delete records
            deleted_count = 0
            for key in matching_keys:
                try:
                    if self.use_vercel_kv:
                        await kv.delete(key)
                    else:
                        await self.redis_service.delete(key)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error deleting record {key}: {e}")
                    continue
            
            # Clean up index entries
            await self._cleanup_record_indexes(user_id, data_type, source_id)
            
            logger.info(f"Deleted {deleted_count} analytics records for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting analytics data: {e}")
            raise
    
    async def get_storage_stats(self, user_id: Optional[str] = None) -> StorageStats:
        """
        Get storage statistics
        
        Args:
            user_id: Optional user ID for user-specific stats
            
        Returns:
            Storage statistics
        """
        try:
            if user_id:
                # Get user-specific stats
                pattern = f"user:{user_id}:*"
            else:
                # Get global stats
                pattern = "*"
            
            # Get all keys matching pattern
            all_keys = await self._get_matching_keys(pattern)
            
            # Calculate statistics
            total_records = len(all_keys)
            total_size_bytes = 0
            records_by_type = {}
            records_by_user = {}
            timestamps = []
            
            for key in all_keys:
                try:
                    # Parse key to get type and user info
                    key_parts = key.split(":")
                    if len(key_parts) >= 2:
                        user_id_from_key = key_parts[1]
                        data_type = key_parts[2] if len(key_parts) > 2 else "unknown"
                        
                        # Count by type
                        records_by_type[data_type] = records_by_type.get(data_type, 0) + 1
                        
                        # Count by user
                        records_by_user[user_id_from_key] = records_by_user.get(user_id_from_key, 0) + 1
                    
                    # Get record size
                    record = await self._retrieve_record(key)
                    if record:
                        record_size = len(json.dumps(asdict(record)).encode('utf-8'))
                        total_size_bytes += record_size
                        timestamps.append(record.timestamp)
                        
                except Exception as e:
                    logger.warning(f"Error processing key {key} for stats: {e}")
                    continue
            
            # Calculate time range
            oldest_record = min(timestamps) if timestamps else None
            newest_record = max(timestamps) if timestamps else None
            
            # Calculate storage efficiency (compression ratio estimate)
            storage_efficiency = 0.8  # Placeholder: would calculate actual compression ratio
            
            return StorageStats(
                total_records=total_records,
                total_size_bytes=total_size_bytes,
                records_by_type=records_by_type,
                records_by_user=records_by_user,
                oldest_record=oldest_record,
                newest_record=newest_record,
                storage_efficiency=storage_efficiency
            )
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            raise
    
    async def cleanup_expired_data(self) -> int:
        """
        Clean up expired data based on retention policies
        
        Returns:
            Number of records cleaned up
        """
        try:
            cleaned_count = 0
            current_time = datetime.utcnow()
            
            # Get all keys
            all_keys = await self._get_matching_keys("*")
            
            for key in all_keys:
                try:
                    # Check if key should be expired
                    if await self._should_expire_key(key, current_time):
                        if self.use_vercel_kv:
                            await kv.delete(key)
                        else:
                            await self.redis_service.delete(key)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error checking expiration for key {key}: {e}")
                    continue
            
            logger.info(f"Cleaned up {cleaned_count} expired analytics records")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {e}")
            raise
    
    def _generate_storage_key(self, record: AnalyticsDataRecord) -> str:
        """Generate storage key for analytics data"""
        date_str = record.timestamp.strftime("%Y%m%d")
        
        if record.data_type == AnalyticsDataType.SOCIAL_MEDIA:
            platform = record.platform or "unknown"
            return f"user:{record.user_id}:social:{platform}:{date_str}:{record.id}"
        
        elif record.data_type == AnalyticsDataType.SEO:
            return f"user:{record.user_id}:seo:{record.source_id}:{date_str}:{record.id}"
        
        elif record.data_type == AnalyticsDataType.CONTENT:
            return f"user:{record.user_id}:content:{record.source_id}:{date_str}:{record.id}"
        
        elif record.data_type == AnalyticsDataType.USER_BEHAVIOR:
            return f"user:{record.user_id}:behavior:{record.source_id}:{date_str}:{record.id}"
        
        elif record.data_type == AnalyticsDataType.SYSTEM:
            return f"user:{record.user_id}:system:{record.metric_name}:{date_str}:{record.id}"
        
        elif record.data_type == AnalyticsDataType.KPI:
            return f"user:{record.user_id}:kpi:{record.metric_name}:{record.source_id}:{record.id}"
        
        elif record.data_type == AnalyticsDataType.GROWTH:
            return f"user:{record.user_id}:growth:{record.metric_name}:{record.source_id}:{record.id}"
        
        elif record.data_type == AnalyticsDataType.REPORTS:
            return f"user:{record.user_id}:reports:{record.source_id}:{date_str}:{record.id}"
        
        else:
            return f"user:{record.user_id}:{record.data_type.value}:{record.source_id}:{date_str}:{record.id}"
    
    def _build_search_pattern(
        self,
        user_id: str,
        data_type: AnalyticsDataType,
        source_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        platform: Optional[str] = None
    ) -> str:
        """Build search pattern for data retrieval"""
        pattern = f"user:{user_id}:{data_type.value}"
        
        if source_id:
            pattern += f":{source_id}"
        
        if metric_name:
            pattern += f":{metric_name}"
        
        if platform and data_type == AnalyticsDataType.SOCIAL_MEDIA:
            pattern += f":{platform}"
        
        pattern += ":*"
        return pattern
    
    async def _store_in_vercel_kv(
        self,
        key: str,
        record: AnalyticsDataRecord,
        retention_policy: DataRetentionPolicy
    ):
        """Store data in Vercel KV"""
        try:
            # Serialize record
            record_data = json.dumps(asdict(record), default=str)
            
            # Set TTL based on retention policy
            ttl = self.retention_ttl.get(retention_policy, 86400)
            
            if ttl > 0:
                await kv.set(key, record_data, ex=ttl)
            else:
                await kv.set(key, record_data)
                
        except Exception as e:
            logger.error(f"Error storing in Vercel KV: {e}")
            raise
    
    async def _store_in_redis(
        self,
        key: str,
        record: AnalyticsDataRecord,
        retention_policy: DataRetentionPolicy
    ):
        """Store data in Redis (fallback)"""
        try:
            # Serialize record
            record_data = json.dumps(asdict(record), default=str)
            
            # Set TTL based on retention policy
            ttl = self.retention_ttl.get(retention_policy, 86400)
            
            await self.redis_service.set(key, record_data, ttl=ttl)
            
        except Exception as e:
            logger.error(f"Error storing in Redis: {e}")
            raise
    
    async def _store_record_index(self, record: AnalyticsDataRecord):
        """Store record index for efficient retrieval"""
        try:
            index_key = f"index:user:{record.user_id}:{record.data_type.value}:{record.id}"
            index_data = {
                "key": self._generate_storage_key(record),
                "timestamp": record.timestamp.isoformat(),
                "source_id": record.source_id,
                "metric_name": record.metric_name
            }
            
            if self.use_vercel_kv:
                await kv.set(index_key, json.dumps(index_data), ex=86400)  # 24 hour TTL
            else:
                await self.redis_service.set(index_key, json.dumps(index_data), ttl=86400)
                
        except Exception as e:
            logger.warning(f"Error storing record index: {e}")
    
    async def _get_matching_keys(self, pattern: str) -> List[str]:
        """Get keys matching a pattern"""
        try:
            if self.use_vercel_kv:
                # Vercel KV doesn't support pattern matching like Redis
                # We'll need to implement a different approach
                # For now, return empty list and log warning
                logger.warning("Pattern matching not supported in Vercel KV, returning empty list")
                return []
            else:
                # Use Redis pattern matching
                return await self.redis_service.keys(pattern)
                
        except Exception as e:
            logger.error(f"Error getting matching keys: {e}")
            return []
    
    async def _filter_keys_by_date(
        self,
        keys: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[str]:
        """Filter keys by date range"""
        try:
            filtered_keys = []
            
            for key in keys:
                try:
                    # Extract date from key (assuming format includes date)
                    if ":" in key:
                        date_part = key.split(":")[-2]  # Second to last part
                        if len(date_part) == 8:  # YYYYMMDD format
                            key_date = datetime.strptime(date_part, "%Y%m%d")
                            
                            # Apply date filters
                            if start_date and key_date < start_date:
                                continue
                            if end_date and key_date > end_date:
                                continue
                            
                            filtered_keys.append(key)
                        else:
                            # If no date in key, include it
                            filtered_keys.append(key)
                    else:
                        filtered_keys.append(key)
                        
                except Exception as e:
                    logger.warning(f"Error parsing date from key {key}: {e}")
                    filtered_keys.append(key)
            
            return filtered_keys
            
        except Exception as e:
            logger.error(f"Error filtering keys by date: {e}")
            return keys
    
    async def _retrieve_record(self, key: str) -> Optional[AnalyticsDataRecord]:
        """Retrieve a single record"""
        try:
            if self.use_vercel_kv:
                record_data = await kv.get(key)
            else:
                record_data = await self.redis_service.get(key)
            
            if record_data:
                record_dict = json.loads(record_data)
                # Convert timestamp string back to datetime
                record_dict["timestamp"] = datetime.fromisoformat(record_dict["timestamp"])
                return AnalyticsDataRecord(**record_dict)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving record from {key}: {e}")
            return None
    
    async def _should_expire_key(self, key: str, current_time: datetime) -> bool:
        """Check if a key should be expired based on retention policy"""
        try:
            # Extract data type from key
            key_parts = key.split(":")
            if len(key_parts) < 3:
                return False
            
            data_type_str = key_parts[2]
            data_type = None
            
            for dt in AnalyticsDataType:
                if dt.value == data_type_str:
                    data_type = dt
                    break
            
            if not data_type:
                return False
            
            # Get retention policy
            retention_policy = self.default_retention_policies.get(data_type, DataRetentionPolicy.DAILY)
            ttl_seconds = self.retention_ttl.get(retention_policy, 86400)
            
            if ttl_seconds == 0:  # Permanent
                return False
            
            # Extract date from key
            if ":" in key:
                date_part = key.split(":")[-2]
                if len(date_part) == 8:  # YYYYMMDD format
                    key_date = datetime.strptime(date_part, "%Y%m%d")
                    age_seconds = (current_time - key_date).total_seconds()
                    return age_seconds > ttl_seconds
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking expiration for key {key}: {e}")
            return False
    
    async def _cleanup_record_indexes(
        self,
        user_id: str,
        data_type: AnalyticsDataType,
        source_id: Optional[str] = None
    ):
        """Clean up record indexes"""
        try:
            pattern = f"index:user:{user_id}:{data_type.value}"
            if source_id:
                pattern += f":{source_id}"
            pattern += ":*"
            
            index_keys = await self._get_matching_keys(pattern)
            
            for index_key in index_keys:
                try:
                    if self.use_vercel_kv:
                        await kv.delete(index_key)
                    else:
                        await self.redis_service.delete(index_key)
                except Exception as e:
                    logger.warning(f"Error deleting index key {index_key}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error cleaning up record indexes: {e}")
    
    def _calculate_summary_statistics(
        self,
        records: List[AnalyticsDataRecord],
        period: str
    ) -> Dict[str, Any]:
        """Calculate summary statistics for analytics data"""
        try:
            if not records:
                return {
                    "period": period,
                    "total_records": 0,
                    "metrics": {},
                    "trends": {}
                }
            
            # Group by metric name
            metrics_data = {}
            for record in records:
                metric_name = record.metric_name
                if metric_name not in metrics_data:
                    metrics_data[metric_name] = []
                metrics_data[metric_name].append(record.metric_value)
            
            # Calculate statistics for each metric
            summary = {
                "period": period,
                "total_records": len(records),
                "metrics": {},
                "trends": {},
                "data_types": {},
                "platforms": {}
            }
            
            for metric_name, values in metrics_data.items():
                # Filter numeric values
                numeric_values = [v for v in values if isinstance(v, (int, float))]
                
                if numeric_values:
                    summary["metrics"][metric_name] = {
                        "count": len(numeric_values),
                        "sum": sum(numeric_values),
                        "average": sum(numeric_values) / len(numeric_values),
                        "min": min(numeric_values),
                        "max": max(numeric_values)
                    }
                else:
                    summary["metrics"][metric_name] = {
                        "count": len(values),
                        "values": list(set(values))  # Unique values
                    }
            
            # Count by data type
            for record in records:
                data_type = record.data_type.value
                summary["data_types"][data_type] = summary["data_types"].get(data_type, 0) + 1
            
            # Count by platform
            for record in records:
                if record.platform:
                    platform = record.platform
                    summary["platforms"][platform] = summary["platforms"].get(platform, 0) + 1
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating summary statistics: {e}")
            return {
                "period": period,
                "total_records": 0,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the Vercel KV service"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "vercel_kv" if self.use_vercel_kv else "redis_fallback",
                "vercel_kv_available": VERCEL_KV_AVAILABLE,
                "storage_connection": "healthy"
            }
            
            # Test storage connection
            try:
                test_key = "health_check_test"
                test_data = {"test": True, "timestamp": datetime.utcnow().isoformat()}
                
                if self.use_vercel_kv:
                    await kv.set(test_key, json.dumps(test_data), ex=60)
                    retrieved_data = await kv.get(test_key)
                    await kv.delete(test_key)
                else:
                    await self.redis_service.set(test_key, json.dumps(test_data), ttl=60)
                    retrieved_data = await self.redis_service.get(test_key)
                    await self.redis_service.delete(test_key)
                
                if retrieved_data:
                    health_status["storage_connection"] = "healthy"
                else:
                    health_status["storage_connection"] = "unhealthy"
                    health_status["status"] = "degraded"
                    
            except Exception as e:
                health_status["storage_connection"] = "unhealthy"
                health_status["status"] = "degraded"
                health_status["storage_error"] = str(e)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in Vercel KV service health check: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }




