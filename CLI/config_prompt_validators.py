from questionary import Validator, ValidationError
from helper_functions import is_int, is_float


class IntRange(Validator):
    def __init__(self, minimum, maximum):
        self.minimum = int(minimum)
        self.maximum = int(maximum)

    def validate(self, document):
        if is_int(document.text) and self.minimum <= int(document.text) <= self.maximum:
            return True
        else:
            raise ValidationError(
                message=f"Must be int between {self.minimum} and {self.maximum}",
                cursor_position=len(document.text)
            )


class FloatRange(Validator):
    def __init__(self, minimum, maximum):
        self.minimum = float(minimum)
        self.maximum = float(maximum)

    def validate(self, document):
        if is_float(document.text) and self.minimum <= float(document.text) <= self.maximum:
            return True
        else:
            raise ValidationError(
                message=f"Must be float between {self.minimum} and {self.maximum}",
                cursor_position=len(document.text)
            )


class MinLength(Validator):
    def __init__(self, min_length):
        self.min_length = int(min_length)

    def validate(self, document):
        if len(str(document.text)) >= self.min_length:
            return True
        else:
            raise ValidationError(message=f"Enter {self.min_length} or more characters")


# Instantiated with list of already-used nicknames
class NicknameValidator(Validator):
    def __init__(self, used_nicknames):
        self.used_nicknames = used_nicknames

    def validate(self, document):
        if len(document.text) == 0:
            raise ValidationError(message="Nickname cannot be blank")
        elif document.text in self.used_nicknames:
            raise ValidationError(message=f'Nickname "{document.text}" already used')
        else:
            return True
