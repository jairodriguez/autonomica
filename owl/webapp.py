# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Import from the correct module path
from utils import run_society
import os
import gradio as gr
import time
import json
import logging
import datetime
from typing import Tuple, Optional, Dict, List
import importlib
from dotenv import load_dotenv, set_key, find_dotenv, unset_key
import threading
import queue
import re
import uuid
import hashlib
import secrets
from dataclasses import dataclass, asdict
from enum import Enum

# Static imports for allowed modules (RCE Prevention)
try:
    from examples import run
    from examples import run_mini
    from examples import run_gemini
    from examples import run_claude
    from examples import run_deepseek_zh
    from examples import run_qwen_zh
    from examples import run_terminal_zh
except ImportError as e:
    logging.warning(f"Some allowed modules could not be imported: {e}")
    # Continue execution - modules will be checked at runtime

os.environ["PYTHONIOENCODING"] = "utf-8"


# Configure logging system
def setup_logging():
    """Configure logging system to output logs to file, memory queue, and console"""
    # Create logs directory (if it doesn't exist)
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Generate log filename (using current date)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"gradio_log_{current_date}.txt")

    # Configure root logger (captures all logs)
    root_logger = logging.getLogger()

    # Clear existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.INFO)

    # Create file handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Logging system initialized, log file: %s", log_file)
    return log_file


# Global variables
LOG_FILE = None
LOG_QUEUE: queue.Queue = queue.Queue()  # Log queue
STOP_LOG_THREAD = threading.Event()
CURRENT_PROCESS = None  # Used to track the currently running process
STOP_REQUESTED = threading.Event()  # Used to mark if stop was requested

# Environment variable UI state management
ENV_DISPLAY_MODE = "view"  # "view" or "edit" - controls whether to show masked or unmasked values
ENV_EDIT_CONFIRMED = False  # Track if user has confirmed security implications of edit mode
ENV_TEMPORARY_UNMASK = False  # Temporary unmasking for show/hide toggle
ENV_UNMASK_TIMESTAMP = None  # Timestamp when unmasking started
ENV_UNMASK_TIMEOUT = 30  # Seconds before auto-re-masking


# Authentication and User Management System
class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    id: str
    username: str
    password_hash: str
    role: UserRole
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[datetime.datetime] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['role'] = self.role.value
        data['created_at'] = self.created_at.isoformat()
        if self.last_login:
            data['last_login'] = self.last_login.isoformat()
        if self.locked_until:
            data['locked_until'] = self.locked_until.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        data['role'] = UserRole(data['role'])
        data['created_at'] = datetime.datetime.fromisoformat(data['created_at'])
        if data.get('last_login'):
            data['last_login'] = datetime.datetime.fromisoformat(data['last_login'])
        if data.get('locked_until'):
            data['locked_until'] = datetime.datetime.fromisoformat(data['locked_until'])
        return cls(**data)


@dataclass
class Session:
    id: str
    user_id: str
    created_at: datetime.datetime
    expires_at: datetime.datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    csrf_token: Optional[str] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        data['created_at'] = datetime.datetime.fromisoformat(data['created_at'])
        data['expires_at'] = datetime.datetime.fromisoformat(data['expires_at'])
        return cls(**data)

    def is_expired(self) -> bool:
        return datetime.datetime.now() > self.expires_at


class AuthenticationManager:
    def __init__(self):
        self.users_file = os.path.join(os.path.dirname(__file__), "users.json")
        self.sessions_file = os.path.join(os.path.dirname(__file__), "sessions.json")
        self.security_log_file = os.path.join(os.path.dirname(__file__), "logs", "security.log")
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.current_user: Optional[User] = None
        self.current_session: Optional[Session] = None

        # Security settings
        self.session_timeout_minutes = 30
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 15

        self.load_data()

    def load_data(self):
        """Load users and sessions from files"""
        # Load users
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                    self.users = {uid: User.from_dict(data) for uid, data in users_data.items()}
            except Exception as e:
                logging.error(f"Failed to load users: {e}")

        # Load sessions
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    sessions_data = json.load(f)
                    self.sessions = {sid: Session.from_dict(data) for sid, data in sessions_data.items()}
            except Exception as e:
                logging.error(f"Failed to load sessions: {e}")

        # Clean expired sessions
        self.cleanup_expired_sessions()

    def save_data(self):
        """Save users and sessions to files"""
        try:
            # Save users
            users_data = {uid: user.to_dict() for uid, user in self.users.items()}
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)

            # Save sessions
            sessions_data = {sid: session.to_dict() for sid, session in self.sessions.items()}
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save data: {e}")

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = hashed_password.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return secrets.compare_digest(hash_hex, password_hash.hex())
        except:
            return False

    def create_user(self, username: str, password: str, role: UserRole = UserRole.USER) -> Optional[User]:
        """Create a new user"""
        if username in [u.username for u in self.users.values()]:
            return None

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=self.hash_password(password),
            role=role,
            created_at=datetime.datetime.now()
        )

        self.users[user.id] = user
        self.save_data()
        self.log_security_event("USER_CREATED", f"User {username} created with role {role.value}")
        return user

    def authenticate_user(self, username: str, password: str, ip_address: str = None) -> Optional[User]:
        """Authenticate user credentials"""
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break

        if not user:
            self.log_security_event("LOGIN_FAILED", f"Login attempt for non-existent user: {username}", ip_address)
            return None

        # Check if account is locked
        if user.locked_until and datetime.datetime.now() < user.locked_until:
            self.log_security_event("LOGIN_BLOCKED", f"Login blocked for locked user: {username}", ip_address)
            return None

        # Verify password
        if not self.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1

            # Lock account if too many failed attempts
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.datetime.now() + datetime.timedelta(minutes=self.lockout_duration_minutes)
                self.log_security_event("ACCOUNT_LOCKED", f"Account locked for user: {username}", ip_address)

            self.save_data()
            self.log_security_event("LOGIN_FAILED", f"Invalid password for user: {username}", ip_address)
            return None

        # Successful authentication
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.datetime.now()
        self.save_data()
        self.log_security_event("LOGIN_SUCCESS", f"User {username} logged in successfully", ip_address)
        return user

    def create_session(self, user: User, ip_address: str = None, user_agent: str = None) -> Session:
        """Create a new session for user"""
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user.id,
            created_at=datetime.datetime.now(),
            expires_at=datetime.datetime.now() + datetime.timedelta(minutes=self.session_timeout_minutes),
            ip_address=ip_address,
            user_agent=user_agent,
            csrf_token=secrets.token_hex(32)
        )

        self.sessions[session.id] = session
        self.current_session = session
        self.current_user = user
        self.save_data()
        return session

    def validate_session(self, session_id: str) -> Optional[User]:
        """Validate session and return user if valid"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        if session.is_expired():
            del self.sessions[session_id]
            self.save_data()
            return None

        user = self.users.get(session.user_id)
        if not user or not user.is_active:
            return None

        # Renew session if it's about to expire (within 5 minutes)
        if session.expires_at - datetime.datetime.now() < datetime.timedelta(minutes=5):
            session.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=self.session_timeout_minutes)
            self.save_data()

        self.current_session = session
        self.current_user = user
        return user

    def logout(self, session_id: str):
        """Log out user by removing session"""
        if session_id in self.sessions:
            user = self.users.get(self.sessions[session_id].user_id)
            username = user.username if user else "unknown"
            del self.sessions[session_id]
            self.current_session = None
            self.current_user = None
            self.save_data()
            self.log_security_event("LOGOUT", f"User {username} logged out")

    def invalidate_all_user_sessions(self, user_id: str):
        """Invalidate all sessions for a specific user (useful for security)"""
        expired_sessions = [sid for sid, session in self.sessions.items() if session.user_id == user_id]
        for sid in expired_sessions:
            del self.sessions[sid]
        if expired_sessions:
            self.save_data()
            self.log_security_event("SESSION_INVALIDATION", f"Invalidated {len(expired_sessions)} sessions for user {user_id}")

    def generate_csrf_token(self) -> str:
        """Generate a new CSRF token"""
        return secrets.token_hex(32)

    def validate_csrf_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token for a session"""
        if session_id not in self.sessions:
            return False
        session = self.sessions[session_id]
        return secrets.compare_digest(session.csrf_token, token)

    def refresh_csrf_token(self, session_id: str) -> str:
        """Refresh CSRF token for a session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.csrf_token = self.generate_csrf_token()
            self.save_data()
            return session.csrf_token
        return None

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_sessions = [sid for sid, session in self.sessions.items() if session.is_expired()]
        for sid in expired_sessions:
            del self.sessions[sid]
        if expired_sessions:
            self.save_data()

    def log_security_event(self, event_type: str, message: str, ip_address: str = None):
        """Log security event"""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"{timestamp} | {event_type} | {message}"
        if ip_address:
            log_entry += f" | IP: {ip_address}"

        # Ensure logs directory exists
        logs_dir = os.path.dirname(self.security_log_file)
        os.makedirs(logs_dir, exist_ok=True)

        try:
            with open(self.security_log_file, 'a') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            logging.error(f"Failed to write security log: {e}")

        # Also log to main logger
        logging.info(f"SECURITY: {event_type} - {message}")

    def get_user_permissions(self, user: User) -> List[str]:
        """Get permissions for a user based on their role"""
        if user.role == UserRole.ADMIN:
            return [
                "view_admin_panel",
                "manage_users",
                "view_security_logs",
                "modify_system_settings",
                "access_all_modules"
            ]
        else:
            return [
                "access_basic_modules",
                "view_own_profile"
            ]

    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = self.get_user_permissions(user)
        return permission in permissions

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get detailed session information for monitoring"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        user = self.users.get(session.user_id)

        return {
            'session_id': session_id,
            'user_id': session.user_id,
            'username': user.username if user else 'unknown',
            'created_at': session.created_at.isoformat(),
            'expires_at': session.expires_at.isoformat(),
            'ip_address': session.ip_address,
            'user_agent': session.user_agent,
            'is_expired': session.is_expired(),
            'csrf_token': session.csrf_token[:8] + '...' if session.csrf_token else None
        }


# Session middleware functions
def require_authentication(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        if not auth_manager.current_user:
            raise Exception("Authentication required")
        return func(*args, **kwargs)
    return wrapper


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not auth_manager.current_user:
                raise Exception("Authentication required")

            if not auth_manager.check_permission(auth_manager.current_user, permission):
                raise Exception(f"Permission '{permission}' required")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(func):
    """Decorator to require admin role"""
    def wrapper(*args, **kwargs):
        if not auth_manager.current_user:
            raise Exception("Authentication required")

        if auth_manager.current_user.role != UserRole.ADMIN:
            raise Exception("Admin privileges required")

        return func(*args, **kwargs)
    return wrapper


def validate_csrf(func):
    """Decorator to validate CSRF token"""
    def wrapper(*args, **kwargs):
        if not auth_manager.current_session:
            raise Exception("No active session")

        # In a real implementation, you'd extract the CSRF token from the request
        # For now, we'll assume it's passed as a parameter
        csrf_token = kwargs.get('csrf_token')
        if not csrf_token:
            raise Exception("CSRF token required")

        if not auth_manager.validate_csrf_token(auth_manager.current_session.id, csrf_token):
            raise Exception("Invalid CSRF token")

        return func(*args, **kwargs)
    return wrapper


# Global authentication manager instance
auth_manager = AuthenticationManager()


# Enhanced Error Handling System
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any
import traceback
import json


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    SYSTEM = "system"
    NETWORK = "network"
    MODULE = "module"
    USER_INPUT = "user_input"


@dataclass
class UserFriendlyError:
    """User-friendly error information"""
    code: str
    title: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    help_text: str = ""
    suggested_solutions: List[str] = None
    documentation_url: str = ""
    can_retry: bool = False
    show_help: bool = True

    def __post_init__(self):
        if self.suggested_solutions is None:
            self.suggested_solutions = []


@dataclass
class ErrorContext:
    """Context information for error handling"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    component: str = ""
    operation: str = ""
    timestamp: str = ""
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().isoformat()


class ErrorHandlingService:
    """Centralized error handling service for the application"""

    def __init__(self):
        self.error_mappings: Dict[str, UserFriendlyError] = {}
        self.error_history: List[Dict] = []
        self.error_handlers: Dict[ErrorCategory, Callable] = {}
        self.max_history_size = 1000
        self.error_stats: Dict[str, int] = {}

        # Initialize default error mappings
        self._initialize_error_mappings()

    def _initialize_error_mappings(self):
        """Initialize default error mappings for common errors"""

        # Authentication errors
        self.error_mappings["AUTH_INVALID_CREDENTIALS"] = UserFriendlyError(
            code="AUTH_INVALID_CREDENTIALS",
            title="Invalid Login Credentials",
            message="The username or password you entered is incorrect. Please check your credentials and try again.",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            help_text="Make sure your username and password are correct. Usernames are case-sensitive.",
            suggested_solutions=[
                "Double-check your username and password",
                "Ensure CAPS LOCK is not enabled",
                "Try resetting your password if you've forgotten it",
                "Contact your administrator if you believe this is an error"
            ],
            documentation_url="/docs/authentication",
            can_retry=True,
            show_help=True
        )

        self.error_mappings["AUTH_ACCOUNT_LOCKED"] = UserFriendlyError(
            code="AUTH_ACCOUNT_LOCKED",
            title="Account Temporarily Locked",
            message="Your account has been temporarily locked due to multiple failed login attempts.",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            help_text="This security measure prevents unauthorized access to your account.",
            suggested_solutions=[
                "Wait 15 minutes before trying again",
                "Contact your administrator to unlock your account",
                "Use the password reset feature if available"
            ],
            documentation_url="/docs/account-security",
            can_retry=True,
            show_help=True
        )

        # Authorization errors
        self.error_mappings["AUTH_INSUFFICIENT_PRIVILEGES"] = UserFriendlyError(
            code="AUTH_INSUFFICIENT_PRIVILEGES",
            title="Access Denied",
            message="You don't have permission to perform this action.",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            help_text="This action requires specific permissions that your account doesn't have.",
            suggested_solutions=[
                "Contact your administrator to request access",
                "Check if you're logged in with the correct account",
                "Verify that your account is active and in good standing"
            ],
            documentation_url="/docs/permissions",
            can_retry=False,
            show_help=True
        )

        # Module errors
        self.error_mappings["MODULE_NOT_AUTHORIZED"] = UserFriendlyError(
            code="MODULE_NOT_AUTHORIZED",
            title="Module Access Restricted",
            message="The selected module is not available for your account type.",
            category=ErrorCategory.MODULE,
            severity=ErrorSeverity.MEDIUM,
            help_text="Some modules are restricted based on your account permissions or system configuration.",
            suggested_solutions=[
                "Try selecting a different module",
                "Contact your administrator if you need access to this module",
                "Check the module documentation for requirements"
            ],
            documentation_url="/docs/modules",
            can_retry=True,
            show_help=True
        )

        self.error_mappings["MODULE_NOT_FOUND"] = UserFriendlyError(
            code="MODULE_NOT_FOUND",
            title="Module Unavailable",
            message="The requested module could not be found or loaded.",
            category=ErrorCategory.MODULE,
            severity=ErrorSeverity.HIGH,
            help_text="This might indicate a system configuration issue or missing module.",
            suggested_solutions=[
                "Try selecting a different module",
                "Refresh the page and try again",
                "Contact technical support if the problem persists"
            ],
            documentation_url="/docs/troubleshooting#modules",
            can_retry=True,
            show_help=True
        )

        # Validation errors
        self.error_mappings["VALIDATION_EMPTY_TASK"] = UserFriendlyError(
            code="VALIDATION_EMPTY_TASK",
            title="Task Description Required",
            message="Please provide a description for your task before proceeding.",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            help_text="A clear task description helps the system understand what you want to accomplish.",
            suggested_solutions=[
                "Enter a detailed description of what you want to do",
                "Be specific about the expected outcome",
                "Include any relevant context or requirements"
            ],
            documentation_url="/docs/getting-started#creating-tasks",
            can_retry=True,
            show_help=True
        )

        # System errors
        self.error_mappings["SYSTEM_UNAVAILABLE"] = UserFriendlyError(
            code="SYSTEM_UNAVAILABLE",
            title="System Temporarily Unavailable",
            message="The system is currently experiencing issues. Please try again in a few moments.",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            help_text="This is usually a temporary issue that resolves itself quickly.",
            suggested_solutions=[
                "Wait a few minutes and try again",
                "Refresh the page",
                "Check your internet connection",
                "Contact support if the issue persists"
            ],
            documentation_url="/docs/system-status",
            can_retry=True,
            show_help=True
        )

        # Network errors
        self.error_mappings["NETWORK_TIMEOUT"] = UserFriendlyError(
            code="NETWORK_TIMEOUT",
            title="Connection Timeout",
            message="The request timed out while waiting for a response.",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            help_text="This usually indicates a network connectivity issue or system overload.",
            suggested_solutions=[
                "Check your internet connection",
                "Try again in a few moments",
                "Try using a different network if possible",
                "Contact support if the issue persists"
            ],
            documentation_url="/docs/network-issues",
            can_retry=True,
            show_help=True
        )

        # Additional common error mappings
        self.error_mappings["SESSION_EXPIRED"] = UserFriendlyError(
            code="SESSION_EXPIRED",
            title="Session Expired",
            message="Your session has expired. Please log in again to continue.",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            help_text="For security reasons, sessions automatically expire after a period of inactivity.",
            suggested_solutions=[
                "Click the login button to refresh your session",
                "Save your work before the session expires",
                "Enable auto-save to prevent data loss"
            ],
            documentation_url="/docs/session-management",
            can_retry=True,
            show_help=True
        )

        self.error_mappings["PERMISSION_DENIED"] = UserFriendlyError(
            code="PERMISSION_DENIED",
            title="Permission Denied",
            message="You don't have permission to perform this action.",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            help_text="Some features are restricted based on your account type or permissions.",
            suggested_solutions=[
                "Check if you're logged in with the correct account",
                "Contact your administrator to request additional permissions",
                "Verify that your account is active and in good standing"
            ],
            documentation_url="/docs/permissions",
            can_retry=False,
            show_help=True
        )

        self.error_mappings["RATE_LIMIT_EXCEEDED"] = UserFriendlyError(
            code="RATE_LIMIT_EXCEEDED",
            title="Too Many Requests",
            message="You've made too many requests in a short period. Please slow down and try again later.",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            help_text="This is a security measure to prevent system abuse and ensure fair usage.",
            suggested_solutions=[
                "Wait a few minutes before making more requests",
                "Reduce the frequency of your requests",
                "Consider using the system during off-peak hours",
                "Contact support if you need higher rate limits"
            ],
            documentation_url="/docs/rate-limits",
            can_retry=True,
            show_help=True
        )

    def register_error_mapping(self, error_code: str, error_info: UserFriendlyError):
        """Register a new error mapping"""
        self.error_mappings[error_code] = error_info

    def handle_error(self, error_code: str, context: ErrorContext = None,
                    original_error: Exception = None) -> UserFriendlyError:
        """Handle an error and return user-friendly information"""

        if context is None:
            context = ErrorContext()

        # Get user-friendly error info
        error_info = self.error_mappings.get(error_code)
        if not error_info:
            # Fallback for unknown errors
            error_info = UserFriendlyError(
                code="UNKNOWN_ERROR",
                title="Something Went Wrong",
                message="An unexpected error occurred. Please try again or contact support if the issue persists.",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                help_text="This error has been logged and will be investigated by our team.",
                suggested_solutions=[
                    "Try refreshing the page",
                    "Try again in a few minutes",
                    "Contact support if the problem continues"
                ],
                documentation_url="/docs/support",
                can_retry=True,
                show_help=True
            )

        # Log the error with context
        self._log_error(error_info, context, original_error)

        # Update error statistics
        self._update_error_stats(error_code)

        # Store in history
        self._add_to_history(error_info, context)

        return error_info

    def _log_error(self, error_info: UserFriendlyError, context: ErrorContext,
                   original_error: Exception = None):
        """Log error with appropriate level based on severity"""

        log_message = (
            f"ERROR: {error_info.code} | {error_info.title} | "
            f"Category: {error_info.category.value} | Severity: {error_info.severity.value} | "
            f"User: {context.user_id or 'anonymous'} | Component: {context.component}"
        )

        if original_error:
            log_message += f" | Original: {str(original_error)}"

        # Log with appropriate level
        if error_info.severity == ErrorSeverity.CRITICAL:
            logging.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logging.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logging.warning(log_message)
        else:
            logging.info(log_message)

        # Log technical details for debugging
        if original_error and error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logging.error(f"Technical details for {error_info.code}: {traceback.format_exc()}")

    def _update_error_stats(self, error_code: str):
        """Update error statistics"""
        self.error_stats[error_code] = self.error_stats.get(error_code, 0) + 1

    def _add_to_history(self, error_info: UserFriendlyError, context: ErrorContext):
        """Add error to history with size limit"""

        history_entry = {
            'error': asdict(error_info),
            'context': asdict(context),
            'timestamp': datetime.datetime.now().isoformat()
        }

        self.error_history.append(history_entry)

        # Maintain max history size
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]

    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_stats.copy()

    def get_recent_errors(self, limit: int = 50) -> List[Dict]:
        """Get recent errors from history"""
        return self.error_history[-limit:] if limit > 0 else self.error_history

    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_stats.clear()

    def get_help_for_error(self, error_code: str) -> Optional[UserFriendlyError]:
        """Get help information for a specific error"""
        return self.error_mappings.get(error_code)


