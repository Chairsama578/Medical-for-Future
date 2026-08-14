import socket
import msgpack

class MessagePackRPCClient:
    def __init__(self, socket_path="/var/run/arduino-router.sock", timeout=2.0):
        self.socket_path = socket_path
        self.timeout = timeout
        self.msgid = 1

    def call(self, method, *params):
        msgid = self.msgid
        self.msgid += 1
        request = [0, msgid, method, list(params)]
        packed = msgpack.packb(request, use_bin_type=True)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            s.connect(self.socket_path)
            s.sendall(packed)
            data = s.recv(65536)
        response = msgpack.unpackb(data, raw=False)
        if not isinstance(response, list) or len(response) != 4:
            raise RuntimeError(f"Invalid RPC response: {response!r}")
        _, rid, error, result = response
        if rid != msgid:
            raise RuntimeError(f"RPC id mismatch: expected {msgid}, got {rid}")
        if error is not None:
            raise RuntimeError(str(error))
        return result
