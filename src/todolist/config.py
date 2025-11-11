import os

from fastapi_mail import ConnectionConfig

from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret
from urllib import parse

BASE_DIR = Path(__file__).resolve().parent.parent 
ROOT_DIR = BASE_DIR.parent 
config = Config(ROOT_DIR / ".env")

#jwt
TODOLIST_JWT_SECRET = config("TODOLIST_JWT_SECRET", default=None)
TODOLIST_JWT_ALG = config("TODOLIST_JWT_ALG", default="HS256")
TODOLIST_JWT_EXP = config("TODLIST_JWT_EXP", cast=int, default=86400) #seconds



#database
DATABASE_HOSTNAME = config("DATABASE_HOSTNAME")
DATABASE_CREDENTIALS = config("DATABASE_CREDENTIALS", cast=Secret)
#handle special characters in credentials
_DATABASE_CREDENTIAL_USER, _DATABASE_CREDENTIAL_PASSWORD = str(DATABASE_CREDENTIALS).split(":")
_QUOTED_DATABASE_PASSWORD = parse.quote(str(_DATABASE_CREDENTIAL_PASSWORD))
DATABASE_NAME = config("DATABASE_NAME", default="todolist")
DATABASE_PORT = config("DATABASE_PORT", default="5432")
DATABASE_ENGINE_MAX_OVERFLOW = config("DATABASE_ENGINE_MAX_OVERFLOW", cast=int, default=10)
# Deal with DB disconnects
DATABASE_ENGINE_POOL_PING = config("DATABASE_ENGINE_POOL_PING", default=False)
DATABASE_ENGINE_POOL_RECYCLE = config("DATABASE_ENGINE_POOL_RECYCLE", cast=int, default=1800)
DATABASE_ENGINE_POOL_SIZE = config("DATABASE_ENGINE_POOL_SIZE", cast=int, default=5)
DATABASE_ENGINE_POOL_TIMEOUT = config("DATABASE_ENGINE_POOL_TIMEOUT", cast=int, default=10)
SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{_DATABASE_CREDENTIAL_USER}:{_QUOTED_DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"

"otp"
OTP_EXPIRY_TIME = config("OTP_EXPIRY_TIME")

#email config

conf = ConnectionConfig(
    MAIL_USERNAME = config("EMAIL_HOST_USER"),
    MAIL_PASSWORD = config("EMAIL_HOST_PASSWORD"),
    MAIL_FROM = config("EMAIL_HOST_USER"),
    MAIL_PORT = config("EMAIL_PORT"),
    MAIL_SERVER = config("EMAIL_HOST"),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
)

# static files
DEFAULT_STATIC_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), os.path.join("static", "dispatch", "dist")
)
STATIC_DIR = config("STATIC_DIR", default=DEFAULT_STATIC_DIR)

# ai
HF_API_TOKEN = config("HF_API_TOKEN")
HF_MODEL = config("HF_MODEL")
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"