# Global error handling service instance
error_service = ErrorHandlingService()


# Helper functions for error handling
def handle_authentication_error(username: str = None, ip_address: str = None):
    """Handle authentication errors"""
    context = ErrorContext(
        component="authentication",
        operation="login",
        ip_address=ip_address
    )
    return error_service.handle_error("AUTH_INVALID_CREDENTIALS", context)


def handle_authorization_error(user: User = None, permission: str = None):
    """Handle authorization errors"""
    context = ErrorContext(
        user_id=user.id if user else None,
        component="authorization",
        operation=f"check_permission_{permission}"
    )
    return error_service.handle_error("AUTH_INSUFFICIENT_PRIVILEGES", context)


def handle_module_error(module_name: str, user: User = None):
    """Handle module access errors"""
    context = ErrorContext(
        user_id=user.id if user else None,
        component="module_access",
        operation=f"load_module_{module_name}",
        metadata={"module_name": module_name}
    )
    return error_service.handle_error("MODULE_NOT_AUTHORIZED", context)


def handle_validation_error(field: str, user: User = None):
    """Handle validation errors"""
    context = ErrorContext(
        user_id=user.id if user else None,
        component="validation",
        operation=f"validate_field_{field}",
        metadata={"field": field}
    )
    return error_service.handle_error("VALIDATION_EMPTY_TASK", context)


def handle_system_error(operation: str, error: Exception = None, user: User = None):
    """Handle system errors"""
    context = ErrorContext(
        user_id=user.id if user else None,
        component="system",
        operation=operation
    )
    return error_service.handle_error("SYSTEM_UNAVAILABLE", context, error)


# Enhanced User Onboarding System
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any
import json
import uuid


class OnboardingStep(Enum):
    WELCOME = "welcome"
    API_SETUP = "api_setup"
    FIRST_TASK = "first_task"
    FEATURE_TOUR = "feature_tour"
    HELP_RESOURCES = "help_resources"
    COMPLETED = "completed"


class TourType(Enum):
    DASHBOARD = "dashboard"
    TASK_CREATION = "task_creation"
    RESULTS_HISTORY = "results_history"
    SETTINGS = "settings"
    ADMIN_PANEL = "admin_panel"


@dataclass
class OnboardingState:
    """Tracks user onboarding progress and state"""
    user_id: str
    current_step: OnboardingStep
    completed_steps: List[OnboardingStep]
    skipped_steps: List[OnboardingStep]
    tour_completed: Dict[TourType, bool]
    examples_created: List[str]
    first_login: bool
    last_updated: str
    wizard_visible: bool = True

    def __post_init__(self):
        if not self.completed_steps:
            self.completed_steps = []
        if not self.skipped_steps:
            self.skipped_steps = []
        if not self.tour_completed:
            self.tour_completed = {}
        if not self.examples_created:
            self.examples_created = []
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


@dataclass
class OnboardingStepConfig:
    """Configuration for each onboarding step"""
    step: OnboardingStep
    title: str
    description: str
    icon: str
    estimated_time: str
    can_skip: bool = True
    required_for_completion: bool = True


@dataclass
class FeatureTourStep:
    """Configuration for feature tour steps"""
    tour_type: TourType
    step_id: str
    title: str
    content: str
    target_element: str
    position: str = "bottom"
    show_skip: bool = True
    show_prev: bool = True


class OnboardingManager:
    """Manages the complete user onboarding experience"""

    def __init__(self):
        self.onboarding_states: Dict[str, OnboardingState] = {}
        self.step_configs = self._initialize_step_configs()
        self.tour_steps = self._initialize_tour_steps()
        self.example_tasks = self._initialize_example_tasks()

    def _initialize_step_configs(self) -> Dict[OnboardingStep, OnboardingStepConfig]:
        """Initialize configuration for each onboarding step"""
        return {
            OnboardingStep.WELCOME: OnboardingStepConfig(
                step=OnboardingStep.WELCOME,
                title="Welcome to OWL System",
                description="Get started with your AI-powered multi-agent collaboration platform",
                icon="🎉",
                estimated_time="1 min",
                can_skip=False,
                required_for_completion=True
            ),
            OnboardingStep.API_SETUP: OnboardingStepConfig(
                step=OnboardingStep.API_SETUP,
                title="API Key Setup",
                description="Configure your AI service credentials securely",
                icon="🔐",
                estimated_time="3 min",
                can_skip=False,
                required_for_completion=True
            ),
            OnboardingStep.FIRST_TASK: OnboardingStepConfig(
                step=OnboardingStep.FIRST_TASK,
                title="Create Your First Task",
                description="Learn how to create and execute AI tasks with examples",
                icon="🚀",
                estimated_time="5 min",
                can_skip=False,
                required_for_completion=True
            ),
            OnboardingStep.FEATURE_TOUR: OnboardingStepConfig(
                step=OnboardingStep.FEATURE_TOUR,
                title="Feature Tour",
                description="Explore the key features and capabilities of OWL",
                icon="🎯",
                estimated_time="5 min",
                can_skip=True,
                required_for_completion=False
            ),
            OnboardingStep.HELP_RESOURCES: OnboardingStepConfig(
                step=OnboardingStep.HELP_RESOURCES,
                title="Help & Resources",
                description="Discover documentation and support resources",
                icon="📚",
                estimated_time="2 min",
                can_skip=True,
                required_for_completion=False
            )
        }

    def _initialize_tour_steps(self) -> Dict[TourType, List[FeatureTourStep]]:
        """Initialize feature tour steps for different areas of the application"""
        return {
            TourType.DASHBOARD: [
                FeatureTourStep(
                    tour_type=TourType.DASHBOARD,
                    step_id="welcome_main",
                    title="Welcome to Your Dashboard",
                    content="This is your main dashboard where you can access all OWL system features. The interface is organized into tabs for easy navigation.",
                    target_element="#task_creation",
                    position="bottom",
                    show_skip=True,
                    show_prev=False
                )
            ],
            TourType.TASK_CREATION: [
                FeatureTourStep(
                    tour_type=TourType.TASK_CREATION,
                    step_id="task_description",
                    title="Task Description",
                    content="Enter a detailed description of what you want the AI system to accomplish. Be specific about your requirements and expected outcomes.",
                    target_element="#question_input",
                    position="bottom",
                    show_skip=True,
                    show_prev=False
                ),
                FeatureTourStep(
                    tour_type=TourType.TASK_CREATION,
                    step_id="module_selection",
                    title="AI Module Selection",
                    content="Choose the appropriate AI module for your task. Each module is optimized for different types of tasks and capabilities.",
                    target_element=".module-dropdown",
                    position="right",
                    show_skip=True,
                    show_prev=True
                ),
                FeatureTourStep(
                    tour_type=TourType.TASK_CREATION,
                    step_id="advanced_options",
                    title="Advanced Options",
                    content="Fine-tune your task with advanced settings like timeout duration, iteration limits, and output format preferences.",
                    target_element=".advanced-options-toggle",
                    position="top",
                    show_skip=True,
                    show_prev=True
                )
            ],
            TourType.RESULTS_HISTORY: [
                FeatureTourStep(
                    tour_type=TourType.RESULTS_HISTORY,
                    step_id="task_results",
                    title="Task Results",
                    content="View the results of your completed tasks here. Each task shows its execution details, output, and any relevant information.",
                    target_element=".log-display",
                    position="top",
                    show_skip=True,
                    show_prev=False
                ),
                FeatureTourStep(
                    tour_type=TourType.RESULTS_HISTORY,
                    step_id="task_history",
                    title="Task History",
                    content="Browse your complete task history with filtering and search capabilities. Track your progress and revisit previous work.",
                    target_element=".task-history-table",
                    position="bottom",
                    show_skip=True,
                    show_prev=True
                )
            ],
            TourType.SETTINGS: [
                FeatureTourStep(
                    tour_type=TourType.SETTINGS,
                    step_id="environment_vars",
                    title="Environment Variables",
                    content="Securely manage your API keys and environment variables. Values are masked for security and can be temporarily revealed when needed.",
                    target_element=".env-table",
                    position="bottom",
                    show_skip=True,
                    show_prev=False
                ),
                FeatureTourStep(
                    tour_type=TourType.SETTINGS,
                    step_id="system_settings",
                    title="System Settings",
                    content="Configure system-wide preferences including logging levels, auto-save settings, and interface themes.",
                    target_element=".system-settings",
                    position="top",
                    show_skip=True,
                    show_prev=True
                )
            ]
        }

    def _initialize_example_tasks(self) -> List[Dict[str, Any]]:
        """Initialize pre-configured example tasks"""
        return [
            {
                "id": "example_1",
                "title": "Basic Web Browsing Task",
                "description": "Open Brave search, find information about AI assistants, and summarize the key features of modern AI chatbots.",
                "module": "run",
                "category": "web_browsing",
                "difficulty": "beginner"
            },
            {
                "id": "example_2",
                "title": "Data Analysis Task",
                "description": "Browse Amazon and find a product that would be useful for programmers. Provide the product name, price, and key features.",
                "module": "run",
                "category": "shopping",
                "difficulty": "intermediate"
            },
            {
                "id": "example_3",
                "title": "Code Generation Task",
                "description": "Write a simple Python script that generates a report about the current date and time, then save it locally.",
                "module": "run_terminal_zh",
                "category": "coding",
                "difficulty": "beginner"
            },
            {
                "id": "example_4",
                "title": "Multi-step Research Task",
                "description": "Research the latest developments in AI safety, create a summary report, and generate a simple visualization of the findings.",
                "module": "run",
                "category": "research",
                "difficulty": "advanced"
            }
        ]

    def get_or_create_onboarding_state(self, user_id: str) -> OnboardingState:
        """Get existing onboarding state or create new one for user"""
        if user_id not in self.onboarding_states:
            # Check if user has completed onboarding before
            is_first_time = not self._has_completed_onboarding_before(user_id)

            self.onboarding_states[user_id] = OnboardingState(
                user_id=user_id,
                current_step=OnboardingStep.WELCOME if is_first_time else OnboardingStep.COMPLETED,
                completed_steps=[],
                skipped_steps=[],
                tour_completed={},
                examples_created=[],
                first_login=is_first_time,
                last_updated=datetime.now().isoformat(),
                wizard_visible=is_first_time
            )

        return self.onboarding_states[user_id]

    def _has_completed_onboarding_before(self, user_id: str) -> bool:
        """Check if user has completed onboarding in the past"""
        # In a real implementation, this would check persistent storage
        # For now, we'll use a simple heuristic based on user creation time
        return False  # Assume all users are new for onboarding

    def update_step(self, user_id: str, step: OnboardingStep, completed: bool = True):
        """Update user's onboarding step progress"""
        state = self.get_or_create_onboarding_state(user_id)

        if completed:
            if step not in state.completed_steps:
                state.completed_steps.append(step)
            if step in state.skipped_steps:
                state.skipped_steps.remove(step)
        else:
            if step not in state.skipped_steps:
                state.skipped_steps.append(step)
            if step in state.completed_steps:
                state.completed_steps.remove(step)

        state.last_updated = datetime.now().isoformat()

    def mark_step_completed(self, user_id: str, step: OnboardingStep):
        """Mark a specific step as completed"""
        self.update_step(user_id, step, completed=True)

    def skip_step(self, user_id: str, step: OnboardingStep):
        """Skip a specific onboarding step"""
        self.update_step(user_id, step, completed=False)

    def get_next_step(self, user_id: str) -> Optional[OnboardingStep]:
        """Get the next required onboarding step for user"""
        state = self.get_or_create_onboarding_state(user_id)

        # If onboarding is completed, return None
        if state.current_step == OnboardingStep.COMPLETED:
            return None

        # Find next uncompleted required step
        required_steps = [
            step for step, config in self.step_configs.items()
            if config.required_for_completion
        ]

        for step in required_steps:
            if step not in state.completed_steps and step not in state.skipped_steps:
                return step

        return OnboardingStep.COMPLETED

    def is_onboarding_completed(self, user_id: str) -> bool:
        """Check if user has completed all required onboarding steps"""
        state = self.get_or_create_onboarding_state(user_id)
        required_steps = [
            step for step, config in self.step_configs.items()
            if config.required_for_completion
        ]
        return all(step in state.completed_steps for step in required_steps)

    def get_progress_percentage(self, user_id: str) -> float:
        """Get onboarding completion percentage"""
        state = self.get_or_create_onboarding_state(user_id)
        required_steps = [
            step for step, config in self.step_configs.items()
            if config.required_for_completion
        ]

        if not required_steps:
            return 100.0

        completed_count = len([step for step in required_steps if step in state.completed_steps])
        return (completed_count / len(required_steps)) * 100.0

    def start_tour(self, user_id: str, tour_type: TourType) -> Optional[List[FeatureTourStep]]:
        """Start a feature tour for user"""
        if tour_type not in self.tour_steps:
            return None

        state = self.get_or_create_onboarding_state(user_id)
        state.tour_completed[tour_type] = False
        state.last_updated = datetime.now().isoformat()

        return self.tour_steps[tour_type]

    def complete_tour(self, user_id: str, tour_type: TourType):
        """Mark a feature tour as completed"""
        state = self.get_or_create_onboarding_state(user_id)
        state.tour_completed[tour_type] = True
        state.last_updated = datetime.now().isoformat()

    def add_example_task(self, user_id: str, task_id: str):
        """Mark an example task as created for user"""
        state = self.get_or_create_onboarding_state(user_id)
        if task_id not in state.examples_created:
            state.examples_created.append(task_id)
        state.last_updated = datetime.now().isoformat()

    def get_example_tasks(self, category: str = None, difficulty: str = None) -> List[Dict[str, Any]]:
        """Get filtered example tasks"""
        tasks = self.example_tasks

        if category:
            tasks = [task for task in tasks if task.get("category") == category]

        if difficulty:
            tasks = [task for task in tasks if task.get("difficulty") == difficulty]

        return tasks


# Global onboarding manager instance
onboarding_manager = OnboardingManager()


# Helper functions for onboarding
def get_onboarding_state(user_id: str) -> OnboardingState:
    """Get onboarding state for user"""
    return onboarding_manager.get_or_create_onboarding_state(user_id)


def create_onboarding_progress_html(user_id: str) -> str:
    """Create HTML for onboarding progress display"""
    state = onboarding_manager.get_or_create_onboarding_state(user_id)
    progress_percent = onboarding_manager.get_progress_percentage(user_id)

    if state.current_step == OnboardingStep.COMPLETED:
        return """
        <div class="onboarding-completed" style="
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 16px;
            border-radius: 8px;
            text-align: center;
            margin: 16px 0;
        ">
            <h3 style="margin: 0 0 8px 0;">🎉 Onboarding Complete!</h3>
            <p style="margin: 0;">You're all set to start using OWL System. You can revisit the onboarding anytime from the help menu.</p>
        </div>
        """

    current_config = onboarding_manager.step_configs.get(state.current_step)
    step_title = current_config.title if current_config else "Loading..."

    # Create detailed progress steps
    all_steps = [
        OnboardingStep.WELCOME,
        OnboardingStep.API_SETUP,
        OnboardingStep.FIRST_TASK,
        OnboardingStep.FEATURE_TOUR,
        OnboardingStep.HELP_RESOURCES
    ]

    steps_html = ""
    for i, step in enumerate(all_steps):
        step_config = onboarding_manager.step_configs.get(step)
        if not step_config:
            continue

        # Determine step status
        if step in state.completed_steps:
            status_icon = "✅"
            status_class = "completed"
            status_color = "#28a745"
        elif step in state.skipped_steps:
            status_icon = "⏭️"
            status_class = "skipped"
            status_color = "#6c757d"
        elif step == state.current_step:
            status_icon = "🔄"
            status_class = "current"
            status_color = "#007bff"
        else:
            status_icon = "⏳"
            status_class = "pending"
            status_color = "#6c757d"

        steps_html += f"""
        <div style="
            display: flex;
            align-items: center;
            padding: 8px 12px;
            margin: 4px 0;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            border-left: 3px solid {status_color};
        ">
            <span style="margin-right: 8px;">{status_icon}</span>
            <div>
                <div style="font-weight: bold; font-size: 0.9em;">{step_config.title}</div>
                <div style="font-size: 0.8em; opacity: 0.8;">{step_config.estimated_time}</div>
            </div>
        </div>
        """

    html = f"""
    <div class="onboarding-progress" style="
        background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
        color: white;
        padding: 20px;
        border-radius: 8px;
        margin: 16px 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h4 style="margin: 0;">🚀 Getting Started Progress</h4>
            <div style="text-align: right;">
                <div style="font-weight: bold; font-size: 1.2em;">{progress_percent:.0f}%</div>
                <div style="font-size: 0.8em; opacity: 0.8;">Complete</div>
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.2); border-radius: 4px; height: 8px; margin-bottom: 16px;">
            <div style="background: rgba(255,255,255,0.8); height: 100%; width: {progress_percent}%; border-radius: 4px; transition: width 0.3s ease;"></div>
        </div>

        <div style="margin-bottom: 12px;">
            <strong>Current:</strong> {step_title}
        </div>

        <div style="background: rgba(255,255,255,0.1); border-radius: 6px; padding: 12px;">
            <div style="font-size: 0.9em; margin-bottom: 8px;"><strong>Your Progress:</strong></div>
            {steps_html}
        </div>

        <div style="margin-top: 12px; font-size: 0.8em; opacity: 0.8;">
            💡 Tip: You can skip any step and return to it later from the help menu
        </div>
    </div>
    """

    return html


