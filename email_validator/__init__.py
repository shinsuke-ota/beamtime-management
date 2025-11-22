class EmailNotValidError(ValueError):
    """Minimal email validation error."""


class ValidatedEmail:
    def __init__(self, email: str):
        self.email = email


def validate_email(email, *_args, **_kwargs):
    if not isinstance(email, str) or "@" not in email:
        raise EmailNotValidError("Invalid email address")
    return ValidatedEmail(email=email)
