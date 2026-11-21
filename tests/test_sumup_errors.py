import httpx
from sumup.errors import APIConnectionError, APIError
from sumup.types import Problem

from src.service.sumup_payment_service import Err, run_catching

_REQUEST = httpx.Request("POST", "https://api.sumup.com/v0/merchants/M/readers/R/go-checkout")


def _fail_with(exc: Exception) -> Err:
    @run_catching
    def call() -> None:
        raise exc

    result = call()
    assert isinstance(result, Err)
    return result


def test_connection_error_keeps_its_message() -> None:
    result = _fail_with(APIConnectionError(request=_REQUEST))
    assert result == Err(error="Connection error.", code=None)


def test_problem_body_shows_the_detail() -> None:
    response = httpx.Response(
        422,
        json={"type": "about:blank", "title": "Reader offline", "status": 422, "detail": "Reader is not connected."},
        headers={"Content-Type": "application/problem+json"},
        request=_REQUEST,
    )
    result = _fail_with(APIError.from_response("The request violates a business rule.", response, body_type=Problem))
    assert result == Err(error="Reader is not connected.", code=422)


def test_raw_json_body_is_kept_as_json() -> None:
    response = httpx.Response(401, json={"error_code": "UNAUTHORIZED"}, request=_REQUEST)
    result = _fail_with(APIError.from_response("Authentication failed.", response))
    assert result == Err(error='{"error_code": "UNAUTHORIZED"}', code=401)
