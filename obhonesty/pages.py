import os
from typing import Callable

import reflex as rx

from obhonesty.aux import two_decimal_points
from obhonesty.constants import *
from obhonesty.item import Item
from obhonesty.order import Order
from obhonesty.state import State
from obhonesty.user import User



def index() -> rx.Component:
    # Welcome Page (Index)
    user_button: Callable[[User], rx.Component] = lambda user: \
        rx.button(
            rx.text(user.nick_name, size=default_button_text_size),
            on_click=State.redirect_to_user_page(user),
            size=default_button_size
        )
    return rx.container(
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.text("Welcome to the", size='3'),
                    justify="center", width="100%",
                ),
                rx.hstack(
                    rx.heading(
                        "Olive Branch honest self-service",
                        size=default_heading_size
                    ),
                    justify="center", width="100%"
                ),
                rx.hstack(
                    rx.text("New here?", size="3"),
                    rx.button(
                        rx.icon("user-plus"),
                        rx.text("Sign up for self-service", size=default_button_text_size),
                        color_scheme="green",
                        on_click=rx.redirect("/signup"),
                        size="3"
                    ),
                    align="center",
                    justify="center",
                    width="100%",
                ),
                rx.scroll_area(
                    rx.flex(
                        rx.foreach(State.users, user_button),
                        padding="8px",
                        spacing="4",
                        style={"width": "max"},
                        wrap="wrap"
                    ),
                    type="always",
                    scrollbars="vertical",
                    style={"height": "80vh"}
                )
            ),
            align="center"
        )
    )


def logout_button() -> rx.Component:
    return rx.button(
        rx.icon("door-open"),
        rx.text("Log out", size=default_button_text_size),
        color_scheme="red",
        on_click=rx.redirect("/"),
        size=default_button_size
    ),


def error_page() -> rx.Component:
    return rx.vstack(
        rx.text(
            "An error occurred, please press the button below.",
            size=default_text_size
        ),
        rx.button(
            rx.icon("door-open"),
            "Return",
            on_click=rx.redirect("/"),
            size=default_button_size
        )
    )


def payment_dialog() -> rx.Component:
    return rx.dialog.root(
        # The Button that opens the modal
        rx.dialog.trigger(
            rx.button(
                rx.icon("credit-card"),
                rx.text("Pay Now", size=default_button_text_size),
                color_scheme="green",
                size='2', # Matches size in item_button
                type="button", # Prevents form submission
                # Only generate the QR when they actually open the dialog
                on_click=State.generate_payment_qr 
            )
        ),
        # The Modal Content
        rx.dialog.content(
            rx.dialog.title("Scan to Pay"),
            rx.dialog.description("Use your phone camera to scan and pay via Bizum, Apple Pay, or Card."),
            
            rx.center(
                rx.vstack(
                    # Show spinner while talking to Stripe (or generating fake QR)
                    rx.cond(
                        State.is_generating_payment,
                        rx.spinner(size="3"),
                    ),
                    # Show QR Code when ready
                    rx.cond(
                        State.payment_qr_code != "",
                        rx.image(
                            src=State.payment_qr_code, 
                            width="250px", 
                            height="250px",
                            border="1px solid #ddd"
                        ),
                    ),
                    rx.text(f"Total Due: €{two_decimal_points(State.get_user_debt)}", weight="bold"),
                    spacing="4"
                )
            ),
            
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Done / Close", 
                        on_click=State.close_payment_dialog,
                        size=default_button_size
                    )
                ),
                justify="end",
                margin_top="20px"
            ),
        ),
    )

