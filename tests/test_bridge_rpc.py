import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from strokeguard.bridge.msgpack_rpc import MessagePackRPCClient

def test_client_message_id_increments():
    c=MessagePackRPCClient()
    assert c.msgid == 1
    c.msgid += 1
    assert c.msgid == 2
