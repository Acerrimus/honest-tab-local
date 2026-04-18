from datetime import datetime

import reflex as rx
from fastapi import FastAPI, status
from obhonesty.models import User, Order, Stripe_Checkout_Session, Payment, Meal
from obhonesty.aux import short_uid

fastapi_app = FastAPI(title="Honesty Bar API")


@fastapi_app.post("/api/test/user", status_code=status.HTTP_201_CREATED)
async def create_test_user(username: str, volunteer: str = ""):
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
                    "volunteer": len(volunteer) > 0,
                    "away": False,
                }
            )
        )
        session.commit()

    return {"username": username, "message": "Test user created successfully"}


@fastapi_app.post("/api/test/orders", status_code=status.HTTP_201_CREATED)
async def create_test_order(
    order_id: str,
    user_nick_name: str,
    time: str,
    item: str,
    quantity: float,
    price: float,
    total: float,
    receiver: str,
    diet: str,
    allergies: str,
    served: str,
    tax_category: str,
    comment: str,
):
    with rx.session() as session:
        session.add(
            Order(
                order_id=order_id,
                user_nick_name=user_nick_name,
                time=time,
                item=item,
                quantity=quantity,
                price=price,
                total=total,
                receiver=receiver,
                diet=diet,
                allergies=allergies,
                served=served,
                tax_category=tax_category,
                comment=comment,
                synced=False,
            )
        )
        session.commit()

    return {"order_id": order_id, "message": "Test order created successfully"}


@fastapi_app.get("/api/test/orders")
async def get_test_orders(username: str):
    with rx.session() as session:
        orders = session.query(Order).filter(Order.user_nick_name == username).all()
        return {"orders": [order.model_dump() for order in orders]}


@fastapi_app.get("/api/test/stripe-checkout-sessions")
async def get_stripe_checkout_sessions(username: str):
    with rx.session() as session:
        checkout_sessions = (
            session.query(Stripe_Checkout_Session)
            .filter(Stripe_Checkout_Session.user == username)
            .all()
        )

        return {
            "checkout_sessions": [
                checkout_session.model_dump() for checkout_session in checkout_sessions
            ]
        }


@fastapi_app.get("/api/test/payments")
async def get_payment(order_id: str):
    with rx.session() as session:
        payment = session.query(Payment).filter(Payment.order_id == order_id).first()

    return {"payment": payment.model_dump() if payment else "None found"}


@fastapi_app.get("/api/test/meals/dinner/today")
async def get_todays_dinner_meals():
    with rx.session() as session:
        todays_dinner_meals = (
            session.execute(Meal.select_todays_dinner_meals()).scalars().all()
        )

        return {"meals": [row.model_dump() for row in todays_dinner_meals]}


@fastapi_app.post("/api/test/meals/dinner/today", status_code=status.HTTP_201_CREATED)
async def create_dinner_meal_for_today(username: str, receiver: str):
    meal_id = str(short_uid())
    with rx.session() as session:
        session.add(
            Meal(
                meal_id=meal_id,
                order_id=str(short_uid()),
                user_nick_name=username,
                receiver=receiver,
                order_time=datetime.now(),
                meal_type="dinner",
                diet="Meat",
                allergies="",
                volunteer=False,
                served=False,
            )
        )
        session.commit()

    return {"meal_id": meal_id, "message": "Test meal created successfully"}
