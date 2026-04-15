"""
Parameter Validator Service for Request Network

Since RequestType metadata lives in Response Network, we perform basic validation:
1. Detect if query contains placeholders like {{param}}
2. Warn if placeholders exist but params are empty
3. Log missing parameters for debugging

Full validation happens in Response Network during execution.
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class ParameterValidator:
    """
    Lightweight parameter validator for Request Network.
    Performs basic checks without needing Request Type metadata.
    """
    
    @staticmethod
    def extract_placeholders_from_template(template: dict) -> List[str]:
        """
        Extract all {{placeholder}} keys from a query template.
        Returns list of placeholder names (without {{  }}).
        """
        import json
        template_str = json.dumps(template)
        # Find all {{  }} patterns
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, template_str)
        return list(set(matches))  # Unique list
    
    @staticmethod
    def validate_params(
        query_params: dict | None,
        query_type: str = None
    ) -> Tuple[bool, List[str]]:
        """
        Basic validation for query parameters.
        
        Args:
            query_params: Dictionary of user-provided parameters
            query_type: Type of request (for logging)
        
        Returns:
            (is_valid, warnings) - Always returns True to not block requests
            Warnings are logged but don't prevent request creation
        """
        warnings = []
        
        if query_params is None:
            query_params = {}
        
        # Basic type check
        if not isinstance(query_params, dict):
            warnings.append(
                f"query_params should be a dictionary, got {type(query_params).__name__}"
            )
            return (True, warnings)  # Don't block, just warn
        
        # Check for empty params (informational only)
        if len(query_params) == 0:
            logger.info(
                f"Request type '{query_type}' submitted with no parameters. "
                "If template requires parameters, query may fail in Response Network."
            )
            warnings.append(
                "No parameters provided. If query template requires parameters, "
                "execution may fail."
            )
        
        # Validate param values are not None
        for key, value in query_params.items():
            if value is None:
                warnings.append(
                    f"Parameter '{key}' is None. Consider removing or providing a value."
                )
        
        # Always return True - we don't block requests
        # Full validation happens in Response Network
        return (True, warnings)
    
    @staticmethod
    def validate_and_log(
        query_params: dict | None,
        query_type: str
    ) -> None:
        """
        Convenience method that validates and logs warnings.
        Doesn't raise exceptions.
        """
        is_valid, warnings = ParameterValidator.validate_params(
            query_params, query_type
        )
        
        if warnings:
            logger.warning(
                f"Parameter validation warnings for '{query_type}': "
                + "; ".join(warnings)
            )
