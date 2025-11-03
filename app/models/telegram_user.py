from dataclasses import dataclass
from typing import Optional


@dataclass
class TelegramUserData:
    tg_id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
