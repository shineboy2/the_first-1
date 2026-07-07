from typing import Dict, Type
from sqlalchemy.orm import Session

from models.external_api import ExternalAPI
from services.base_external_handler import BaseExternalHandler
from services.external_api_handler import ExternalAPIHandler

class HandlerRegistry:
    """
    Registry for all external API handlers.
    Maps handler_class names from the database to Python handler classes.
    """
    _handlers: Dict[str, Type[BaseExternalHandler]] = {}
    
    @classmethod
    def register(cls, name: str, handler_class: Type[BaseExternalHandler]):
        """Register a new handler class."""
        cls._handlers[name] = handler_class
        
    @classmethod
    def get_handler(cls, api_name: str, db: Session) -> BaseExternalHandler:
        """
        Get the appropriate handler instance for a given API name.
        Defaults to ExternalAPIHandler (generic) if none found or handler_class is generic.
        """
        api_config = db.query(ExternalAPI).filter(ExternalAPI.name == api_name).first()
        
        if not api_config:
            raise ValueError(f"External API '{api_name}' not found")
            
        handler_name = api_config.handler_class
        
        if handler_name in cls._handlers:
            return cls._handlers[handler_name](db)
            
        # Fallback to generic handler
        return ExternalAPIHandler(db)
        
    @classmethod
    def list_handlers(cls) -> list:
        """List all available registered handlers."""
        # Add generic handler manually as it's the fallback default
        handlers = [{"name": "generic", "description": "Generic HTTP Request Handler (Default)"}]
        
        for k, v in cls._handlers.items():
            if k != "generic":
                handlers.append({
                    "name": k,
                    "description": getattr(v, "__doc__", "").strip().split('\n')[0] or f"Handler for {k}"
                })
                
        return handlers

# Auto-register handlers here
from services.face_recognition_handler import FaceRecognitionHandler
HandlerRegistry.register("face_recognition", FaceRecognitionHandler)
