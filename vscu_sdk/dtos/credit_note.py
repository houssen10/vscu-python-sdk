from typing import Optional, Dict, Any
from .invoice import InvoiceDTO


class CreditNoteDTO(InvoiceDTO):
    """
    Represents a Credit Note (Refund) payload for KRA eTIMS VSCU.
    
    Notes:
    - Receipt type is set to 'R' (Refund).
    - orgInvcNo must reference the original full fiscal invoice number (e.g. KRACU0300010006/5).
    - invcNo shares the same sequential counter as standard Sales invoices.
    - rfdDt (Refund Date) and rfdRsnCd (Reason Code, e.g. '01' for Return) are mandatory.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        super().__init__(data)
        self.rcpt_ty_cd = "R"  # Force refund receipt type
