import base64
import json
import httpx
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models.external_api import ExternalAPI

logger = logging.getLogger(__name__)

class ExternalAPIHandler:
    def __init__(self, db: Session):
        self.db = db

    def execute_api_call(self, api_name: str, payload_vars: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point to call an external API dynamically based on its configuration.
        """
        api_config = self.db.query(ExternalAPI).filter(ExternalAPI.name == api_name).first()
        if not api_config:
            raise ValueError(f"External API '{api_name}' not found")
        
        if not api_config.is_active:
            raise ValueError(f"External API '{api_name}' is inactive")

        # 1. Resolve Auth (Token or Static Header)
        auth_headers = self._resolve_auth(api_config)
        
        # 2. Render Payload
        rendered_payload = self._render_payload(api_config.payload_template, payload_vars)
        
        # Combine static headers and auth headers
        final_headers = api_config.static_headers or {}
        final_headers.update(auth_headers)

        # 3. Make the Request
        return self._make_request(
            method=api_config.http_method,
            url=api_config.endpoint_url,
            headers=final_headers,
            json_payload=rendered_payload
        )

    def _resolve_auth(self, api_config: ExternalAPI) -> Dict[str, str]:
        """Resolves authentication based on auth_type"""
        auth_type = api_config.auth_type
        
        if auth_type == "none":
            return {}
        elif auth_type == "static_key":
            # Assume auth_config looks like {"headers": {"Authorization": "Bearer XYZ"}}
            if api_config.auth_config and "headers" in api_config.auth_config:
                return api_config.auth_config["headers"]
            return {}
        elif auth_type == "dynamic_token":
            return self._fetch_dynamic_token(api_config)
        else:
            raise ValueError(f"Unsupported auth_type '{auth_type}'")

    def _fetch_dynamic_token(self, api_config: ExternalAPI) -> Dict[str, str]:
        """
        Fetches dynamic token, optionally using Redis for caching (mocked for simplicity here).
        Requires auth_config to have: auth_url, auth_payload, token_path, header_template
        """
        config = api_config.auth_config or {}
        auth_url = config.get("auth_url")
        auth_payload = config.get("auth_payload")
        token_path = config.get("token_path")
        header_template = config.get("header_template", {"Authorization": "Bearer {token}"})
        
        if not all([auth_url, auth_payload, token_path]):
               raise ValueError("Incomplete dynamic auth config")
               
        # Make request to get token
        try:
             # Basic implementation without caching. For production, Redis check would go here.
             response = httpx.post(auth_url, json=auth_payload, timeout=10.0)
             response.raise_for_status()
             data = response.json()
             
             # Extract token from dotted path (e.g. data.access_token)
             token = data
             for key in token_path.split("."):
                 token = token.get(key, {})
             
             if not isinstance(token, str):
                 raise ValueError("Token not found or not a string")
                 
             # Render Header
             resolved_headers = {}
             for k, v in header_template.items():
                   resolved_headers[k] = v.replace("{token}", token)
                   
             return resolved_headers
             
        except Exception as e:
             logger.error(f"Failed to fetch dynamic token: {str(e)}")
             raise Exception("Failed to authenticate with external API provider")

    def _render_payload(self, template: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Any:
        """
        Recursively traverse the template and replace placeholders with values from context.
        Handles base64 representation if required.
        """
        if not template:
            return context # Fallback to raw context if no template

        return self._render_node(template, context)

    def _render_node(self, node: Any, context: Dict[str, Any]) -> Any:
        if isinstance(node, dict):
            return {k: self._render_node(v, context) for k, v in node.items()}
        elif isinstance(node, list):
            return [self._render_node(v, context) for v in node]
        elif isinstance(node, str):
            # Check for {{key}} simple replacement
            rendered = node
            for k, v in context.items():
                if f"{{{{{k}}}}}" in rendered:
                    # If the value is a string, simple replace
                    if isinstance(v, str):
                         rendered = rendered.replace(f"{{{{{k}}}}}", v)
                    else:
                         # For complex types, if it's an exact match replace the node entirely
                         if rendered == f"{{{{{k}}}}}":
                             return v
            return rendered
        else:
            return node

    def _make_request(self, method: str, url: str, headers: Dict[str, str], json_payload: Any) -> Dict[str, Any]:
        """
        Executes the HTTP call
        """
        try:
            # We use httpx.Client to manage connections properly or httpx.request
            # Setting a reasonable timeout for external API calls
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json_payload
                )
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Try parsing JSON response
                try:
                    return response.json()
                except ValueError:
                    return {"text_response": response.text}
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise Exception(f"External API Error ({e.response.status_code}): {e.response.text[:200]}")
        except httpx.RequestError as e:
             logger.error(f"Request error occurred: {str(e)}")
             raise Exception(f"External API Connection Error: {str(e)}")
        except Exception as e:
             logger.error(f"Unexpected error calling API: {str(e)}")
             raise Exception(f"Unexpected error: {str(e)}")
