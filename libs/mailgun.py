from typing import List
from requests import Response, post
import os 

FAILED_LOAD_API_KEY="Failed to load MailGUN API key."
FAILED_LOAD_DOMAIN="Failed to load MAILGUN domain."
ERROR_SENDING_EMAIL="Error in sending confirmation email, user registration failed"


class MailGunException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Mailgun:
    MAILGUN_DOMAIN=os.environ.get("MAILGUN_DOMAIN") # can be none
    MAILGUN_API_KEY=os.environ.get("MAILGUN_API_KEY") # can be none
    
    FROM_TITLE="Store Rest API"
    FROM_EMAIL="eunbi1.yoon@lge.com"

    # list string -> too send multiple receiver
    @classmethod
    def send_confirmation_email(cls, email: List[str], subject: str, text: str, html: str) -> Response:
        # send the request mailgun api with post request
        if cls.MAILGUN_API_KEY is None:
            raise MailGunException(FAILED_LOAD_API_KEY)

        if cls.MAILGUN_DOMAIN is None:
            raise MailGunException(FAILED_LOAD_DOMAIN)

        response= post(
            f"http://api.mailgun.net/v3/{cls.MAILGUN_DOMAIN}/messages",
            auth=("api", cls.MAILGUN_API_KEY),
            data={
                "from":f"{cls.FROM_TITLE} <{cls.FROM_EMAIL}>",
                "to": email,
                "subject":subject,
                "text":text,
                "html":html,
            }
            )
        
        if response.status_code!=200:
            raise MailGunException(ERROR_SENDING_EMAIL)
        
        return response