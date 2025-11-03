from typing import Dict

from telegram import Update

from app.models.telegram_user import TelegramUserData


class UserCache:
    """
    In-memory cache for Telegram users during bot runtime
    """

    def __init__(self) -> None:
        self._by_id: Dict[int, TelegramUserData] = {}

    def get_or_create(self, update: Update) -> TelegramUserData:
        """
        Get user from memory cache or create if not presented
        """
        tg_user = update.effective_user
        tg_id = tg_user.id

        cached_user = self._by_id.get(tg_id)
        # if user already presented in telegram_users_by_tg_id => update data and return
        if cached_user:
            cached_user.username = tg_user.username or f"user_{tg_id}"
            cached_user.first_name = tg_user.first_name
            cached_user.last_name = tg_user.last_name
            return cached_user

        # if user is not presented in telegram_users_by_tg_id => create new record
        new_user = TelegramUserData(
            tg_id=tg_id,
            username=tg_user.username or f"user_{tg_id}",
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        self._by_id[tg_id] = new_user
        return new_user

    def clear(self) -> None:
        """
        Completely clear user cache
        """
        self._by_id.clear()
