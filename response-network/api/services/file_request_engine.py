"""
File Request Engine — Core engine for generating request files
and parsing JSON response files.

This is the heart of the file-based request system.
It handles:
1. Filename generation from templates
2. Request file content generation (JSON, CSV, text)
3. JSON response parsing with configurable key extraction
"""
import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class FileRequestEngine:
    """
    Central engine for file-based request processing.
    All methods are static — no state needed.
    """

    # ═══════════════════════════════════════════════════════
    # File Name Generation
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def generate_filename(config, request_data: dict) -> str:
        """
        Generate a filename from the config's filename_template.

        System placeholders:
            {request_id}   — UUID of the incoming request
            {request_type} — query_type name
            {timestamp}    — current timestamp (YYYYMMDDHHmmss)
            {date}         — current date (YYYYMMDD)
            {uuid}         — random UUID4

        Data placeholders:
            Any key from request_data (query_params)

        Example template: "INQ_{national_code}_{date}.json"
        """
        template = config.filename_template
        now = datetime.utcnow()

        # Build context with system variables
        context = {
            "request_id": str(request_data.get("request_id", uuid.uuid4())),
            "request_type": str(request_data.get("request_type", "unknown")),
            "timestamp": now.strftime("%Y%m%d%H%M%S"),
            "date": now.strftime("%Y%m%d"),
            "uuid": str(uuid.uuid4()),
        }

        # Add all request_data keys (query_params)
        for key, value in request_data.items():
            if key not in context:
                context[key] = str(value) if value is not None else ""

        # Render template — use safe substitution to avoid KeyError
        try:
            result = template
            for key, value in context.items():
                result = result.replace("{" + key + "}", value)
            # Sanitize filename: remove path traversal characters
            result = result.replace("..", "").replace("/", "_").replace("\\", "_")
            return result
        except Exception as e:
            logger.error(f"Filename generation error: {e}")
            # Fallback to safe default
            return f"request_{context['timestamp']}_{context['uuid'][:8]}.json"

    # ═══════════════════════════════════════════════════════
    # File Content Generation
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def generate_file_content(config, request_data: dict) -> bytes:
        """
        Generate file content based on content_format and content_template.

        Supported formats:
        - "json": Render JSON template with {{placeholder}} substitution
        - "csv": Generate CSV from headers + row_template
        - "text": Custom text template rendering
        - "custom_template": Raw template with {{placeholder}}
        """
        content_format = config.content_format or "json"
        template = config.content_template or {}
        encoding = config.content_encoding or "utf-8"

        if content_format == "json":
            content = FileRequestEngine._generate_json(template, request_data)
        elif content_format == "csv":
            content = FileRequestEngine._generate_csv(template, request_data)
        elif content_format in ("text", "custom_template"):
            content = FileRequestEngine._generate_text(template, request_data)
        else:
            # Default: dump request_data as JSON
            content = json.dumps(request_data, ensure_ascii=False, indent=2)

        return content.encode(encoding)

    @staticmethod
    def _generate_json(template: dict, data: dict) -> str:
        """
        Generate JSON content by rendering a template with {{placeholder}} values.

        If template is empty/None, just dump the data as JSON.
        Otherwise, walk through the template and replace {{key}} with values from data.
        """
        if not template:
            return json.dumps(data, ensure_ascii=False, indent=2)

        rendered = FileRequestEngine._render_template_value(template, data)
        return json.dumps(rendered, ensure_ascii=False, indent=2)

    @staticmethod
    def _generate_csv(template: dict, data: dict) -> str:
        """
        Generate CSV content.

        Template format:
        {
            "headers": ["col1", "col2"],
            "row_template": "{{field1}},{{field2}}"
        }
        """
        headers = template.get("headers", [])
        row_template = template.get("row_template", "")

        lines = []
        if headers:
            lines.append(",".join(headers))

        if row_template:
            rendered_row = FileRequestEngine._render_string(row_template, data)
            lines.append(rendered_row)

        return "\n".join(lines)

    @staticmethod
    def _generate_text(template: dict, data: dict) -> str:
        """
        Generate plain text from a custom template.

        Template format:
        {
            "template": "HEADER LINE\n{{field1}}|{{field2}}\nFOOTER"
        }
        """
        text_template = template.get("template", "")
        if not text_template:
            return json.dumps(data, ensure_ascii=False)
        return FileRequestEngine._render_string(text_template, data)

    @staticmethod
    def _render_template_value(node: Any, context: dict) -> Any:
        """Recursively render {{placeholder}} in template structures."""
        if isinstance(node, dict):
            return {k: FileRequestEngine._render_template_value(v, context) for k, v in node.items()}
        elif isinstance(node, list):
            return [FileRequestEngine._render_template_value(v, context) for v in node]
        elif isinstance(node, str):
            return FileRequestEngine._render_string(node, context)
        else:
            return node

    @staticmethod
    def _render_string(template_str: str, context: dict) -> str:
        """Replace {{key}} placeholders with values from context."""
        result = template_str
        for key, value in context.items():
            placeholder = "{{" + str(key) + "}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value) if value is not None else "")
        return result

    # ═══════════════════════════════════════════════════════
    # Content Hash
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def compute_content_hash(content: bytes) -> str:
        """Compute SHA-256 hash of file content for deduplication."""
        return hashlib.sha256(content).hexdigest()

    # ═══════════════════════════════════════════════════════
    # JSON Response Parsing
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def parse_response(parser_config: dict, raw_content: bytes) -> dict:
        """
        Parse a JSON response file using the parser configuration.

        Steps:
        1. JSON decode (UTF-8)
        2. Error detection (if configured)
        3. Navigate to data_root
        4. Extract specified keys (extract_keys)
        5. Apply post-processing

        Args:
            parser_config: The response_parser_config dict from FileRequestConfig
            raw_content: Raw bytes of the response file

        Returns:
            {
                "success": bool,
                "data": dict | list,     # Extracted data
                "error": str | None,     # Error message if error detected
                "raw": dict              # Full raw JSON for debugging
            }
        """
        # Step 1: JSON decode
        try:
            raw_json = json.loads(raw_content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return {
                "success": False,
                "data": None,
                "error": f"JSON decode error: {str(e)}",
                "raw": None,
            }

        if not parser_config:
            # No parser config — return raw JSON as-is
            return {
                "success": True,
                "data": raw_json,
                "error": None,
                "raw": raw_json,
            }

        # Step 2: Error detection
        error_config = parser_config.get("error_detection")
        if error_config and error_config.get("enabled"):
            is_error, error_msg = FileRequestEngine._detect_error(raw_json, error_config)
            if is_error:
                return {
                    "success": False,
                    "data": None,
                    "error": error_msg or "Error detected in response",
                    "raw": raw_json,
                }

        # Step 3: Navigate to data_root
        data_root = parser_config.get("data_root", "")
        if data_root:
            data = FileRequestEngine._resolve_dot_path(raw_json, data_root)
            if data is None:
                return {
                    "success": False,
                    "data": None,
                    "error": f"data_root path '{data_root}' not found in response",
                    "raw": raw_json,
                }
        else:
            data = raw_json

        # Step 4: Extract keys
        extract_keys = parser_config.get("extract_keys", {})
        if extract_keys:
            data = FileRequestEngine._extract_keys(data, extract_keys)
        else:
            # No extract_keys — check include_unmapped
            post_config = parser_config.get("post_processing", {})
            if not post_config.get("include_unmapped", True):
                # No keys specified and include_unmapped is False → empty result
                data = {} if isinstance(data, dict) else []

        # Step 5: Post-processing
        post_config = parser_config.get("post_processing")
        if post_config:
            data = FileRequestEngine._apply_post_processing(data, post_config)

        return {
            "success": True,
            "data": data,
            "error": None,
            "raw": raw_json,
        }

    @staticmethod
    def _resolve_dot_path(data: Any, path: str) -> Any:
        """
        Navigate into a nested structure using dot-notation.

        Examples:
            _resolve_dot_path({"a": {"b": 1}}, "a.b") → 1
            _resolve_dot_path({"items": [{"x": 1}]}, "items.0.x") → 1
            _resolve_dot_path({"a": 1}, "a.b.c") → None
        """
        if not path:
            return data

        current = data
        for key in path.split("."):
            if current is None:
                return None

            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    current = current[idx] if 0 <= idx < len(current) else None
                except (ValueError, IndexError):
                    return None
            else:
                return None

        return current

    @staticmethod
    def _extract_keys(
        data: Union[dict, list], key_mapping: Dict[str, str]
    ) -> Union[dict, list]:
        """
        Extract specific keys from data using the mapping.

        key_mapping: {output_name: source_dot_path}

        If data is a dict → returns a dict with mapped keys.
        If data is a list → applies mapping to each item in the list.
        """
        if isinstance(data, list):
            return [
                FileRequestEngine._extract_keys_from_item(item, key_mapping)
                for item in data
                if isinstance(item, dict)
            ]
        elif isinstance(data, dict):
            return FileRequestEngine._extract_keys_from_item(data, key_mapping)
        else:
            return data

    @staticmethod
    def _extract_keys_from_item(item: dict, key_mapping: Dict[str, str]) -> dict:
        """Extract keys from a single dict item using the mapping."""
        result = {}
        for output_name, source_path in key_mapping.items():
            value = FileRequestEngine._resolve_dot_path(item, source_path)
            result[output_name] = value
        return result

    @staticmethod
    def _detect_error(raw_json: dict, error_config: dict) -> tuple:
        """
        Check if the response indicates an error.

        Returns: (is_error: bool, error_message: str | None)
        """
        indicator_path = error_config.get("error_indicator_path", "")
        error_values = error_config.get("error_values", [])
        message_path = error_config.get("error_message_path", "")

        if not indicator_path:
            return (False, None)

        indicator_value = FileRequestEngine._resolve_dot_path(raw_json, indicator_path)

        if indicator_value is None:
            # Path not found — not necessarily an error
            return (False, None)

        # Compare as string for flexibility
        str_value = str(indicator_value)
        is_error = str_value in [str(v) for v in error_values]

        error_message = None
        if is_error and message_path:
            error_message = FileRequestEngine._resolve_dot_path(raw_json, message_path)
            if error_message is not None:
                error_message = str(error_message)

        return (is_error, error_message)

    @staticmethod
    def _apply_post_processing(
        data: Union[dict, list], config: dict
    ) -> Union[dict, list]:
        """
        Apply post-processing transformations to extracted data.

        Options:
        - flatten_nested: Flatten nested dicts (e.g., {"a": {"b": 1}} → {"a.b": 1})
        - null_handling: "keep" | "remove" | "default_empty_string"
        - include_unmapped: Whether to keep keys not in extract_keys (handled upstream)
        """
        null_handling = config.get("null_handling", "keep")
        flatten = config.get("flatten_nested", False)

        if isinstance(data, list):
            return [
                FileRequestEngine._post_process_item(item, null_handling, flatten)
                for item in data
            ]
        elif isinstance(data, dict):
            return FileRequestEngine._post_process_item(data, null_handling, flatten)
        return data

    @staticmethod
    def _post_process_item(item: Any, null_handling: str, flatten: bool) -> Any:
        """Apply post-processing to a single item."""
        if not isinstance(item, dict):
            return item

        result = item

        # Flatten nested objects
        if flatten:
            result = FileRequestEngine._flatten_dict(result)

        # Handle nulls
        if null_handling == "remove":
            result = {k: v for k, v in result.items() if v is not None}
        elif null_handling == "default_empty_string":
            result = {k: (v if v is not None else "") for k, v in result.items()}

        return result

    @staticmethod
    def _flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """
        Flatten a nested dictionary.
        {"a": {"b": 1, "c": {"d": 2}}} → {"a.b": 1, "a.c.d": 2}
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(FileRequestEngine._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
