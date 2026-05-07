from obhonesty.constants import *
from obhonesty.models import Meal, Order, User, Item
from obhonesty.state import State
import reflex as rx
from obhonesty.aux import get_full_breakfast_item, two_decimal_points
import os

is_test_environment = True if os.getenv("TEST") else False


def user_button(*children, **kwargs):
    return rx.button(
        *children,
        font_size="1.5rem",
        padding="1.5rem 2rem",
        border_radius="0.5rem",
        **kwargs,
    )


def user_button_dialog(user: User) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            user_button(
                user.nick_name,
                **{"data-testid": f"user-button-{user.nick_name}"},
                disabled=State.current_user != None,
            )
        ),
        rx.dialog.content(
            rx.form(
                rx.flex(
                    rx.dialog.title(f"{user.nick_name} - Log in to your account"),
                    rx.box(
                        rx.text(
                            "Please enter the first five characters of your email address to login to your account.",
                            weight="bold",
                        ),
                        rx.hstack(
                            rx.text("This includes symbols such as "),
                            rx.text("@", weight="bold"),
                            rx.text(" and "),
                            rx.text(".", weight="bold"),
                        ),
                        rx.hstack(
                            rx.text("Eg. john@smith.com = "),
                            rx.text("john@", weight="bold"),
                        ),
                        rx.text(
                            "If your email address is five characters or less, please enter the full email address."
                        ),
                    ),
                    rx.input(
                        name="user_nick_name",
                        type="hidden",
                        display="none",
                        value=user.nick_name,
                        size="3",
                    ),
                    rx.vstack(
                        rx.vstack(
                            rx.input(
                                placeholder="Enter the first five characters of your email here",
                                type="password",
                                name="email_first_five_chars",
                                max_length=5,
                                required=True,
                                width="100%",
                                **{"data-testid": f"user-email-password"},
                            ),
                            rx.cond(
                                State.is_email_login_incorrect,
                                rx.text(
                                    "This does not match the first five characters of your email, please try again.",
                                    color=ERROR_MESSAGE_COLOUR,
                                    **{"data-testid": f"wrong-password-error"},
                                ),
                            ),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.button(
                                "Submit",
                                type="submit",
                                size=default_button_size,
                                **{"data-testid": "password-submit-button"},
                            ),
                            rx.dialog.close(
                                rx.button("Close", size=default_button_size)
                            ),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text("Forgotten your email?", weight="bold"),
                        rx.text("See reception for help."),
                    ),
                    direction="column",
                    spacing="3",
                ),
                on_submit=State.handle_user_login_form_submit,
            ),
        ),
        on_open_change=State.handle_user_login_dialog_open_change,
    )


def logout_button() -> rx.Component:
    return (
        rx.button(
            rx.icon("door-open"),
            rx.text("Log out", size=default_button_text_size),
            color_scheme="red",
            on_click=State.handle_user_logout,
            size=default_button_size,
        ),
    )


def item_button(item: Item) -> rx.Component:
    title: str = f"{item.name} (€{two_decimal_points(item.price)})"

    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.text(title, size=default_button_text_size),
                color_scheme="blue",
                size=default_button_size,
                # Reset temp quantity to 1 every time we open a fresh dialog
                on_click=lambda: State.open_item_dialog(item.name),
                **{"data-testid": f"order_item_button"},
                disabled=State.are_user_buttons_disabled,
            )
        ),
        rx.cond(
            State.is_stripe_dialog_active,
            stripe_payment_dialog(item.name, item.price * State.temp_quantity),
            rx.dialog.content(
                rx.dialog.title(title),
                rx.dialog.description(item.description),
                rx.vstack(
                    rx.input(
                        placeholder="Quantity",
                        name="quantity",
                        default_value="1",
                        type="number",
                        # --- Track input in real-time ---
                        on_change=State.set_temp_quantity,
                        **{"data-testid": "item_quantity_input"},
                    ),
                    rx.text(
                        "Total: €",
                        State.temp_quantity * item.price,
                        weight="bold",
                        **{"data-testid": "item_total"},
                    ),
                    rx.flex(
                        # We use the payment_dialog logic but trigger it differently
                        rx.dialog.close(
                            rx.button(
                                "Register (Add to Tab)",
                                size=default_button_size,
                                on_click=[State.order_item, State.close_item_dialog],
                                **{"data-testid": "item_register"},
                            )
                        ),
                        rx.button(
                            rx.icon("credit-card"),
                            rx.text("Pay Now", size=default_button_text_size),
                            color_scheme="green",
                            size=default_button_size,
                            type="button",
                            # Pass specific item details to backend
                            loading=State.is_order_request_loading,
                            on_click=[
                                State.set_order_request_id,
                                lambda: State.show_stripe_item_payment_dialog(
                                    item.name, item.price
                                ),
                            ],
                            **{"data-testid": "item_pay_now"},
                        ),
                        rx.dialog.close(
                            rx.button(
                                f"Cancel",
                                on_click=State.close_item_dialog,
                                size=default_button_size,
                            )
                        ),
                        spacing="3",
                        justify="end",
                        margin_top="10px",
                    ),
                    spacing="3",
                ),
            ),
        ),
    )


