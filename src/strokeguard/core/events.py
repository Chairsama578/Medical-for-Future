import json, sqlite3, time
from pathlib import Path

class EventStore:
    def __init__(self, path="data/strokeguard_events.db"):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                kind TEXT NOT NULL,
                state TEXT,
                score REAL,
                payload TEXT NOT NULL
            )""")

    def log(self, kind, state=None, score=None, payload=None):
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO events(ts,kind,state,score,payload) VALUES(?,?,?,?,?)",
                      (time.time(),kind,state,score,json.dumps(payload or {})))
