from app.config import logger, settings
from app.db import UserRepo
from app.models.telegram_user import TelegramUserData


def user_role_allowed(telegram_user: TelegramUserData, user_repo: UserRepo) -> bool:
    role = user_repo.upsert_and_get_role(
        telegram_user,
    )
    logger.info("User %s have %s role", telegram_user.username, role)
    return role in settings.allowed_roles
