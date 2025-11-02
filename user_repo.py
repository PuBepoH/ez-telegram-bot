from dataclasses import dataclass
from typing import Optional, cast

import psycopg

from config import POSTGRES_DSN

GET_ROLE_SQL = """
SELECT role
FROM bot.users
WHERE tg_id = %s
  AND is_active = TRUE
LIMIT 1;
"""

SET_ROLE_SQL = """
INSERT INTO bot.users (tg_id, role, username, first_name, last_name, is_active, last_seen_at)
VALUES (%s, %s, NULL, NULL, NULL, TRUE, NOW())
ON CONFLICT (tg_id) DO UPDATE
SET
    role = EXCLUDED.role,
    is_active = TRUE,
    last_seen_at = NOW();
"""

UPSERT_USER_SQL = """
INSERT INTO bot.users (tg_id, role, username, first_name, last_name, last_seen_at)
VALUES (%s, %s, %s, %s, %s, NOW())
ON CONFLICT (tg_id) DO UPDATE
SET
    username = EXCLUDED.username,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    last_seen_at = NOW()
RETURNING role;
"""


@dataclass
class TelegramUserData:
    tg_id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserRepo:
    def __init__(self):
        self.conn = psycopg.connect(POSTGRES_DSN, autocommit=True)

    def upsert_and_get_role(
        self,
        user: TelegramUserData,
        default_role: str = "guest",
    ) -> str:
        """
        Update/create user and return his role
        If user new - we grant him default_role
        Admin is seeded by init_db() and will keep 'admin' role
        """
        with psycopg.connect(POSTGRES_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    UPSERT_USER_SQL,
                    (
                        user.tg_id,
                        default_role,
                        user.username,
                        user.first_name,
                        user.last_name,
                    ),
                )
                row = cur.fetchone()

                if row is not None:
                    role_val: str = cast(str, row[0])
                else:
                    role_val = default_role

        return role_val

    def set_role(self, tg_id: int, role: str) -> None:
        """
        Forcibly set a user's role (e.g. admin promotes someone to 'user').
        Creates the user if missing.
        """
        with psycopg.connect(POSTGRES_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    SET_ROLE_SQL,
                    (tg_id, role),
                )

    def get_role(self, tg_id: int) -> Optional[str]:
        with psycopg.connect(POSTGRES_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(GET_ROLE_SQL, (tg_id,))
                row = cur.fetchone()
                return cast(Optional[str], row[0] if row else None)
