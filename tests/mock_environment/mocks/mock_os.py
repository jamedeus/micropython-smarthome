import sys

# Save so messages can be written to both stdout and dupterm stream
_original_stdout = sys.stdout


class StdoutDuplicator:
    '''Replaces sys.stdout to simulate behavior of micropython os.dupterm.
    Always writes output to sys.stdout, also writes to another stream-like
    object if set (self.dupterm_stream).
    '''

    def __init__(self):
        # Stream-like object that will receive everything written to stdout
        self.dupterm_stream = None

    def write(self, data):
        '''Write to stdout and dupterm_stream (if set)'''

        _original_stdout.write(data)
        if self.dupterm_stream:
            self.dupterm_stream.write(data.encode())

    def flush(self):
        '''Flush stdout and dupterm_stream (if set)'''

        _original_stdout.flush()
        if self.dupterm_stream:
            self.dupterm_stream.flush()


# Replace sys.stdout with duplicator
stdout_duplicator = StdoutDuplicator()
sys.stdout = stdout_duplicator


def dupterm(stream_object, index=0):
    '''Simulate behavior of micropython os.dupterm. Takes stream-like object,
    sets as StdoutDuplicator.dupterm_stream so that all terminal output will
    also be written to the stream-like object. Call with None to reset.
    '''
    if index != 0:
        raise ValueError('invalid dupterm index')

    # Save current stream before overwriting
    prev_stream = stdout_duplicator.dupterm_stream
    stdout_duplicator.dupterm_stream = stream_object

    # Return previous stream
    return prev_stream