def stripe_payment_dialog(name, amount) -> rx.Component:
  return rx.dialog.content(
      rx.dialog.title(f"Pay for {name}"),
      rx.center(
          rx.vstack(
              rx.cond(
                State.is_stripe_session_paid,
                rx.vstack(
                    rx.text("Paid! Thank you.", weight="bold"),
                    rx.text("Press close below to finish.")
                ),
                rx.vstack(
                    rx.cond(
                        State.payment_qr_code != "",
                        rx.image(
                            src=State.payment_qr_code, 
                            width="250px", 
                            height="250px",
                            border="1px solid #ddd"
                        ),
                        rx.spinner(size="3"),
                    ),
                    rx.text(f"Scan to pay via Stripe"),
                    rx.text("Total: €", two_decimal_points(amount), weight="bold"),
                    spacing="4"
                ),
              ),
          rx.cond(
              ~State.is_stripe_session_paid,
              rx.text("Having issues paying? Please close and contact reception.", size=default_text_size),
          ),
          rx.cond(            
              ~State.is_stripe_session_paid,
              rx.button("Back", on_click=State.close_item_dialog)
          ),
          rx.dialog.close(
              rx.button("Close", on_click=State.close_item_dialog)
          )
      ),
      justify="end",
      margin_top="20px"
      ),
      on_interact_outside=rx.prevent_default,
      on_escape_key_down=rx.prevent_default,
  )

def item_button(item: Item) -> rx.Component:
  title: str = f"{item.name} (€{two_decimal_points(item.price)})"
  return rx.dialog.root(
      rx.dialog.trigger(rx.button(
          rx.text(title, size=default_button_text_size),
          color_scheme="blue",
          size=default_button_size,
          # Reset temp quantity to 1 every time we open a fresh dialog
          on_click=lambda: State.open_item_dialog(item.name)
      )),
      rx.cond(
          State.is_stripe_dialog_active,
          stripe_payment_dialog(item.name, item.price * State.temp_quantity),
      rx.dialog.content(
          rx.dialog.title(title),
          rx.dialog.description(item.description),
          rx.vstack(
              rx.form(
                  rx.flex(
                      rx.input(
                          name="item_name",
                          type="hidden",
                          value=item.name
                      ),
                      rx.input(
                          placeholder="Quantity",
                          name="quantity",
                          default_value='1',
                          type="number",
                          # --- Track input in real-time ---
                          on_change=State.set_temp_quantity 
                      )
                  ),
                  rx.text("Total: €", State.temp_quantity * item.price, weight="bold"),
                  rx.flex(
                      # We use the payment_dialog logic but trigger it differently
                      rx.button(
                          rx.icon("credit-card"),
                          rx.text("Pay Now", size=default_button_text_size),
                          color_scheme="green",
                          size='2',
                          type="button",
                          # Pass specific item details to backend
                          on_click=lambda: State.show_stripe_item_payment_dialog(item.name, item.price * State.temp_quantity)
                      ),
                      rx.dialog.close(
                          rx.button("Register (Tab)", size=default_button_size, on_click=[State.order_item, State.close_item_dialog])
                      ),
                      rx.dialog.close(
                          rx.button(f"Cancel", on_click=State.close_item_dialog)
                      ),
                      spacing="3",
                      justify="end",
                      margin_top="10px"
                  ),
              ), 
              spacing="3"
          ),
      )),
      )

