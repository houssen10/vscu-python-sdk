import os
from typing import Optional, Dict, Any


class VscuConfig:
    """Configuration holder for VSCU client connection and authentication."""

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        options = options or {}
        
        self.base_url: str = options.get("base_url") or os.getenv("VSCU_BASE_URL", "")
        # Ensure trailing slash if base_url is present
        if self.base_url and not self.base_url.endswith("/"):
            self.base_url += "/"
            
        self.timeout: float = float(options.get("timeout", 30.0))
        
        # Cloudflare Access Service Token credentials (if VSCU is behind a Cloudflare Tunnel)
        self.cf_access_client_id: Optional[str] = (
            options.get("cf_access_client_id") or os.getenv("CF_ACCESS_CLIENT_ID")
        )
        self.cf_access_client_secret: Optional[str] = (
            options.get("cf_access_client_secret") or os.getenv("CF_ACCESS_CLIENT_SECRET")
        )

    @property
    def has_cf_auth(self) -> bool:
        return bool(self.cf_access_client_id and self.cf_access_client_secret)
