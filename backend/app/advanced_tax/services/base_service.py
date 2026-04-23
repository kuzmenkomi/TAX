"""
Base Service Class for Advanced Tax Engine
All services inherit from this for consistency and common operations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Abstract base service for all Advanced Tax Engine services.
    
    Provides:
    - Database session management
    - Error handling
    - Logging
    - Input validation
    """
    
    def __init__(self, db: Session, user_id: int, country: str = "MX"):
        """
        Initialize service
        
        Args:
            db: Database session
            user_id: Current user ID
            country: Country code (MX, BR, AR, etc.)
        """
        self.db = db
        self.user_id = user_id
        self.country = country
        self.service_name = self.__class__.__name__
        
        logger.debug(f"[{self.service_name}] Initialized for user={user_id}, country={country}")
    
    @abstractmethod
    def validate_inputs(self, **kwargs) -> bool:
        """Validate input parameters. Must be implemented by subclass."""
        pass
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log structured event for monitoring and debugging
        
        Args:
            event_type: Type of event (e.g., "HARVEST_IDENTIFIED", "MATCH_FOUND")
            data: Event metadata
        """
        event = {
            'service': self.service_name,
            'user_id': self.user_id,
            'country': self.country,
            'event_type': event_type,
            'data': data,
        }
        logger.info(f"[{self.service_name}] {event_type}: {data}")
    
    def log_error(self, error_type: str, error_msg: str, traceback: str = None) -> None:
        """Log errors"""
        logger.error(
            f"[{self.service_name}] {error_type}: {error_msg}",
            extra={'traceback': traceback}
        )
    
    def get_user_data(self) -> Optional[Dict]:
        """
        Get user from database - can be overridden to fetch from backend
        """
        # This would query the user table
        # For now, return stub
        return {
            'id': self.user_id,
            'country': self.country,
        }
    
    def validate_user_exists(self) -> bool:
        """Check if user exists in database"""
        user = self.get_user_data()
        return user is not None
    
    def format_decimal_value(self, value: float, decimals: int = 2) -> str:
        """Format decimal value to string"""
        return f"{value:.{decimals}f}"
    
    def format_percentage(self, value: float) -> str:
        """Format percentage"""
        return f"{value:.2f}%"
    
    def __repr__(self):
        return f"<{self.service_name} user={self.user_id}>"
