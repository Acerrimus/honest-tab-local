import time
import reflex as rx
from fastapi import FastAPI, status
from obhonesty.models import User

fastapi_app = FastAPI(title="Honesty Bar API")


@fastapi_app.post("/api/test/user", status_code=status.HTTP_201_CREATED)
async def create_test_user():
    username = f"CypressUser{int(time.time() * 1000)}"
    with rx.session() as session:
        session.add(
            User.model_validate(
                {
                    "nick_name": username,
                    "first_name": username,
                    "last_name": "Test",
                    "phone_number": "0123456789",
                    "email": "test@test.com",
                    "diet": "Vegan",
                    "allergies": "Nuts",
                    "current_guest": "Yes",
                    "synced": False,
                    "volunteer": False,
                    "away": False,
                }
            )
        )
        session.commit()
    return {"username": username, "message": "Test user created successfully"}
