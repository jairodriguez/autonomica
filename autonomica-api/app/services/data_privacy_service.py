import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.vercel_kv_service import VercelKVService
from app.services.analytics_auth_service import AnalyticsAuthService, UserRole, Permission


class DataCategory(Enum):
    """Categories of data for privacy compliance"""
    PERSONAL = "personal"           # Personally identifiable information
    ANALYTICS = "analytics"         # Analytics and performance data
    BEHAVIORAL = "behavioral"       # User behavior and interaction data
    TECHNICAL = "technical"         # Technical and system data
    FINANCIAL = "financial"         # Financial and business data
    SENSITIVE = "sensitive"         # Sensitive personal data


class RetentionPolicy(Enum):
    """Data retention policy types"""
    IMMEDIATE = "immediate"         # Delete immediately
    SHORT_TERM = "short_term"      # 30 days
    MEDIUM_TERM = "medium_term"    # 90 days
    LONG_TERM = "long_term"        # 1 year
    EXTENDED = "extended"          # 3 years
    PERMANENT = "permanent"        # Keep indefinitely


class DataRight(Enum):
    """User data rights under GDPR"""
    ACCESS = "access"               # Right to access personal data
    RECTIFICATION = "rectification" # Right to correct inaccurate data
    ERASURE = "erasure"            # Right to be forgotten
    PORTABILITY = "portability"    # Right to data portability
    RESTRICTION = "restriction"    # Right to restrict processing
    OBJECTION = "objection"        # Right to object to processing


