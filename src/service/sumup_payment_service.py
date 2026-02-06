import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Literal, Self

import stamina
from stamina.instrumentation import RetryDetails, set_on_retry_hooks
from sumup import APIError, Sumup
from sumup.readers import (
    CreateReaderBody,
    CreateReaderCheckoutBody,
    CreateReaderCheckoutBodyTotalAmount,
    Reader,
    StatusResponse,
)
from sumup.readers.types import StatusResponseDataState
from sumup.transactions import GetTransactionV21Params, TransactionFull

from src.logger_handler import LoggerHandler

_logger = LoggerHandler("SumupPaymentService")


def _stamina_retry_hook(details: RetryDetails) -> None:
    """Log retry events using our LoggerHandler format."""
    _logger.warning(
        f"Retry scheduled for {details.name}: attempt {details.retry_num}, "
        f"waiting {details.wait_for:.2f}s (total waited: {details.waited_so_far:.2f}s), "
        f"caused by: {details.caused_by!r}"
    )


# Replace default stamina hooks with our custom one
set_on_retry_hooks([_stamina_retry_hook])


@dataclass
class Success[T]:
    data: T


@dataclass
class Err:
    error: str
    code: int | None


type Result[T] = Success[T] | Err


def run_catching[**P, T](
    fn: Callable[P, T],
) -> Callable[P, Result[T]]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T]:
        try:
            return Success(fn(*args, **kwargs))
        except Exception as exc:
            reason: str = str(exc)
            code = None
            if isinstance(exc, APIError):
                reason = str(exc.body)
                code = exc.status
            return Err(error=reason, code=code)

    return wrapper


class _SumupSdkClient:
    def __init__(self, api_key: str, merchant_code: str) -> None:
        self._client = Sumup(api_key=api_key)
        self._merchant_code = merchant_code

    @run_catching
    def list_readers(self) -> list[Reader]:
        return self._client.readers.list(merchant_code=self._merchant_code).items

    @run_catching
    def create_reader(self, name: str, pairing_code: str) -> Reader:
        return self._client.readers.create(
            self._merchant_code,
            CreateReaderBody(
                name=name,
                pairing_code=pairing_code,
            ),
        )

    @run_catching
    def delete_reader(self, reader_id: str) -> None:
        return self._client.readers.delete(
            merchant_code=self._merchant_code,
            id=reader_id,
        )

    @run_catching
    def create_checkout(
        self,
        reader_id: str,
        value: int,
        currency: str,
        minor_unit: int,
        description: str,
    ) -> str:
        return self._client.readers.create_checkout(
            merchant_code=self._merchant_code,
            reader_id=reader_id,
            body=CreateReaderCheckoutBody(
                total_amount=CreateReaderCheckoutBodyTotalAmount(
                    value=value,
                    currency=currency,
                    minor_unit=minor_unit,
                ),
                description=description,
                return_url=None,
            ),
        ).data.client_transaction_id

    @run_catching
    @stamina.retry(on=APIError, attempts=3)
    def terminate_checkout(self, reader_id: str) -> None:
        return self._client.readers.terminate_checkout(self._merchant_code, reader_id)

    @run_catching
    def get_status(self, reader_id: str) -> StatusResponse:
        return self._client.readers.get_status(self._merchant_code, reader_id)

    @run_catching
    @stamina.retry(on=APIError, attempts=3)
    def get_transaction(self, client_transaction_id: str) -> TransactionFull:
        return self._client.transactions.get(
            self._merchant_code,
            GetTransactionV21Params(client_transaction_id=client_transaction_id),
        )


class SumupPaymentService:
    _instance: Self | None = None

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, api_key: str | None = None, merchant_code: str | None = None) -> None:
        if getattr(self, "_initialized", False):
            return
        if not api_key or not merchant_code:
            raise ValueError("api_key and merchant_code are required for first initialization")
        self._client: _SumupSdkClient = _SumupSdkClient(api_key=api_key, merchant_code=merchant_code)
        self._initialized = True
        _logger.info("SumupPaymentService initialized")

    def get_all_readers(self) -> list[Reader]:
        result = self._client.list_readers()
        if isinstance(result, Err):
            _logger.error(f"Failed to list readers: {result.error} (code: {result.code})")
            return []
        return result.data

    def create_reader(self, name: str, pairing_code: str) -> Result[Reader]:
        return self._client.create_reader(name, pairing_code)

    def delete_reader(self, reader_id: str) -> Result[None]:
        return self._client.delete_reader(reader_id)

    def trigger_checkout(
        self,
        reader_id: str,
        value: int,
        description: str,
    ) -> Result[str]:
        """Return the client_transaction_id of the created checkout."""
        return self._client.create_checkout(
            reader_id=reader_id,
            value=value,
            currency="EUR",
            minor_unit=2,
            description=description,
        )

    def terminate_checkout(self, reader_id: str) -> bool:
        try:
            self._client.terminate_checkout(reader_id)
        except Exception as e:
            _logger.error(f"Failed to terminate checkout on reader {reader_id}: {e}")
            return False
        return True

    def wait_for_complete(
        self,
        reader_id: str,
        poll_interval_s: float = 1.0,
        timeout_s: float = 60.0,
        iteration: int = 0,
    ) -> StatusResponseDataState | Literal["UNKNOWN"]:
        """Poll reader status until it returns IDLE or hits timeout. Returns the final state."""
        state = "UNKNOWN"
        max_iteration = 3
        if iteration >= max_iteration:
            _logger.error(f"Maximum retry attempts reached while waiting for reader {reader_id} to become IDLE.")
            return state
        start = time.time()
        while True:
            status = self._client.get_status(reader_id)
            if isinstance(status, Err):
                _logger.error(f"Failed to get status for reader {reader_id}: {status.error} (code: {status.code})")
            else:
                state = status.data.data.state or "UNKNOWN"
            if state == "IDLE":
                break
            if time.time() - start >= timeout_s:
                break
            time.sleep(poll_interval_s)
        if state != "IDLE":
            _logger.warning(f"Timeout reached waiting for reader {reader_id} to become IDLE. Final state: {state}")
            # best is to set termination again each iteration just to be sure since this does not return anything
            self.terminate_checkout(reader_id)
            if iteration == 0:
                _logger.info(f"Termination started on reader {reader_id} due to timeout.")
            self.wait_for_complete(reader_id, poll_interval_s=0.5, timeout_s=2, iteration=iteration + 1)
        return state

    def get_transaction(self, client_transaction_id: str) -> Result[TransactionFull]:
        return self._client.get_transaction(client_transaction_id)