def user_page() -> rx.Component:
  return rx.container(rx.center(
        rx.cond(
            State.no_user,
            error_page(),
            rx.vstack(
                rx.heading(
                    f"Hello {State.current_user.nick_name}", size=default_heading_size
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("list"),
                        rx.text("View orders", size=default_button_text_size),
                        on_click=rx.redirect("/info"),
                        color_scheme="green",
                        size=default_button_size
                    ),
                    logout_button(),
                    rx.text(
                        "(please log out when you're done)",
                        size=default_text_size
                    ),
                    align="center"
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("egg-fried"),
                        rx.text(
                            "Sign up for breakfast / packed lunch",
                            size=default_button_text_size
                        ),
                        on_click=rx.redirect("/breakfast"),
                        size=default_button_size,
                        disabled=~State.breakfast_signup_available,
                    ),
                    rx.text(
                        f"(last sign-up at {State.admin_data['breakfast_signup_deadline']})",
                        size=default_text_size
                    ),
                    align="center"
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("utensils"),
                        rx.text("Sign up for dinner", size=default_button_text_size),
                        on_click=rx.redirect("/dinner"),
                        size=default_button_size,
                        disabled=~State.dinner_signup_available
                    ),
                    rx.text(
                        f"(last sign-up at {State.admin_data['dinner_signup_deadline']}, "
                        f"for late sign-ups, please ask the kitchen staff)",
                        size=default_text_size
                    ),
                    align="center"
                ),
                rx.hstack(
                    rx.button(
                        rx.icon("euro"),
                        rx.text("Pay tab", size=default_button_text_size),
                        on_click=rx.redirect("/info"),
                        size=default_button_size,
                        color_scheme="yellow"
                    ),
                    rx.text(
                        f"Pay your tab securely via Stripe.",
                        size=default_text_size
                    ),
                    align="center"
                ),
                rx.text("Register an item", weight="bold", size=default_text_size), 
                rx.scroll_area(
                    rx.flex(
                        rx.foreach(State.items.values(), item_button),
                        padding="8px",
                        spacing="4",
                        style={"width": "max"},
                        wrap="wrap"
                    ),
                    type="always",
                    scrollbars="vertical",
                    style={"height": "60vh"}
                ),
                rx.hstack(
                    rx.text("Didn't find the item? No problem, just", size=default_text_size),
                    rx.button(
                        rx.icon("circle-plus"),
                        rx.text("Register manually", size=default_button_text_size),
                        color_scheme="sky",
                        on_click=rx.redirect("/custom_item"),
                        size=default_button_size
                    ),
                    align="center"
                )
            )
        )))


def custom_item_page() -> rx.Component:
    return rx.container(rx.center(rx.vstack(
        rx.heading("Register custom item", size=default_heading_size),
        rx.form(
            rx.vstack(
                rx.text("Name"),
                rx.input(placeholder="What did you get?", name="custom_item_name"),
                rx.text("Price"),
                rx.form.field(
                    rx.form.control(
                        rx.input(
                            placeholder="E.g. 2.50 for (2.50€)",
                            name="custom_item_price",
                            on_change=State.set_custom_item_price
                        ),
                        as_child=True
                    ),
                    rx.form.message(
                        "Please enter a valid price",
                        match="valueMissing",
                        force_match=State.invalid_custom_item_price,
                        color="var(--red-11)"
                    )
                ),
                rx.text("Category"),
                rx.select(
                    [str(x) for x in TaxCategory],
                    default_value=TaxCategory.NON_ALCOHOLIC,
                    name="tax_category",
                    required=True
                ),
                rx.text("Comment"),
                rx.input(placeholder="optional", name="custom_item_description"),
                rx.button(
                    rx.text("Register", size=default_button_text_size), type="submit",
                    size=default_button_size
                )
            ),
            on_submit=State.order_custom_item
        ),
        rx.button(
            rx.text("Cancel", size=default_button_text_size),
            on_click=rx.redirect("/user"),
            size=default_button_size
        )
    )))

message_name_already_taken: str = "Already taken"

