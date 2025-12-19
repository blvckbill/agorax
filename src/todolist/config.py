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
TODOLIST_JWT_EXP = config("TODOLIST_JWT_EXP", cast=int, default=86400) #seconds



DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL:
    # If Railway gave us a URL, we just use it directly
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
else:
    # Fallback to manual construction
    DATABASE_HOSTNAME = config("DATABASE_HOSTNAME", default="localhost")
    DATABASE_CREDENTIALS = config("DATABASE_CREDENTIALS", cast=Secret, default="user:password")
    DATABASE_NAME = config("DATABASE_NAME", default="todolist")
    DATABASE_PORT = config("DATABASE_PORT", default="5432")

    # Handle special characters
    _user, _password = str(DATABASE_CREDENTIALS).split(":", 1)
    _quoted_password = parse.quote(_password)
    
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{_user}:{_quoted_password}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"

DATABASE_ENGINE_MAX_OVERFLOW = config("DATABASE_ENGINE_MAX_OVERFLOW", cast=int, default=10)
DATABASE_ENGINE_POOL_PING = config("DATABASE_ENGINE_POOL_PING", default=False)
DATABASE_ENGINE_POOL_RECYCLE = config("DATABASE_ENGINE_POOL_RECYCLE", cast=int, default=1800)
DATABASE_ENGINE_POOL_SIZE = config("DATABASE_ENGINE_POOL_SIZE", cast=int, default=5)
DATABASE_ENGINE_POOL_TIMEOUT = config("DATABASE_ENGINE_POOL_TIMEOUT", cast=int, default=10)

"otp"
# OTP_EXPIRY_TIME = config("OTP_EXPIRY_TIME")

#email config

# conf = ConnectionConfig(
#     MAIL_USERNAME = config("EMAIL_HOST_USER"),
#     MAIL_PASSWORD = config("EMAIL_HOST_PASSWORD"),
#     MAIL_FROM = config("EMAIL_HOST_USER"),
#     MAIL_PORT = config("EMAIL_PORT"),
#     MAIL_SERVER = config("EMAIL_HOST"),
#     MAIL_STARTTLS = True,
#     MAIL_SSL_TLS = False,
# )

# static files
DEFAULT_STATIC_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), os.path.join("static", "dispatch", "dist")
)
STATIC_DIR = config("STATIC_DIR", default=DEFAULT_STATIC_DIR)

# ai
GOOGLE_API_KEY = config("GOOGLE_API_KEY", default=None)

#rabbit
RABBIT_URL = config("RABBITMQ_URL", default=None) 
if not RABBIT_URL:
    RABBITMQ_USER = config("RABBITMQ_USER", default="guest")
    RABBITMQ_PASSWORD = config("RABBITMQ_PASSWORD", default="guest")
    RABBITMQ_HOST = config("RABBITMQ_HOST", default="localhost")
    RABBITMQ_PORT = config("RABBITMQ_PORT", default="5672")
    
    RABBIT_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"

#redis
REDIS_URL = config("REDIS_URL", default=None)
if REDIS_URL:
    from urllib.parse import urlparse
    _parsed = urlparse(REDIS_URL)
    REDIS_HOST = _parsed.hostname
    REDIS_PORT = _parsed.port
else:
    REDIS_HOST = config("REDIS_HOST", default="localhost")
    REDIS_PORT = config("REDIS_PORT", default="6379")