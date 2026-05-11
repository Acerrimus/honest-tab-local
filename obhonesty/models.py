import reflex as rx
from datetime import datetime, timedelta
from sqlalchemy import select, func
from obhonesty.aux import get_madrid_datetime_now

# These classes specify the table info for the SQL database, storing google sheets data offline.
# They must be updated if any new columns are added.

# synced is a prop only in the postgres db.


class User(rx.Model, table=True):
    nick_name: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    volunteer: bool
    away: bool
    diet: str
    allergies: str
    synced: bool
    # these must default to False otherwise the app crashes on startup
    current_guest: bool = False
    active_tab: bool = True
    prepaid_dinners_quantity: int = 0

    @classmethod
    def select_users_with_an_active_tab(cls):
        return select(cls).where(cls.active_tab == True)


class Order(rx.Model, table=True):
    order_id: str
    user_nick_name: str
    time: str
    item: str
    quantity: float
    price: float
    total: float
    receiver: str
    diet: str
    allergies: str
    served: str
    tax_category: str
    comment: str
    synced: bool


class Payment(rx.Model, table=True):
    payment_id: str
    order_id: str
    paid_time: str
    method: str
    checkout_staff: str
    is_synced: bool = False


class Stripe_Checkout_Session(rx.Model, table=True):
    payment_order_id: str
    datetime_requested: str
    stripe_payment_id: str
    ob_payment_id: str
    order_id: str
    user: str
    synced: bool
    system_provider_handling_fee_amount: float
    item: str
    quantity: float
    price: float
    total: str


class Item(rx.Model, table=True):
    name: str
    price: float
    description: str
    tax_category: str


class Admin(rx.Model, table=True):
    key: str
    value: str


class Meal(rx.Model, table=True):
    meal_id: str
    order_id: str
    user_nick_name: str
    receiver: str
    order_time: datetime
    meal_type: str
    diet: str
    allergies: str
    volunteer: bool
    served: bool

    @classmethod
    def select_todays_meals(cls, meal_type: str | None = None):
        now = get_madrid_datetime_now()
        today = now.date()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)

        return (
            select(cls).where(
                cls.meal_type == meal_type,
                cls.order_time >= start,
                cls.order_time < end,
            )
            if meal_type is not None
            else select(cls).where(cls.order_time >= start, cls.order_time < end)
        ).order_by(cls.order_time, cls.receiver)

    @classmethod
    def select_todays_breakfast_meals(cls):
        return cls.select_todays_meals("breakfast")

    @classmethod
    def select_todays_dinner_meals(cls):
        return cls.select_todays_meals("dinner")

    @classmethod
    def get_todays_meal_counts(cls):
        start = datetime.combine(get_madrid_datetime_now().date(), datetime.min.time())
        end = start + timedelta(days=1)
        query_args = [
            cls.volunteer,
            cls.meal_type,
            cls.diet,
            cls.served,
        ]
        counts = (
            rx.session()
            .query(*query_args, func.count())
            .filter(cls.order_time >= start, cls.order_time < end)
            .group_by(*query_args)
            .all()
        )
        totals = {
            "breakfast": {key: 0 for key in ["total", "served"]},
            "dinner": {
                user_type: {"meat": 0, "vegetarian": 0, "vegan": 0, "served": 0}
                for user_type in ["guest", "volunteer"]
            },
        }

        for count in counts:
            if "breakfast" in count:
                totals["breakfast"]["total"] += count[4]

                if count[3]:
                    totals["breakfast"]["served"] += count[4]

                continue

            user_type = "volunteer" if count[0] else "guest"
            totals["dinner"][user_type][count[2].lower()] += count[4]

            if count[3]:
                totals["dinner"][user_type]["served"] += count[4]

        return totals