def user_signup_page() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.heading("Welcome to the Olive Branch", size=default_heading_size),
                rx.text("Please fill in your details to get started with self-service"),
                rx.form(
                    rx.vstack(
                        rx.text("User name", weight="medium"),
                        rx.form.field(
                            rx.form.control(
                                rx.input(
                                    placeholder="E.g. 'Bob' (required)",
                                    on_change=State.set_new_nick_name,
                                    name="nick_name",
                                    required=True,
                                    width="200%"
                                ),
                                as_child=True
                            ),
                            rx.form.message(
                                message_name_already_taken,
                                match="valueMissing",
                                force_match=State.invalid_new_user_name,
                                color="var(--red-11)"
                            )
                        ),
                        rx.text("First name", weight="medium"),
                        rx.input(
                            placeholder="E.g. 'Robert' (required)",
                            name="first_name",
                            required=True,
                            width="100%"
                        ),
                        rx.text("Last name", weight="medium"),
                        rx.input(
                            placeholder="E.g. 'Robertson' (required)",
                            name="last_name",
                            required=True,
                            width="100%"
                        ),
                        rx.text("Phone number", weight="medium"),
                        rx.input(
                            placeholder="E.g. '+45 12345666' (required)",
                            name="phone_number",
                            required=True,
                            width="100%"
                        ),
                        rx.text("Email", weight="medium"),
                        rx.input(
                            placeholder="E.g. 'olivebranchelchorro@gmail.com' (required)",
                            name="email",
                            required=True,
                            type="email",
                            width="100%"
                        ),
                        rx.text("Dietary preferences", weight="medium"),
                        rx.select(
                            [str(x) for x in Diet],
                            default_value=Diet.VEGAN,
                            name="diet",
                            required=True
                        ),
                        rx.text("Allergies", weight="medium"),
                        rx.input(
                            placeholder="E.g. Gluten-free",
                            name="allergies"
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.text("Submit", size=default_button_text_size), type="submit",
                            size=default_button_size
                        )
                    ),
                    on_submit=State.submit_signup,
                    reset_on_submit=True
                ),
                rx.button(
                    rx.text("Cancel", size=default_button_text_size),
                    on_click=rx.redirect("/"),
                    size=default_button_size,
                    color_scheme='red'
                ),
            ),
        ),
    )

def dinner_signup_page() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.vstack(
                    rx.heading("Sign up for dinner", size=default_heading_size),
                    rx.text(
                        f"Note: you are signing up for todays dinner. "
                        f"Sign up again tomorrow for tomorrows dinner. "
                        f"Price per person is {State.admin_data['dinner_price']}€. "
                        f"If you are signing up yourself, just write your own full name. "
                        f"You can also sign up someone else on your tab, "
                        f"in that case write the full name of the guest "
                        f"whom you are signing up."
                    ),
                    rx.text("First name of dinner guest", weight="bold"),
                    rx.input(
                        placeholder="First name of dinner guest",
                        name="first_name",
                        default_value=State.current_user.first_name,
                        required=True,
                        on_change=State.set_dinner_signup_first_name
                    ),
                    rx.text("Last name of dinner guest", weight="bold"),
                    rx.input(
                        placeholder="Last name of dinner guest",
                        name="last_name",
                        default_value=State.current_user.last_name,
                        required=True,
                        on_change=State.set_dinner_signup_last_name
                    ),
                    rx.text("Dietary preferences", weight="bold"),
                    rx.select(
                        [str(x) for x in Diet],
                        default_value=State.current_user.diet,
                        name="diet",
                        on_change=State.set_dinner_dietary_preference,
                    ),
                    rx.text("Allergies", weight="bold"),
                    rx.input(
                        default_value=State.current_user.allergies,
                        name="allergies",
                        on_change=State.set_dinner_allergies
                    ),
                    rx.button(
                        rx.text("Register", size=default_button_text_size),
                        type="submit",
                        size=default_button_size,
                        on_click=State.sign_guest_up_for_dinner
                    ),
                    rx.dialog.root(
                        rx.dialog.trigger(
                            rx.button(
                                rx.icon("credit-card"),
                                rx.text("Pay Now", size=default_button_text_size),
                                color_scheme="green",
                                size=default_button_size,
                                type="button",
                                on_click=lambda: State.sign_guest_up_for_dinner(True)
                            )
                        ),                 
                        rx.cond(
                            State.ordered_item == "dinner",
                            stripe_payment_dialog("dinner", State.admin_data['dinner_price'])
                            )
                    ),
                    rx.button(
                        rx.text("Cancel", size=default_button_text_size),
                        on_click=rx.redirect("/user"),
                        size=default_button_size,
                        color_scheme='red'
                    )
                ),
            )
        ),
        on_mount=State.set_dinner_signup_default_values,
    )