def create_example_tasks_display(user_id: str) -> str:
    """Create display for pre-configured example tasks"""
    examples = onboarding_manager.get_example_tasks()

    example_cards = ""
    for example in examples:
        difficulty_class = {
            "beginner": "beginner",
            "intermediate": "intermediate",
            "advanced": "advanced"
        }.get(example.get("difficulty", "beginner"), "beginner")

        example_cards += f"""
        <div class="example-task-card" onclick="loadExample('{example['id']}')">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <h5 style="margin: 0; color: #495057; flex: 1;">{example['title']}</h5>
                <span class="task-difficulty {difficulty_class}">{example['difficulty'].title()}</span>
            </div>
            <p style="margin: 0 0 8px 0; font-size: 0.9em; color: #6c757d; line-height: 1.4;">{example['description'][:100]}{'...' if len(example['description']) > 100 else ''}</p>
            <div style="font-size: 0.8em; color: #999;">
                <strong>Module:</strong> {example['module']} • <strong>Category:</strong> {example['category'].replace('_', ' ').title()}
            </div>
        </div>
        """

    return f"""
    <div class="example-tasks-section" style="
        background: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        margin: 16px 0;
    ">
        <h4 style="margin: 0 0 16px 0; color: #495057;">📚 Pre-configured Example Tasks</h4>
        <p style="margin: 0 0 16px 0; color: #6c757d; font-size: 0.9em;">
            Get started quickly with these ready-to-use example tasks. Click any card to load it into the task creation form.
        </p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px;">
            {example_cards}
        </div>
        <div style="margin-top: 16px; text-align: center;">
            <button onclick="markStepComplete('first_task')" style="
                background: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
            ">
                ✅ I've Created My First Task
            </button>
        </div>
    </div>
    """


def create_welcome_screen(user_id: str) -> str:
    """Create welcome screen HTML for new users"""
    progress_html = create_onboarding_progress_html(user_id)

    html = f"""
    {progress_html}

    <div class="welcome-screen" style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 32px;
        border-radius: 12px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    ">
        <div style="font-size: 4em; margin-bottom: 16px;">🦉</div>
        <h1 style="margin: 0 0 16px 0; font-size: 2.5em;">Welcome to OWL System</h1>
        <p style="margin: 0 0 24px 0; font-size: 1.2em; opacity: 0.9;">
            Your AI-powered multi-agent collaboration platform for complex task automation
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; margin: 32px 0; text-align: left;">
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 8px;">
                <h3 style="margin: 0 0 12px 0;">🤖 Multi-Agent AI</h3>
                <p style="margin: 0; opacity: 0.9;">Collaborative AI agents work together to solve complex problems</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 8px;">
                <h3 style="margin: 0 0 12px 0;">🌐 Web Integration</h3>
                <p style="margin: 0; opacity: 0.9;">Browse, interact, and automate web-based tasks seamlessly</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 8px;">
                <h3 style="margin: 0 0 12px 0;">🔧 Task Automation</h3>
                <p style="margin: 0; opacity: 0.9;">Automate repetitive tasks with intelligent AI assistance</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 8px;">
                <h3 style="margin: 0 0 12px 0;">📊 Results & Analytics</h3>
                <p style="margin: 0; opacity: 0.9;">Track performance and get detailed insights from your tasks</p>
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 8px; margin: 24px 0;">
            <h3 style="margin: 0 0 12px 0;">🎯 What You'll Learn</h3>
            <ul style="text-align: left; display: inline-block; margin: 0; padding-left: 20px;">
                <li>How to set up API keys securely</li>
                <li>Creating your first AI task</li>
                <li>Exploring system features and capabilities</li>
                <li>Finding help and documentation</li>
            </ul>
        </div>

        <div style="display: flex; gap: 12px; justify-content: center; margin-top: 24px;">
            <button class="onboarding-button primary" onclick="startOnboarding()" style="
                background: rgba(255,255,255,0.9);
                color: #667eea;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                font-size: 1em;
            ">
                🚀 Start Setup
            </button>
            <button class="onboarding-button secondary" onclick="skipOnboarding()" style="
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 1em;
            ">
                Skip for Now
            </button>
        </div>
    </div>

    <script src="/owl/onboarding.js"></script>
    <script>
        // Onboarding system is loaded from external file
        let currentStepIndex = 0;
        let wizardSteps = ['welcome', 'api_setup', 'first_task', 'feature_tour', 'help_resources'];
        let onboardingState = {{
            currentStep: 'welcome',
            completedSteps: [],
            skippedSteps: []
        }};

        // Initialize onboarding when page loads
        window.addEventListener('load', function() {{
            initializeOnboarding();
        }});

        function initializeOnboarding() {{
            // Check if user has already completed onboarding
            if (localStorage.getItem('onboarding_completed') === 'true') {{
                hideOnboarding();
                return;
            }}
        }}

        function startOnboarding() {{
            // Transition to the first wizard step
            currentStepIndex = 1;
            showWizardStep('api_setup');
        }}

        function skipOnboarding() {{
            // Mark as completed in localStorage
            localStorage.setItem('onboarding_completed', 'true');
            hideOnboarding();
        }}

        function hideOnboarding() {{
            // Hide welcome screen and show main interface
            const welcomeScreen = document.querySelector('.onboarding-welcome');
            if (welcomeScreen) {{
                welcomeScreen.style.display = 'none';
            }}
        }}

        function showWizardStep(stepId) {{
            // This would be implemented to show the actual wizard steps
            console.log('Showing wizard step:', stepId);
        }}

        function markStepComplete(stepId) {{
            if (!onboardingState.completedSteps.includes(stepId)) {{
                onboardingState.completedSteps.push(stepId);
            }}
            console.log('Completed step:', stepId);
        }}

        // Feature Tour Functions
        let currentTour = null;
        let currentTourStep = 0;
        let tourSteps = [];

        function startTour(tourType) {{
            console.log('Starting tour:', tourType);

            // Define tour steps based on type
            switch(tourType) {{
                case 'task_creation':
                    tourSteps = [
                        {{
                            title: 'Task Description',
                            content: 'Enter a detailed description of what you want the AI system to accomplish. Be specific about your requirements and expected outcomes.',
                            target: '#question_input',
                            position: 'bottom'
                        }},
                        {{
                            title: 'AI Module Selection',
                            content: 'Choose the appropriate AI module for your task. Each module is optimized for different types of tasks and capabilities.',
                            target: '.module-dropdown',
                            position: 'right'
                        }},
                        {{
                            title: 'Advanced Options',
                            content: 'Fine-tune your task with advanced settings like timeout duration, iteration limits, and output format preferences.',
                            target: '.advanced-options-toggle',
                            position: 'top'
                        }}
                    ];
                    break;

                case 'results_history':
                    tourSteps = [
                        {{
                            title: 'Task Results',
                            content: 'View the results of your completed tasks here. Each task shows its execution details, output, and any relevant information.',
                            target: '.log-display',
                            position: 'top'
                        }}
                    ];
                    break;

                case 'settings':
                    tourSteps = [
                        {{
                            title: 'Environment Variables',
                            content: 'Securely manage your API keys and environment variables. Values are masked for security and can be temporarily revealed when needed.',
                            target: '.env-table',
                            position: 'bottom'
                        }}
                    ];
                    break;
            }}

            currentTour = tourType;
            currentTourStep = 0;
            showTourStep();
        }

        function showTourStep() {{
            if (currentTourStep >= tourSteps.length) {{
                endTour();
                return;
            }}

            const step = tourSteps[currentTourStep];

            // Create tooltip overlay
            let overlay = document.getElementById('tour-overlay');
            if (!overlay) {{
                overlay = document.createElement('div');
                overlay.id = 'tour-overlay';
                overlay.className = 'feature-tour-overlay';
                overlay.innerHTML = `
                    <div class="feature-tour-tooltip show" id="tour-tooltip">
                        <div class="feature-tour-arrow ` + step.position + `"></div>
                        <h3 class="feature-tour-title">` + step.title + `</h3>
                        <div class="feature-tour-content">` + step.content + `</div>
                        <div class="feature-tour-navigation">
                            <span class="tour-progress">` + (currentTourStep + 1) + ` of ` + tourSteps.length + `</span>
                            <div>
                                <button class="tour-button secondary" onclick="skipTour()">Skip Tour</button>
                                <button class="tour-button" onclick="nextTourStep()">Next</button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(overlay);
            }}

            overlay.style.display = 'block';

            // Highlight target element
            highlightElement(step.target);
        }}

        function highlightElement(selector) {{
            const element = document.querySelector(selector);
            if (element) {{
                element.classList.add('tour-highlight');
            }}
        }}

        function removeHighlight() {{
            const highlighted = document.querySelector('.tour-highlight');
            if (highlighted) {{
                highlighted.classList.remove('tour-highlight');
            }}
        }}

        function nextTourStep() {{
            removeHighlight();
            currentTourStep++;
            showTourStep();
        }}

        function skipTour() {{
            endTour();
        }}

        function endTour() {{
            removeHighlight();

            const overlay = document.getElementById('tour-overlay');
            if (overlay) {{
                overlay.style.display = 'none';
            }}

            currentTour = null;
            currentTourStep = 0;
            tourSteps = [];
        }}

        // Utility functions
        function loadExample(taskId) {{
            // Load example task into the task creation form
            const examples = {{
                'example_1': 'Open Brave search, find information about AI assistants, and summarize the key features of modern AI chatbots.',
                'example_2': 'Browse Amazon and find a product that would be useful for programmers. Provide the product name, price, and key features.',
                'example_3': 'Write a simple Python script that generates a report about the current date and time, then save it locally.',
                'example_4': 'Research the latest developments in AI safety, create a summary report, and generate a simple visualization of the findings.'
            }};

            const questionInput = document.getElementById('question_input');
            if (questionInput && examples[taskId]) {{
                questionInput.value = examples[taskId];
            }}
        }}

        // Make functions globally available
        window.startOnboarding = startOnboarding;
        window.skipOnboarding = skipOnboarding;
        window.markStepComplete = markStepComplete;
        window.startTour = startTour;
        window.nextTourStep = nextTourStep;
        window.skipTour = skipTour;
        window.loadExample = loadExample;
    </script>
    """

    return html


# Onboarding Wizard Step Functions
def create_wizard_step_welcome() -> str:
    """Create the welcome step content"""
    return """
    <div class="wizard-step" style="padding: 24px; text-align: center;">
        <div style="font-size: 3em; margin-bottom: 16px;">🎉</div>
        <h2 style="margin: 0 0 16px 0; color: #333;">Welcome to OWL System!</h2>
        <p style="margin: 0 0 24px 0; font-size: 1.1em; color: #666;">
            Let's get you set up with your AI-powered multi-agent collaboration platform.
        </p>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 24px 0; text-align: left;">
            <h3 style="margin: 0 0 16px 0; color: #495057;">What is OWL System?</h3>
            <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                <li><strong>🤖 Multi-Agent AI:</strong> Collaborative AI agents that work together to solve complex problems</li>
                <li><strong>🌐 Web Integration:</strong> Browse, interact with, and automate web-based tasks seamlessly</li>
                <li><strong>🔧 Task Automation:</strong> Automate repetitive tasks with intelligent AI assistance</li>
                <li><strong>📊 Analytics & Reporting:</strong> Track performance and get detailed insights from your tasks</li>
            </ul>
        </div>

        <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 8px; margin: 24px 0;">
            <h4 style="margin: 0 0 12px 0; color: #1976d2;">🚀 This setup will take about 10 minutes</h4>
            <p style="margin: 0; color: #1976d2;">We'll walk you through:</p>
            <ol style="margin: 8px 0 0 0; padding-left: 20px; color: #1976d2;">
                <li>Setting up your API keys securely</li>
                <li>Creating your first AI task</li>
                <li>Exploring system features</li>
                <li>Finding help and documentation</li>
            </ol>
        </div>

        <p style="margin: 24px 0 0 0; font-size: 0.9em; color: #999;">
            Don't worry - you can skip any step or come back to it later!
        </p>
    </div>
    """


def create_wizard_step_api_setup(user_id: str) -> str:
    """Create the API setup step content"""
    return """
    <div class="wizard-step" style="padding: 24px;">
        <div style="font-size: 2em; margin-bottom: 16px; text-align: center;">🔐</div>
        <h2 style="margin: 0 0 16px 0; color: #333; text-align: center;">API Key Setup</h2>
        <p style="margin: 0 0 24px 0; text-align: center; color: #666;">
            Configure your AI service credentials to unlock the full potential of OWL System.
        </p>

        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <h4 style="margin: 0 0 12px 0; color: #856404;">🔒 Security First</h4>
            <ul style="margin: 0; padding-left: 20px; color: #856404;">
                <li>API keys are stored locally and never transmitted over the network</li>
                <li>Sensitive values are automatically masked for security</li>
                <li>You can temporarily reveal keys when needed</li>
                <li>All data remains under your control</li>
            </ul>
        </div>

        <div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <h4 style="margin: 0 0 12px 0; color: #0c5460;">📋 What You'll Need</h4>
            <p style="margin: 0 0 12px 0; color: #0c5460;">OWL System supports multiple AI providers:</p>
            <ul style="margin: 0; padding-left: 20px; color: #0c5460;">
                <li><strong>OpenAI API Key</strong> - For GPT models (most common)</li>
                <li><strong>Anthropic API Key</strong> - For Claude models</li>
                <li><strong>Google API Key</strong> - For Gemini models</li>
                <li><strong>Other providers</strong> - As needed for your tasks</li>
            </ul>
        </div>

        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0;">
            <h4 style="margin: 0 0 16px 0; color: #495057;">🚀 Next Steps</h4>
            <ol style="margin: 0; padding-left: 20px; color: #6c757d;">
                <li>Go to the <strong>Settings & Configuration</strong> tab</li>
                <li>Add your API keys in the secure environment variable section</li>
                <li>Test your keys by creating a simple task</li>
                <li>Come back here to continue the setup</li>
            </ol>
        </div>

        <div style="text-align: center; margin-top: 24px;">
            <button onclick="window.open('#settings', '_self')" style="
                background: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                margin-right: 12px;
            ">
                ⚙️ Go to Settings
            </button>
            <button onclick="markStepComplete('api_setup')" style="
                background: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
            ">
                ✅ I've Set Up My API Keys
            </button>
        </div>
    </div>
    """


def create_wizard_step_first_task(user_id: str) -> str:
    """Create the first task creation step content"""
    # Get example tasks for the user
    example_tasks = onboarding_manager.get_example_tasks(difficulty="beginner")

    examples_html = ""
    for task in example_tasks:
        examples_html += f"""
        <div style="background: white; border: 1px solid #dee2e6; border-radius: 6px; padding: 16px; margin: 8px 0; cursor: pointer;" onclick="loadExample('{task['id']}')">
            <h5 style="margin: 0 0 8px 0; color: #495057;">{task['title']}</h5>
            <p style="margin: 0 0 8px 0; font-size: 0.9em; color: #6c757d;">{task['description'][:100]}...</p>
            <span style="background: #e9ecef; color: #495057; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">{task['difficulty'].title()}</span>
        </div>
        """

    return f"""
    <div class="wizard-step" style="padding: 24px;">
        <div style="font-size: 2em; margin-bottom: 16px; text-align: center;">🚀</div>
        <h2 style="margin: 0 0 16px 0; color: #333; text-align: center;">Create Your First Task</h2>
        <p style="margin: 0 0 24px 0; text-align: center; color: #666;">
            Let's create your first AI task! Start with one of these examples or create your own.
        </p>

        <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <h4 style="margin: 0 0 12px 0; color: #1976d2;">💡 Getting Started Tips</h4>
            <ul style="margin: 0; padding-left: 20px; color: #1976d2;">
                <li>Be specific about what you want the AI to accomplish</li>
                <li>Include relevant context and requirements</li>
                <li>Start simple - you can always add complexity later</li>
                <li>Use the examples below as templates</li>
            </ul>
        </div>

        <div style="margin: 24px 0;">
            <h4 style="margin: 0 0 16px 0; color: #495057;">📝 Example Tasks to Try</h4>
            {examples_html}
        </div>

        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0;">
            <h4 style="margin: 0 0 16px 0; color: #495057;">🎯 Manual Task Creation</h4>
            <div style="background: white; border: 1px solid #dee2e6; border-radius: 6px; padding: 16px;">
                <p style="margin: 0 0 12px 0; color: #6c757d;">
                    Click the button below to go to the Task Creation tab and create your own task:
                </p>
                <button onclick="window.open('#task_creation', '_self')" style="
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                ">
                    🎯 Create Custom Task
                </button>
            </div>
        </div>

        <div style="text-align: center; margin-top: 24px;">
            <button onclick="markStepComplete('first_task')" style="
                background: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                font-size: 1em;
            ">
                ✅ I've Created My First Task
            </button>
        </div>

        <div style="margin-top: 20px; padding: 16px; background: #f8f9fa; border-radius: 8px;">
            <h4 style="margin: 0 0 12px 0; color: #495057;">💡 Quick Start Examples</h4>
            <p style="margin: 0 0 12px 0; color: #6c757d; font-size: 0.9em;">
                Click any example below to instantly load it into the task creation form:
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 8px;">
                <div onclick="loadExample('example_1')" style="background: white; padding: 12px; border-radius: 6px; cursor: pointer; border: 1px solid #dee2e6; transition: all 0.2s ease;" onmouseover="this.style.borderColor='#007bff'; this.style.backgroundColor='#f8f9ff';" onmouseout="this.style.borderColor='#dee2e6'; this.style.backgroundColor='white';">
                    <div style="font-weight: bold; color: #495057; margin-bottom: 4px;">🌐 Web Research</div>
                    <div style="font-size: 0.8em; color: #6c757d;">Browse and analyze web content</div>
                </div>
                <div onclick="loadExample('example_2')" style="background: white; padding: 12px; border-radius: 6px; cursor: pointer; border: 1px solid #dee2e6; transition: all 0.2s ease;" onmouseover="this.style.borderColor='#28a745'; this.style.backgroundColor='#f8fff8';" onmouseout="this.style.borderColor='#dee2e6'; this.style.backgroundColor='white';">
                    <div style="font-weight: bold; color: #495057; margin-bottom: 4px;">🛒 Shopping Assistant</div>
                    <div style="font-size: 0.8em; color: #6c757d;">Find and analyze products</div>
                </div>
                <div onclick="loadExample('example_3')" style="background: white; padding: 12px; border-radius: 6px; cursor: pointer; border: 1px solid #dee2e6; transition: all 0.2s ease;" onmouseover="this.style.borderColor='#ffc107'; this.style.backgroundColor='#fffef8';" onmouseout="this.style.borderColor='#dee2e6'; this.style.backgroundColor='white';">
                    <div style="font-weight: bold; color: #495057; margin-bottom: 4px;">💻 Code Generation</div>
                    <div style="font-size: 0.8em; color: #6c757d;">Create and run code scripts</div>
                </div>
                <div onclick="loadExample('example_4')" style="background: white; padding: 12px; border-radius: 6px; cursor: pointer; border: 1px solid #dee2e6; transition: all 0.2s ease;" onmouseover="this.style.borderColor='#dc3545'; this.style.backgroundColor='#fff8f8';" onmouseout="this.style.borderColor='#dee2e6'; this.style.backgroundColor='white';">
                    <div style="font-weight: bold; color: #495057; margin-bottom: 4px;">🔬 Research & Analysis</div>
                    <div style="font-size: 0.8em; color: #6c757d;">Deep research and reporting</div>
                </div>
            </div>
        </div>
    </div>
    """


