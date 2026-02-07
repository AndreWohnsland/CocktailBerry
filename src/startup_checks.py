import sys
from dataclasses import dataclass

from src import FUTURE_PYTHON_VERSION
from src.config.config_manager import CONFIG as cfg
from src.logger_handler import LoggerHandler
from src.machine.rfid import RFIDReader
from src.service.sumup_payment_service import Err, SumupPaymentService
from src.updater import UpdateInfo, Updater
from src.utils import has_connection

_logger = LoggerHandler("startup_checks")


@dataclass
class PaymentCheckResult:
    """Result of a payment startup check."""

    ok: bool
    reason: str = ""


def can_update() -> UpdateInfo:
    """Check if there is an update and it is possible."""
    if not cfg.MAKER_SEARCH_UPDATES:
        return UpdateInfo(UpdateInfo.Status.DISABLED, "Automatic update search is disabled.")
    updater = Updater()
    return updater.check_for_updates()


def connection_okay() -> bool:
    """Check if there is an internet connection, if needed."""
    # only needed if microservice is also active
    if not cfg.MAKER_CHECK_INTERNET or not cfg.MICROSERVICE_ACTIVE:
        return True
    return has_connection()


def is_python_deprecated() -> bool:
    """Check if to display the deprecation warning for newer python version install."""
    sys_python = sys.version_info
    return sys_python < FUTURE_PYTHON_VERSION


def check_payment_service() -> PaymentCheckResult:
    """Check if the configured payment service can start properly."""
    if not cfg.payment_enabled:
        return PaymentCheckResult(ok=True)
    if cfg.sumup_payment:
        return _check_sumup()
    if cfg.cocktailberry_payment:
        return _check_cocktailberry_nfc()
    return PaymentCheckResult(ok=True)


def _check_sumup() -> PaymentCheckResult:
    """Validate SumUp payment prerequisites."""
    # Try to initialize the client and list readers to verify credentials
    try:
        service = SumupPaymentService(
            api_key=cfg.PAYMENT_SUMUP_API_KEY,
            merchant_code=cfg.PAYMENT_SUMUP_MERCHANT_CODE,
        )
        result = service.get_all_readers_result()
        if isinstance(result, Err):
            return PaymentCheckResult(ok=False, reason=f"SumUp API error: {result.error} (code: {result.code})")
        _logger.info(f"SumUp startup check passed, {len(result.data)} reader(s) found.")
    except Exception as e:
        return PaymentCheckResult(ok=False, reason=f"SumUp API error: {e}")
    if not cfg.PAYMENT_SUMUP_TERMINAL_ID:
        _logger.warning("Reader is not set, but it is required for payments. Please set it up.")
    return PaymentCheckResult(ok=True)


def _check_cocktailberry_nfc() -> PaymentCheckResult:
    """Validate CocktailBerry NFC payment prerequisites."""
    if RFIDReader().rfid is None:
        return PaymentCheckResult(ok=False, reason=f"Could not set up or use {cfg.RFID_READER} reader, see logs.")
    return PaymentCheckResult(ok=True)
