from app.db import UserRepo, init_db
from app.services import TelegramApp, UserCache, ask_gpt


def main():
    # database init
    init_db()

    TelegramApp().with_dependencies(
        user_repo=UserRepo(),
        ask_gpt=ask_gpt,
        user_cache=UserCache(),
    ).register().run()


if __name__ == "__main__":
    main()
