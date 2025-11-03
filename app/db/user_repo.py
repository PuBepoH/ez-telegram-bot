from contextlib import contextmanager
from typing import Iterator, Optional, cast

import psycopg
from psycopg import Connection, Cursor

from app.config import settings
from app.models.telegram_user import TelegramUserData

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
    last_seen_at = NOW(),
    is_active = TRUE
RETURNING role;
"""


class UserRepo:
    conn: Connection

    def __init__(self):
        self.conn: Connection = psycopg.connect(settings.postgres_dsn, autocommit=True)

    @contextmanager
    def _cursor(self) -> Iterator[Cursor]:
        conn = cast(Connection, self.conn)
        cur = conn.cursor()  # pylint: disable=no-member
        try:
            yield cast(Cursor, cur)
        finally:
            cur.close()

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
        with self._cursor() as cur:
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
            return cast(str, row[0] if row else default_role)

    def set_role(self, tg_id: int, role: str) -> None:
        """
        Forcibly set a user's role (e.g. admin promotes someone to 'user').
        Creates the user if missing.
        """
        with self._cursor() as cur:
            cur.execute(
                SET_ROLE_SQL,
                (tg_id, role),
            )

    def get_role(self, tg_id: int) -> Optional[str]:
        with self._cursor() as cur:
            cur.execute(GET_ROLE_SQL, (tg_id,))
            row = cur.fetchone()
            return cast(Optional[str], row[0] if row else None)