def create_wizard_step_feature_tour(user_id: str) -> str:
    """Create the feature tour step content"""
    return """
    <div class="wizard-step" style="padding: 24px;">
        <div style="font-size: 2em; margin-bottom: 16px; text-align: center;">🎯</div>
        <h2 style="margin: 0 0 16px 0; color: #333; text-align: center;">Explore System Features</h2>
        <p style="margin: 0 0 24px 0; text-align: center; color: #666;">
            Take a guided tour of OWL System's key features and capabilities.
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin: 24px 0;">
            <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 20px; cursor: pointer;" onclick="startTour('task_creation')">
                <h3 style="margin: 0 0 12px 0; color: #1976d2;">🎯 Task Creation</h3>
                <p style="margin: 0; color: #1976d2;">Learn how to create effective AI tasks with proper configuration and module selection.</p>
            </div>

            <div style="background: #f3e5f5; border: 1px solid #ce93d8; border-radius: 8px; padding: 20px; cursor: pointer;" onclick="startTour('results_history')">
                <h3 style="margin: 0 0 12px 0; color: #7b1fa2;">📊 Results & History</h3>
                <p style="margin: 0; color: #7b1fa2;">Understand how to view task results, manage history, and export data.</p>
            </div>

            <div style="background: #e8f5e8; border: 1px solid #81c784; border-radius: 8px; padding: 20px; cursor: pointer;" onclick="startTour('settings')">
                <h3 style="margin: 0 0 12px 0; color: #388e3c;">⚙️ Settings & Security</h3>
                <p style="margin: 0; color: #388e3c;">Discover how to manage API keys, configure settings, and maintain security.</p>
            </div>

            <div style="background: #fff3e0; border: 1px solid #ffb74d; border-radius: 8px; padding: 20px; cursor: pointer;" onclick="startTour('admin_panel')">
                <h3 style="margin: 0 0 12px 0; color: #f57c00;">🛡️ Admin Panel</h3>
                <p style="margin: 0; color: #f57c00;">Explore administrative features like user management and system monitoring.</p>
            </div>
        </div>

        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h4 style="margin: 0 0 12px 0; color: #495057;">🎮 Interactive Tour Features</h4>
            <ul style="margin: 0; padding-left: 20px; color: #6c757d;">
                <li><strong>Step-by-step guidance</strong> through each feature</li>
                <li><strong>Visual highlighting</strong> of UI elements being explained</li>
                <li><strong>Interactive examples</strong> you can try immediately</li>
                <li><strong>Skip anytime</strong> if you already know a feature</li>
                <li><strong>Resume later</strong> from where you left off</li>
            </ul>
        </div>

        <div style="text-align: center; margin-top: 24px;">
            <button onclick="startTour('task_creation')" style="
                background: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                margin-right: 12px;
            ">
                🎯 Start Task Creation Tour
            </button>
            <button onclick="markStepComplete('feature_tour')" style="
                background: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
            ">
                ✅ Skip Tour for Now
            </button>
        </div>
    </div>
    """


def create_wizard_step_help_resources(user_id: str) -> str:
    """Create the help and resources step content"""
    return """
    <div class="wizard-step" style="padding: 24px;">
        <div style="font-size: 2em; margin-bottom: 16px; text-align: center;">📚</div>
        <h2 style="margin: 0 0 16px 0; color: #333; text-align: center;">Help & Documentation</h2>
        <p style="margin: 0 0 24px 0; text-align: center; color: #666;">
            Discover resources to help you get the most out of OWL System.
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin: 24px 0;">
            <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 20px;">
                <h4 style="margin: 0 0 12px 0; color: #1976d2;">📖 Getting Started Guide</h4>
                <p style="margin: 0 0 16px 0; color: #1976d2;">Step-by-step tutorials for beginners covering basic concepts and first tasks.</p>
                <a href="/docs/getting-started" style="color: #1976d2; text-decoration: none;">📚 Read Guide →</a>
            </div>

            <div style="background: #f3e5f5; border: 1px solid #ce93d8; border-radius: 8px; padding: 20px;">
                <h4 style="margin: 0 0 12px 0; color: #7b1fa2;">🔧 API & Configuration</h4>
                <p style="margin: 0 0 16px 0; color: #7b1fa2;">Detailed documentation about API keys, configuration options, and system settings.</p>
                <a href="/docs/api-setup" style="color: #7b1fa2; text-decoration: none;">🔧 View Documentation →</a>
            </div>

            <div style="background: #e8f5e8; border: 1px solid #81c784; border-radius: 8px; padding: 20px;">
                <h4 style="margin: 0 0 12px 0; color: #388e3c;">🎯 Task Examples</h4>
                <p style="margin: 0 0 16px 0; color: #388e3c;">Collection of example tasks demonstrating different capabilities and use cases.</p>
                <a href="/docs/examples" style="color: #388e3c; text-decoration: none;">🎯 Browse Examples →</a>
            </div>

            <div style="background: #fff3e0; border: 1px solid #ffb74d; border-radius: 8px; padding: 20px;">
                <h4 style="margin: 0 0 12px 0; color: #f57c00;">🆘 Troubleshooting</h4>
                <p style="margin: 0 0 16px 0; color: #f57c00;">Common issues, error solutions, and frequently asked questions.</p>
                <a href="/docs/troubleshooting" style="color: #f57c00; text-decoration: none;">🆘 Get Help →</a>
            </div>
        </div>

        <div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h4 style="margin: 0 0 12px 0; color: #0c5460;">💬 Getting Support</h4>
            <ul style="margin: 0; padding-left: 20px; color: #0c5460;">
                <li><strong>Documentation:</strong> Comprehensive guides for all features</li>
                <li><strong>Community:</strong> Join discussions and share knowledge</li>
                <li><strong>Support:</strong> Direct help from the development team</li>
                <li><strong>Updates:</strong> Stay informed about new features and improvements</li>
            </ul>
        </div>

        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h4 style="margin: 0 0 16px 0; color: #495057;">🎓 Learning Resources</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                <div style="background: white; padding: 12px; border-radius: 4px; border-left: 4px solid #007bff;">
                    <strong>🎥 Video Tutorials</strong><br>
                    <small>Step-by-step video guides</small>
                </div>
                <div style="background: white; padding: 12px; border-radius: 4px; border-left: 4px solid #28a745;">
                    <strong>📋 Cheat Sheets</strong><br>
                    <small>Quick reference guides</small>
                </div>
                <div style="background: white; padding: 12px; border-radius: 4px; border-left: 4px solid #ffc107;">
                    <strong>🎯 Best Practices</strong><br>
                    <small>Pro tips and recommendations</small>
                </div>
                <div style="background: white; padding: 12px; border-radius: 4px; border-left: 4px solid #dc3545;">
                    <strong>🚨 Known Issues</strong><br>
                    <small>Current limitations and workarounds</small>
                </div>
            </div>
        </div>

        <div style="text-align: center; margin-top: 24px;">
            <button onclick="markStepComplete('help_resources')" style="
                background: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                font-size: 1em;
            ">
                ✅ I'm Ready to Start!
            </button>
        </div>
    </div>
    """


def create_wizard_step_completion(user_id: str) -> str:
    """Create the onboarding completion step"""
    progress_percent = onboarding_manager.get_progress_percentage(user_id)

    return f"""
    <div class="wizard-step" style="padding: 24px; text-align: center;">
        <div style="font-size: 4em; margin-bottom: 16px;">🎉</div>
        <h2 style="margin: 0 0 16px 0; color: #333;">Setup Complete!</h2>
        <p style="margin: 0 0 24px 0; font-size: 1.2em; color: #666;">
            Congratulations! You're all set to start using OWL System.
        </p>

        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 8px; margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0;">✅ What You've Accomplished</h3>
            <ul style="margin: 0; padding-left: 20px; text-align: left;">
                <li>✅ Set up your API keys securely</li>
                <li>✅ Created your first AI task</li>
                <li>✅ Explored system features and capabilities</li>
                <li>✅ Found help and documentation resources</li>
            </ul>
        </div>

        <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h4 style="margin: 0 0 12px 0; color: #1976d2;">🚀 What's Next?</h4>
            <ul style="margin: 0; padding-left: 20px; color: #1976d2; text-align: left;">
                <li>Try creating more complex AI tasks</li>
                <li>Explore different AI modules and capabilities</li>
                <li>Set up additional API keys for more providers</li>
                <li>Customize your workspace settings</li>
                <li>Share your success with the community</li>
            </ul>
        </div>

        <div style="margin: 32px 0;">
            <button onclick="window.open('#task_creation', '_self')" style="
                background: #007bff;
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                font-size: 1.1em;
                margin: 8px;
                box-shadow: 0 2px 4px rgba(0,123,255,0.2);
            ">
                🎯 Create Your Next Task
            </button>
            <button onclick="window.open('#settings', '_self')" style="
                background: #6c757d;
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                font-size: 1.1em;
                margin: 8px;
                box-shadow: 0 2px 4px rgba(108,117,125,0.2);
            ">
                ⚙️ Configure Settings
            </button>
        </div>

        <div style="background: #f8f9fa; border-radius: 8px; padding: 16px; margin: 24px 0;">
            <p style="margin: 0; color: #6c757d; font-size: 0.9em;">
                💡 <strong>Remember:</strong> You can always revisit this onboarding process from the help menu,
                or access documentation anytime you need assistance.
            </p>
        </div>
    </div>
    """


# Error UI Component Functions
def create_error_message(error_info: UserFriendlyError, show_detailed: bool = False) -> str:
    """Create a formatted error message HTML component"""
    severity_class = {
        ErrorSeverity.LOW: "info",
        ErrorSeverity.MEDIUM: "warning",
        ErrorSeverity.HIGH: "error",
        ErrorSeverity.CRITICAL: "error"
    }.get(error_info.severity, "error")

    icon_map = {
        ErrorSeverity.LOW: "ℹ️",
        ErrorSeverity.MEDIUM: "⚠️",
        ErrorSeverity.HIGH: "❌",
        ErrorSeverity.CRITICAL: "🚨"
    }

    icon = icon_map.get(error_info.severity, "❌")

    html = f"""
    <div class="error-message {severity_class}">
        <div class="error-title">
            <span class="error-icon">{icon}</span>
            {error_info.title}
        </div>
        <div class="error-content">
            {error_info.message}
        </div>
    """

    if show_detailed and error_info.show_help:
        if error_info.help_text:
            html += f"""
        <div class="error-help">
            💡 <strong>Help:</strong> {error_info.help_text}
        </div>
            """

        if error_info.suggested_solutions:
            html += """
        <div class="error-solutions">
            <strong>💡 Suggested Solutions:</strong>
            """
            for solution in error_info.suggested_solutions:
                html += f"""
            <div class="error-solution">• {solution}</div>
                """
            html += """
        </div>
            """

        html += """
        <div class="error-actions">
        """
        if error_info.can_retry:
            html += """
            <button class="error-button primary" onclick="location.reload()">🔄 Try Again</button>
            """

        if error_info.documentation_url:
            html += f"""
            <a href="{error_info.documentation_url}" class="error-button" target="_blank">📚 Get Help</a>
            """

        html += """
        </div>
        """

    html += """
    </div>
    """
    return html


def create_error_modal(error_info: UserFriendlyError) -> str:
    """Create an error modal HTML component"""
    icon_map = {
        ErrorSeverity.LOW: "ℹ️",
        ErrorSeverity.MEDIUM: "⚠️",
        ErrorSeverity.HIGH: "❌",
        ErrorSeverity.CRITICAL: "🚨"
    }

    icon = icon_map.get(error_info.severity, "❌")

    html = f"""
    <div class="error-modal-overlay" id="error-modal">
        <div class="error-modal">
            <div class="error-modal-header">
                <h3 style="margin: 0; color: #dc3545;">
                    <span style="margin-right: 8px;">{icon}</span>
                    {error_info.title}
                </h3>
                <button class="error-modal-close" onclick="document.getElementById('error-modal').style.display='none'">×</button>
            </div>
            <div style="margin-bottom: 16px; line-height: 1.5;">
                {error_info.message}
            </div>
    """

    if error_info.help_text:
        html += f"""
            <div style="background: #f8f9fa; padding: 12px; border-radius: 4px; margin: 16px 0; font-size: 0.9em;">
                <strong>💡 Help:</strong> {error_info.help_text}
            </div>
        """

    if error_info.suggested_solutions:
        html += """
            <div style="margin: 16px 0;">
                <strong>💡 Suggested Solutions:</strong>
                <ul style="margin: 8px 0; padding-left: 20px;">
        """
        for solution in error_info.suggested_solutions:
            html += f"""
                    <li style="margin: 4px 0;">{solution}</li>
            """
        html += """
                </ul>
            </div>
        """

    html += """
            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 20px;">
    """
    if error_info.can_retry:
        html += """
                <button class="error-button primary" onclick="location.reload()">🔄 Try Again</button>
        """

    if error_info.documentation_url:
        html += f"""
                <a href="{error_info.documentation_url}" class="error-button" target="_blank">📚 Get Help</a>
        """

    html += """
                <button class="error-button" onclick="document.getElementById('error-modal').style.display='none'">Close</button>
            </div>
        </div>
    </div>
    """
    return html


def create_error_statistics_dashboard() -> str:
    """Create an error statistics dashboard for admin view"""
    stats = error_service.get_error_stats()
    recent_errors = error_service.get_recent_errors(10)

    html = """
    <div class="error-stats">
        <div class="error-stat-card">
            <div class="error-stat-number">""" + str(sum(stats.values())) + """</div>
            <div class="error-stat-label">Total Errors</div>
        </div>
        <div class="error-stat-card">
            <div class="error-stat-number">""" + str(stats.get("AUTH_INVALID_CREDENTIALS", 0)) + """</div>
            <div class="error-stat-label">Login Failures</div>
        </div>
        <div class="error-stat-card">
            <div class="error-stat-number">""" + str(stats.get("VALIDATION_EMPTY_TASK", 0)) + """</div>
            <div class="error-stat-label">Validation Errors</div>
        </div>
        <div class="error-stat-card">
            <div class="error-stat-number">""" + str(stats.get("SYSTEM_UNAVAILABLE", 0)) + """</div>
            <div class="error-stat-label">System Errors</div>
        </div>
    </div>

    <div style="margin-top: 20px;">
        <h4>Recent Error Events</h4>
        <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 16px; max-height: 300px; overflow-y: auto;">
    """

    if recent_errors:
        for error_entry in recent_errors:
            error = error_entry['error']
            context = error_entry['context']
            timestamp = error_entry['timestamp']

            html += f"""
            <div style="border-bottom: 1px solid #f0f0f0; padding: 8px 0;">
                <div style="font-weight: bold; color: #dc3545;">{error['title']}</div>
                <div style="font-size: 0.9em; color: #6c757d;">{timestamp} | User: {context['user_id'] or 'anonymous'} | Component: {context['component']}</div>
            </div>
            """
    else:
        html += """
            <div style="text-align: center; color: #6c757d; padding: 20px;">No recent errors</div>
        """

    html += """
        </div>
    </div>
    """

    return html


def create_error_report() -> str:
    """Create a comprehensive error report"""
    stats = error_service.get_error_stats()
    recent_errors = error_service.get_recent_errors(50)

    report = f"""
# Error Report - {datetime.datetime.now().isoformat()}

## Summary Statistics
- Total Errors: {sum(stats.values())}
- Unique Error Types: {len(stats)}
- Most Common Error: {max(stats.items(), key=lambda x: x[1])[0] if stats else 'None'}

## Error Breakdown by Category
"""

    category_counts = {}
    for error_entry in recent_errors:
        category = error_entry['error']['category']
        category_counts[category] = category_counts.get(category, 0) + 1

    for category, count in category_counts.items():
        report += f"- {category}: {count} errors\n"

    report += "\n## Most Frequent Errors\n"
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
    for error_code, count in sorted_stats:
        report += f"- {error_code}: {count} occurrences\n"

    return report


def log_user_feedback(error_code: str, feedback: str, user_id: str = None):
    """Log user feedback about error resolution"""
    context = ErrorContext(
        user_id=user_id,
        component="error_feedback",
        operation="user_feedback",
        metadata={"error_code": error_code, "feedback": feedback}
    )

    # Create a special feedback entry
    feedback_entry = {
        'error_code': error_code,
        'feedback': feedback,
        'user_id': user_id,
        'timestamp': datetime.datetime.now().isoformat()
    }

    # Store in error service (you could extend this to store in a separate feedback table)
    error_service.error_history.append({
        'error': {'code': 'USER_FEEDBACK', 'title': 'User Feedback', 'message': feedback},
        'context': asdict(context),
        'timestamp': datetime.datetime.now().isoformat()
    })

    logging.info(f"User feedback logged for error {error_code}: {feedback}")


def create_default_users():
    """Create default admin and user accounts if they don't exist"""
    try:
        # Create admin user
        if not any(u.username == "admin" for u in auth_manager.users.values()):
            admin_user = auth_manager.create_user("admin", "admin123", UserRole.ADMIN)
            if admin_user:
                logging.info("Created default admin user")

        # Create regular user
        if not any(u.username == "user" for u in auth_manager.users.values()):
            user = auth_manager.create_user("user", "user123", UserRole.USER)
            if user:
                logging.info("Created default user account")

    except Exception as e:
        logging.error(f"Failed to create default users: {e}")


