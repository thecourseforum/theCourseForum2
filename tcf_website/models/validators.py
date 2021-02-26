from django.core.exceptions import ValidationError


def validate_caps(value: str):
    if not value.isupper():
        raise ValidationError(f'{value} is not all caps.')