@dataclass
class DataRetentionRule:
    """Rule for data retention policy"""
    id: str
    data_category: DataCategory
    retention_policy: RetentionPolicy
    retention_days: int
    description: str
    legal_basis: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class DataProcessingConsent:
    """User consent for data processing"""
    id: str
    user_id: str
    data_category: DataCategory
    consent_given: bool
    consent_date: datetime
    consent_version: str
    legal_basis: str
    purpose: str
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class DataSubjectRequest:
    """Data subject request (DSR) under GDPR"""
    id: str
    user_id: str
    request_type: DataRight
    status: str  # pending, processing, completed, rejected
    description: str
    requested_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    data_export_path: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class PrivacyAuditLog:
    """Audit log for privacy-related activities"""
    id: str
    user_id: str
    action: str
    data_category: DataCategory
    data_id: Optional[str] = None
    legal_basis: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class DataPrivacyService:
    """Service for managing data privacy and GDPR compliance"""
    
    def __init__(
        self,
        db: AsyncSession,
        redis_service: RedisService,
        cache_service: CacheService,
        vercel_kv_service: VercelKVService,
        auth_service: AnalyticsAuthService
    ):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        self.vercel_kv_service = vercel_kv_service
        self.auth_service = auth_service
        
        # Initialize default retention rules
        self._initialize_retention_rules()
    
    def _initialize_retention_rules(self):
        """Initialize default data retention rules"""
        self.default_retention_rules = {
            DataCategory.PERSONAL: DataRetentionRule(
                id="personal_data_retention",
                data_category=DataCategory.PERSONAL,
                retention_policy=RetentionPolicy.SHORT_TERM,
                retention_days=30,
                description="Personal data retention for analytics purposes",
                legal_basis="Legitimate interest in providing analytics services"
            ),
            DataCategory.ANALYTICS: DataRetentionRule(
                id="analytics_data_retention",
                data_category=DataCategory.ANALYTICS,
                retention_policy=RetentionPolicy.MEDIUM_TERM,
                retention_days=90,
                description="Analytics data retention for performance insights",
                legal_basis="Legitimate interest in improving service performance"
            ),
            DataCategory.BEHAVIORAL: DataRetentionRule(
                id="behavioral_data_retention",
                data_category=DataCategory.BEHAVIORAL,
                retention_policy=RetentionPolicy.SHORT_TERM,
                retention_days=30,
                description="User behavior data retention for UX improvement",
                legal_basis="Legitimate interest in improving user experience"
            ),
            DataCategory.TECHNICAL: DataRetentionRule(
                id="technical_data_retention",
                data_category=DataCategory.TECHNICAL,
                retention_policy=RetentionPolicy.MEDIUM_TERM,
                retention_days=90,
                description="Technical data retention for system maintenance",
                legal_basis="Legitimate interest in system reliability"
            ),
            DataCategory.FINANCIAL: DataRetentionRule(
                id="financial_data_retention",
                data_category=DataCategory.FINANCIAL,
                retention_policy=RetentionPolicy.EXTENDED,
                retention_days=1095,  # 3 years
                description="Financial data retention for compliance",
                legal_basis="Legal obligation for financial record keeping"
            ),
            DataCategory.SENSITIVE: DataRetentionRule(
                id="sensitive_data_retention",
                data_category=DataCategory.SENSITIVE,
                retention_policy=RetentionPolicy.IMMEDIATE,
                retention_days=0,
                description="Sensitive data not retained",
                legal_basis="Data minimization principle"
            )
        }
    
    async def get_retention_rule(
        self,
        data_category: DataCategory
    ) -> Optional[DataRetentionRule]:
        """Get retention rule for a specific data category"""
        
        return self.default_retention_rules.get(data_category)
    
    async def get_all_retention_rules(self) -> List[DataRetentionRule]:
        """Get all retention rules"""
        
        return list(self.default_retention_rules.values())
    
    async def update_retention_rule(
        self,
        admin_user_id: str,
        data_category: DataCategory,
        retention_policy: RetentionPolicy,
        retention_days: int,
        description: str,
        legal_basis: str
    ) -> Optional[DataRetentionRule]:
        """Update retention rule (admin only)"""
        
        try:
            # Check if admin user has permission to manage privacy settings
            if not await self.auth_service.check_permission(admin_user_id, Permission.MANAGE_USERS):
                return None
            
            # Update retention rule
            rule = self.default_retention_rules[data_category]
            rule.retention_policy = retention_policy
            rule.retention_days = retention_days
            rule.description = description
            rule.legal_basis = legal_basis
            rule.updated_at = datetime.utcnow()
            
            # Store updated rule in Vercel KV
            await self.vercel_kv_service.store_analytics_data(
                user_id="system",
                data_type="retention_rules",
                source_id=rule.id,
                data=rule.__dict__,
                ttl=0
            )
            
            # Log the update
            await self._log_privacy_audit(
                user_id=admin_user_id,
                action="update_retention_rule",
                data_category=data_category,
                legal_basis=legal_basis,
                additional_info={
                    "retention_policy": retention_policy.value,
                    "retention_days": retention_days
                }
            )
            
            return rule
            
        except Exception as e:
            await self._log_privacy_audit(
                user_id=admin_user_id,
                action="update_retention_rule_error",
                data_category=data_category,
                legal_basis="error",
                additional_info={"error": str(e)}
            )
            return None
    
    async def record_data_processing_consent(
        self,
        user_id: str,
        data_category: DataCategory,
        consent_given: bool,
        consent_version: str,
        legal_basis: str,
        purpose: str,
        expires_at: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[DataProcessingConsent]:
        """Record user consent for data processing"""
        
        try:
            consent = DataProcessingConsent(
                id=f"consent_{user_id}_{data_category.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                user_id=user_id,
                data_category=data_category,
                consent_given=consent_given,
                consent_date=datetime.utcnow(),
                consent_version=consent_version,
                legal_basis=legal_basis,
                purpose=purpose,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Store consent in Vercel KV
            await self.vercel_kv_service.store_analytics_data(
                user_id=user_id,
                data_type="data_consent",
                source_id=consent.id,
                data=consent.__dict__,
                ttl=0  # No expiration for consent records
            )
            
            # Log consent recording
            await self._log_privacy_audit(
                user_id=user_id,
                action="record_consent",
                data_category=data_category,
                legal_basis=legal_basis,
                additional_info={
                    "consent_given": consent_given,
                    "purpose": purpose,
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
            )
            
            return consent
            
        except Exception as e:
            await self._log_privacy_audit(
                user_id=user_id,
                action="record_consent_error",
                data_category=data_category,
                legal_basis="error",
                additional_info={"error": str(e)}
            )
            return None
    
    async def get_user_consent(
        self,
        user_id: str,
        data_category: DataCategory
    ) -> Optional[DataProcessingConsent]:
        """Get user consent for a specific data category"""
        
        try:
            # Get all consent records for user
            consent_data = await self.vercel_kv_service.get_analytics_data(
                user_id=user_id,
                data_type="data_consent"
            )
            
            # Find the most recent active consent for the category
            active_consents = []
            for consent in consent_data:
                if isinstance(consent, dict):
                    consent_obj = DataProcessingConsent(**consent)
                    if (consent_obj.data_category == data_category and 
                        consent_obj.consent_given and 
                        not consent_obj.revoked_at and
                        (not consent_obj.expires_at or consent_obj.expires_at > datetime.utcnow())):
                        active_consents.append(consent_obj)
            
            if not active_consents:
                return None
            
            # Return the most recent consent
            active_consents.sort(key=lambda x: x.consent_date, reverse=True)
            return active_consents[0]
            
        except Exception:
            return None
    
    async def revoke_consent(
        self,
        user_id: str,
        data_category: DataCategory
    ) -> bool:
        """Revoke user consent for data processing"""
        
        try:
            # Get current consent
            current_consent = await self.get_user_consent(user_id, data_category)
            if not current_consent:
                return False
            
            # Mark consent as revoked
            current_consent.revoked_at = datetime.utcnow()
            
            # Store updated consent
            await self.vercel_kv_service.store_analytics_data(
                user_id=user_id,
                data_type="data_consent",
                source_id=current_consent.id,
                data=current_consent.__dict__,
                ttl=0
            )
            
            # Log consent revocation
            await self._log_privacy_audit(
                user_id=user_id,
                action="revoke_consent",
                data_category=data_category,
                legal_basis="user_request",
                additional_info={"revoked_at": current_consent.revoked_at.isoformat()}
            )
            
            return True
            
        except Exception as e:
            await self._log_privacy_audit(
                user_id=user_id,
                action="revoke_consent_error",
                data_category=data_category,
                legal_basis="error",
                additional_info={"error": str(e)}
            )
            return False
    
    async def create_data_subject_request(
        self,
        user_id: str,
        request_type: DataRight,
        description: str
    ) -> Optional[DataSubjectRequest]:
        """Create a data subject request (DSR)"""
        
        try:
            dsr = DataSubjectRequest(
                id=f"dsr_{user_id}_{request_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                user_id=user_id,
                request_type=request_type,
                status="pending",
                description=description
            )
            
            # Store DSR in Vercel KV
            await self.vercel_kv_service.store_analytics_data(
                user_id=user_id,
                data_type="data_subject_requests",
                source_id=dsr.id,
                data=dsr.__dict__,
                ttl=0
            )
            
            # Log DSR creation
            await self._log_privacy_audit(
                user_id=user_id,
                action="create_dsr",
                data_category=DataCategory.PERSONAL,
                legal_basis="user_rights",
                additional_info={
                    "request_type": request_type.value,
                    "description": description
                }
            )
            
            return dsr
            
        except Exception as e:
            await self._log_privacy_audit(
                user_id=user_id,
                action="create_dsr_error",
                data_category=DataCategory.PERSONAL,
                legal_basis="error",
                additional_info={"error": str(e)}
            )
            return None
    
    async def process_data_subject_request(
        self,
        admin_user_id: str,
        dsr_id: str,
        status: str,
        notes: Optional[str] = None,
        rejection_reason: Optional[str] = None
    ) -> Optional[DataSubjectRequest]:
        """Process a data subject request (admin only)"""
        
        try:
            # Check if admin user has permission to manage privacy
            if not await self.auth_service.check_permission(admin_user_id, Permission.MANAGE_USERS):
                return None
            
            # Get DSR
            dsr_data = await self.vercel_kv_service.get_analytics_data(
                user_id="system",
                data_type="data_subject_requests",
                source_id=dsr_id
            )
            
            if not dsr_data:
                return None
            
            dsr = DataSubjectRequest(**dsr_data)
            
            # Update DSR status
            dsr.status = status
            dsr.processed_at = datetime.utcnow()
            dsr.notes = notes
            dsr.rejection_reason = rejection_reason
            
            if status == "completed":
                dsr.completed_at = datetime.utcnow()
            
            # Store updated DSR
            await self.vercel_kv_service.store_analytics_data(
                user_id="system",
                data_type="data_subject_requests",
                source_id=dsr_id,
                data=dsr.__dict__,
                ttl=0
            )
            
            # Log DSR processing
            await self._log_privacy_audit(
                user_id=admin_user_id,
                action="process_dsr",
                data_category=DataCategory.PERSONAL,
                legal_basis="admin_processing",
                additional_info={
                    "dsr_id": dsr_id,
                    "status": status,
                    "notes": notes,
                    "rejection_reason": rejection_reason
                }
            )
            
            return dsr
            
        except Exception as e:
            await self._log_privacy_audit(
                user_id=admin_user_id,
                action="process_dsr_error",
                data_category=DataCategory.PERSONAL,
                legal_basis="error",
                additional_info={"error": str(e)}
            )
            return None
    
    async def execute_data_right(
        self,
        user_id: str,
        data_right: DataRight
    ) -> Dict[str, Any]:
        """Execute a specific data right for a user"""
        
        try:
            if data_right == DataRight.ACCESS:
                return await self._execute_access_right(user_id)
            elif data_right == DataRight.ERASURE:
                return await self._execute_erasure_right(user_id)
            elif data_right == DataRight.PORTABILITY:
                return await self._execute_portability_right(user_id)
            else:
                return {
                    "success": False,
                    "error": f"Data right {data_right.value} not yet implemented"
                }
                
        except Exception as e:
            await self._log_privacy_audit(
                user_id=user_id,
                action=f"execute_{data_right.value}_error",
                data_category=DataCategory.PERSONAL,
                legal_basis="error",
                additional_info={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_access_right(self, user_id: str) -> Dict[str, Any]:
        """Execute right to access personal data"""
        
        try:
            # Collect all personal data for the user
            personal_data = {}
            
            # Get user permissions
            user_permissions = await self.auth_service.authenticate_user(user_id)
            if user_permissions:
                personal_data["permissions"] = user_permissions.__dict__
            
            # Get consent records
            consent_data = await self.vercel_kv_service.get_analytics_data(
                user_id=user_id,
                data_type="data_consent"
            )
            personal_data["consent_records"] = consent_data
            
            # Get DSRs
            dsr_data = await self.vercel_kv_service.get_analytics_data(
                user_id=user_id,
                data_type="data_subject_requests"
            )
            personal_data["data_subject_requests"] = dsr_data
            
            # Get analytics data (filtered for personal data only)
            analytics_data = await self.vercel_kv_service.get_analytics_data(
                user_id=user_id,
                data_type="analytics"
            )
            personal_data["analytics_data"] = analytics_data
            
            # Log access right execution
            await self._log_privacy_audit(
                user_id=user_id,
                action="execute_access_right",
                data_category=DataCategory.PERSONAL,
                legal_basis="user_rights",
                additional_info={"data_types": list(personal_data.keys())}
            )
            
            return {
                "success": True,
                "data": personal_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_erasure_right(self, user_id: str) -> Dict[str, Any]:
        """Execute right to be forgotten (data erasure)"""
        
        try:
            # Get retention rules to determine what can be deleted
            retention_rules = self.default_retention_rules
            
            # Delete personal data based on retention policies
            deleted_data = {}
            
            for data_type in ["analytics", "user_permissions", "data_consent", "data_subject_requests"]:
                try:
                    # Get data for this type
                    data = await self.vercel_kv_service.get_analytics_data(
                        user_id=user_id,
                        data_type=data_type
                    )
                    
                    if data:
                        # Delete the data
                        for item in data:
                            if isinstance(item, dict) and "id" in item:
                                await self.vercel_kv_service.delete_analytics_data(
                                    user_id=user_id,
                                    data_type=data_type,
                                    source_id=item["id"]
                                )
                        
                        deleted_data[data_type] = len(data)
                        
                except Exception as e:
                    deleted_data[data_type] = f"Error: {str(e)}"
            
            # Log erasure right execution
            await self._log_privacy_audit(
                user_id=user_id,
                action="execute_erasure_right",
                data_category=DataCategory.PERSONAL,
                legal_basis="user_rights",
                additional_info={"deleted_data": deleted_data}
            )
            
            return {
                "success": True,
                "deleted_data": deleted_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_portability_right(self, user_id: str) -> Dict[str, Any]:
        """Execute right to data portability"""
        
        try:
            # Collect all user data for export
            user_data = await self._execute_access_right(user_id)
            
            if not user_data["success"]:
                return user_data
            
            # Format data for portability (JSON format)
            export_data = {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "data_format": "json",
                "data": user_data["data"]
            }
            
            # Store export in Vercel KV
            export_id = f"export_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            await self.vercel_kv_service.store_analytics_data(
                user_id=user_id,
                data_type="data_exports",
                source_id=export_id,
                data=export_data,
                ttl=604800  # 7 days
            )
            
            # Log portability right execution
            await self._log_privacy_audit(
                user_id=user_id,
                action="execute_portability_right",
                data_category=DataCategory.PERSONAL,
                legal_basis="user_rights",
                additional_info={"export_id": export_id}
            )
            
            return {
                "success": True,
                "export_id": export_id,
                "data": export_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_expired_data(self) -> Dict[str, Any]:
        """Clean up data that has exceeded retention policies"""
        
        try:
            cleanup_results = {}
            
            for data_category, rule in self.default_retention_rules.items():
                if rule.retention_policy == RetentionPolicy.IMMEDIATE:
                    continue
                
                try:
                    # Calculate cutoff date
                    cutoff_date = datetime.utcnow() - timedelta(days=rule.retention_days)
                    
                    # Get all data for this category
                    all_data = await self.vercel_kv_service.get_all_analytics_data(
                        data_type="analytics"
                    )
                    
                    expired_count = 0
                    for data in all_data:
                        if isinstance(data, dict) and "created_at" in data:
                            try:
                                created_at = datetime.fromisoformat(data["created_at"])
                                if created_at < cutoff_date:
                                    # Delete expired data
                                    await self.vercel_kv_service.delete_analytics_data(
                                        user_id=data.get("user_id", "system"),
                                        data_type="analytics",
                                        source_id=data.get("id", "unknown")
                                    )
                                    expired_count += 1
                            except (ValueError, TypeError):
                                continue
                    
                    cleanup_results[data_category.value] = {
                        "expired_deleted": expired_count,
                        "retention_days": rule.retention_days
                    }
                    
                except Exception as e:
                    cleanup_results[data_category.value] = {
                        "error": str(e)
                    }
            
            # Log cleanup operation
            await self._log_privacy_audit(
                user_id="system",
                action="cleanup_expired_data",
                data_category=DataCategory.TECHNICAL,
                legal_basis="data_retention_policy",
                additional_info={"cleanup_results": cleanup_results}
            )
            
            return {
                "success": True,
                "cleanup_results": cleanup_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await self._log_privacy_audit(
                user_id="system",
                action="cleanup_expired_data_error",
                data_category=DataCategory.TECHNICAL,
                legal_basis="error",
                additional_info={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _log_privacy_audit(
        self,
        user_id: str,
        action: str,
        data_category: DataCategory,
        legal_basis: str,
        data_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        """Log privacy-related audit events"""
        
        try:
            audit_log = PrivacyAuditLog(
                id=f"privacy_audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                user_id=user_id,
                action=action,
                data_category=data_category,
                data_id=data_id,
                legal_basis=legal_basis,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_info=additional_info
            )
            
            # Store audit log in Vercel KV
            await self.vercel_kv_service.store_analytics_data(
                user_id="system",
                data_type="privacy_audit_logs",
                source_id=audit_log.id,
                data=audit_log.__dict__,
                ttl=31536000  # 1 year
            )
            
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Error logging privacy audit event: {e}")
    
    async def get_privacy_audit_logs(
        self,
        admin_user_id: str,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        data_category: Optional[DataCategory] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PrivacyAuditLog]:
        """Get privacy audit logs (admin only)"""
        
        try:
            # Check if admin user has permission to view audit logs
            if not await self.auth_service.check_permission(admin_user_id, Permission.VIEW_USER_DATA):
                return []
            
            # Get all privacy audit logs
            audit_logs_data = await self.vercel_kv_service.get_analytics_data(
                user_id="system",
                data_type="privacy_audit_logs"
            )
            
            audit_logs = []
            for log_data in audit_logs_data:
                if isinstance(log_data, dict):
                    audit_log = PrivacyAuditLog(**log_data)
                    
                    # Apply filters
                    if user_id and audit_log.user_id != user_id:
                        continue
                    if action and audit_log.action != action:
                        continue
                    if data_category and audit_log.data_category != data_category:
                        continue
                    if start_date and audit_log.timestamp < start_date:
                        continue
                    if end_date and audit_log.timestamp > end_date:
                        continue
                    
                    audit_logs.append(audit_log)
            
            # Sort by timestamp (newest first) and limit results
            audit_logs.sort(key=lambda x: x.timestamp, reverse=True)
            return audit_logs[:limit]
            
        except Exception as e:
            await self._log_privacy_audit(
                user_id=admin_user_id,
                action="get_privacy_audit_logs_error",
                data_category=DataCategory.TECHNICAL,
                legal_basis="error",
                additional_info={"error": str(e)}
            )
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        
        try:
            # Test Vercel KV connection
            kv_health = await self.vercel_kv_service.health_check()
            
            # Get privacy statistics
            all_consent = await self.vercel_kv_service.get_all_analytics_data(
                data_type="data_consent"
            )
            
            all_dsrs = await self.vercel_kv_service.get_all_analytics_data(
                data_type="data_subject_requests"
            )
            
            active_consent = sum(
                1 for c in all_consent 
                if isinstance(c, dict) and c.get("consent_given", False) and not c.get("revoked_at")
            )
            
            pending_dsrs = sum(
                1 for d in all_dsrs 
                if isinstance(d, dict) and d.get("status") == "pending"
            )
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "vercel_kv": kv_health
                },
                "privacy": {
                    "total_consent_records": len(all_consent),
                    "active_consent": active_consent,
                    "total_dsrs": len(all_dsrs),
                    "pending_dsrs": pending_dsrs
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }




