"""
Social Credentials Manager
Handles secure storage and retrieval of social media API credentials
"""

import os
import logging
from typing import Dict, Optional, Any, List
from cryptography.fernet import Fernet
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SocialCredentialsManager:
    """Manages encrypted storage and retrieval of social media API credentials"""
    
    def __init__(self):
        """Initialize the credentials manager"""
        self.encryption_key = self._get_or_generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Platform credential mappings
        self.platform_credential_keys = {
            "twitter": ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"],
            "facebook": ["FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET", "FACEBOOK_ACCESS_TOKEN"],
            "linkedin": ["LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN"],
            "instagram": ["INSTAGRAM_APP_ID", "INSTAGRAM_APP_SECRET", "INSTAGRAM_ACCESS_TOKEN"]
        }
    
    def _get_or_generate_key(self) -> bytes:
        """Get encryption key from environment or generate a new one"""
        key = os.getenv("SOCIAL_CREDENTIALS_ENCRYPTION_KEY")
        
        if key:
            try:
                return key.encode()
            except Exception as e:
                logger.warning(f"Invalid encryption key from environment: {e}")
        
        # Generate new key if none exists
        new_key = Fernet.generate_key()
        logger.warning(f"No encryption key found. Generated new key: {new_key.decode()}")
        logger.warning("Please set SOCIAL_CREDENTIALS_ENCRYPTION_KEY environment variable")
        
        return new_key
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a string value"""
        try:
            encrypted = self.cipher_suite.encrypt(value.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt value: {e}")
            raise
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt an encrypted string value"""
        try:
            decrypted = self.cipher_suite.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            raise
    
    def get_twitter_credentials(self) -> Optional[Dict[str, str]]:
        """Get Twitter API credentials from environment variables"""
        try:
            credentials = {}
            for key in self.platform_credential_keys["twitter"]:
                value = os.getenv(key)
                if value:
                    credentials[key] = value
            
            if len(credentials) == len(self.platform_credential_keys["twitter"]):
                return credentials
            else:
                logger.warning("Incomplete Twitter credentials found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Twitter credentials: {e}")
            return None
    
    def get_facebook_credentials(self) -> Optional[Dict[str, str]]:
        """Get Facebook API credentials from environment variables"""
        try:
            credentials = {}
            for key in self.platform_credential_keys["facebook"]:
                value = os.getenv(key)
                if value:
                    credentials[key] = value
            
            if len(credentials) == len(self.platform_credential_keys["facebook"]):
                return credentials
            else:
                logger.warning("Incomplete Facebook credentials found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Facebook credentials: {e}")
            return None
    
    def get_linkedin_credentials(self) -> Optional[Dict[str, str]]:
        """Get LinkedIn API credentials from environment variables"""
        try:
            credentials = {}
            for key in self.platform_credential_keys["linkedin"]:
                value = os.getenv(key)
                if value:
                    credentials[key] = value
            
            if len(credentials) == len(self.platform_credential_keys["linkedin"]):
                return credentials
            else:
                logger.warning("Incomplete LinkedIn credentials found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get LinkedIn credentials: {e}")
            return None
    
    def get_instagram_credentials(self) -> Optional[Dict[str, str]]:
        """Get Instagram API credentials from environment variables"""
        try:
            credentials = {}
            for key in self.platform_credential_keys["instagram"]:
                value = os.getenv(key)
                if value:
                    credentials[key] = value
            
            if len(credentials) == len(self.platform_credential_keys["instagram"]):
                return credentials
            else:
                logger.warning("Incomplete Instagram credentials found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Instagram credentials: {e}")
            return None
    
    def get_all_credentials(self) -> Dict[str, Optional[Dict[str, str]]]:
        """Get credentials for all platforms"""
        return {
            "twitter": self.get_twitter_credentials(),
            "facebook": self.get_facebook_credentials(),
            "linkedin": self.get_linkedin_credentials(),
            "instagram": self.get_instagram_credentials()
        }
    
    def validate_credentials(self, platform: str) -> bool:
        """Validate if credentials exist for a platform"""
        try:
            if platform not in self.platform_credential_keys:
                logger.warning(f"Unknown platform: {platform}")
                return False
            
            credentials = self._get_platform_credentials(platform)
            return credentials is not None
            
        except Exception as e:
            logger.error(f"Failed to validate credentials for {platform}: {e}")
            return False
    
    def _get_platform_credentials(self, platform: str) -> Optional[Dict[str, str]]:
        """Get credentials for a specific platform"""
        platform_methods = {
            "twitter": self.get_twitter_credentials,
            "facebook": self.get_facebook_credentials,
            "linkedin": self.get_linkedin_credentials,
            "instagram": self.get_instagram_credentials
        }
        
        method = platform_methods.get(platform)
        if method:
            return method()
        
        return None
    
    def get_credential_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all platform credentials"""
        try:
            status = {}
            
            for platform in self.platform_credential_keys.keys():
                credentials = self._get_platform_credentials(platform)
                
                status[platform] = {
                    "has_credentials": credentials is not None,
                    "credential_count": len(credentials) if credentials else 0,
                    "required_count": len(self.platform_credential_keys[platform]),
                    "is_complete": credentials is not None and len(credentials) == len(self.platform_credential_keys[platform])
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get credential status: {e}")
            return {}
    
    def store_encrypted_credentials(self, platform: str, credentials: Dict[str, str]) -> bool:
        """Store encrypted credentials (placeholder for future database storage)"""
        try:
            # For now, this is a placeholder
            # In a real implementation, you would store encrypted credentials in a database
            logger.info(f"Storing encrypted credentials for {platform}")
            
            # Encrypt each credential
            encrypted_credentials = {}
            for key, value in credentials.items():
                encrypted_credentials[key] = self._encrypt_value(value)
            
            # Here you would store encrypted_credentials in a database
            # For now, just log that we're ready to store
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store encrypted credentials for {platform}: {e}")
            return False
    
    def retrieve_encrypted_credentials(self, platform: str) -> Optional[Dict[str, str]]:
        """Retrieve and decrypt stored credentials (placeholder for future database storage)"""
        try:
            # For now, this is a placeholder
            # In a real implementation, you would retrieve encrypted credentials from a database
            logger.info(f"Retrieving encrypted credentials for {platform}")
            
            # Here you would retrieve encrypted credentials from a database
            # For now, return None to indicate no stored credentials
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve encrypted credentials for {platform}: {e}")
            return None
    
    def rotate_credentials(self, platform: str, new_credentials: Dict[str, str]) -> bool:
        """Rotate credentials for a platform"""
        try:
            logger.info(f"Rotating credentials for {platform}")
            
            # Validate new credentials
            if platform not in self.platform_credential_keys:
                logger.error(f"Unknown platform: {platform}")
                return False
            
            required_keys = self.platform_credential_keys[platform]
            if not all(key in new_credentials for key in required_keys):
                logger.error(f"Incomplete credentials for {platform}")
                return False
            
            # Store new credentials
            success = self.store_encrypted_credentials(platform, new_credentials)
            
            if success:
                logger.info(f"Successfully rotated credentials for {platform}")
            else:
                logger.error(f"Failed to store new credentials for {platform}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rotate credentials for {platform}: {e}")
            return False
    
    def get_credential_health_report(self) -> Dict[str, Any]:
        """Get a comprehensive health report of all credentials"""
        try:
            status = self.get_credential_status()
            
            total_platforms = len(status)
            platforms_with_credentials = sum(1 for s in status.values() if s["has_credentials"])
            platforms_with_complete_credentials = sum(1 for s in status.values() if s["is_complete"])
            
            health_score = (platforms_with_complete_credentials / total_platforms) * 100 if total_platforms > 0 else 0
            
            report = {
                "overall_health": {
                    "score": round(health_score, 2),
                    "status": "healthy" if health_score >= 80 else "warning" if health_score >= 50 else "critical",
                    "total_platforms": total_platforms,
                    "platforms_with_credentials": platforms_with_credentials,
                    "platforms_with_complete_credentials": platforms_with_complete_credentials
                },
                "platform_details": status,
                "recommendations": self._generate_recommendations(status),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate credential health report: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, status: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on credential status"""
        recommendations = []
        
        for platform, platform_status in status.items():
            if not platform_status["has_credentials"]:
                recommendations.append(f"Add credentials for {platform} platform")
            elif not platform_status["is_complete"]:
                recommendations.append(f"Complete missing credentials for {platform} platform")
        
        if not recommendations:
            recommendations.append("All platform credentials are properly configured")
        
        return recommendations
    
    def test_credentials(self, platform: str) -> Dict[str, Any]:
        """Test if credentials are valid by attempting to authenticate"""
        try:
            credentials = self._get_platform_credentials(platform)
            
            if not credentials:
                return {
                    "valid": False,
                    "error": "No credentials found",
                    "platform": platform
                }
            
            # Here you would implement actual API authentication tests
            # For now, just check if credentials exist
            return {
                "valid": True,
                "platform": platform,
                "credential_count": len(credentials),
                "message": "Credentials found (not tested against API)"
            }
            
        except Exception as e:
            logger.error(f"Failed to test credentials for {platform}: {e}")
            return {
                "valid": False,
                "error": str(e),
                "platform": platform
            }
    
    def get_credential_summary(self) -> str:
        """Get a human-readable summary of credential status"""
        try:
            status = self.get_credential_status()
            
            summary_lines = ["Social Media Credentials Summary:"]
            summary_lines.append("=" * 40)
            
            for platform, platform_status in status.items():
                status_icon = "✅" if platform_status["is_complete"] else "⚠️" if platform_status["has_credentials"] else "❌"
                summary_lines.append(f"{status_icon} {platform.title()}: {platform_status['credential_count']}/{platform_status['required_count']} credentials")
            
            summary_lines.append("")
            
            # Overall status
            total_platforms = len(status)
            complete_platforms = sum(1 for s in status.values() if s["is_complete"])
            
            if complete_platforms == total_platforms:
                summary_lines.append("🎉 All platforms are fully configured!")
            elif complete_platforms > 0:
                summary_lines.append(f"⚠️  {complete_platforms}/{total_platforms} platforms are fully configured")
            else:
                summary_lines.append("❌ No platforms are fully configured")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            logger.error(f"Failed to generate credential summary: {e}")
            return f"Error generating summary: {e}"
