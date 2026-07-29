from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    """
    Pydantic schema to validate incoming user login credentials.
    """
    email: EmailStr
    password: str

class Token(BaseModel):
    """
    Pydantic schema validating output authentication JWT data structure.
    """
    access_token: str
    token_type: str
