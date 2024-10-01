import time

# Save original time method (returns epoch with subseconds)
original_time = time.time


def mock_time():
    '''Mock time.time method that returns epoch with no subseconds (matches
    micropython time module behavior).
    '''
    return int(original_time())