def stripe_payment_dialog(name, amount) -> rx.Component:
    close_dialog_button = rx.dialog.close(
        rx.button(
            "Close",
            on_click=State.close_item_dialog,
            size=default_button_size,
            **{"data-testid": "stripe_dialog_close"},
        )
    )

    return rx.cond(
        State.has_stripe_qr_generation_failed | State.show_stripe_timeout_message,
        rx.dialog.content(
            rx.vstack(
                rx.text(
                    rx.cond(
                        State.show_stripe_timeout_message,
                        "This transaction has timed out, please try again. Please see reception if you have already completed payment.",
                        "There are some issues with the internet connection. Please see reception to complete payment.",
                    ),
                    size=default_text_size,
                    weight="bold",
                ),
                close_dialog_button,
            ),
            on_interact_outside=rx.prevent_default,
            on_escape_key_down=rx.prevent_default,
        ),
        rx.dialog.content(
            rx.dialog.title(
                f"Pay for {name}",
                **{"data-testid": "stripe_dialog_title"},
            ),
            rx.center(
                rx.vstack(
                    rx.cond(
                        State.is_payment_status_written_to_db,
                        rx.vstack(
                            rx.text(
                                "Paid! Thank you.",
                                **{"data-testid": "stripe_payment_successful_text"},
                            ),
                            rx.cond(
                                State.current_user.current_guest
                                & State.is_closing_account,
                                rx.text(
                                    "Please see reception to complete your checkout.",
                                    weight="bold",
                                    **{"data-testid": "checkout-complete-text"},
                                ),
                            ),
                            rx.text("Press close below to finish."),
                        ),
                        rx.vstack(
                            rx.cond(
                                State.payment_qr_code != "",
                                rx.image(
                                    src=State.payment_qr_code
                                    if not is_test_environment
                                    else rx.asset("test_url.png"),
                                    width="250px",
                                    height="250px",
                                    border="1px solid #ddd",
                                    **{"data-testid": "stripe_qr_code_image"},
                                ),
                                rx.spinner(size="3"),
                            ),
                            rx.text(f"Scan to pay via Stripe"),
                            rx.vstack(
                                rx.text(
                                    f"Paying with Stripe incurs a System Provider Handling Fee of {SYSTEM_PROVIDER_HANDLING_FEE * 100}%"
                                ),
                                rx.text(
                                    f"Subtotal: €{two_decimal_points(amount)}",
                                    weight="bold",
                                    **{"data-testid": "stripe-subtotal"},
                                ),
                                rx.text(
                                    f"System Provider Handling Fee: €{two_decimal_points(State.stripe_system_provider_handling_fee_amount)}",
                                    weight="bold",
                                    **{"data-testid": "stripe-handling-fee"},
                                ),
                                rx.text(
                                    f"Total: €{two_decimal_points(State.stripe_total)}",
                                    weight="bold",
                                    **{"data-testid": "stripe-total"},
                                ),
                                spacing="1",
                            ),
                            rx.text("For other payment methods please see reception."),
                            spacing="4",
                        ),
                    ),
                    rx.cond(
                        ~State.is_payment_status_written_to_db,
                        rx.text(
                            "Having issues paying? Please close and contact reception.",
                            size=default_text_size,
                        ),
                    ),
                    rx.cond(
                        State.show_stripe_connection_failure_message,
                        rx.vstack(
                            rx.text(
                                "There are some issues with the internet connection. Please see reception to complete payment or click back.",
                                size=default_text_size,
                                weight="bold",
                            ),
                            rx.text(
                                "Have you already paid? Show reception your payment confirmation and press close to exit back to the menu.",
                                size=default_text_size,
                                weight="bold",
                            ),
                        ),
                    ),
                    rx.hstack(
                        rx.cond(
                            ~State.is_payment_status_written_to_db,
                            rx.button(
                                "Back",
                                on_click=State.close_item_dialog,
                                size=default_button_size,
                            ),
                        ),
                        rx.cond(
                            # if paying the tab the close button should immediately redirect
                            State.is_payment_status_written_to_db & State.ordered_item
                            == "",
                            rx.button(
                                "Close",
                                on_click=rx.redirect(
                                    rx.cond(State.is_closing_account, "/", "/user")
                                ),
                                size=default_button_size,
                                **{"data-testid": "stripe_dialog_close"},
                            ),
                            close_dialog_button,
                        ),
                    ),
                ),
                justify="end",
                margin_top="20px",
            ),
            on_interact_outside=rx.prevent_default,
            on_escape_key_down=rx.prevent_default,
        ),
    )


