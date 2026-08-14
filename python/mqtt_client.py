#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mqtt_client.py — MQTT Cloud subscriber for StrokeGuard UNO Q
============================================================
Nhận sensor data từ HiveMQ Cloud (ESP32 publish) và đưa vào pipeline AI
dưới dạng DICT chuẩn hóa:

    {
      "ts": ..., "ir": ..., "red": ...,
      "ax": ..., "ay": ..., "az": ...,
      "gx": ..., "gy": ..., "gz": ...,
      "device": "...",
      "bpm": float|None, "spo2": float|None,
      "roll": float|None, "pitch": float|None,
    }

Hỗ trợ 3 dạng payload từ ESP32:
  1. JSON mới (10 fields, có "device"):
     {"device":"esp32-strokeguard-01","ax":..,"ay":..,"az":..,
      "gx":..,"gy":..,"gz":..,"ir":..,"red":..,"ts":..}
     -> bpm/spo2/roll/pitch = None (UNO Q tự tính roll/pitch từ accel)
  2. JSON cũ (13 fields): ts,ir,red,bpm,spo2,ax,ay,az,gx,gy,gz,roll,pitch
  3. CSV 13 fields (protocol Bridge cũ)

Config: file mqtt_config.json nằm CẠNH file này.
Khi username/password còn là placeholder (REPLACE_WITH_*), subscriber
không spam reconnect: log 1 lần mỗi 60s và chờ. Điền creds xong → restart
app là chạy.
"""
import json
import os
import sys
import threading
import time

# vendor/ chứa paho-mqtt (pure python) — dùng khi container không có sẵn lib
_VENDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

try:
    import paho.mqtt.client as mqtt
    _PAHO_OK = True
except ImportError:
    _PAHO_OK = False

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "mqtt_config.json")


def load_mqtt_config(path=None):
    """Đọc config MQTT. Trả dict hoặc None (thiếu file / lỗi JSON)."""
    p = path or _CONFIG_PATH
    try:
        with open(p, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg
    except FileNotFoundError:
        print(f"[MQTT] Không tìm thấy {p} — MQTT tắt", flush=True)
        return None
    except Exception as e:
        print(f"[MQTT] Lỗi đọc config {p}: {e}", flush=True)
        return None


def creds_ready(cfg):
    """True khi username/password đã được điền thật (không phải placeholder)."""
    u = str(cfg.get("username", "")).strip()
    p = str(cfg.get("password", "")).strip()
    return bool(u and p and not u.startswith("REPLACE_WITH")
                and not p.startswith("REPLACE_WITH"))


def _f(v):
    """float-safe: None/''/lạ -> None."""
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def normalize_payload(payload, log=print):
    """Chuyển payload ESP32 (JSON/CSV) -> dict chuẩn hóa. Trả None nếu lạ."""
    payload = (payload or "").strip()
    if not payload:
        return None
    d = {}
    if payload.startswith("{"):
        try:
            d = json.loads(payload)
        except Exception as e:
            log(f"[MQTT] JSON lỗi: {e}", flush=True)
            return None
        has_device = "device" in d
        # Format mới: device + ax..gz + ir/red + ts (KHÔNG có bpm/spo2/roll/pitch)
        if has_device and ("ax" in d):
            return {
                "ts": _f(d.get("ts")) or time.time(),
                "ir": _f(d.get("ir", 0)) or 0.0,
                "red": _f(d.get("red", 0)) or 0.0,
                "ax": _f(d.get("ax", 0)) or 0.0,
                "ay": _f(d.get("ay", 0)) or 0.0,
                "az": _f(d.get("az", 0)) or 0.0,
                "gx": _f(d.get("gx", 0)) or 0.0,
                "gy": _f(d.get("gy", 0)) or 0.0,
                "gz": _f(d.get("gz", 0)) or 0.0,
                "device": str(d.get("device", "esp32-unknown")),
                "bpm": _f(d.get("hr", d.get("bpm"))),  # firmware mới gửi "hr"
                "spo2": _f(d.get("spo2")),
                "finger": bool(d.get("finger", False)),
                "roll": _f(d.get("roll")),   # None -> main.py tự tính từ accel
                "pitch": _f(d.get("pitch")),
            }
        # Format cũ: JSON 13 fields ts,ir,red,bpm,spo2,ax,ay,az,gx,gy,gz,roll,pitch
        if "ax" in d and "ir" in d:
            return {
                "ts": _f(d.get("ts")) or time.time(),
                "ir": _f(d.get("ir", 0)) or 0.0,
                "red": _f(d.get("red", 0)) or 0.0,
                "ax": _f(d.get("ax", 0)) or 0.0,
                "ay": _f(d.get("ay", 0)) or 0.0,
                "az": _f(d.get("az", 0)) or 0.0,
                "gx": _f(d.get("gx", 0)) or 0.0,
                "gy": _f(d.get("gy", 0)) or 0.0,
                "gz": _f(d.get("gz", 0)) or 0.0,
                "device": str(d.get("device", "esp32-strokeguard-01")),
                "bpm": _f(d.get("bpm", d.get("hr", 0))),
                "spo2": _f(d.get("spo2", 0)),
                "finger": bool(d.get("finger", False)),
                "roll": _f(d.get("roll", 0)),
                "pitch": _f(d.get("pitch", 0)),
            }
        log(f"[MQTT] JSON thiếu field quen thuộc: {payload[:100]}", flush=True)
        return None
    # CSV 13 fields (protocol cũ)
    parts = payload.split(",")
    if len(parts) != 13:
        log(f"[MQTT] Bỏ qua payload lạ ({len(parts)} fields): {payload[:80]}",
            flush=True)
        return None
    try:
        vals = [float(x) for x in parts]
    except ValueError:
        log(f"[MQTT] CSV không phải số: {payload[:80]}", flush=True)
        return None
    (ts, ir, red, bpm, spo2,
     ax, ay, az, gx, gy, gz, roll, pitch) = vals
    return {
        "ts": ts, "ir": ir, "red": red,
        "ax": ax, "ay": ay, "az": az,
        "gx": gx, "gy": gy, "gz": gz,
        "device": "esp32-csv",
        "bpm": bpm, "spo2": spo2,
        "roll": roll, "pitch": pitch,
    }


class MQTTSubscriber:
    """Subscribe MQTT Cloud, parse payload -> dict -> callback."""

    def __init__(self, on_data, cfg=None, logger=print):
        self.cb = on_data
        self.cfg = cfg or {}
        self.log = logger
        self._client = None
        self._stop = threading.Event()
        self._thread = None
        self.last_message_ts = 0.0      # epoch của message gần nhất (0 = chưa có)
        self.connected = False
        self.last_connect_attempt = 0.0
        self._creds_warned = False
        self.msg_count = 0

    # ------------------------------------------------------------------
    def start(self):
        if not _PAHO_OK:
            self.log("[MQTT] THIẾU thư viện paho-mqtt — cài: "
                     "python3 -m pip install paho-mqtt (hoặc vendor/)", flush=True)
            return False
        if not self.cfg.get("enabled", False):
            self.log("[MQTT] disabled trong config", flush=True)
            return False
        if not creds_ready(self.cfg):
            self.log("[MQTT] Chưa có username/password — điền vào "
                     + _CONFIG_PATH + " rồi restart app", flush=True)
            return False
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="mqtt-sub")
        self._thread.start()
        self.log("[MQTT] Subscriber thread started", flush=True)
        return True

    # ------------------------------------------------------------------
    def _loop(self):
        self._backoff = 5
        while not self._stop.is_set():
            try:
                self._run_once()
            except Exception as e:
                self.log(f"[MQTT] Lỗi: {e}", flush=True)
            # reconnect với backoff 5s → 60s
            for _ in range(min(self._backoff, 60)):
                if self._stop.is_set():
                    return
                time.sleep(1)
            self._backoff = min(self._backoff + 5, 60)

    def _run_once(self):
        self.last_connect_attempt = time.time()
        kwargs = {}
        if hasattr(mqtt, "CallbackAPIVersion"):  # paho-mqtt >= 2.0
            kwargs["callback_api_version"] = mqtt.CallbackAPIVersion.VERSION1
        client = mqtt.Client(client_id=self.cfg.get("client_id", "unoq-strokeguard"),
                             protocol=mqtt.MQTTv311, clean_session=True, **kwargs)
        client.username_pw_set(self.cfg.get("username", ""),
                               self.cfg.get("password", ""))
        if self.cfg.get("tls", True):
            client.tls_set()  # HiveMQ Cloud: CA bundle mặc định hệ thống
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect
        self._client = client
        self.log(f"[MQTT] Đang kết nối {self.cfg.get('broker')}:"
                 f"{self.cfg.get('port')} ...", flush=True)
        client.connect(self.cfg.get("broker"),
                       int(self.cfg.get("port", 8883)),
                       keepalive=30)
        client.loop_forever(retry_first_connection=True)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self._backoff = 5  # reset backoff sau khi nối lại thành công
            topic = self.cfg.get("topic", "strokeguard/#")
            client.subscribe(topic, qos=1)
            self.log(f"[MQTT] ĐÃ KẾT NỐI HiveMQ Cloud — subscribe '{topic}'",
                     flush=True)
        else:
            reasons = {1: "sai username/password (rc=1)",
                       2: "không được phép (rc=2)", 5: "chưa xác thực (rc=5)"}
            self.log(f"[MQTT] Kết nối thất bại rc={rc} "
                     f"({reasons.get(rc, 'xem tài liệu MQTT')})", flush=True)

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            self.log(f"[MQTT] Mất kết nối (rc={rc}) — sẽ tự reconnect", flush=True)
        else:
            # rc=0 = broker/remote đóng kết nối (vd: session takeover, idle kick)
            self.log("[MQTT] Broker đóng kết nối (rc=0) — reconnect...", flush=True)
        try:
            client.reconnect()
        except Exception as e:
            self.log(f"[MQTT] Reconnect thất bại: {e}", flush=True)

    def reconnect_now(self):
        """Chủ động cắt kết nối — vòng _loop sẽ connect lại ngay.
        Dùng khi nghi kết nối/subscription bị 'đóng băng' phía broker
        (kết nối vẫn 'sống' theo TCP nhưng broker không forward msg nữa)."""
        try:
            if self._client is not None:
                self._client.disconnect()
        except Exception:
            pass
        self.connected = False

    # ------------------------------------------------------------------
    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", "replace").strip()
            d = normalize_payload(payload, log=self.log)
            if d is None:
                return
            self.last_message_ts = time.time()
            self.msg_count += 1
            self.cb(d)
        except Exception as e:
            self.log(f"[MQTT] Lỗi xử lý message: {e}", flush=True)

    def active_recently(self, window=5.0):
        """True nếu có message MQTT trong `window` giây."""
        return (self.last_message_ts > 0
                and (time.time() - self.last_message_ts) < window)

    def stop(self):
        self._stop.set()
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass


# singleton cho main.py
mqtt_subscriber = None


def init_mqtt(on_data):
    """Khởi tạo subscriber toàn cục; trả về instance hoặc None."""
    global mqtt_subscriber
    cfg = load_mqtt_config()
    if not cfg or not cfg.get("enabled", False):
        return None
    mqtt_subscriber = MQTTSubscriber(on_data, cfg)
    mqtt_subscriber.start()
    return mqtt_subscriber
