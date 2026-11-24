from typing import Optional, Dict, Any
from .base import BaseResource


class Items(BaseResource):
    """Resource for managing Item master registration and KRA classification."""

    def save_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register or update item information in the VSCU / KRA catalog.
        
        Endpoint: saveItem
        """
        return self.request("POST", "saveItem", data=data)

    def get_item_list(self, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve list of registered items.
        
        Endpoint: selectItemList
        """
        return self.request("POST", "selectItemList", data=query or {})

    def get_item_cls_list(self, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve KRA item classification / HS code catalog.
        
        Endpoint: selectItemClsList
        """
        return self.request("POST", "selectItemClsList", data=query or {})

    def select_code_list(self, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve standard KRA reference codes (currencies, units, countries, payment types).
        
        Endpoint: selectCodeList
        """
        return self.request("POST", "selectCodeList", data=query or {})
