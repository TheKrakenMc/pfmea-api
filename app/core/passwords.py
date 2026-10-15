from typing import Annotated
from pydantic import AfterValidator, StringConstraints


def validate_password_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password exceeds the supported UTF-8 length")
    return value


Password = Annotated[
    str,
    StringConstraints(min_length=8, max_length=72),
    AfterValidator(validate_password_bytes),
]