def late_dinner_signup_page() -> rx.Component:
    return rx.container(rx.center(
        rx.vstack(
            rx.form(
                rx.vstack(
                    rx.heading("Late dinner signup", size=default_heading_size),
                    rx.text("Full name of dinner guest", weight="bold"),
                    rx.input(placeholder="Full name", name="full_name", required=True),
                    rx.text("User paying for this dinner sign-up", weight="bold"),
                    rx.select(State.get_all_nick_names, required=True, name="nick_name"),
                    rx.text("Dietary preferences", weight="bold"),
                    rx.select(
                        [str(x) for x in Diet],
                        default_value=str(Diet.VEGAN),
                        name="diet"
                    ),
                    rx.text("Allergies", weight="bold"),
                    rx.input(
                        name="allergies"
                    ),
                    rx.button(
                        rx.text("Register", size=default_button_text_size),
                        type="submit",
                        size=default_button_size
                    )
                ),
                on_submit=State.order_dinner_late,
                reset_on_submit=True
            ),
            rx.button(
                rx.text("Cancel", size=default_button_text_size),
                on_click=rx.redirect("/admin/dinner"),
                size=default_button_size
            )
        )
    ))

def breakfast_signup_page() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.heading("Sign up for breakfast", size=default_heading_size),
                rx.text(
                    "Note: you are signing up for todays breakfast. "
                    "Sign up again tomorrow for tomorrows breakfast."
                ),
                rx.text("* = Required field"),
                rx.spacer(),
                rx.text("First name of breakfast guest *"),
                rx.input(
                    placeholder="First name of breakfast guest",
                    default_value=State.current_user.first_name,
                    name="first_name",
                    on_change=State.set_breakfast_signup_first_name
                ),
                rx.text("Last name of breakfast guest *"),
                rx.input(
                    placeholder="Last name of breakfast guest",
                    default_value=State.current_user.last_name,
                    name="last_name",
                    on_change=State.set_breakfast_signup_last_name
                ),
                rx.text("Breakfast item *"),
                rx.select.root(
                    rx.select.trigger(),
                    rx.select.content(
                        rx.foreach(
                            [str(x) for x in BreakfastMenuItem],
                            lambda item: rx.select.item(
                                f"{item} ({State.admin_data[item + '_price']}€)",
                                value=item
                            )
                        )
                    ),
                    name="menu_item",
                    on_change=State.set_breakfast_signup_item
                ),
                rx.text("Allergies"),
                rx.input(
                    name="allergies",
                    default_value=State.current_user.allergies,
                    on_change=State.set_breakfast_signup_allergies
                ),
                rx.button(
                    rx.text("Register", size=default_button_text_size),
                    size=default_button_size,
                    loading=State.is_breakfast_button_loading,
                    on_click=[State.set_breakfast_signup_request_id, State.sign_guest_up_for_breakfast]
                ),
                rx.button(
                    rx.icon("credit-card"),
                    rx.text("Pay Now", size=default_button_text_size),
                    color_scheme="green",
                    size=default_button_size,
                    type="button",
                    loading=State.is_breakfast_button_loading,
                    on_click=[State.set_breakfast_signup_request_id, lambda: State.sign_guest_up_for_breakfast(True)]
                ),
                rx.dialog.root(
                  stripe_payment_dialog("breakfast", State.get_breakfast_price),
                  open=State.ordered_item == "breakfast"
                ),
                rx.button(
                    rx.text("Cancel", size=default_button_text_size),
                    on_click=rx.redirect("/user"),
                    size=default_button_size
                )

            )
    ),
    on_mount=State.set_breakfast_signup_default_values
    )

