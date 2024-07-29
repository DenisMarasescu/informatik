from typing import Optional, TypedDict


class ProxySettings(TypedDict, total=False):
    server: str
    bypass: Optional[str]
    username: Optional[str]
    password: Optional[str]


class StealthModeConfig(TypedDict):
    vendor: str
    renderer: str
    nav_user_agent: str
