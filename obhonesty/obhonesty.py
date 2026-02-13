"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from sqlalchemy import select
import asyncio
from datetime import datetime, timedelta

from obhonesty.pages import * 
from obhonesty.state import State
from obhonesty.sheet import user_sheet, item_sheet, order_sheet, admin_sheet
from obhonesty.models import User as User_Model, Order as Order_Model, Item as Item_Model, Admin as Admin_Model, Meal as Meal_Model
from obhonesty.aux import check_internet_connection, get_model_string_type_columns, sanitise_record_strings, short_uid, generate_receiver_from_names
from obhonesty.constants import DATETIME_FORMAT

app = rx.App()
app.add_page(index, route="/", on_load=[State.clear_temp_state_values, State.reload_sheet_data])
app.add_page(user_page, route="/user", on_load=[State.clear_temp_state_values, State.on_user_login, State.reload_sheet_data])
app.add_page(user_signup_page, route="/signup", on_load=State.cancel_timeout)
app.add_page(dinner_signup_page, route="/dinner", on_load=State.cancel_timeout)
app.add_page(breakfast_signup_page, route="/breakfast", on_load=State.cancel_timeout)
app.add_page(custom_item_page, route="/custom_item", on_load=State.cancel_timeout)
app.add_page(user_info_page, route="/info", on_load=State.reload_sheet_data)
app.add_page(admin, route="/admin", on_load=[State.clear_temp_state_values, State.reload_sheet_data])
app.add_page(admin_dinner, route="/admin/dinner", on_load=State.reload_sheet_data)
app.add_page(admin_breakfast, route="/admin/breakfast", on_load=State.reload_sheet_data)
app.add_page(admin_tax, route="/admin/tax", on_load=State.reload_sheet_data)
app.add_page(admin_user_page, route="/admin/user", on_load=State.reload_sheet_data)
app.add_page(late_dinner_signup_page, route="/admin/late", on_load=State.reload_sheet_data)

def get_records(sheet, headers: list[str] = [], add_synced: bool = False):
    check_internet_connection()

    if sheet is None:
        return []
    
    records = sheet.get_all_records(expected_headers=headers)

    for record in records:
        if "" in record:
            del record[""]

    if not add_synced:
        return records
    
    return [{**record, "synced": True} for record in records]

def sync_new_orders(unsynced_orders):
    new_rows = []
    for order in unsynced_orders:
        new_rows.append([
            order.order_id,
            order.user_nick_name,
            order.time,
            order.item,
            order.quantity,
            order.price,
            order.total,
            order.receiver,
            order.diet,
            order.allergies,
            order.served,
            order.tax_category,
            order.comment,
            order.paid == 1,
            order.paid_time,
            order.method, 
            order.checkout_staff
            ])
    order_sheet.append_rows(new_rows, value_input_option="USER_ENTERED", table_range="A1")

def sync_new_users(unsynced_users):
    new_rows = []
    for user in unsynced_users:
        new_rows.append([
            user.nick_name,
            user.first_name,
            user.last_name,
            user.phone_number,
            user.email,
            user.diet,
            user.allergies,
            user.volunteer,
            user.away,
            "",
            user.current_guest,
            user.active_tab,
            ])
    user_sheet.append_rows(new_rows, value_input_option="USER_ENTERED", table_range="A1")
        

def sync_orders():
    order_string_columns = get_model_string_type_columns(Order_Model)

    with rx.session() as session:
        order_data = get_records(order_sheet, [
            'order_id', 'user', 'time', 'item', 'quantity', 'price', 'total',
            'diet', 'allergies', 'served', 'tax_category', 'comment', 'paid',
            'paid_time', 'method', 'checkout_staff'
        ], True)
        current_unsynced_orders = session.query(Order_Model).filter(~Order_Model.synced).all()

        if not len(current_unsynced_orders):
            for order in order_data:
                order["user_nick_name"] = order["user"]
                del order["user"]
                sanitise_record_strings(order_string_columns, order)

            for row in session.exec(Order_Model.select()).all():
                session.delete(row)

            session.add_all(
                Order_Model.model_validate(order) for order in order_data
            )

        google_sheet_order_ids = [order["order_id"] for order in order_data]
        remaining_unsynced_orders = []

        for order in current_unsynced_orders:
            if order.order_id in google_sheet_order_ids:
                order.synced = True
                continue
            
            remaining_unsynced_orders.append(order)

        if len(session.new) or len(session.dirty):
            session.commit()

        if len(remaining_unsynced_orders):
            sync_new_orders(remaining_unsynced_orders)