def show_row(order: Order):
    return rx.table.row(
        rx.table.cell(order.time),
        rx.table.cell(
            rx.cond(
                order.item == "Breakfast sign-up",
                get_full_breakfast_item(order.diet),
                order.item,
            ),
            **{"data-testid": f"ordered_item"},
        ),
        rx.table.cell(
            rx.cond(
                State.prepaid_dinner_ids.contains(order.order_id),
                rx.text.strong("Prepaid dinner"),
                f"{order.quantity}",
            ),
            align="right",
            **{"data-testid": "ordered_item_quantity"},
        ),
        rx.table.cell(
            rx.cond(
                State.prepaid_dinner_ids.contains(order.order_id),
                "€0",
                f"€{two_decimal_points(order.price)}",
            ),
            align="right",
        ),
        rx.table.cell(
            rx.cond(
                State.prepaid_dinner_ids.contains(order.order_id),
                "€0",
                f"€{two_decimal_points(order.total)}",
            ),
            align="right",
            **{"data-testid": "ordered_item_total"},
        ),
    )


def admin_refresh_top_bar() -> rx.Component:
    return rx.flex(
        rx.button(
            rx.icon("door-open"),
            rx.text("Go back", size=default_button_text_size),
            on_click=rx.redirect("/admin"),
            color_scheme="red",
            size=default_button_size,
        ),
        rx.button(
            rx.icon("refresh-cw"),
            rx.text("Reload", size=default_button_text_size),
            on_click=State.reload_sheet_data,
            color_scheme="green",
            size=default_button_size,
            disabled=State.is_loading_admin_meal_table,
        ),
        spacing="2",
    )


def show_signup(meal: Meal):
    has_allergies = meal.allergies != ""
    is_served = State.optimistic_served_states[meal.meal_id]
    return rx.table.row(
        rx.table.cell(meal.receiver, **{"data-testid": "meal-receiver"}),
        rx.table.cell(meal.diet, **{"data-testid": "diet"}),
        rx.table.cell(meal.allergies, **{"data-testid": "allergies"}),
        rx.cond(
            meal.meal_type == "dinner",
            rx.table.cell(rx.cond(meal.volunteer, "yes", "")),
        ),
        rx.table.cell(
            rx.button(
                rx.text(rx.cond(is_served, "✅", "✖️"), size="8"),
                on_click=lambda: State.set_served(meal.meal_id, ~is_served),
                color_scheme=rx.cond(is_served, "green", "red"),
                size="4",
                **{"data-testid": "served-button"},
            )
        ),
        key=meal.meal_id,
        bg=rx.cond(has_allergies, "#FC281D20", "transparent"),
        **{"data-testid": "meal-row"},
    )
