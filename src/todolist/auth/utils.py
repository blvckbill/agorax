import secrets
import string

from fastapi import BackgroundTasks, status
from fastapi_mail import MessageSchema, FastMail, MessageType
from pydantic import EmailStr

from starlette.responses import JSONResponse

from src.todolist.config import conf

def generate_random_string(length: int):
    """generates a random string of length length"""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


# async def send_mail(
#         email: EmailStr,
#         subject: str,
#         body: str
# ) -> JSONResponse:
#     """function to send email"""

#     message = MessageSchema(
#         subject=subject,
#         recipients=[email],
#         body=body,
#         subtype=MessageType.plain
#     )

#     fm = FastMail(conf)

#     fm.send_message(message)

#     return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "email has been sent"})