from typing import Optional, Dict, Any
from .base import BaseResource


class Sales(BaseResource):
    """Resource for managing fiscal Sales Invoices and Credit Notes."""

    def save_sales(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a Sales Invoice payload to the VSCU service.
        
        Endpoint: trnsSales/saveSales
        """
        return self.request("POST", "trnsSales/saveSales", data=data)

    def save_credit_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a Credit Note (Refund) payload to the VSCU service.
        Uses the same saveSales endpoint with rcptTyCd='R'.
        
        Endpoint: trnsSales/saveSales
        """
        return self.request("POST", "trnsSales/saveSales", data=data)

    def select_items(self, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for items stored within the VSCU cache/system.
        
        Endpoint: selectItems
        """
        return self.request("POST", "selectItems", data=query or {})

    def select_customer(self, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Lookup customer details and PIN status.
        
        Endpoint: selectCustomer
        """
        return self.request("POST", "selectCustomer", data=query or {})

    def select_invoice_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve saved fiscal invoice details by tin, bhfId, and invcNo.
        
        :param data: {'tin': str, 'bhfId': str, 'invcNo': int}
        Endpoint: trnsSales/selectInvoiceDetails
        """
        return self.request("POST", "trnsSales/selectInvoiceDetails", data=data)
