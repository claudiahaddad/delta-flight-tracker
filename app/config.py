from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./flights.db"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    notification_email: str = "claudiaa6499@gmail.com"
    from_email: str = ""
    check_interval_minutes: int = 60
    app_name: str = "Delta Flight Tracker"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