def sync_users():
    user_string_columns = get_model_string_type_columns(User_Model)

    with rx.session() as session:
        user_data = get_records(user_sheet, [
                'nick_name', 'first_name', 'last_name', 'phone_number', 'email',
                'diet', 'allergies', 'volunteer', 'away', 'owes', "current_guest", "active_tab"
            ], True)
        current_unsynced_users = session.query(User_Model).filter(~User_Model.synced).all()

        if not len(current_unsynced_users):
            for user in user_data:
                del user["owes"]
                for key in ["volunteer", "away", "current_guest", "active_tab"]:
                    user[key] = user[key].lower() in ["yes", "true"]

                user = sanitise_record_strings(user_string_columns, user)

            for row in session.exec(User_Model.select()).all():
                session.delete(row)

            session.add_all(
                User_Model.model_validate(user) for user in user_data
            )

        google_sheet_user_nick_names = [user["nick_name"] for user in user_data]
        remaining_unsynced_users = []

        for user in current_unsynced_users:
            if user.nick_name in google_sheet_user_nick_names:
                user.synced = True
                continue
            
            remaining_unsynced_users.append(user)

        if len(session.new) or len(session.dirty):
            session.commit()

        if len(remaining_unsynced_users):
            sync_new_users(remaining_unsynced_users)

def sync_items():
    with rx.session() as session:
        item_data = get_records(item_sheet, [
            'name', 'price', 'description', 'tax_category'
        ])

        for row in session.exec(Item_Model.select()).all():
            session.delete(row)

        session.add_all(
            Item_Model.model_validate(item) for item in item_data
        )

        session.commit()

def sync_admin_data():
    with rx.session() as session:
        admin_data = get_records(admin_sheet)[0]

        for row in session.exec(Admin_Model.select()).all():
            session.delete(row)

        session.add_all(
            Admin_Model.model_validate({"key": key, "value": str(admin_data[key])}) for key in admin_data
        )

        session.commit()


def update_meals_table_for_todays_dinner():
    with rx.session() as session:
        volunteers: list[User_Model] = session.exec(
            select(User_Model).where(User_Model.volunteer == True)
            ).scalars().all()
        orders = session.exec(Order_Model.select()).all()
        now = datetime.now()
        dinner_meals_today = session.execute(Meal_Model.select_todays_dinner_meals()).scalars().all()
        dinner_orders_today = list(filter(lambda order: order.item == "Dinner sign-up" and datetime.strptime(order.time, DATETIME_FORMAT).date() == now.date(), orders))
        dinner_orders_today_as_receivers = list(map(lambda order: order.receiver, dinner_orders_today))
        # remove guest meals from today's dinner meals if they've been removed from orders
        for meal in dinner_meals_today:
            if meal.receiver in dinner_orders_today_as_receivers or meal.volunteer:
                continue

            session.delete(meal)
                
        dinner_meals_today_as_receivers = list(map(lambda meal: meal.receiver, dinner_meals_today))

        # add volunteers to today's dinner meals if not already added
        for volunteer in volunteers:
            volunteer_receiver_name = generate_receiver_from_names(volunteer.first_name, volunteer.last_name)

            if volunteer_receiver_name in dinner_meals_today_as_receivers:
                continue
            
            session.add(
                Meal_Model(
                    meal_id=str(short_uid()),
                    order_id="N/A",
                    user_nick_name=volunteer.nick_name,
                    receiver=volunteer_receiver_name,
                    order_time=now,
                    meal_type="dinner",
                    diet=volunteer.diet,
                    allergies=volunteer.allergies,
                    volunteer=True,
                    served=False
                )
            )

        # add new orders to today's dinner meals if not already added
        for order in dinner_orders_today:
            if order.receiver in dinner_meals_today_as_receivers:
                continue
            
            session.add(
                Meal_Model(
                    meal_id=str(short_uid()),
                    order_id=order.order_id,
                    user_nick_name=order.user_nick_name,
                    receiver=order.receiver,
                    order_time=datetime.strptime(order.time, DATETIME_FORMAT),
                    meal_type="dinner",
                    diet=volunteer.diet,
                    allergies=volunteer.allergies,
                    volunteer=False,
                    served=False
                    )
                )
            
        if len(session.new) or len(session.dirty) or len(session.deleted):
            session.commit()

async def sync_google_sheet_and_local_db():
    sync_orders()
    await asyncio.sleep(1)
    sync_users()
    await asyncio.sleep(1)
    sync_items()
    await asyncio.sleep(1)
    sync_admin_data()

async def run_loop_tasks():
    while True:
        try:
            update_meals_table_for_todays_dinner()
            await sync_google_sheet_and_local_db()

        except Exception as e:
            print(e)
        
        await asyncio.sleep(5)
            
app.register_lifespan_task(run_loop_tasks)