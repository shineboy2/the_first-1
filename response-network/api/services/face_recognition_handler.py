import base64
import httpx
import logging
from typing import Dict, Any

from models.external_api import ExternalAPI
from services.base_external_handler import BaseExternalHandler

logger = logging.getLogger(__name__)

class FaceRecognitionHandler(BaseExternalHandler):
    """
    Handler for FF.Security Face Recognition API.
    Executes a 5-step flow: login, detect, search dossiers, get face objects, download images.
    """
    
    def get_name(self) -> str:
        return "face_recognition"
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        if "file_data" not in params and "base64Image" not in params:
             raise ValueError("Image data (file_data or base64Image) is required")
        return True
    
    def execute(self, request_data: Dict[str, Any], api_name: str = "face_recognition", api_config: ExternalAPI = None) -> Dict[str, Any]:
        """Execute the 5-step Face Recognition flow."""
        # 1. Load config
        config = api_config or self.db.query(ExternalAPI).filter(ExternalAPI.name == api_name).first()
        if not config:
            raise ValueError(f"External API '{api_name}' not found")
        if not config.is_active:
            raise ValueError(f"External API '{api_name}' is inactive")
            
        base_url = config.endpoint_url.rstrip("/")
        auth = config.auth_config or {}
        username = auth.get("username", "")
        password = auth.get("password", "")
        threshold = auth.get("threshold", 0.75)
        limit = auth.get("limit", 10)
        ordering = auth.get("ordering", "-looks_like_confidence")
        
        # 2. Extract image bytes
        image_b64 = request_data.get("file_data") or request_data.get("base64Image")
        if not image_b64:
             raise ValueError("No image data found in request")
             
        # Remove data URI prefix if present
        if isinstance(image_b64, str) and "," in image_b64:
             image_b64 = image_b64.split(",", 1)[1]
             
        try:
             image_bytes = base64.b64decode(image_b64)
        except Exception:
             raise ValueError("Invalid base64 image data")
             
        # Execute Steps
        try:
            # Step 1: Login
            token = self._login(base_url, username, password)
            
            # Step 2: Detect
            detect_result = self._detect(base_url, token, image_bytes)
            faces = detect_result.get("objects", {}).get("face", [])
            if not faces:
                return {
                    "api_response": {
                        "detect_id": None, 
                        "detection_score": 0, 
                        "total_matches": 0, 
                        "similar_faces": [],
                        "message": "No face detected in the provided image"
                    }
                }
            
            detect_id = faces[0]["id"]
            detection_score = faces[0].get("detection_score", 0)
            
            # Step 3: Search dossiers
            dossiers = self._search_dossiers(base_url, token, detect_id, threshold, limit, ordering)
            if not dossiers:
                return {
                    "api_response": {
                        "detect_id": detect_id, 
                        "detection_score": detection_score,
                        "total_matches": 0, 
                        "similar_faces": [],
                        "message": "No similar faces found"
                    }
                }
            
            # Step 4: Get face objects (URLs)
            face_ids = [d.get("looks_like", {}).get("matched_object") for d in dossiers 
                        if isinstance(d, dict) and d.get("looks_like", {}).get("matched_object")]
            
            face_objects = self._get_face_objects(base_url, token, face_ids)
            
            # Step 5: Download images -> base64
            api_response = self._build_result(base_url, token, detect_id, detection_score, dossiers, face_objects)
            
            return {"api_response": api_response}
            
        except Exception as e:
            logger.error(f"Face Recognition API error: {str(e)}", exc_info=True)
            raise Exception(f"Face Recognition API failed: {str(e)}")

    # ─── Private Methods ───────────────────────────
    
    def _login(self, base_url: str, username: str, password: str) -> str:
        """POST /auth/login/ with Basic Auth"""
        if not username or not password:
             raise ValueError("API username and password are required in auth_config")
             
        credentials = f"{username}:{password}"
        basic_token = base64.b64encode(credentials.encode()).decode()
        
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{base_url}/auth/login/",
                headers={"Authorization": f"Basic {basic_token}"},
                json={"video_auth_token": ""}
            )
            resp.raise_for_status()
            return resp.json().get("token")
            
    def _detect(self, base_url: str, token: str, image_bytes: bytes) -> dict:
        """POST /detect/ multipart"""
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{base_url}/detect/",
                headers={"Authorization": f"Token {token}"},
                files={"photo": ("image.jpg", image_bytes, "image/jpeg")},
                data={"attributes": '{"face": {}}'}
            )
            resp.raise_for_status()
            return resp.json()
            
    def _search_dossiers(self, base_url: str, token: str, detect_id: str, threshold: float, limit: int, ordering: str) -> list:
        """GET /dossiers/?looks_like=detection:{detect_id}"""
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{base_url}/dossiers/",
                headers={"Authorization": f"Token {token}"},
                params={
                    "looks_like": f"detection:{detect_id}",
                    "threshold": threshold,
                    "limit": limit,
                    "ordering": ordering,
                }
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
            
    def _get_face_objects(self, base_url: str, token: str, face_ids: list) -> list:
        """GET /objects/faces/?id_in={ids}"""
        if not face_ids:
            return []
            
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{base_url}/objects/faces/",
                headers={"Authorization": f"Token {token}"},
                params={"id_in": ",".join(str(fid) for fid in face_ids), "limit": 200}
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
            
    def _download_image_as_base64(self, base_url: str, token: str, url: str) -> str:
        """Download image from FF.Security and encode as base64"""
        if not url:
            return ""
            
        if url.startswith("http"):
            full_url = url
        else:
            # Ensure proper joining
            if url.startswith("/"):
                 full_url = f"{base_url}{url}"
            else:
                 full_url = f"{base_url}/{url}"
        
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    full_url,
                    headers={"Authorization": f"Token {token}"}
                )
                resp.raise_for_status()
                b64 = base64.b64encode(resp.content).decode()
                content_type = resp.headers.get("content-type", "image/jpeg")
                return f"data:{content_type};base64,{b64}"
        except Exception as e:
            logger.warning(f"Failed to download image {full_url}: {e}")
            return ""
            
    def _build_result(self, base_url, token, detect_id, score, dossiers, face_objects):
        """Combine dossier metadata + downloaded images"""
        # Index face objects by ID for lookup
        face_map = {str(fo.get("id")): fo for fo in face_objects}
        
        similar_faces = []
        for dossier in dossiers:
            matched_id = str(dossier.get("looks_like", {}).get("matched_object", ""))
            face_obj = face_map.get(matched_id, {})
            
            # Download both images
            source_b64 = ""
            thumb_b64 = ""
            if face_obj.get("source_photo"):
                source_b64 = self._download_image_as_base64(
                    base_url, token, face_obj["source_photo"])
            if face_obj.get("thumbnail"):
                thumb_b64 = self._download_image_as_base64(
                    base_url, token, face_obj["thumbnail"])
            
            similar_faces.append({
                "dossier_id": dossier.get("id"),
                "dossier_name": dossier.get("name", ""),
                "confidence": dossier.get("looks_like", {}).get("confidence", 0),
                "face_id": matched_id,
                "dossier_lists": dossier.get("dossier_lists", []),
                "source_photo_b64": source_b64,
                "thumbnail_b64": thumb_b64,
                "source_coords": {
                    "left": face_obj.get("source_coords_left"),
                    "top": face_obj.get("source_coords_top"),
                    "right": face_obj.get("source_coords_right"),
                    "bottom": face_obj.get("source_coords_bottom"),
                }
            })
        
        return {
            "detect_id": detect_id,
            "detection_score": score,
            "total_matches": len(similar_faces),
            "similar_faces": similar_faces
        }
