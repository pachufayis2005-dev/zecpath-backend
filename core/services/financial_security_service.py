from decimal import Decimal

from core.models import FinancialAuditLog


class FinancialSecurityService:
    """
    Handles financial security monitoring.

    Detects suspiciously large transactions and records
    them in the financial audit log.
    """

    SUSPICIOUS_AMOUNT = Decimal("100000")

    @staticmethod
    def is_suspicious(transaction):
        """
        Returns True when the transaction amount reaches
        or exceeds the suspicious transaction threshold.
        """

        return transaction.amount >= FinancialSecurityService.SUSPICIOUS_AMOUNT

    @staticmethod
    def log_suspicious_transaction(transaction):
        """
        Creates a financial audit log when a transaction
        is considered suspicious.
        """

        if not FinancialSecurityService.is_suspicious(transaction):
            return None

        return FinancialAuditLog.objects.create(
            transaction=transaction,
            employer=transaction.employer,
            action=FinancialAuditLog.SUSPICIOUS_TRANSACTION,
            message=(
                "Transaction exceeded the configured "
                "financial monitoring threshold."
            ),
        )