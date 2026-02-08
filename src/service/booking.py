from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from src.dialog_handler import DIALOG_HANDLER as DH


@dataclass
class CocktailBooking:
    message: str
    result: "Result"

    class Result(StrEnum):
        """Enumeration of possible cocktail booking results."""

        SUCCESS = "SUCCESS"
        INACTIVE = "INACTIVE"
        INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
        NOT_ALLOWED_ALCOHOL = "NOT_ALLOWED_ALCOHOL"
        NO_USER = "NO_USER"
        USER_NOT_KNOWN = "USER_NOT_KNOWN"
        API_NOT_REACHABLE = "API_NOT_REACHABLE"
        CANCELED = "CANCELED"

    @classmethod
    def inactive(cls) -> Self:
        """Create an inactive booking instance."""
        return cls(
            message=DH.get_translation("payment_inactive"),
            result=cls.Result.INACTIVE,
        )

    @classmethod
    def successful_booking(cls, current_balance: float) -> Self:
        """Create a successful booking instance."""
        return cls(
            message=DH.get_translation("payment_successful", current_balance=current_balance),
            result=cls.Result.SUCCESS,
        )

    @classmethod
    def insufficient_balance(cls) -> Self:
        """Create an insufficient balance booking instance."""
        return cls(
            message=DH.get_translation("payment_insufficient_balance"),
            result=cls.Result.INSUFFICIENT_BALANCE,
        )

    @classmethod
    def too_young(cls) -> Self:
        """Create a too young booking instance."""
        return cls(
            message=DH.get_translation("payment_too_young"),
            result=cls.Result.NOT_ALLOWED_ALCOHOL,
        )

    @classmethod
    def no_user_logged_in(cls) -> Self:
        """Create a no user logged in booking instance."""
        return cls(
            message=DH.get_translation("payment_no_user"),
            result=cls.Result.NO_USER,
        )

    @classmethod
    def api_not_reachable(cls) -> Self:
        """Create an API not reachable booking instance."""
        return cls(
            message=DH.get_translation("payment_api_not_reachable"),
            result=cls.Result.API_NOT_REACHABLE,
        )

    @classmethod
    def user_not_known(cls) -> Self:
        """Create a user not known booking instance."""
        return cls(
            message=DH.get_translation("payment_user_not_found"),
            result=cls.Result.USER_NOT_KNOWN,
        )

    @classmethod
    def api_interface_conflict(cls) -> Self:
        """Create a machine issue booking instance."""
        return cls(
            message=DH.get_translation("api_interface_conflict"),
            result=cls.Result.API_NOT_REACHABLE,
        )

    @classmethod
    def canceled(cls) -> Self:
        """Create a canceled booking instance."""
        return cls(
            message=DH.get_translation("payment_canceled"),
            result=cls.Result.CANCELED,
        )

    # SumUp-specific booking results
    @classmethod
    def sumup_successful(cls) -> Self:
        """Create a successful SumUp payment booking instance."""
        return cls(
            message=DH.get_translation("sumup_payment_successful"),
            result=cls.Result.SUCCESS,
        )

    @classmethod
    def sumup_waiting_for_payment(cls) -> Self:
        """Create a SumUp waiting for payment booking instance."""
        return cls(
            message=DH.get_translation("sumup_waiting_for_payment"),
            result=cls.Result.NO_USER,
        )

    @classmethod
    def sumup_payment_declined(cls) -> Self:
        """Create a SumUp payment declined booking instance."""
        return cls(
            message=DH.get_translation("sumup_payment_declined"),
            result=cls.Result.CANCELED,
        )

    @classmethod
    def sumup_no_terminal(cls) -> Self:
        """Create a SumUp no terminal configured booking instance."""
        return cls(
            message=DH.get_translation("sumup_no_terminal"),
            result=cls.Result.API_NOT_REACHABLE,
        )

    @classmethod
    def sumup_checkout_failed(cls) -> Self:
        """Create a SumUp checkout failed booking instance."""
        return cls(
            message=DH.get_translation("sumup_checkout_failed"),
            result=cls.Result.API_NOT_REACHABLE,
        )
