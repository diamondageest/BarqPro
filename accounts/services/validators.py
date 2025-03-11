from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator


class NumericLengthValidator(BaseValidator):
    """Validate field for numeric characters with optional length."""

    def __init__(self, field_name, length=None):
        super().__init__(limit_value=length)
        self.field_name = field_name
        self.length = length

    def __call__(self, value):
        """Validate value as numeric, with optional length requirement."""
        if not self.length and not str(value).isdigit():
            raise ValidationError(
                f"{self.field_name} must contain only numeric characters."
            )
        elif self.length and (
            not str(value).isdigit() or len(str(value)) != self.length
        ):
            raise ValidationError(
                f"{self.field_name} must be {self.length} digits and contain only numeric characters."
            )
        # check if tax_number starts and ends with 3 character
        if self.field_name == "Tax Number":
            if not str(value).startswith("3") or not str(value).endswith("3"):
                raise ValidationError(f"{self.field_name} must start and end with 3")


class VatValidator(BaseValidator):
    """Validate that VAT is either 0.0 or 15.0."""

    def __init__(self):
        super().__init__(limit_value=15.0)

    def __call__(self, value):
        """Validate that VAT value is either 0.0 or 15.0."""
        if value not in (0.0, 15.0):
            raise ValidationError("VAT must be either 0.0 or 15.0.")
