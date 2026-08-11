import requests

class WebhookNotifier:
    """Optional caregiver notification. Never required for local AI/alert operation."""
    def __init__(self, url=None, timeout=3):
        self.url=url
        self.timeout=timeout

    def send(self, event):
        if not self.url:
            return False
        try:
            r=requests.post(self.url,json=event,timeout=self.timeout)
            return r.ok
        except requests.RequestException:
            return False
