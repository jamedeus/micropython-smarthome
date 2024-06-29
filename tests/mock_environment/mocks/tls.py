import ssl

PROTOCOL_TLS_SERVER = ssl.PROTOCOL_TLS_SERVER


# Mock load_cert_chain to do nothing (micropython supports passing binary cert
# and key args, cpython raises exception if args are not file paths)
class SSLContext(ssl.SSLContext):
    def load_cert_chain(cert, key, password=None):
        pass
