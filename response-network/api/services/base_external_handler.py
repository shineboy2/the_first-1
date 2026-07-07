"""
Base External Handler Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseExternalHandler(ABC):
    """
    Base interface for all External API Handlers.
    This allows for both generic configurations and custom multi-step integrations.
    """
    
    def __init__(self, db_session):
        """Initialize with database session."""
        self.db = db_session
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return the identifier name of this handler.
        Should match the handler_class in external_apis table.
        """
        pass
    
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate input parameters before execution.
        Raises ValueError if invalid, or returns bool.
        """
        pass
    
    @abstractmethod
    def execute(self, request_data: Dict[str, Any], api_name: str = None, api_config: Any = None) -> Dict[str, Any]:
        """
        Executes the API request and returns the parsed result.
        
        Args:
            request_data: The incoming query_params from the request
            api_name: The name of the API configuration to use (mostly useful for generic handler)
            api_config: The external API configuration object
            
        Returns:
            Dictionary containing the response to be stored in query_results
        """
        pass
