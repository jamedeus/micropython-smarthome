'''Custom questionary validators used by config_generator.py to prevent
invalid user input.
'''

from questionary import Validator, ValidationError
from helper_functions import is_int, is_float


class IntRange(Validator):
    '''Takes minimum and maximum integers, prevents submitting anything except
    an integer within range (inclusive).
    '''

    def __init__(self, minimum, maximum):
        self.minimum = int(minimum)
        self.maximum = int(maximum)

    def validate(self, document):
        if is_int(document.text) and self.minimum <= int(document.text) <= self.maximum:
            return True
        raise ValidationError(
            message=f"Must be int between {self.minimum} and {self.maximum}",
            cursor_position=len(document.text)
        )


class FloatRange(Validator):
    '''Takes minimum and maximum floats, prevents submitting anything except
    an integer within range (inclusive).
    '''

    def __init__(self, minimum, maximum):
        self.minimum = float(minimum)
        self.maximum = float(maximum)

    def validate(self, document):
        if is_float(document.text) and self.minimum <= float(document.text) <= self.maximum:
            return True
        raise ValidationError(
            message=f"Must be float between {self.minimum} and {self.maximum}",
            cursor_position=len(document.text)
        )


class MinLength(Validator):
    '''Takes integer number of characters, prevents user from submitting a
    string with fewer characters.
    '''

    def __init__(self, min_length):
        self.min_length = int(min_length)

    def validate(self, document):
        if len(str(document.text)) >= self.min_length:
            return True
        raise ValidationError(message=f"Enter {self.min_length} or more characters")


class LengthRange(Validator):
    '''Takes minimum and maximum characters (integer), prevents user from
    submitting a string with fewer or greater characters
    '''

    def __init__(self, min_length, max_length):
        self.min_length = int(min_length)
        self.max_length = int(max_length)

    def validate(self, document):
        if self.min_length <= len(str(document.text)) <= self.max_length:
            return True
        raise ValidationError(
            message=f"Must be between {self.min_length} and {self.max_length} characters"
        )


class NicknameValidator(Validator):
    '''Takes list of existing device and sensor nicknames, prevents user from
    submitting a duplicate nickname or a blank string.
    '''

    def __init__(self, used_nicknames):
        self.used_nicknames = used_nicknames

    def validate(self, document):
        if len(document.text) == 0:
            raise ValidationError(message="Nickname cannot be blank")
        if document.text in self.used_nicknames:
            raise ValidationError(message=f'Nickname "{document.text}" already used')
        return True
