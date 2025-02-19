"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from obhonesty.pages import * 
from obhonesty.state import State

app = rx.App()
app.add_page(index, route="/", on_load=State.reload_sheet_data)
app.add_page(user_page, route="/user", on_load=State.reload_sheet_data)
app.add_page(user_signup_page, route="/signup")
app.add_page(dinner_signup_page, route="/dinner")
app.add_page(breakfast_signup_page, route="/breakfast")
app.add_page(custom_item_page, route="/custom_item")
app.add_page(user_info_page, route="/info", on_load=State.reload_sheet_data)
app.add_page(admin, route="/admin")
app.add_page(admin_dinner, route="/admin/dinner", on_load=State.reload_sheet_data)
app.add_page(admin_breakfast, route="/admin/breakfast", on_load=State.reload_sheet_data)
app.add_page(admin_tax, route="/admin/tax", on_load=State.reload_sheet_data)
app.add_page(admin_user_page, route="/admin/user", on_load=State.reload_sheet_data)
app.add_page(late_dinner_signup_page, route="/admin/late", on_load=State.reload_sheet_data)
