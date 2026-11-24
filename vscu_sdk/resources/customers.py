from typing import Optional, Dict, Any
from .base import BaseResource


class Customers(BaseResource):
    """Resource for querying customer tax status and KRA PIN verification."""

    def select_customer(self, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query customer details by KRA PIN.
        
        :param query: {'custTin': 'P0...'}
        Endpoint: selectCustomer
        """
        return self.request("POST", "selectCustomer", data=query or {})
