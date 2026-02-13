"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
import asyncio
from datetime import datetime

from obhonesty.pages import * 
from obhonesty.state import State
from obhonesty.sheet import user_sheet, item_sheet, order_sheet, admin_sheet
from obhonesty.models import User as User_Model, Order as Order_Model, Item as Item_Model, Admin as Admin_Model


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
        
def sync_orders():
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
    with rx.session() as session:
        user_data = get_records(user_sheet, [
                'nick_name', 'first_name', 'last_name', 'phone_number', 'email',
                'diet', 'allergies', 'volunteer', 'away', 'owes', "current_guest", "active_tab"
            ], True)

        for user in user_data:
            del user["owes"]
            for key in ["volunteer", "away", "current_guest", "active_tab"]:
                user[key] = user[key].lower() in ["yes", "true"]

            user["phone_number"] = str(user["phone_number"])

        for row in session.exec(User_Model.select()).all():
            session.delete(row)

        session.add_all(
            User_Model.model_validate(user) for user in user_data
            )
        
        session.commit()

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

async def sync_google_sheet_and_local_db():
    while True:
        try:
            sync_orders()
            sync_users()
            sync_items()
            sync_admin_data()
            await asyncio.sleep(20)

        except Exception as e:
            print(e)
            await asyncio.sleep(60)
            
app.register_lifespan_task(sync_google_sheet_and_local_db)