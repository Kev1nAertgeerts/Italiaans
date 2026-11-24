import re
from apps.accounts.models import LoginHistory

_BROWSER_PATTERNS = (
    ("Edg", "Microsoft Edge"),
    ("OPR", "Opera"),
    ("Opera", "Opera"),
    ("Firefox", "Firefox"),
    ("Chrome", "Chrome"),
    ("CriOS", "Chrome"),
    ("FxiOS", "Firefox"),
    ("Safari", "Safari"),
    ("MSIE", "Internet Explorer"),
    ("Trident", "Internet Explorer"),
)

class UserAgentParser:
    def _client_ip(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR") or "127.0.0.1"


    def _match_version(self, user_agent, token):
        match = re.search(rf"{re.escape(token)}[/\s]([\d.]+)", user_agent)
        return match.group(1) if match else ""


    def _parse_browser(self, user_agent):
        for token, name in _BROWSER_PATTERNS:
            if token == "Safari" and any(
                marker in user_agent for marker in ("Chrome", "CriOS", "FxiOS", "Edg", "OPR")
            ):
                continue
            if token not in user_agent:
                continue
            if token == "Safari":
                version = self._match_version(user_agent, "Version") or self._match_version(user_agent, "Safari")
            elif token == "Trident":
                version = self._match_version(user_agent, "rv") or "11"
            else:
                version = self._match_version(user_agent, token)
            return f"{name} {version}".strip()
        return "Unknown"


    def _parse_os(self, user_agent):
        if "Windows NT 10.0" in user_agent:
            return "Windows 10/11"
        if "Windows NT 6.3" in user_agent:
            return "Windows 8.1"
        if "Windows NT 6.2" in user_agent:
            return "Windows 8"
        if "Windows NT 6.1" in user_agent:
            return "Windows 7"
        if "Windows" in user_agent:
            return "Windows"
        if "Android" in user_agent:
            version = self._match_version(user_agent, "Android")
            return f"Android {version}".strip()
        if "iPhone" in user_agent or "iPad" in user_agent:
            match = re.search(r"OS ([\d_]+)", user_agent)
            version = match.group(1).replace("_", ".") if match else ""
            return f"iOS {version}".strip()
        if "Mac OS X" in user_agent:
            match = re.search(r"Mac OS X ([\d_]+)", user_agent)
            version = match.group(1).replace("_", ".") if match else ""
            return f"macOS {version}".strip()
        if "Linux" in user_agent:
            return "Linux"
        return "Unknown"


    def _parse_device(self, user_agent):
        if "iPad" in user_agent or "Tablet" in user_agent or "PlayBook" in user_agent:
            return "Tablet"
        if "Mobi" in user_agent or "iPhone" in user_agent or "Android" in user_agent:
            return "Mobile"
        if user_agent:
            return "Desktop"
        return "Unknown"


    def parse_user_agent(self, user_agent):
        user_agent = user_agent or ""
        return {
            "device": self._parse_device(user_agent),
            "browser": self._parse_browser(user_agent),
            "os": self._parse_os(user_agent),
        }


    def save_login_history(self, request):
        parsed = self.parse_user_agent(request.META.get("HTTP_USER_AGENT"))
        LoginHistory.objects.create(
            user=request.user,
            login_ip=self._client_ip(request),
            login_device=parsed["device"],
            login_location="",
            login_browser=parsed["browser"],
            login_os=parsed["os"],
        )