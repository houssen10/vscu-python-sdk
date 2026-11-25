import requests
from typing import Optional, Dict, Any, Union
from .config import VscuConfig
from .resources.sales import Sales
from .resources.items import Items
from .resources.customers import Customers


class Vscu:
    """
    Main VSCU client entrypoint.
    
    Usage:
        client = Vscu({
            "base_url": "http://localhost:8088/",
            "timeout": 30.0,
            "cf_access_client_id": "...",     # Optional Cloudflare tunnel token
            "cf_access_client_secret": "..."
        })
        
        # Access resources
        client.sales().save_sales(invoice_dto.to_dict())
    """

    def __init__(self, config: Optional[Union[VscuConfig, Dict[str, Any]]] = None):
        if isinstance(config, VscuConfig):
            self.config = config
        else:
            self.config = VscuConfig(config or {})

        self.session = requests.Session()

        # Cached resource instances
        self._sales: Optional[Sales] = None
        self._items: Optional[Items] = None
        self._customers: Optional[Customers] = None

    def sales(self) -> Sales:
        """Access the Sales & Credit Notes resource."""
        if self._sales is None:
            self._sales = Sales(self.session, self.config)
        return self._sales

    def items(self) -> Items:
        """Access the Items master & classification resource."""
        if self._items is None:
            self._items = Items(self.session, self.config)
        return self._items

    def customers(self) -> Customers:
        """Access the Customer PIN verification resource."""
        if self._customers is None:
            self._customers = Customers(self.session, self.config)
        return self._customers

    def initialize(self, tin: str, bhf_id: str, dvc_srl_no: str) -> Dict[str, Any]:
        """
        Perform one-time VSCU device initialization for a TIN + branch.

        Endpoint: initializer/selectInitInfo
        """
        return self.sales().request(
            "POST",
            "initializer/selectInitInfo",
            data={"tin": tin, "bhfId": bhf_id, "dvcSrlNo": dvc_srl_no},
        )

    @staticmethod
    def build_qr_code_url(tin: str, bhf_id: str, rcpt_sign: str, sandbox: bool = False) -> str:
        """Build the KRA eTIMS verification QR code URL from the signed receipt."""
        host = "etims-sbx.kra.go.ke" if sandbox else "etims.kra.go.ke"
        return f"https://{host}/common/link/etims/receipt/indexEtimsReceiptData?Data={tin}{bhf_id}{rcpt_sign}"