def user_info_page() -> rx.Component:
    def show_row(order: Order):
        return rx.table.row(
            rx.table.cell(order.time),
            rx.table.cell(order.item),
            rx.table.cell(f"{order.quantity}", align="right"),
            rx.table.cell(f"€{two_decimal_points(order.price)}", align="right"),
            rx.table.cell(f"€{two_decimal_points(order.total)}", align="right")
        )
    
    return rx.container(rx.center(rx.vstack(
        rx.heading(
            f"Hello {State.current_user.nick_name}", size=default_heading_size
        ),
        rx.button(
            rx.text(f"Back to orders and items", size=default_button_text_size),
            on_click=rx.redirect("/user"),
            color_scheme="red",
            size=default_button_size
        ),
        rx.text(
            "Note: new registrations may take a moment to show. "
            "If you made a registration by mistake, please talk to the reception "
            "and they will help correcting it.",
            size=default_text_size
        ),
        rx.text(f"Total amount due: €{two_decimal_points(State.get_user_debt)} ",
            size=default_text_size, weight="bold"),
        rx.hstack(
            rx.dialog.root(
                rx.dialog.trigger(
                    rx.button(
                        rx.icon("euro"),
                        rx.text("Pay tab", size=default_button_text_size, weight="bold"),
                        on_click=lambda: State.generate_item_payment_qr("tab", State.get_user_debt),
                        size=default_button_size,
                        color_scheme="yellow",
                    )
                ),
                stripe_payment_dialog("tab", State.get_user_debt)
            ),
            rx.text(
                f"Pay your tab securely via Stripe. Please review your registrations below before paying.",
                size=default_text_size
            ),
            align="center"
        ),
        rx.text("Registrations:", size=default_text_size, weight="bold"),
        rx.scroll_area(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Time"),
                        rx.table.column_header_cell("Item"),
                        rx.table.column_header_cell("Quantity", align="right"),
                        rx.table.column_header_cell("Unit Price", align="right"),
                        rx.table.column_header_cell("Total", align="right")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        State.current_user_orders, show_row
                    )
                )
            ),
            scrollbars="vertical",
            style={"height": "70vh"}
        )
    )))

def admin() -> rx.Component:
    def user_button(user: User):
        return rx.button(
            rx.text(
                f"{user.first_name} {user.last_name} ({user.nick_name})",
                size=default_button_text_size
            ),
            on_click=State.redirect_to_admin_user_page(user),
            size=default_button_size
        )
    return rx.container(rx.center(
        rx.vstack(
            rx.heading(f"Admin", size=default_heading_size),
            rx.button(
                rx.icon("refresh-cw"),
                rx.text("Reload", size=default_button_text_size),
                on_click=State.reload_sheet_data,
                color_scheme="green",
                size=default_button_size
            ),
            rx.button(
                rx.text("Dinner", size=default_button_text_size),
                on_click=rx.redirect("/admin/dinner"),
                size=default_button_size
            ),
            rx.button(
                rx.text("Breakfast", size=default_button_text_size),
                on_click=rx.redirect("/admin/breakfast"),
                size=default_button_size	
            ),
            rx.button(
                rx.text("Tax", size=default_button_text_size),
                on_click=rx.redirect("/admin/tax"),
                size=default_button_size
            ),
            rx.text("Users:"),
            rx.foreach(State.users, user_button)
        ) 
    ))

def admin_tax() -> rx.Component:
    return rx.container(rx.center(rx.vstack(
        rx.heading("Tax categories", size=default_heading_size),
        rx.button(
            rx.text("Go back", size=default_button_text_size),
            on_click=rx.redirect("/admin"),
            size=default_button_size
        ),
        rx.foreach(
            State.tax_categories.items(),
            lambda x: rx.text(f"{x[0]}: {x[1]}")
        )
    )))

def admin_refresh_top_bar() -> rx.Component:
    return rx.flex(
        rx.button(
            rx.icon("door-open"), rx.text("Go back", size=default_button_text_size),
            on_click=rx.redirect("/admin"), color_scheme="red",
            size=default_button_size
        ),
        rx.button(
            rx.icon("refresh-cw"), rx.text("Reload", size=default_button_text_size),
            on_click=State.reload_sheet_data,
            color_scheme="green",
            size=default_button_size
        ),
        spacing="2"
    )

