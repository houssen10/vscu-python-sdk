import requests
from urllib.parse import urljoin
from typing import Optional, Dict, Any
from ..config import VscuConfig
from ..exceptions import VscuException


class BaseResource:
    """Base API resource handling HTTP requests to the VSCU middleware."""

    def __init__(self, session: requests.Session, config: VscuConfig):
        self.session = session
        self.config = config

    def request(
        self,
        method: str,
        uri: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request against the VSCU service.
        
        :param method: HTTP method (POST, GET, etc.)
        :param uri: Endpoint path relative to base_url
        :param data: JSON payload dictionary
        :return: Decoded JSON response
        """
        base_url = self.config.base_url
        if not base_url:
            raise VscuException("VSCU base_url is not configured.")

        # Ensure correct URL construction
        url = urljoin(base_url, uri.lstrip("/"))
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Attach Cloudflare Access headers if configured
        if self.config.cf_access_client_id:
            headers["CF-Access-Client-Id"] = self.config.cf_access_client_id.strip()
        if self.config.cf_access_client_secret:
            headers["CF-Access-Client-Secret"] = self.config.cf_access_client_secret.strip()

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                json=data,
                headers=headers,
                timeout=self.config.timeout,
                **kwargs
            )
            
            # Check for HTTP errors or parse response
            try:
                response_json = response.json()
            except Exception:
                response_json = {"raw_text": response.text}

            if not response.ok:
                error_msg = response_json.get("resultMsg") or response_json.get("message") or response.text
                raise VscuException(
                    message=f"VSCU Request failed: {error_msg}",
                    status_code=response.status_code,
                    response_data=response_json
                )

            return response_json

        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", None)
            raise VscuException(
                message=f"Connection error to VSCU at {url}: {str(e)}",
                status_code=status_code
            ) from e
