from requests import *
from requests.sessions import Session

# Save reference to original request method
vanilla_request = Session.request


# Raise ValueError instead of JSONDecodeError to match urequests behavior
class MockResponse(Response):
    def json(self):
        try:
            return super().json()
        # Json mock replaces JSONDecodeError with OSError, both are
        # caught so the mock will work regardless of which was applied first
        except (OSError, JSONDecodeError):
            raise ValueError("Invalid JSON")


# Intercept instantiation of Response class, replace with custom subclass
def mock_request(self, *args, **kwargs):
    # Pass args to unmodified request class
    vanilla_response = vanilla_request(self, *args, **kwargs)

    # Copy attributes to subclass with custom json method, return
    response = MockResponse()
    response.__dict__ = vanilla_response.__dict__.copy()
    return response


Response = MockResponse
Session.request = mock_request
