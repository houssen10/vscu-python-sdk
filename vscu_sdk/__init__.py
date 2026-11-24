"""
VSCU Python SDK
---------------
A comprehensive Python SDK for integrating with the KRA eTIMS VSCU
(Virtual Sales Control Unit) REST API.
"""

from .config import VscuConfig
from .exceptions import VscuException
from .client import Vscu
from .dtos.invoice import InvoiceDTO
from .dtos.item import ItemDTO
from .dtos.credit_note import CreditNoteDTO
from .erpnext.connector import ERPNextVscuConnector

__version__ = "1.0.0"
__all__ = [
    "Vscu",
    "VscuConfig",
    "VscuException",
    "InvoiceDTO",
    "ItemDTO",
    "CreditNoteDTO",
    "ERPNextVscuConnector",
]
