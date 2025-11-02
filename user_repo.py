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
        pass

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

    def get_role(self, tg_id: int) -> Optional[str]:
        with psycopg.connect(POSTGRES_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(GET_ROLE_SQL, (tg_id,))
                row = cur.fetchone()
                return row[0] if row else None