def admin_dinner() -> rx.Component:
    def show_signup(signup: Order):
        return rx.table.row( 
            rx.table.cell(signup.receiver),
            rx.table.cell(signup.diet),
            rx.table.cell(signup.allergies),
            rx.table.cell(signup.comment),
            rx.table.cell(
                rx.checkbox(
                    checked=signup.served_bool,
                    on_change=lambda val, oid=signup.order_id: State.set_served(oid, val)
                )
            ),
            key=signup.order_id
            
        )

    return rx.container(rx.center(
        rx.vstack(
            rx.heading("Dinner", size=default_heading_size), 
            rx.hstack(
                admin_refresh_top_bar(),
                rx.button(
                    rx.text("Late sign-up", size=default_button_text_size),
                    on_click=rx.redirect("/admin/late"),
                    size=default_button_size
                ),
                spacing="2"
            ),
            # Make the two columns share the available space evenly
            rx.hstack(
                rx.vstack(
                    rx.text(f"Total eating dinner: {State.dinner_count}"),

                    rx.text(f"Meat: {State.dinner_count_meat}"),
                    rx.text(f"Vegatarian: {State.dinner_count_vegetarian}"),                  
                    rx.text(f"Vegan: {State.dinner_count_vegan}"),
                    flex="1"
                ),
                rx.vstack(
                    rx.text(f"Guests eating dinner: {State.dinner_count_volunteers}"),
                    rx.text(f"Meat: {State.dinner_count_meat - State.dinner_count_meat_volunteers}"),
                    rx.text(f"Vegatarian: {State.dinner_count_vegetarian - State.dinner_count_vegetarian_volunteers}"),
                    rx.text(f"Vegan: {State.dinner_count_vegan - State.dinner_count_vegan_volunteers}"),
                    flex="1"
                ),
                rx.vstack(
                    rx.text(f"Volunteers eating dinner: {State.dinner_count - State.dinner_count_volunteers}"),
                    rx.text(f"Meat: {State.dinner_count_meat_volunteers}"),
                    rx.text(f"Vegatarian: {State.dinner_count_vegetarian_volunteers}"),
                    rx.text(f"Vegan: {State.dinner_count_vegan_volunteers}"),
                    flex="1"
                ),
                spacing="4",
                justify="between",
                width="100%"
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Name"),
                        rx.table.column_header_cell("Diet"),
                        rx.table.column_header_cell("Allergies"),
                        rx.table.column_header_cell("Volunteer"),
                        rx.table.column_header_cell("Served"),
                    )
                ),
                rx.table.body(
                    rx.foreach(State.dinner_signups, show_signup)
                ),
                variant="surface",
                size="3"
            )
        )
    )
)

def admin_breakfast() -> rx.Component:
    def show_signup(signup: Order):
        return rx.table.row( 
            rx.table.cell(signup.time),
            rx.table.cell(signup.receiver),
            rx.table.cell(signup.diet),
            rx.table.cell(signup.allergies),
            rx.table.cell(
                rx.checkbox(
                    checked=signup.served_bool,
                    on_change=lambda val, oid=signup.order_id: State.set_served(oid, val)
                )
            ),
            key=signup.order_id
        )

    return rx.container(rx.center(
        rx.vstack(
            rx.heading("Breakfast", size=default_heading_size),
            admin_refresh_top_bar(), 
            rx.scroll_area(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Time"),
                            rx.table.column_header_cell("Name"),
                            rx.table.column_header_cell("Menu item"),
                            rx.table.column_header_cell("Allergies"),
                            rx.table.column_header_cell("Served")
                        )
                    ),
                    rx.table.body(
                        rx.foreach(State.breakfast_signups, show_signup)
                    ),
                    variant="surface",
                    size="3"
                ),
                type="always",
                scrollbars="vertical",
                style={"height": "80vh"}
            ),
        )
    ))

def admin_user_page() -> rx.Component:
    return rx.container(rx.center(rx.vstack(
        rx.heading("User information", size=default_heading_size),
        rx.button(
            rx.text("Go back", size=default_button_text_size),
            on_click=rx.redirect("/admin"),
            size=default_button_size
        ),
        rx.text(f"Full name: {State.current_user.first_name} {State.current_user.last_name}"),
        rx.text(f"Nick name: {State.current_user.nick_name}"),
        rx.text(f"Owes: {State.get_user_debt}€")
    )))