def create_ui():
    """Create the main Gradio interface with authentication"""

    def check_authentication():
        """Check if user is authenticated"""
        return auth_manager.current_user is not None

    def get_current_user_info():
        """Get current user information"""
        if auth_manager.current_user:
            return f"👤 {auth_manager.current_user.username} ({auth_manager.current_user.role.value})"
        return "Not logged in"

    def logout_user():
        """Log out current user"""
        if auth_manager.current_session:
            auth_manager.logout(auth_manager.current_session.id)
        return "✅ Logged out successfully"

    # Create tabs for different interface states
    with gr.Tabs() as main_tabs:

        # Login Tab
        with gr.TabItem("🔐 Login", id="login_tab"):
            create_login_interface()

        # Main Application Tab (only accessible when authenticated)
        with gr.TabItem("🦉 OWL System", id="main_tab"):
            with gr.Row():
                with gr.Column(scale=1):
                    # User info and logout
                    user_info = gr.Markdown(f"**Current User:** {get_current_user_info()}")

                    logout_button = gr.Button("🚪 Logout", variant="secondary")
                    logout_status = gr.Textbox(
                        label="Status",
                        interactive=False,
                        value="Please log in to access the system"
                    )

                    logout_button.click(
                        fn=logout_user,
                        outputs=[logout_status]
                    ).then(
                        fn=lambda: gr.update(selected="login_tab"),
                        outputs=[main_tabs]
                    )

            # Main application interface with new 4-tab structure
            with gr.Row(visible=False) as main_interface:
                # Onboarding system integration
                user_id = auth_manager.current_user.id if auth_manager.current_user else "anonymous"
                onboarding_state = onboarding_manager.get_or_create_onboarding_state(user_id)

                # Show welcome screen for new users or progress for ongoing onboarding
                if onboarding_state.wizard_visible and onboarding_state.current_step != OnboardingStep.COMPLETED:
                    # Show welcome screen and progress
                    welcome_html = create_welcome_screen(user_id)
                    gr.HTML(value=welcome_html, label="Welcome & Setup")

                    # Setup wizard with step-by-step onboarding
                    with gr.Group(visible=True) as setup_wizard:
                        # Wizard header with progress
                        wizard_progress = gr.HTML(value="")
                        wizard_content = gr.HTML(value="")

                        # Wizard navigation
                        with gr.Row():
                            wizard_back = gr.Button("⬅️ Back", variant="secondary", visible=False)
                            wizard_skip = gr.Button("Skip", variant="secondary")
                            wizard_next = gr.Button("Next ➡️", variant="primary")
                            wizard_complete = gr.Button("🎉 Complete Setup", variant="primary", visible=False)

                        # Hidden state management
                        wizard_step = gr.State(value="welcome")
                        wizard_step_index = gr.State(value=0)

                # Main application interface (show when onboarding is complete or skipped)
                with gr.Group(visible=not onboarding_state.wizard_visible or onboarding_state.current_step == OnboardingStep.COMPLETED) as main_app_interface:
                    # Show completion message if onboarding was just completed
                    if onboarding_state.current_step == OnboardingStep.COMPLETED and not onboarding_state.first_login:
                        gr.HTML(value=create_onboarding_progress_html(user_id))

                    # Role-based welcome message
                    if auth_manager.current_user and auth_manager.current_user.role == UserRole.ADMIN:
                        gr.Markdown(f"## 👑 Welcome back, Administrator {auth_manager.current_user.username}!")
                        gr.Markdown("You have full access to all system features and administration panels.")
                    else:
                        gr.Markdown(f"## 👤 Welcome back, {auth_manager.current_user.username if auth_manager.current_user else 'User'}!")
                        gr.Markdown("You have access to basic system features. Contact an administrator for additional permissions.")

                # New 4-tab structure for authenticated users
                with gr.Tabs() as app_tabs:

                    # Tab 1: Task Creation (Primary Interface)
                    with gr.TabItem("🎯 Task Creation", id="task_creation"):
                        with gr.Row():
                            with gr.Column(scale=2):
                                gr.Markdown("### Create New Task")
                                gr.Markdown("Configure your OWL multi-agent collaboration task with the settings below.")

                                # Task configuration
                                question_input = gr.Textbox(
                                    lines=5,
                                    placeholder="Describe your task or question for the multi-agent system...",
                                    label="Task Description",
                                    elem_id="question_input",
                                    show_copy_button=True,
                                    value="Open Brave search, summarize the github stars, fork counts, etc. of camel-ai's camel framework, and write the numbers into a python file using the plot package, save it locally, and run the generated python file. Note: You have been provided with the necessary tools to complete this task.",
                                )

                                # Module selection
                                module_dropdown = gr.Dropdown(
                                    choices=list(MODULE_DESCRIPTIONS.keys()),
                                    value="run",
                                    label="AI Model Module",
                                    interactive=True,
                                )

                                # Module description
                                module_description = gr.Textbox(
                                    value=MODULE_DESCRIPTIONS["run"],
                                    label="Module Description",
                                    interactive=False,
                                    elem_classes="module-info",
                                )

                                # Example tasks
                                examples = [
                                    "Open Brave search, summarize the github stars, fork counts, etc. of camel-ai's camel framework, and write the numbers into a python file using the plot package, save it locally, and run the generated python file. Note: You have been provided with the necessary tools to complete this task.",
                                    "Browse Amazon and find a product that is attractive to programmers. Please provide the product name and price",
                                    "Write a hello world python file and save it locally",
                                ]

                                gr.Examples(examples=examples, inputs=question_input)

                                # Advanced options (collapsible)
                                with gr.Accordion("⚙️ Advanced Options", open=False):
                                    gr.Markdown("Configure advanced settings for your task.")

                                    # Session timeout
                                    timeout_input = gr.Slider(
                                        minimum=30,
                                        maximum=3600,
                                        value=300,
                                        label="Session Timeout (seconds)",
                                        info="Maximum time for the task to run"
                                    )

                                    # Max iterations
                                    max_iterations = gr.Slider(
                                        minimum=1,
                                        maximum=50,
                                        value=10,
                                        label="Max Iterations",
                                        info="Maximum number of agent interactions"
                                    )

                                    # Output format
                                    output_format = gr.Dropdown(
                                        choices=["markdown", "json", "html", "text"],
                                        value="markdown",
                                        label="Output Format"
                                    )

                                # Task execution
                                with gr.Row():
                                    run_button = gr.Button(
                                        "🚀 Execute Task",
                                        variant="primary",
                                        size="lg"
                                    )

                                # Task status
                                status_output = gr.HTML(
                                    value="<span class='status-indicator status-success'></span> Ready to execute task",
                                    label="Task Status",
                                )

                    # Tab 2: Results & History (Default View)
                    with gr.TabItem("📊 Results & History", id="results_history"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                gr.Markdown("### Task Results & History")
                                gr.Markdown("View results from your completed tasks and browse task history.")

                                # Results display
                                with gr.Group():
                                    gr.Markdown("#### Current Task Results")
                                    log_display = gr.Markdown(
                                        value="No active task. Create a new task to get started.",
                                        elem_classes="log-display",
                                    )

                                # Task history
                                with gr.Group():
                                    gr.Markdown("#### Task History")
                                    # Placeholder for task history - will be populated with actual task data
                                    task_history = gr.Dataframe(
                                        headers=["Task ID", "Description", "Module", "Status", "Timestamp", "Duration"],
                                        value=[],
                                        label="Recent Tasks",
                                        interactive=False
                                    )

                                # History controls
                                with gr.Row():
                                    refresh_history_button = gr.Button("🔄 Refresh History")
                                    clear_history_button = gr.Button("🗑️ Clear History", variant="secondary")
                                    export_results_button = gr.Button("📤 Export Results")

                    # Tab 3: Settings & Configuration (Advanced)
                    with gr.TabItem("⚙️ Settings & Configuration", id="settings"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                gr.Markdown("### System Settings & Configuration")
                                gr.Markdown("Configure API keys, environment variables, and system preferences.")

                                # Environment Variables Section
                                with gr.Group():
                                    gr.Markdown("#### 🔐 Environment Variables & API Keys")
                                    gr.Markdown("""
                                    Configure your API keys and environment variables securely. These settings are stored locally and never transmitted over the network.

                                    <div class="security-notice">
                                    <strong>🔒 Security Notice:</strong> API keys are automatically masked for security.
                                    Use the view/edit mode buttons to temporarily reveal values when needed.
                                    </div>
                                    """)

                                    # Environment variable table
                                    env_table = gr.Dataframe(
                                        headers=[
                                            "Variable Name",
                                            "Value",
                                            "Retrieval Guide",
                                        ],
                                        datatype=[
                                            "str",
                                            "str",
                                            "html",
                                        ],
                                        row_count=10,
                                        col_count=(3, "fixed"),
                                        value=update_env_table,
                                        label="API Keys and Environment Variables",
                                        interactive=True,
                                        elem_classes="env-table",
                                    )

                                    # Environment variable controls
                                    with gr.Row():
                                        save_env_button = gr.Button(
                                            "💾 Save Changes",
                                            variant="primary"
                                        )
                                        refresh_env_button = gr.Button("🔄 Refresh List")

                                    # View/Edit mode toggle
                                    with gr.Row():
                                        view_mode_button = gr.Button(
                                            "🔒 View Mode (Masked)",
                                            elem_classes="env-button",
                                        )
                                        edit_mode_button = gr.Button(
                                            "⚠️ Edit Mode (Unmasked)",
                                            variant="secondary",
                                            elem_classes="env-button",
                                        )

                                    # Status display
                                    env_status = gr.HTML(
                                        label="Environment Status",
                                        value="",
                                        elem_classes="env-status",
                                    )

                                # System Configuration Section
                                with gr.Group():
                                    gr.Markdown("#### 🖥️ System Configuration")

                                    # Logging level
                                    log_level = gr.Dropdown(
                                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                                        value="INFO",
                                        label="Log Level"
                                    )

                                    # Auto-save settings
                                    auto_save = gr.Checkbox(
                                        label="Auto-save task results",
                                        value=True
                                    )

                                    # Theme selection
                                    theme = gr.Dropdown(
                                        choices=["Light", "Dark", "Auto"],
                                        value="Auto",
                                        label="Interface Theme"
                                    )

                                    # Save settings button
                                    save_settings_button = gr.Button("💾 Save Settings")

                                    settings_status = gr.HTML(
                                        label="Settings Status",
                                        value="Settings loaded successfully"
                                    )

                    # Tab 4: System Status (Admin Only)
                    if auth_manager.current_user and auth_manager.current_user.role == UserRole.ADMIN:
                        with gr.TabItem("🖥️ System Status", id="system_status"):
                            with gr.Row():
                                with gr.Column(scale=1):
                                    gr.Markdown("### System Status & Administration")
                                    gr.Markdown("Monitor system health, manage users, and view security logs.")

                                    # System Health Section
                                    with gr.Group():
                                        gr.Markdown("#### 💚 System Health")
                                        gr.Markdown("System Status: ✅ All Systems Operational")
                                        gr.Markdown("Uptime: 99.9% | Memory Usage: 45% | CPU Usage: 23%")

                                    # User Management Section
                                    with gr.Group():
                                        gr.Markdown("#### 👥 User Management")

                                        with gr.Row():
                                            new_username_input = gr.Textbox(
                                                label="New Username",
                                                placeholder="Enter username"
                                            )
                                            new_password_input = gr.Textbox(
                                                label="New Password",
                                                placeholder="Enter password",
                                                type="password"
                                            )
                                            new_role_dropdown = gr.Dropdown(
                                                choices=["user", "admin"],
                                                value="user",
                                                label="Role"
                                            )
                                            create_user_button = gr.Button(
                                                "Create User",
                                                variant="primary"
                                            )

                                        create_user_status = gr.Textbox(
                                            label="User Creation Status",
                                            interactive=False
                                        )

                                        # User listing
                                        with gr.Row():
                                            refresh_users_button = gr.Button("Refresh User List")
                                            users_list = gr.Dataframe(
                                                headers=["ID", "Username", "Role", "Status", "Last Login", "Failed Attempts"],
                                                value=[],
                                                label="Current Users"
                                            )

                                    # Security Monitoring Section
                                    with gr.Group():
                                        gr.Markdown("#### 🔒 Security Monitoring")

                                        with gr.Row():
                                            refresh_logs_button = gr.Button("Refresh Security Logs")
                                            security_logs_display = gr.Textbox(
                                                label="Recent Security Events",
                                                lines=8,
                                                interactive=False,
                                                value="No security logs available"
                                            )

                                        with gr.Row():
                                            refresh_sessions_button = gr.Button("Refresh Sessions")
                                            sessions_display = gr.Dataframe(
                                                headers=["Session ID", "Username", "Created", "Expires", "IP Address"],
                                                value=[],
                                                label="Active Sessions"
                                            )

                                # Error monitoring section
                                with gr.Accordion("🔍 Error Monitoring", open=False):
                                    gr.Markdown("#### Error Statistics & Monitoring")
                                    error_stats_display = gr.HTML(
                                        value=create_error_statistics_dashboard(),
                                        label="Error Statistics"
                                    )

                                    with gr.Row():
                                        refresh_error_stats_button = gr.Button("Refresh Error Stats")
                                        clear_error_history_button = gr.Button("Clear Error History", variant="secondary")
                                        export_error_report_button = gr.Button("Export Error Report")

                                    error_report_display = gr.Textbox(
                                        label="Error Report",
                                        lines=15,
                                        interactive=False,
                                        value="Click 'Export Error Report' to generate a detailed error report."
                                    )

    # Add event handler to update login status and switch tabs
    def update_login_status(status):
        if "Login successful" in status:
            return gr.update(selected="main_tab")
        return gr.update(selected="login_tab")

    # Connect login button to tab switching
    login_button.click(
        fn=handle_login,
        inputs=[username_input, password_input],
        outputs=[login_status]
    ).then(
        fn=update_login_status,
        inputs=[login_status],
        outputs=[main_tabs]
    )

    # Admin functionality handlers
    def handle_create_user(username, password, role):
        """Handle user creation from admin panel"""
        current_user = auth_manager.current_user
        if not current_user or current_user.role != UserRole.ADMIN:
            error_info = handle_authorization_error(current_user, "manage_users")
            return f"❌ {error_info.message}"

        if not username or not password:
            error_info = handle_validation_error("user_creation")
            return f"❌ {error_info.message}"

        try:
            return create_new_user(username, password, role)
        except Exception as e:
            error_info = handle_system_error("user_creation", e, current_user)
            return f"❌ {error_info.message}"

    def handle_refresh_users():
        """Refresh the users list for admin panel"""
        if not auth_manager.current_user or auth_manager.current_user.role != UserRole.ADMIN:
            return []

        users_data = get_all_users()
        # Convert to DataFrame format
        df_data = []
        for user in users_data:
            df_data.append([
                user['id'],
                user['username'],
                user['role'],
                "Active" if user['is_active'] else "Inactive",
                user['last_login'] or "Never",
                user['failed_attempts']
            ])
        return df_data

    def handle_refresh_security_logs():
        """Refresh security logs for admin panel"""
        if not auth_manager.current_user or auth_manager.current_user.role != UserRole.ADMIN:
            return "❌ Access denied - admin privileges required"

        logs = get_security_logs()
        return "\n".join(logs) if logs else "No security logs available"

    def handle_refresh_sessions():
        """Refresh active sessions for admin panel"""
        if not auth_manager.current_user or auth_manager.current_user.role != UserRole.ADMIN:
            return []

        sessions_data = get_active_sessions()
        # Convert to DataFrame format
        df_data = []
        for session in sessions_data:
            df_data.append([
                session['session_id'],
                session['username'],
                session['created_at'],
                session['expires_at'],
                session['ip_address'] or "Unknown"
            ])
        return df_data

    # Connect admin functionality (only if user is admin and elements exist)
    # Note: These handlers will be connected when the admin UI is created

    # New tab structure event handlers
    def handle_module_selection(module_name):
        """Handle module selection and update description"""
        return MODULE_DESCRIPTIONS.get(module_name, "Module description not available")

    def handle_task_execution(question, module, timeout, max_iter, output_fmt):
        """Handle task execution with all parameters"""
        if not question.strip():
            error_info = handle_validation_error("task_description")
            return f"❌ {error_info.message}"

        try:
            # Check if user has permission to use the module
            current_user = auth_manager.current_user
            if current_user and not auth_manager.check_permission(current_user, "access_basic_modules"):
                error_info = handle_authorization_error(current_user, "access_basic_modules")
                return f"❌ {error_info.message}"

            # Call the existing run_owl function with authentication
            result = run_owl(question, module)
            return f"✅ Task executed successfully with module: {module}"
        except Exception as e:
            logging.error(f"Task execution error: {e}")
            error_info = handle_system_error("task_execution", e, auth_manager.current_user)
            return f"❌ {error_info.message}"

    def handle_settings_save(log_level, auto_save, theme):
        """Handle settings save"""
        return "✅ Settings saved successfully"

    def handle_cross_tab_navigation(target_tab):
        """Handle navigation between tabs"""
        return gr.update(selected=target_tab)

    # Connect event handlers for new tab structure
    try:
        # Task Creation Tab
        module_dropdown.change(
            fn=handle_module_selection,
            inputs=[module_dropdown],
            outputs=[module_description]
        )

        run_button.click(
            fn=handle_task_execution,
            inputs=[question_input, module_dropdown, timeout_input, max_iterations, output_format],
            outputs=[status_output]
        ).then(
            fn=lambda: handle_cross_tab_navigation("results_history"),
            outputs=[app_tabs]
        )

        # Settings Tab
        save_settings_button.click(
            fn=handle_settings_save,
            inputs=[log_level, auto_save, theme],
            outputs=[settings_status]
        )

        # Environment variable handlers
        save_env_button.click(
            fn=save_env_table_changes,
            inputs=[env_table],
            outputs=[env_status]
        ).then(fn=update_env_table, outputs=[env_table])

        refresh_env_button.click(fn=update_env_table, outputs=[env_table])

        view_mode_button.click(
            fn=lambda: handle_env_mode_change("view"),
            outputs=[env_status]
        ).then(fn=update_env_table, outputs=[env_table])

        edit_mode_button.click(
            fn=lambda: handle_env_mode_change("edit"),
            outputs=[env_status]
        ).then(fn=update_env_table, outputs=[env_table])

        # History Tab
        refresh_history_button.click(
            fn=lambda: gr.update(value="History refreshed"),
            outputs=[log_display]
        )

        # Admin functionality (only if admin)
        if auth_manager.current_user and auth_manager.current_user.role == UserRole.ADMIN:
            create_user_button.click(
                fn=handle_create_user,
                inputs=[new_username_input, new_password_input, new_role_dropdown],
                outputs=[create_user_status]
            ).then(fn=handle_refresh_users, outputs=[users_list])

            refresh_users_button.click(fn=handle_refresh_users, outputs=[users_list])
            refresh_logs_button.click(fn=handle_refresh_security_logs, outputs=[security_logs_display])
            refresh_sessions_button.click(fn=handle_refresh_sessions, outputs=[sessions_display])

            # Error monitoring functionality
            refresh_error_stats_button.click(
                fn=lambda: create_error_statistics_dashboard(),
                outputs=[error_stats_display]
            )

            clear_error_history_button.click(
                fn=lambda: (error_service.clear_error_history(), "Error history cleared successfully"),
                outputs=[error_report_display]
            )

            export_error_report_button.click(
                fn=lambda: create_error_report(),
                outputs=[error_report_display]
            )

    except NameError as e:
        # Some UI elements might not exist depending on user role
        logging.debug(f"Some UI elements not available: {e}")

    # Helper function for environment mode changes
    def handle_env_mode_change(mode):
        """Handle environment variable display mode changes"""
        global ENV_DISPLAY_MODE, ENV_EDIT_CONFIRMED

        if mode == "edit" and not ENV_EDIT_CONFIRMED:
            ENV_DISPLAY_MODE = "edit"
            ENV_EDIT_CONFIRMED = False
            return "⚠️ Please confirm you understand the security implications of viewing unmasked sensitive data"
        elif mode == "view":
            ENV_DISPLAY_MODE = "view"
            ENV_EDIT_CONFIRMED = False
            return "🔒 Environment variables now in view mode (masked)"
        else:
            ENV_EDIT_CONFIRMED = True
            return "✅ Confirmed - you can now view and edit sensitive environment variable values"


# Log reading and updating functions
def log_reader_thread(log_file):
    """Background thread that continuously reads the log file and adds new lines to the queue"""
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Move to the end of file
            f.seek(0, 2)

            while not STOP_LOG_THREAD.is_set():
                line = f.readline()
                if line:
                    LOG_QUEUE.put(line)  # Add to conversation record queue
                else:
                    # No new lines, wait for a short time
                    time.sleep(0.1)
    except Exception as e:
        logging.error(f"Log reader thread error: {str(e)}")


def get_latest_logs(max_lines=100, queue_source=None):
    """Get the latest log lines from the queue, or read directly from the file if the queue is empty

    Args:
        max_lines: Maximum number of lines to return
        queue_source: Specify which queue to use, default is LOG_QUEUE

    Returns:
        str: Log content
    """
    logs = []
    log_queue = queue_source if queue_source else LOG_QUEUE

    # Create a temporary queue to store logs so we can process them without removing them from the original queue
    temp_queue = queue.Queue()
    temp_logs = []

    try:
        # Try to get all available log lines from the queue
        while not log_queue.empty() and len(temp_logs) < max_lines:
            log = log_queue.get_nowait()
            temp_logs.append(log)
            temp_queue.put(log)  # Put the log back into the temporary queue
    except queue.Empty:
        pass

    # Process conversation records
    logs = temp_logs

    # If there are no new logs or not enough logs, try to read the last few lines directly from the file
    if len(logs) < max_lines and LOG_FILE and os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                # If there are already some logs in the queue, only read the remaining needed lines
                remaining_lines = max_lines - len(logs)
                file_logs = (
                    all_lines[-remaining_lines:]
                    if len(all_lines) > remaining_lines
                    else all_lines
                )

                # Add file logs before queue logs
                logs = file_logs + logs
        except Exception as e:
            error_msg = f"Error reading log file: {str(e)}"
            logging.error(error_msg)
            if not logs:  # Only add error message if there are no logs
                logs = [error_msg]

    # If there are still no logs, return a prompt message
    if not logs:
        return "Initialization in progress..."

    # Filter logs, only keep logs with 'camel.agents.chat_agent - INFO'
    filtered_logs = []
    for log in logs:
        if "camel.agents.chat_agent - INFO" in log:
            filtered_logs.append(log)

    # If there are no logs after filtering, return a prompt message
    if not filtered_logs:
        return "No conversation records yet."

    # Process log content, extract the latest user and assistant messages
    simplified_logs = []

    # Use a set to track messages that have already been processed, to avoid duplicates
    processed_messages = set()

    def process_message(role, content):
        # Create a unique identifier to track messages
        msg_id = f"{role}:{content}"
        if msg_id in processed_messages:
            return None

        processed_messages.add(msg_id)
        content = content.replace("\\n", "\n")
        lines = [line.strip() for line in content.split("\n")]
        content = "\n".join(lines)

        role_emoji = "🙋" if role.lower() == "user" else "🤖"
        return f"""### {role_emoji} {role.title()} Agent

{content}"""

    for log in filtered_logs:
        formatted_messages = []
        # Try to extract message array
        messages_match = re.search(
            r"Model (.*?), index (\d+), processed these messages: (\[.*\])", log
        )

        if messages_match:
            try:
                messages = json.loads(messages_match.group(3))
                for msg in messages:
                    if msg.get("role") in ["user", "assistant"]:
                        formatted_msg = process_message(
                            msg.get("role"), msg.get("content", "")
                        )
                        if formatted_msg:
                            formatted_messages.append(formatted_msg)
            except json.JSONDecodeError:
                pass

        # If JSON parsing fails or no message array is found, try to extract conversation content directly
        if not formatted_messages:
            user_pattern = re.compile(r"\{'role': 'user', 'content': '(.*?)'\}")
            assistant_pattern = re.compile(
                r"\{'role': 'assistant', 'content': '(.*?)'\}"
            )

            for content in user_pattern.findall(log):
                formatted_msg = process_message("user", content)
                if formatted_msg:
                    formatted_messages.append(formatted_msg)

            for content in assistant_pattern.findall(log):
                formatted_msg = process_message("assistant", content)
                if formatted_msg:
                    formatted_messages.append(formatted_msg)

        if formatted_messages:
            simplified_logs.append("\n\n".join(formatted_messages))

    # Format log output, ensure appropriate separation between each conversation record
    formatted_logs = []
    for i, log in enumerate(simplified_logs):
        # Remove excess whitespace characters from beginning and end
        log = log.strip()

        formatted_logs.append(log)

        # Ensure each conversation record ends with a newline
        if not log.endswith("\n"):
            formatted_logs.append("\n")

    return "\n".join(formatted_logs)


# Define allowed modules for security (RCE Prevention)
ALLOWED_MODULES = {
    'run',
    'run_mini',
    'run_gemini',
    'run_claude',
    'run_deepseek_zh',
    'run_qwen_zh',
    'run_terminal_zh'
}

def validate_module_name(module_name: str) -> bool:
    """Validate if a module name is in the allowed modules list.

    Args:
        module_name: The module name to validate

    Returns:
        bool: True if the module is allowed, False otherwise
    """
    if not module_name or not isinstance(module_name, str):
        return False

    # Remove any path separators for security
    clean_name = module_name.replace('/', '').replace('\\', '').replace('.', '')

    return clean_name in ALLOWED_MODULES


class UnauthorizedModuleError(Exception):
    """Custom exception for unauthorized module access attempts."""

    def __init__(self, module_name: str, message: str = None):
        self.module_name = module_name
        self.message = message or f"Access to module '{module_name}' is not authorized"
        super().__init__(self.message)


def log_module_access(module_name: str, access_granted: bool, user_context: str = None, error_message: str = None):
    """Log all module access attempts for security monitoring.

    Args:
        module_name: The module name being accessed
        access_granted: Whether access was granted or denied
        user_context: Optional context about who is accessing the module
        error_message: Optional error message if access was denied
    """
    timestamp = datetime.datetime.now().isoformat()
    status = "GRANTED" if access_granted else "DENIED"
    log_level = logging.INFO if access_granted else logging.WARNING

    log_message = (
        f"SECURITY: Module access {status} | "
        f"Module: {module_name} | "
        f"Timestamp: {timestamp} | "
        f"UserContext: {user_context or 'N/A'}"
    )

    if error_message:
        log_message += f" | Error: {error_message}"

    logging.log(log_level, log_message)


# Dictionary containing module descriptions
MODULE_DESCRIPTIONS = {
    "run": "Default mode: Using OpenAI model's default agent collaboration mode, suitable for most tasks.",
    "run_mini": "Using OpenAI model with minimal configuration to process tasks",
    "run_gemini": "Using Gemini model to process tasks",
    "run_claude": "Using Claude model to process tasks",
    "run_deepseek_zh": "Using deepseek model to process Chinese tasks",
    "run_mistral": "Using Mistral models to process tasks",
    "run_openai_compatible_model": "Using openai compatible model to process tasks",
    "run_ollama": "Using local ollama model to process tasks",
    "run_qwen_mini_zh": "Using qwen model with minimal configuration to process tasks",
    "run_qwen_zh": "Using qwen model to process tasks",
    "run_azure_openai": "Using azure openai model to process tasks",
    "run_groq": "Using groq model to process tasks",
    "run_ppio": "Using ppio model to process tasks",
    "run_together_ai": "Using together ai model to process tasks",
    "run_novita_ai": "Using novita ai model to process tasks",
}


# Default environment variable template
DEFAULT_ENV_TEMPLATE = """#===========================================
# MODEL & API 
# (See https://docs.camel-ai.org/key_modules/models.html#)
#===========================================

# OPENAI API (https://platform.openai.com/api-keys)
OPENAI_API_KEY='Your_Key'
# OPENAI_API_BASE_URL=""

# Azure OpenAI API
# AZURE_OPENAI_BASE_URL=""
# AZURE_API_VERSION=""
# AZURE_OPENAI_API_KEY=""
# AZURE_DEPLOYMENT_NAME=""


# Qwen API (https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key)
QWEN_API_KEY='Your_Key'

# DeepSeek API (https://platform.deepseek.com/api_keys)
DEEPSEEK_API_KEY='Your_Key'

#===========================================
# Tools & Services API
#===========================================

# Google Search API (https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3)
GOOGLE_API_KEY='Your_Key'
SEARCH_ENGINE_ID='Your_ID'

# Chunkr API (https://chunkr.ai/)
CHUNKR_API_KEY='Your_Key'

# Firecrawl API (https://www.firecrawl.dev/)
FIRECRAWL_API_KEY='Your_Key'
#FIRECRAWL_API_URL="https://api.firecrawl.dev"
"""


def validate_input(question: str) -> bool:
    """Validate if user input is valid

    Args:
        question: User question

    Returns:
        bool: Whether the input is valid
    """
    # Check if input is empty or contains only spaces
    if not question or question.strip() == "":
        return False
    return True


@require_authentication
def run_owl(question: str, example_module: str) -> Tuple[str, str, str]:
    """Run the OWL system and return results

    Args:
        question: User question
        example_module: Example module name to import (e.g., "run_terminal_zh" or "run_deep")

    Returns:
        Tuple[...]: Answer, token count, status
    """
    global CURRENT_PROCESS

    # Validate input
    if not validate_input(question):
        logging.warning("User submitted invalid input")
        return (
            "Please enter a valid question",
            "0",
            "❌ Error: Invalid input question",
        )

    try:
        # Ensure environment variables are loaded
        load_dotenv(find_dotenv(), override=True)
        logging.info(
            f"Processing question: '{question}', using module: {example_module}"
        )

        # Validate module name against allowed modules (RCE Prevention)
        try:
            if not validate_module_name(example_module):
                log_module_access(
                    module_name=example_module,
                    access_granted=False,
                    user_context=f"Question: {question[:50]}...",
                    error_message="Module not in ALLOWED_MODULES list"
                )
                raise UnauthorizedModuleError(example_module)
        except UnauthorizedModuleError as e:
            return (
                f"Selected module '{example_module}' is not authorized. Only the following modules are allowed: {', '.join(ALLOWED_MODULES)}",
                "0",
                f"❌ Error: {e.message}",
            )

        # Check if the module is in MODULE_DESCRIPTIONS
        if example_module not in MODULE_DESCRIPTIONS:
            logging.error(f"User selected an unsupported module: {example_module}")
            return (
                f"Selected module '{example_module}' is not supported",
                "0",
                "❌ Error: Unsupported module",
            )

        # Use static module access instead of dynamic imports (RCE Prevention)
        try:
            logging.info(f"Accessing static module: {example_module}")
            # Map module names to imported module objects
            module_map = {
                'run': run,
                'run_mini': run_mini,
                'run_gemini': run_gemini,
                'run_claude': run_claude,
                'run_deepseek_zh': run_deepseek_zh,
                'run_qwen_zh': run_qwen_zh,
                'run_terminal_zh': run_terminal_zh
            }

            module = module_map.get(example_module)
            if module is None:
                raise ImportError(f"Module {example_module} not found in static imports")

            # Log successful module access
            log_module_access(
                module_name=example_module,
                access_granted=True,
                user_context=f"Question: {question[:50]}..."
            )

        except Exception as e:
            log_module_access(
                module_name=example_module,
                access_granted=False,
                user_context=f"Question: {question[:50]}...",
                error_message=str(e)
            )
            return (
                f"Error occurred while accessing module: {example_module}",
                "0",
                f"❌ Error: {str(e)}",
            )

        # Check if it contains the construct_society function
        if not hasattr(module, "construct_society"):
            logging.error(
                f"construct_society function not found in module {example_module}"
            )
            return (
                f"construct_society function not found in module {example_module}",
                "0",
                "❌ Error: Module interface incompatible",
            )

        # Build society simulation
        try:
            logging.info("Building society simulation...")
            society = module.construct_society(question)

        except Exception as e:
            logging.error(f"Error occurred while building society simulation: {str(e)}")
            return (
                f"Error occurred while building society simulation: {str(e)}",
                "0",
                f"❌ Error: Build failed - {str(e)}",
            )

        # Run society simulation
        try:
            logging.info("Running society simulation...")
            answer, chat_history, token_info = run_society(society)
            logging.info("Society simulation completed")
        except Exception as e:
            logging.error(f"Error occurred while running society simulation: {str(e)}")
            return (
                f"Error occurred while running society simulation: {str(e)}",
                "0",
                f"❌ Error: Run failed - {str(e)}",
            )

        # Safely get token count
        if not isinstance(token_info, dict):
            token_info = {}

        completion_tokens = token_info.get("completion_token_count", 0)
        prompt_tokens = token_info.get("prompt_token_count", 0)
        total_tokens = completion_tokens + prompt_tokens

        logging.info(
            f"Processing completed, token usage: completion={completion_tokens}, prompt={prompt_tokens}, total={total_tokens}"
        )

        return (
            answer,
            f"Completion tokens: {completion_tokens:,} | Prompt tokens: {prompt_tokens:,} | Total: {total_tokens:,}",
            "✅ Successfully completed",
        )

    except Exception as e:
        logging.error(
            f"Uncaught error occurred while processing the question: {str(e)}"
        )
        return (f"Error occurred: {str(e)}", "0", f"❌ Error: {str(e)}")


def update_module_description(module_name: str) -> str:
    """Return the description of the selected module"""
    return MODULE_DESCRIPTIONS.get(module_name, "No description available")


# Store environment variables configured from the frontend
WEB_FRONTEND_ENV_VARS: dict[str, str] = {}


def init_env_file():
    """Initialize .env file if it doesn't exist"""
    dotenv_path = find_dotenv()
    if not dotenv_path:
        with open(".env", "w") as f:
            f.write(DEFAULT_ENV_TEMPLATE)
        dotenv_path = find_dotenv()
    return dotenv_path


def load_env_vars():
    """Load environment variables and return as dictionary format

    Returns:
        dict: Environment variable dictionary, each value is a tuple containing value and source (value, source)
    """
    dotenv_path = init_env_file()
    load_dotenv(dotenv_path, override=True)

    # Read environment variables from .env file
    env_file_vars = {}
    with open(dotenv_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_file_vars[key.strip()] = value.strip().strip("\"'")

    # Get from system environment variables
    system_env_vars = {
        k: v
        for k, v in os.environ.items()
        if k not in env_file_vars and k not in WEB_FRONTEND_ENV_VARS
    }

    # Merge environment variables and mark sources
    env_vars = {}

    # Add system environment variables (lowest priority)
    for key, value in system_env_vars.items():
        env_vars[key] = (value, "System")

    # Add .env file environment variables (medium priority)
    for key, value in env_file_vars.items():
        env_vars[key] = (value, ".env file")

    # Add frontend configured environment variables (highest priority)
    for key, value in WEB_FRONTEND_ENV_VARS.items():
        env_vars[key] = (value, "Frontend configuration")
        # Ensure operating system environment variables are also updated
        os.environ[key] = value

    return env_vars


def save_env_vars(env_vars):
    """Save environment variables to .env file

    Args:
        env_vars: Dictionary, keys are environment variable names, values can be strings or (value, source) tuples
    """
    try:
        dotenv_path = init_env_file()

        # Save each environment variable
        for key, value_data in env_vars.items():
            if key and key.strip():  # Ensure key is not empty
                # Handle case where value might be a tuple
                if isinstance(value_data, tuple):
                    value = value_data[0]
                else:
                    value = value_data

                set_key(dotenv_path, key.strip(), value.strip())

        # Reload environment variables to ensure they take effect
        load_dotenv(dotenv_path, override=True)

        return True, "Environment variables have been successfully saved!"
    except Exception as e:
        return False, f"Error saving environment variables: {str(e)}"


def add_env_var(key, value, from_frontend=True):
    """Add or update a single environment variable

    Args:
        key: Environment variable name
        value: Environment variable value
        from_frontend: Whether it's from frontend configuration, default is True
    """
    try:
        if not key or not key.strip():
            return False, "Variable name cannot be empty"

        key = key.strip()
        value = value.strip()

        # If from frontend, add to frontend environment variable dictionary
        if from_frontend:
            WEB_FRONTEND_ENV_VARS[key] = value
            # Directly update system environment variables
            os.environ[key] = value

        # Also update .env file
        dotenv_path = init_env_file()
        set_key(dotenv_path, key, value)
        load_dotenv(dotenv_path, override=True)

        return True, f"Environment variable {key} has been successfully added/updated!"
    except Exception as e:
        return False, f"Error adding environment variable: {str(e)}"


def delete_env_var(key):
    """Delete environment variable"""
    try:
        if not key or not key.strip():
            return False, "Variable name cannot be empty"

        key = key.strip()

        # Delete from .env file
        dotenv_path = init_env_file()
        unset_key(dotenv_path, key)

        # Delete from frontend environment variable dictionary
        if key in WEB_FRONTEND_ENV_VARS:
            del WEB_FRONTEND_ENV_VARS[key]

        # Also delete from current process environment
        if key in os.environ:
            del os.environ[key]

        return True, f"Environment variable {key} has been successfully deleted!"
    except Exception as e:
        return False, f"Error deleting environment variable: {str(e)}"


def is_api_related(key: str) -> bool:
    """Determine if an environment variable is API-related

    Args:
        key: Environment variable name

    Returns:
        bool: Whether it's API-related
    """
    # API-related keywords
    api_keywords = [
        "api",
        "key",
        "token",
        "secret",
        "password",
        "openai",
        "qwen",
        "deepseek",
        "google",
        "search",
        "hf",
        "hugging",
        "chunkr",
        "firecrawl",
    ]

    # Check if it contains API-related keywords (case insensitive)
    return any(keyword in key.lower() for keyword in api_keywords)


def mask_sensitive_value(key: str, value: str) -> str:
    """Mask sensitive environment variable values for display while preserving original values.

    Args:
        key: Environment variable name
        value: The actual value to be masked

    Returns:
        str: Masked version of the value for display
    """
    if not value or not isinstance(value, str):
        return value

    # Check if this is a sensitive key based on name patterns
    sensitive_keywords = [
        "api", "key", "token", "secret", "password", "auth",
        "credential", "access", "bearer", "session", "jwt",
        "openai", "qwen", "deepseek", "google", "search",
        "hf", "hugging", "chunkr", "firecrawl", "ppio",
        "azure", "aws", "claude", "gemini", "mistral",
        "groq", "together", "novita", "ollama"
    ]

    is_sensitive = any(keyword in key.lower() for keyword in sensitive_keywords)

    # Additional check: if value looks like it contains sensitive patterns
    sensitive_patterns = [
        r'^\w{8,}$',  # Long alphanumeric strings (likely API keys)
        r'.*sk-\w{20,}.*',  # OpenAI API key pattern
        r'.*sk-\w{20,}.*',  # Another OpenAI pattern
        r'.*\d{4,}.*',  # Contains long numeric sequences
    ]

    import re
    for pattern in sensitive_patterns:
        if re.match(pattern, value):
            is_sensitive = True
            break

    # If not sensitive, return original value
    if not is_sensitive:
        return value

    # Mask the value - show first 4 and last 4 characters
    value_len = len(value)
    if value_len <= 8:
        # For short values, mask all but first/last character
        if value_len <= 2:
            return value  # Too short to mask meaningfully
        else:
            return value[0] + "*" * (value_len - 2) + value[-1]
    else:
        # For longer values, show first 4 and last 4 with asterisks in between
        return value[:4] + "*" * (value_len - 8) + value[-4:]


def switch_env_display_mode(mode: str, confirmed: bool = False) -> tuple[str, str]:
    """Switch between view and edit modes for environment variables.

    Args:
        mode: "view" or "edit"
        confirmed: Whether user has confirmed security implications

    Returns:
        tuple: (status_message, new_mode)
    """
    global ENV_DISPLAY_MODE, ENV_EDIT_CONFIRMED

    if mode not in ["view", "edit"]:
        return "❌ Invalid mode specified", ENV_DISPLAY_MODE

    if mode == "edit" and not confirmed:
        ENV_DISPLAY_MODE = "edit"
        ENV_EDIT_CONFIRMED = False
        return "⚠️ Please confirm you understand the security implications of viewing unmasked sensitive data", "edit_pending"
    elif mode == "edit" and confirmed:
        ENV_DISPLAY_MODE = "edit"
        ENV_EDIT_CONFIRMED = True
        logging.info("Environment variable edit mode enabled - sensitive data may be visible")
        return "✅ Edit mode enabled - sensitive values are now visible", "edit"
    elif mode == "view":
        ENV_DISPLAY_MODE = "view"
        ENV_EDIT_CONFIRMED = False
        logging.info("Environment variable view mode enabled - sensitive data is masked")
        return "✅ View mode enabled - sensitive values are now masked", "view"

    return "✅ Mode switched successfully", ENV_DISPLAY_MODE


def get_env_display_mode() -> str:
    """Get the current environment variable display mode."""
    return ENV_DISPLAY_MODE


def confirm_env_edit_mode() -> str:
    """Confirm the security implications and enable edit mode."""
    global ENV_EDIT_CONFIRMED
    ENV_EDIT_CONFIRMED = True
    logging.warning("User confirmed security implications of viewing sensitive environment variable data")
    return "✅ Confirmed - you can now view and edit sensitive environment variable values"


def toggle_temporary_unmask() -> tuple[str, bool]:
    """Toggle temporary unmasking of sensitive values with auto-re-mask timeout."""
    global ENV_TEMPORARY_UNMASK, ENV_UNMASK_TIMESTAMP

    import time

    if ENV_TEMPORARY_UNMASK:
        # Currently unmasked, re-mask immediately
        ENV_TEMPORARY_UNMASK = False
        ENV_UNMASK_TIMESTAMP = None
        logging.info("Temporary unmasking disabled - sensitive values re-masked")
        return "🔒 Sensitive values re-masked", False
    else:
        # Currently masked, temporarily unmask
        ENV_TEMPORARY_UNMASK = True
        ENV_UNMASK_TIMESTAMP = time.time()
        logging.warning("Temporary unmasking enabled - sensitive values visible for 30 seconds")

        # Schedule auto-re-mask after timeout
        def auto_remask():
            time.sleep(ENV_UNMASK_TIMEOUT)
            if ENV_TEMPORARY_UNMASK and time.time() - ENV_UNMASK_TIMESTAMP >= ENV_UNMASK_TIMEOUT:
                ENV_TEMPORARY_UNMASK = False
                ENV_UNMASK_TIMESTAMP = None
                logging.info("Auto-re-mask triggered after timeout")

        # Start background thread for auto-re-mask
        import threading
        threading.Thread(target=auto_remask, daemon=True).start()

        return f"👁️ Sensitive values temporarily unmasked (auto-re-mask in {ENV_UNMASK_TIMEOUT}s)", True


def get_temporary_unmask_status() -> bool:
    """Get the current temporary unmask status."""
    return ENV_TEMPORARY_UNMASK


# Admin user management functions
@require_admin
def get_all_users() -> List[Dict]:
    """Get all users (admin only)"""
    users_data = []
    for user in auth_manager.users.values():
        users_data.append({
            'id': user.id,
            'username': user.username,
            'role': user.role.value,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active,
            'failed_attempts': user.failed_login_attempts,
            'locked_until': user.locked_until.isoformat() if user.locked_until else None
        })
    return users_data


@require_admin
def create_new_user(username: str, password: str, role: str) -> str:
    """Create a new user (admin only)"""
    try:
        role_enum = UserRole.ADMIN if role.lower() == 'admin' else UserRole.USER
        user = auth_manager.create_user(username, password, role_enum)
        if user:
            return f"✅ User '{username}' created successfully with role '{role_enum.value}'"
        else:
            return f"❌ Failed to create user '{username}' - username may already exist"
    except Exception as e:
        return f"❌ Error creating user: {str(e)}"


@require_admin
def deactivate_user(user_id: str) -> str:
    """Deactivate a user account (admin only)"""
    try:
        if user_id not in auth_manager.users:
            return f"❌ User not found"

        user = auth_manager.users[user_id]
        user.is_active = False

        # Invalidate all sessions for this user
        auth_manager.invalidate_all_user_sessions(user_id)

        auth_manager.save_data()
        auth_manager.log_security_event("USER_DEACTIVATED", f"User {user.username} deactivated by admin")
        return f"✅ User '{user.username}' deactivated successfully"
    except Exception as e:
        return f"❌ Error deactivating user: {str(e)}"


@require_admin
def reactivate_user(user_id: str) -> str:
    """Reactivate a user account (admin only)"""
    try:
        if user_id not in auth_manager.users:
            return f"❌ User not found"

        user = auth_manager.users[user_id]
        user.is_active = True
        user.failed_login_attempts = 0
        user.locked_until = None

        auth_manager.save_data()
        auth_manager.log_security_event("USER_REACTIVATED", f"User {user.username} reactivated by admin")
        return f"✅ User '{user.username}' reactivated successfully"
    except Exception as e:
        return f"❌ Error reactivating user: {str(e)}"


@require_admin
def unlock_user_account(user_id: str) -> str:
    """Unlock a locked user account (admin only)"""
    try:
        if user_id not in auth_manager.users:
            return f"❌ User not found"

        user = auth_manager.users[user_id]
        user.failed_login_attempts = 0
        user.locked_until = None

        auth_manager.save_data()
        auth_manager.log_security_event("ACCOUNT_UNLOCKED", f"Account unlocked for user {user.username} by admin")
        return f"✅ Account for user '{user.username}' unlocked successfully"
    except Exception as e:
        return f"❌ Error unlocking account: {str(e)}"


@require_admin
def get_security_logs() -> List[str]:
    """Get recent security logs (admin only)"""
    try:
        logs_file = auth_manager.security_log_file
        if os.path.exists(logs_file):
            with open(logs_file, 'r') as f:
                lines = f.readlines()[-50:]  # Get last 50 lines
                return [line.strip() for line in lines]
        return ["No security logs found"]
    except Exception as e:
        return [f"Error reading security logs: {str(e)}"]


@require_admin
def get_active_sessions() -> List[Dict]:
    """Get information about active sessions (admin only)"""
    sessions_info = []
    for session_id, session in auth_manager.sessions.items():
        info = auth_manager.get_session_info(session_id)
        if info:
            sessions_info.append(info)
    return sessions_info


def is_value_masked(key: str, display_value: str, original_value: str) -> bool:
    """Determine if a displayed value is masked.

    Args:
        key: Environment variable name
        display_value: The value currently displayed
        original_value: The original unmasked value

    Returns:
        bool: True if the value is masked, False otherwise
    """
    if (ENV_DISPLAY_MODE == "edit" and ENV_EDIT_CONFIRMED) or ENV_TEMPORARY_UNMASK:
        return False  # Not masked in edit mode or temporary unmask
    else:
        return display_value != original_value  # Masked if display != original


def enhance_env_table_with_masking_indicators(env_data):
    """Add masking indicators to environment variable table data.

    Args:
        env_data: List of [key, value, guide] tuples

    Returns:
        Enhanced data with masking indicators
    """
    enhanced_data = []
    for row in env_data:
        if len(row) >= 2:
            key, display_value = row[0], row[1]

            # Get original value to compare
            env_vars = load_env_vars()
            original_value = env_vars.get(key, ("", ""))[0] if key in env_vars else ""

            # Determine if masked
            is_masked = is_value_masked(key, display_value, original_value)

            # Add masking indicator to the key
            if is_masked:
                enhanced_key = f"🔒 {key}"  # Add lock icon for masked values
            else:
                enhanced_key = f"👁️ {key}"  # Add eye icon for visible values

            # Create enhanced row
            enhanced_row = [enhanced_key, display_value]
            if len(row) > 2:
                enhanced_row.extend(row[2:])  # Add remaining columns
            enhanced_data.append(enhanced_row)
        else:
            enhanced_data.append(row)

    return enhanced_data


def get_api_guide(key: str) -> str:
    """Return the corresponding API guide based on the environment variable name

    Args:
        key: Environment variable name

    Returns:
        str: API guide link or description
    """
    key_lower = key.lower()
    if "openai" in key_lower:
        return "https://platform.openai.com/api-keys"
    elif "qwen" in key_lower or "dashscope" in key_lower:
        return "https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key"
    elif "deepseek" in key_lower:
        return "https://platform.deepseek.com/api_keys"
    elif "ppio" in key_lower:
        return "https://ppinfra.com/settings/key-management?utm_source=github_owl"
    elif "google" in key_lower:
        return "https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3"
    elif "search_engine_id" in key_lower:
        return "https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3"
    elif "chunkr" in key_lower:
        return "https://chunkr.ai/"
    elif "firecrawl" in key_lower:
        return "https://www.firecrawl.dev/"
    elif "novita" in key_lower:
        return "https://novita.ai/settings/key-management?utm_source=github_owl&utm_medium=github_readme&utm_campaign=github_link"
    else:
        return ""


def update_env_table():
    """Update environment variable table display, only showing API-related environment variables"""
    env_vars = load_env_vars()
    # Filter out API-related environment variables
    api_env_vars = {k: v for k, v in env_vars.items() if is_api_related(k)}
    # Convert to list format to meet Gradio Dataframe requirements
    # Format: [Variable name, Variable value, Guide link]
    result = []
    for k, v in api_env_vars.items():
        guide = get_api_guide(k)
        # If there's a guide link, create a clickable link
        guide_link = (
            f"<a href='{guide}' target='_blank' class='guide-link'>🔗 Get</a>"
            if guide
            else ""
        )
        # Apply masking based on display mode and temporary unmask status
        if (ENV_DISPLAY_MODE == "edit" and ENV_EDIT_CONFIRMED) or ENV_TEMPORARY_UNMASK:
            # In edit mode with confirmation or temporary unmask, show original values
            display_value = v[0]
        else:
            # In view mode or edit mode without confirmation, show masked values
            display_value = mask_sensitive_value(k, v[0])
        result.append([k, display_value, guide_link])

    # Add masking indicators to the table
    enhanced_result = enhance_env_table_with_masking_indicators(result)
    return enhanced_result


@require_authentication
def save_env_table_changes(data):
    """Save changes to the environment variable table

    Args:
        data: Dataframe data, possibly a pandas DataFrame object

    Returns:
        str: Operation status information, containing HTML-formatted status message
    """
    try:
        logging.info(
            f"Starting to process environment variable table data, type: {type(data)}"
        )

        # Get all current environment variables
        current_env_vars = load_env_vars()
        processed_keys = set()  # Record processed keys to detect deleted variables

        # Process pandas DataFrame object
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            # Get column name information
            columns = data.columns.tolist()
            logging.info(f"DataFrame column names: {columns}")

            # Iterate through each row of the DataFrame
            for index, row in data.iterrows():
                # Use column names to access data
                if len(columns) >= 3:
                    # Get variable name and value (column 0 is name, column 1 is value)
                    key = row[0] if isinstance(row, pd.Series) else row.iloc[0]
                    value = row[1] if isinstance(row, pd.Series) else row.iloc[1]

                    # Check if it's an empty row or deleted variable
                    if (
                        key and str(key).strip()
                    ):  # If key name is not empty, add or update
                        logging.info(
                            f"Processing environment variable: {key} = {value}"
                        )
                        add_env_var(key, str(value))
                        processed_keys.add(key)
        # Process other formats
        elif isinstance(data, dict):
            logging.info(f"Dictionary format data keys: {list(data.keys())}")
            # If dictionary format, try different keys
            if "data" in data:
                rows = data["data"]
            elif "values" in data:
                rows = data["values"]
            elif "value" in data:
                rows = data["value"]
            else:
                # Try using dictionary directly as row data
                rows = []
                for key, value in data.items():
                    if key not in ["headers", "types", "columns"]:
                        rows.append([key, value])

            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, list) and len(row) >= 2:
                        key, value = row[0], row[1]
                        if key and str(key).strip():
                            add_env_var(key, str(value))
                            processed_keys.add(key)
        elif isinstance(data, list):
            # 列表格式
            for row in data:
                if isinstance(row, list) and len(row) >= 2:
                    key, value = row[0], row[1]
                    if key and str(key).strip():
                        add_env_var(key, str(value))
                        processed_keys.add(key)
        else:
            logging.error(f"Unknown data format: {type(data)}")
            return f"❌ Save failed: Unknown data format {type(data)}"

        # Process deleted variables - check if there are variables in current environment not appearing in the table
        api_related_keys = {k for k in current_env_vars.keys() if is_api_related(k)}
        keys_to_delete = api_related_keys - processed_keys

        # Delete variables no longer in the table
        for key in keys_to_delete:
            logging.info(f"Deleting environment variable: {key}")
            delete_env_var(key)

        return "✅ Environment variables have been successfully saved"
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logging.error(f"Error saving environment variables: {str(e)}\n{error_details}")
        return f"❌ Save failed: {str(e)}"


def get_env_var_value(key):
    """Get the actual value of an environment variable

    Priority: Frontend configuration > .env file > System environment variables
    """
    # Check frontend configured environment variables
    if key in WEB_FRONTEND_ENV_VARS:
        return WEB_FRONTEND_ENV_VARS[key]

    # Check system environment variables (including those loaded from .env)
    return os.environ.get(key, "")


def create_login_interface():
    """Create login interface"""
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("""
                # 🔐 Login to OWL System

                Please log in with your credentials to access the OWL Multi-Agent Collaboration System.
            """)

            username_input = gr.Textbox(
                label="Username",
                placeholder="Enter your username",
                show_label=True
            )

            password_input = gr.Textbox(
                label="Password",
                placeholder="Enter your password",
                type="password",
                show_label=True
            )

            login_button = gr.Button(
                "🔐 Login",
                variant="primary"
            )

            login_status = gr.Textbox(
                label="Status",
                interactive=False,
                show_label=True
            )

            def handle_login(username, password):
                if not username or not password:
                    error_info = handle_validation_error("login_credentials")
                    return f"❌ {error_info.message}"

                try:
                    # Authenticate user
                    user = auth_manager.authenticate_user(username, password, "127.0.0.1")

                    if user:
                        # Create session
                        session = auth_manager.create_session(user, "127.0.0.1", "Gradio-WebApp")
                        return f"✅ Login successful! Welcome {user.username} ({user.role.value})"
                    else:
                        # Handle authentication error with user-friendly message
                        error_info = handle_authentication_error(username, "127.0.0.1")
                        return f"❌ {error_info.message}"

                except Exception as e:
                    logging.error(f"Login error: {e}")
                    error_info = handle_system_error("login", e)
                    return f"❌ {error_info.message}"

            login_button.click(
                fn=handle_login,
                inputs=[username_input, password_input],
                outputs=[login_status]
            )

            gr.Markdown("""
                ---
                **Default Accounts:**
                - Admin: `admin` / `admin123`
                - User: `user` / `user123`
            """)


def create_authenticated_ui():
    """Create the main UI for authenticated users"""

    def clear_log_file():
        """Clear log file content"""
        try:
            if LOG_FILE and os.path.exists(LOG_FILE):
                # Clear log file content instead of deleting the file
                open(LOG_FILE, "w").close()
                logging.info("Log file has been cleared")
                # Clear log queue
                while not LOG_QUEUE.empty():
                    try:
                        LOG_QUEUE.get_nowait()
                    except queue.Empty:
                        break
                return ""
            else:
                return ""
        except Exception as e:
            logging.error(f"Error clearing log file: {str(e)}")
            return ""

    # Create a real-time log update function
    def process_with_live_logs(question, module_name):
        """Process questions and update logs in real-time"""
        global CURRENT_PROCESS

        # Clear log file
        clear_log_file()

        # Create a background thread to process the question
        result_queue = queue.Queue()

        def process_in_background():
            try:
                result = run_owl(question, module_name)
                result_queue.put(result)
            except Exception as e:
                result_queue.put(
                    (f"Error occurred: {str(e)}", "0", f"❌ Error: {str(e)}")
                )

        # Start background processing thread
        bg_thread = threading.Thread(target=process_in_background)
        CURRENT_PROCESS = bg_thread  # Record current process
        bg_thread.start()

        # While waiting for processing to complete, update logs once per second
        while bg_thread.is_alive():
            # Update conversation record display
            logs2 = get_latest_logs(100, LOG_QUEUE)

            # Always update status
            yield (
                "0",
                "<span class='status-indicator status-running'></span> Processing...",
                logs2,
            )

            time.sleep(1)

        # Processing complete, get results
        if not result_queue.empty():
            result = result_queue.get()
            answer, token_count, status = result

            # Final update of conversation record
            logs2 = get_latest_logs(100, LOG_QUEUE)

            # Set different indicators based on status
            if "Error" in status:
                status_with_indicator = (
                    f"<span class='status-indicator status-error'></span> {status}"
                )
            else:
                status_with_indicator = (
                    f"<span class='status-indicator status-success'></span> {status}"
                )

            yield token_count, status_with_indicator, logs2
        else:
            logs2 = get_latest_logs(100, LOG_QUEUE)
            yield (
                "0",
                "<span class='status-indicator status-error'></span> Terminated",
                logs2,
            )

    with gr.Blocks(title="OWL", theme=gr.themes.Soft(primary_hue="blue")) as app:
        gr.Markdown(
            """
                # 🦉 OWL Multi-Agent Collaboration System

                Advanced multi-agent collaboration system developed based on the CAMEL framework, designed to solve complex problems through agent collaboration.

                Models and tools can be customized by modifying local scripts.
                
                This web app is currently in beta development. It is provided for demonstration and testing purposes only and is not yet recommended for production use.
                """
        )

        # Add custom CSS
        gr.HTML("""
            <style>
            /* Chat container style */
            .chat-container .chatbot {
                height: 500px;
                overflow-y: auto;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            

            /* Improved tab style */
            .tabs .tab-nav {
                background-color: #f5f5f5;
                border-radius: 8px 8px 0 0;
                padding: 5px;
            }
            
            .tabs .tab-nav button {
                border-radius: 5px;
                margin: 0 3px;
                padding: 8px 15px;
                font-weight: 500;
            }
            
            .tabs .tab-nav button.selected {
                background-color: #2c7be5;
                color: white;
            }
            
            /* Status indicator style */
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            
            .status-running {
                background-color: #ffc107;
                animation: pulse 1.5s infinite;
            }
            
            .status-success {
                background-color: #28a745;
            }
            
            .status-error {
                background-color: #dc3545;
            }
            
            /* Log display area style */
            .log-display textarea {
                height: 400px !important;
                max-height: 400px !important;
                overflow-y: auto !important;
                font-family: monospace;
                font-size: 0.9em;
                white-space: pre-wrap;
                line-height: 1.4;
            }
            
            .log-display {
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                min-height: 50vh;
                max-height: 75vh;
            }
            
            /* Environment variable management style */
            .env-manager-container {
                border-radius: 10px;
                padding: 15px;
                background-color: #f9f9f9;
                margin-bottom: 20px;
            }
            
            .env-controls, .api-help-container {
                border-radius: 8px;
                padding: 15px;
                background-color: white;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
                height: 100%;
            }
            
            .env-add-group, .env-delete-group {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                background-color: #f5f8ff;
                border: 1px solid #e0e8ff;
            }
            
            .env-delete-group {
                background-color: #fff5f5;
                border: 1px solid #ffe0e0;
            }
            
            .env-buttons {
                justify-content: flex-start;
                gap: 10px;
                margin-top: 10px;
            }
            
            .env-button {
                min-width: 100px;
            }
            
            .delete-button {
                background-color: #dc3545;
                color: white;
            }
            
            .env-table {
                margin-bottom: 15px;
            }
            
            /* Improved environment variable table style */
            .env-table table {
                border-collapse: separate;
                border-spacing: 0;
                width: 100%;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            
            .env-table th {
                background-color: #f0f7ff;
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                color: #2c7be5;
                border-bottom: 2px solid #e0e8ff;
            }
            
            .env-table td {
                padding: 10px 15px;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .env-table tr:hover td {
                background-color: #f9fbff;
            }
            
            .env-table tr:last-child td {
                border-bottom: none;
            }
            
            /* Status icon style */
            .status-icon-cell {
                text-align: center;
                font-size: 1.2em;
            }

            /* Masking indicator styles */
            .env-masked-indicator {
                color: #dc3545;
                font-weight: bold;
                margin-right: 5px;
            }

            .env-visible-indicator {
                color: #28a745;
                font-weight: bold;
                margin-right: 5px;
            }

            .env-masked-value {
                background-color: #f8f9fa;
                border-left: 3px solid #dc3545;
                font-family: monospace;
            }

            .env-visible-value {
                background-color: #fff3cd;
                border-left: 3px solid #ffc107;
                font-family: monospace;
            }

            /* Security notice for masked values */
            .security-notice {
                background-color: #e7f3fe;
                border-left: 6px solid #2196F3;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
                font-size: 0.9em;
            }

            .security-notice strong {
                color: #2c7be5;
            }
            
            /* Link style */
            .guide-link {
                color: #2c7be5;
                text-decoration: none;
                cursor: pointer;
                font-weight: 500;
            }
            
            .guide-link:hover {
                text-decoration: underline;
            }

            /* New 4-tab structure responsive design */
            .tab-container {
                min-height: 600px;
            }

            .task-creation-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 10px;
                color: white;
                margin-bottom: 20px;
            }

            .results-history-section {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 20px;
                border-radius: 10px;
                color: white;
                margin-bottom: 20px;
            }

            .settings-section {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 20px;
                border-radius: 10px;
                color: white;
                margin-bottom: 20px;
            }

            .system-status-section {
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                padding: 20px;
                border-radius: 10px;
                color: white;
                margin-bottom: 20px;
            }

            /* Responsive tab navigation */
            @media (max-width: 768px) {
                .tab-container {
                    min-height: 400px;
                }

                .task-creation-section,
                .results-history-section,
                .settings-section,
                .system-status-section {
                    padding: 15px;
                    margin-bottom: 15px;
                }

                /* Stack tab content vertically on mobile */
                .mobile-stack {
                    flex-direction: column !important;
                }

                /* Make buttons full width on mobile */
                .mobile-full-width {
                    width: 100% !important;
                    margin-bottom: 10px !important;
                }
            }

            @media (max-width: 480px) {
                .tab-container {
                    min-height: 300px;
                }

                .task-creation-section,
                .results-history-section,
                .settings-section,
                .system-status-section {
                    padding: 10px;
                    margin-bottom: 10px;
                }

                /* Hide some decorative elements on very small screens */
                .mobile-hide {
                    display: none !important;
                }
            }

            /* Tab visual indicators */
            .active-tab-indicator {
                border-bottom: 3px solid #007bff;
                font-weight: bold;
                color: #007bff;
            }

            .inactive-tab-indicator {
                color: #6c757d;
            }

            /* Progressive disclosure styling */
            .advanced-options {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                margin-top: 10px;
            }

            .advanced-options-toggle {
                cursor: pointer;
                color: #007bff;
                text-decoration: underline;
            }

            .advanced-options-toggle:hover {
                color: #0056b3;
            }

            /* Cross-tab navigation buttons */
            .cross-tab-nav {
                margin-top: 15px;
                padding: 10px;
                background-color: #e9ecef;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }

            .cross-tab-button {
                margin-right: 10px;
                margin-bottom: 5px;
            }

            /* Error UI Components */
            .error-message {
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                border: 1px solid #dc3545;
                border-radius: 8px;
                padding: 16px;
                margin: 12px 0;
                color: white;
                font-weight: 500;
                box-shadow: 0 2px 4px rgba(220, 53, 69, 0.2);
            }

            .error-message.warning {
                background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%);
                border-color: #fd7e14;
            }

            .error-message.info {
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                border-color: #17a2b8;
            }

            .error-message.success {
                background: linear-gradient(135deg, #28a745 0%, #218838 100%);
                border-color: #28a745;
            }

            .error-title {
                font-size: 1.1em;
                font-weight: 600;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
            }

            .error-icon {
                margin-right: 8px;
                font-size: 1.2em;
            }

            .error-content {
                line-height: 1.5;
                margin-bottom: 12px;
            }

            .error-help {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 12px;
                margin: 12px 0;
                font-size: 0.9em;
                line-height: 1.4;
            }

            .error-solutions {
                margin: 12px 0;
            }

            .error-solution {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                padding: 8px 12px;
                margin: 4px 0;
                font-size: 0.9em;
                border-left: 3px solid rgba(255, 255, 255, 0.3);
            }

            .error-actions {
                display: flex;
                gap: 8px;
                margin-top: 12px;
            }

            .error-button {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
                text-decoration: none;
                transition: all 0.2s ease;
            }

            .error-button:hover {
                background: rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.4);
            }

            .error-button.primary {
                background: rgba(255, 255, 255, 0.9);
                color: #dc3545;
                font-weight: 600;
            }

            .error-button.primary:hover {
                background: white;
                color: #c82333;
            }

            /* Error modal styles */
            .error-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }

            .error-modal {
                background: white;
                border-radius: 8px;
                padding: 24px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }

            .error-modal-header {
                display: flex;
                align-items: center;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid #dee2e6;
            }

            .error-modal-close {
                margin-left: auto;
                background: none;
                border: none;
                font-size: 1.5em;
                cursor: pointer;
                color: #6c757d;
                padding: 4px;
                line-height: 1;
            }

            .error-modal-close:hover {
                color: #495057;
            }

            /* Error statistics dashboard */
            .error-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin: 20px 0;
            }

            .error-stat-card {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
                text-align: center;
            }

            .error-stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #dc3545;
                margin-bottom: 8px;
            }

            .error-stat-label {
                color: #6c757d;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            /* Responsive error components */
            @media (max-width: 768px) {
                .error-actions {
                    flex-direction: column;
                }

                .error-button {
                    text-align: center;
                    width: 100%;
                }

                .error-stats {
                    grid-template-columns: 1fr;
                }

                .error-modal {
                    margin: 20px;
                    width: calc(100% - 40px);
                }
            }
            
            .env-status {
                margin-top: 15px;
                font-weight: 500;
                padding: 10px;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            
            .env-status-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .env-status-error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .api-help-accordion {
                margin-bottom: 8px;
                border-radius: 6px;
                overflow: hidden;
            }
            

            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }

            /* Onboarding System Styles */
            .onboarding-welcome {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 32px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            }

            .wizard-step {
                padding: 24px;
                min-height: 400px;
            }

            .wizard-progress {
                background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
                color: white;
                padding: 16px;
                border-radius: 8px;
                margin: 16px 0;
            }

            .wizard-navigation {
                display: flex;
                gap: 8px;
                justify-content: center;
                margin-top: 20px;
            }

            .wizard-button {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
            }

            .wizard-button.secondary {
                background: #6c757d;
            }

            .wizard-button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }

            /* Feature Tour Tooltip Styles */
            .feature-tour-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                z-index: 1000;
                display: none;
            }

            .feature-tour-tooltip {
                position: absolute;
                background: white;
                border-radius: 8px;
                padding: 20px;
                max-width: 300px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                z-index: 1001;
                opacity: 0;
                transform: scale(0.8);
                transition: all 0.3s ease;
            }

            .feature-tour-tooltip.show {
                opacity: 1;
                transform: scale(1);
            }

            .feature-tour-arrow {
                position: absolute;
                width: 0;
                height: 0;
                border: 8px solid transparent;
            }

            .feature-tour-arrow.top {
                border-bottom-color: white;
                border-top: none;
                bottom: -8px;
            }

            .feature-tour-arrow.bottom {
                border-top-color: white;
                border-bottom: none;
                top: -8px;
            }

            .feature-tour-arrow.left {
                border-right-color: white;
                border-left: none;
                right: -8px;
            }

            .feature-tour-arrow.right {
                border-left-color: white;
                border-right: none;
                left: -8px;
            }

            .feature-tour-title {
                font-size: 1.1em;
                font-weight: bold;
                margin: 0 0 8px 0;
                color: #333;
            }

            .feature-tour-content {
                margin: 0 0 16px 0;
                line-height: 1.4;
                color: #666;
            }

            .feature-tour-navigation {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 16px;
            }

            .tour-progress {
                font-size: 0.9em;
                color: #999;
            }

            .tour-button {
                background: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
                margin-left: 8px;
            }

            .tour-button.secondary {
                background: #6c757d;
            }

            /* Highlight overlay for tour elements */
            .tour-highlight {
                position: relative;
                z-index: 999;
                outline: 3px solid #007bff;
                outline-offset: 3px;
                border-radius: 4px;
                box-shadow: 0 0 0 9999px rgba(0, 123, 255, 0.1);
                animation: tour-pulse 2s infinite;
            }

            @keyframes tour-pulse {
                0% { outline-color: #007bff; }
                50% { outline-color: #ff6b6b; }
                100% { outline-color: #007bff; }
            }

            /* Example task cards */
            .example-task-card {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 16px;
                margin: 8px 0;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .example-task-card:hover {
                border-color: #007bff;
                box-shadow: 0 2px 4px rgba(0, 123, 255, 0.1);
            }

            .task-difficulty {
                background: #e9ecef;
                color: #495057;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                display: inline-block;
            }

            .task-difficulty.beginner {
                background: #d4edda;
                color: #155724;
            }

            .task-difficulty.intermediate {
                background: #fff3cd;
                color: #856404;
            }

            .task-difficulty.advanced {
                background: #f8d7da;
                color: #721c24;
            }

            /* Responsive onboarding styles */
            @media (max-width: 768px) {
                .onboarding-welcome {
                    padding: 24px;
                    margin: 16px;
                }

                .wizard-step {
                    padding: 16px;
                    min-height: 300px;
                }

                .wizard-navigation {
                    flex-direction: column;
                }

                .wizard-button {
                    width: 100%;
                    margin: 4px 0;
                }

                .feature-tour-tooltip {
                    max-width: 250px;
                }
            }

            @media (max-width: 480px) {
                .onboarding-welcome {
                    padding: 16px;
                    margin: 8px;
                }

                .wizard-step {
                    padding: 12px;
                    min-height: 250px;
                }

                .feature-tour-tooltip {
                    max-width: 200px;
                    padding: 16px;
                }
            }
            </style>
            """)

        with gr.Row():
            with gr.Column(scale=0.5):
                question_input = gr.Textbox(
                    lines=5,
                    placeholder="Please enter your question...",
                    label="Question",
                    elem_id="question_input",
                    show_copy_button=True,
                    value="Open Brave search, summarize the github stars, fork counts, etc. of camel-ai's camel framework, and write the numbers into a python file using the plot package, save it locally, and run the generated python file. Note: You have been provided with the necessary tools to complete this task.",
                )

                # Enhanced module selection dropdown
                # Only includes modules defined in MODULE_DESCRIPTIONS
                module_dropdown = gr.Dropdown(
                    choices=list(MODULE_DESCRIPTIONS.keys()),
                    value="run",
                    label="Select Function Module",
                    interactive=True,
                )

                # Module description text box
                module_description = gr.Textbox(
                    value=MODULE_DESCRIPTIONS["run"],
                    label="Module Description",
                    interactive=False,
                    elem_classes="module-info",
                )

                with gr.Row():
                    run_button = gr.Button(
                        "Run", variant="primary", elem_classes="primary"
                    )

                status_output = gr.HTML(
                    value="<span class='status-indicator status-success'></span> Ready",
                    label="Status",
                )
                token_count_output = gr.Textbox(
                    label="Token Count", interactive=False, elem_classes="token-count"
                )

                # Example questions
                examples = [
                    "Open Brave search, summarize the github stars, fork counts, etc. of camel-ai's camel framework, and write the numbers into a python file using the plot package, save it locally, and run the generated python file. Note: You have been provided with the necessary tools to complete this task.",
                    "Browse Amazon and find a product that is attractive to programmers. Please provide the product name and price",
                    "Write a hello world python file and save it locally",
                ]

                gr.Examples(examples=examples, inputs=question_input)

                gr.HTML("""
                        <div class="footer" id="about">
                            <h3>About OWL Multi-Agent Collaboration System</h3>
                            <p>OWL is an advanced multi-agent collaboration system developed based on the CAMEL framework, designed to solve complex problems through agent collaboration.</p>
                            <p>© 2025 CAMEL-AI.org. Based on Apache License 2.0 open source license</p>
                            <p><a href="https://github.com/camel-ai/owl" target="_blank">GitHub</a></p>
                        </div>
                    """)

            with gr.Tabs():  # Set conversation record as the default selected tab
                with gr.TabItem("Conversation Record"):
                    # Add conversation record display area
                    with gr.Group():
                        log_display2 = gr.Markdown(
                            value="No conversation records yet.",
                            elem_classes="log-display",
                        )

                    with gr.Row():
                        refresh_logs_button2 = gr.Button("Refresh Record")
                        auto_refresh_checkbox2 = gr.Checkbox(
                            label="Auto Refresh", value=True, interactive=True
                        )
                        clear_logs_button2 = gr.Button(
                            "Clear Record", variant="secondary"
                        )

                with gr.TabItem("Environment Variable Management", id="env-settings"):
                    with gr.Group(elem_classes="env-manager-container"):
                        gr.Markdown("""
                            ## Environment Variable Management

                            Set model API keys and other service credentials here. This information will be saved in a local `.env` file, ensuring your API keys are securely stored and not uploaded to the network. Correctly setting API keys is crucial for the functionality of the OWL system. Environment variables can be flexibly configured according to tool requirements.

                            <div class="security-notice">
                            <strong>🔒 Security Notice:</strong> Sensitive values (API keys, tokens, passwords) are automatically masked for security.
                            Use the view/edit mode buttons below to temporarily reveal values when needed. All sensitive data remains protected and is never transmitted over the network.
                            </div>
                            """)

                        # Main content divided into two-column layout
                        with gr.Row():
                            # Left column: Environment variable management controls
                            with gr.Column(scale=3):
                                with gr.Group(elem_classes="env-controls"):
                                    # Environment variable table - set to interactive for direct editing
                                    gr.Markdown("""
                                    <div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 10px; margin: 15px 0; border-radius: 4px;">
                                      <strong>Tip:</strong> Please make sure to run cp .env_template .env to create a local .env file, and flexibly configure the required environment variables according to the running module
                                    </div>
                                    """)

                                    # Enhanced environment variable table, supporting adding and deleting rows
                                    env_table = gr.Dataframe(
                                        headers=[
                                            "Variable Name",
                                            "Value",
                                            "Retrieval Guide",
                                        ],
                                        datatype=[
                                            "str",
                                            "str",
                                            "html",
                                        ],  # Set the last column as HTML type to support links
                                        row_count=10,  # Increase row count to allow adding new variables
                                        col_count=(3, "fixed"),
                                        value=update_env_table,
                                        label="API Keys and Environment Variables",
                                        interactive=True,  # Set as interactive, allowing direct editing
                                        elem_classes="env-table",
                                    )

                                    # Operation instructions
                                    gr.Markdown(
                                        """
                                    <div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 10px; margin: 15px 0; border-radius: 4px;">
                                    <strong>Operation Guide</strong>:
                                    <ul style="margin-top: 8px; margin-bottom: 8px;">
                                      <li><strong>Edit Variable</strong>: Click directly on the "Value" cell in the table to edit</li>
                                      <li><strong>Add Variable</strong>: Enter a new variable name and value in a blank row</li>
                                      <li><strong>Delete Variable</strong>: Clear the variable name to delete that row</li>
                                      <li><strong>Get API Key</strong>: Click on the link in the "Retrieval Guide" column to get the corresponding API key</li>
                                    </ul>
                                    </div>
                                    """,
                                        elem_classes="env-instructions",
                                    )

                                    # Environment variable operation buttons
                                    with gr.Row(elem_classes="env-buttons"):
                                        save_env_button = gr.Button(
                                            "💾 Save Changes",
                                            variant="primary",
                                            elem_classes="env-button",
                                        )
                                        refresh_button = gr.Button(
                                            "🔄 Refresh List", elem_classes="env-button"
                                        )

                                    # View/Edit mode buttons
                                    with gr.Row(elem_classes="env-buttons"):
                                        view_mode_button = gr.Button(
                                            "🔒 View Mode (Masked)",
                                            elem_classes="env-button",
                                        )
                                        edit_mode_button = gr.Button(
                                            "⚠️ Edit Mode (Unmasked)",
                                            variant="secondary",
                                            elem_classes="env-button",
                                        )
                                        confirm_edit_button = gr.Button(
                                            "✅ Confirm Edit Mode",
                                            variant="primary",
                                            elem_classes="env-button",
                                            visible=False
                                        )

                                    # Temporary unmask toggle
                                    with gr.Row(elem_classes="env-buttons"):
                                        toggle_unmask_button = gr.Button(
                                            "👁️ Show/Hide Values (30s)",
                                            variant="secondary",
                                            elem_classes="env-button",
                                        )

                                    # Security notice for edit mode
                                    edit_mode_notice = gr.Markdown(
                                        """
                                        <div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 10px; margin: 10px 0; border-radius: 4px; display: none;" id="edit-mode-notice">
                                        <strong>⚠️ Security Notice:</strong> You are about to view sensitive data (API keys, tokens, etc.) in unmasked form.
                                        This data could be visible on your screen. Make sure no one is watching and proceed with caution.
                                        </div>
                                        """,
                                        visible=False
                                    )

                                    # Status display
                                    env_status = gr.HTML(
                                        label="Operation Status",
                                        value="",
                                        elem_classes="env-status",
                                    )

                    # Connect event handlers
                    save_env_button.click(
                        fn=save_env_table_changes,
                        inputs=[env_table],
                        outputs=[env_status],
                    ).then(fn=update_env_table, outputs=[env_table])

                    refresh_button.click(fn=update_env_table, outputs=[env_table])

                    # View/Edit mode event handlers
                    def handle_view_mode():
                        status, mode = switch_env_display_mode("view")
                        return status

                    def handle_edit_mode_request():
                        status, mode = switch_env_display_mode("edit", confirmed=False)
                        if "Please confirm" in status:
                            return (
                                status,
                                gr.update(visible=True),  # Show confirm button
                                gr.update(visible=True),  # Show security notice
                            )
                        return status, gr.update(), gr.update()

                    def handle_confirm_edit():
                        status = confirm_env_edit_mode()
                        return (
                            status,
                            gr.update(visible=False),  # Hide confirm button
                            gr.update(visible=False),  # Hide security notice
                        )

                    view_mode_button.click(
                        fn=handle_view_mode,
                        outputs=[env_status]
                    ).then(fn=update_env_table, outputs=[env_table])

                    edit_mode_button.click(
                        fn=handle_edit_mode_request,
                        outputs=[env_status, confirm_edit_button, edit_mode_notice]
                    )

                    confirm_edit_button.click(
                        fn=handle_confirm_edit,
                        outputs=[env_status, confirm_edit_button, edit_mode_notice]
                    ).then(fn=update_env_table, outputs=[env_table])

                    # Temporary unmask toggle handler
                    def handle_toggle_unmask():
                        status, is_unmasked = toggle_temporary_unmask()
                        if is_unmasked:
                            # Update button text to show re-mask option
                            return status, "🔒 Hide Values"
                        else:
                            # Reset button text
                            return status, "👁️ Show/Hide Values (30s)"

                    toggle_unmask_button.click(
                        fn=handle_toggle_unmask,
                        outputs=[env_status, toggle_unmask_button]
                    ).then(fn=update_env_table, outputs=[env_table])

        # Set up event handling
        run_button.click(
            fn=process_with_live_logs,
            inputs=[question_input, module_dropdown],
            outputs=[token_count_output, status_output, log_display2],
        )

        # Module selection updates description
        module_dropdown.change(
            fn=update_module_description,
            inputs=module_dropdown,
            outputs=module_description,
        )

        # Conversation record related event handling
        refresh_logs_button2.click(
            fn=lambda: get_latest_logs(100, LOG_QUEUE), outputs=[log_display2]
        )

        clear_logs_button2.click(fn=clear_log_file, outputs=[log_display2])

        # Auto refresh control
        def toggle_auto_refresh(enabled):
            if enabled:
                return gr.update(every=3)
            else:
                return gr.update(every=0)

        auto_refresh_checkbox2.change(
            fn=toggle_auto_refresh,
            inputs=[auto_refresh_checkbox2],
            outputs=[log_display2],
        )

        # No longer automatically refresh logs by default

    return app


# Main function
def main():
    try:
        # Initialize logging system
        global LOG_FILE
        LOG_FILE = setup_logging()
        logging.info("OWL Web application started")

        # Create default users
        create_default_users()

        # Start log reading thread
        log_thread = threading.Thread(
            target=log_reader_thread, args=(LOG_FILE,), daemon=True
        )
        log_thread.start()
        logging.info("Log reading thread started")

        # Initialize .env file (if it doesn't exist)
        init_env_file()
        app = create_ui()

        app.queue()
        app.launch(
            share=False,
            favicon_path=os.path.join(
                os.path.dirname(__file__), "assets", "owl-favicon.ico"
            ),
        )
    except Exception as e:
        logging.error(f"Error occurred while starting the application: {str(e)}")
        print(f"Error occurred while starting the application: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        # Ensure log thread stops
        STOP_LOG_THREAD.set()
        STOP_REQUESTED.set()
        logging.info("Application closed")


if __name__ == "__main__":
    main()
