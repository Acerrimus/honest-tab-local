import reflex as rx
import os
from obhonesty.aux import two_decimal_points, get_full_breakfast_item
from obhonesty.constants import *
from obhonesty.order import Order
from obhonesty.state import State
from obhonesty.user import User
from obhonesty.models import Meal as Meal_Model, Item
from obhonesty.elements import user_button

is_test_environment = True if os.getenv("TEST") else False


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


def index() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.text("Welcome to the", size="3"),
                    justify="center",
                    width="100%",
                ),
                rx.hstack(
                    rx.heading(
                        "Olive Branch honest self-service",
                        size=default_heading_size,
                        **{"data-testid": "title"},
                    ),
                    justify="center",
                    width="100%",
                ),
                rx.cond(
                    State.has_homepage_load_completed,
                    rx.hstack(
                        rx.text("New here?", size="3"),
                        rx.button(
                            rx.icon("user-plus"),
                            rx.text(
                                "Sign up for self-service",
                                size=default_button_text_size,
                                **{"data-testid": "sign-up-user-button"},
                            ),
                            color_scheme="green",
                            on_click=rx.redirect("/signup"),
                            size="3",
                        ),
                        align="center",
                        justify="center",
                        width="100%",
                    ),
                    rx.text("Loading..."),
                ),
                rx.cond(
                    State.has_homepage_load_completed,
                    rx.scroll_area(
                        rx.flex(
                            rx.foreach(State.users, user_button_dialog),
                            padding="8px",
                            spacing="5",
                            style={"width": "max"},
                            wrap="wrap",
                        ),
                        type="always",
                        scrollbars="vertical",
                        style={"height": "80vh"},
                    ),
                ),
            ),
            align="center",
        )
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


def error_page() -> rx.Component:
    return rx.vstack(
        rx.text(
            "An error occurred, please press the button below.", size=default_text_size
        ),
        rx.button(
            rx.icon("door-open"),
            "Return",
            on_click=State.redirect_to_homepage,
            size=default_button_size,
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


def user_page() -> rx.Component:
    return rx.container(
        rx.center(
            rx.cond(
                State.no_user,
                error_page(),
                rx.vstack(
                    rx.heading(
                        f"Hello {State.current_user.nick_name}",
                        size=default_heading_size,
                        **{"data-testid": f"user-page-heading"},
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("list"),
                            rx.text("View orders", size=default_button_text_size),
                            on_click=rx.redirect("/info"),
                            color_scheme="green",
                            size=default_button_size,
                            disabled=State.are_user_buttons_disabled,
                            **{"data-testid": "view-orders-button"},
                        ),
                        logout_button(),
                        rx.text(
                            "(please log out when you're done)", size=default_text_size
                        ),
                        align="center",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("egg-fried"),
                            rx.text(
                                "Sign up for breakfast / packed lunch",
                                size=default_button_text_size,
                            ),
                            on_click=rx.redirect("/breakfast"),
                            size=default_button_size,
                            disabled=(
                                ~State.breakfast_signup_available
                                & (not is_test_environment)
                            )
                            | State.are_user_buttons_disabled,
                            **{"data-testid": "breakfast-signup-button"},
                        ),
                        rx.text(
                            f"(last sign-up at {State.admin_data['breakfast_signup_deadline']})",
                            size=default_text_size,
                        ),
                        align="center",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("utensils"),
                            rx.text(
                                "Sign up for dinner",
                                size=default_button_text_size,
                            ),
                            on_click=rx.redirect("/dinner"),
                            size=default_button_size,
                            disabled=(
                                ~State.dinner_signup_available
                                & (not is_test_environment)
                            )
                            | State.are_user_buttons_disabled,
                            **{"data-testid": "dinner-signup-button"},
                        ),
                        rx.text(
                            f"(last sign-up at {State.admin_data['dinner_signup_deadline']}, "
                            f"for late sign-ups, please ask the kitchen staff)",
                            size=default_text_size,
                        ),
                        align="center",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("euro"),
                            rx.text("Pay tab", size=default_button_text_size),
                            on_click=rx.redirect("/info"),
                            size=default_button_size,
                            color_scheme="yellow",
                            disabled=State.are_user_buttons_disabled,
                            **{"data-testid": "pay-tab-button"},
                        ),
                        rx.text(
                            f"Pay your tab securely via Stripe.", size=default_text_size
                        ),
                        align="center",
                    ),
                    rx.text("Register an item", weight="bold", size=default_text_size),
                    rx.scroll_area(
                        rx.flex(
                            rx.foreach(State.items.values(), item_button),
                            padding="8px",
                            spacing="4",
                            style={"width": "max"},
                            wrap="wrap",
                        ),
                        type="always",
                        scrollbars="vertical",
                        style={"height": "60vh"},
                    ),
                    rx.hstack(
                        rx.text(
                            "Didn't find the item? No problem, just",
                            size=default_text_size,
                        ),
                        rx.button(
                            rx.icon("circle-plus"),
                            rx.text("Register manually", size=default_button_text_size),
                            color_scheme="sky",
                            on_click=rx.redirect("/custom_item"),
                            size=default_button_size,
                            disabled=State.are_user_buttons_disabled,
                        ),
                        align="center",
                    ),
                ),
            )
        )
    )


def custom_item_page() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.heading("Register custom item", size=default_heading_size),
                rx.form(
                    rx.vstack(
                        rx.text("Name"),
                        rx.input(
                            placeholder="What did you get?", name="custom_item_name"
                        ),
                        rx.text("Price"),
                        rx.form.field(
                            rx.form.control(
                                rx.input(
                                    placeholder="E.g. 2.50 for (2.50€)",
                                    name="custom_item_price",
                                    on_change=State.set_custom_item_price,
                                ),
                                as_child=True,
                            ),
                            rx.form.message(
                                "Please enter a valid price",
                                match="valueMissing",
                                force_match=State.invalid_custom_item_price,
                                color=ERROR_MESSAGE_COLOUR,
                            ),
                        ),
                        rx.text("Category"),
                        rx.select(
                            [str(x) for x in TaxCategory],
                            default_value=TaxCategory.NON_ALCOHOLIC,
                            name="tax_category",
                            required=True,
                        ),
                        rx.text("Comment"),
                        rx.input(
                            placeholder="optional", name="custom_item_description"
                        ),
                        rx.button(
                            rx.text("Register", size=default_button_text_size),
                            type="submit",
                            size=default_button_size,
                        ),
                    ),
                    on_submit=State.order_custom_item,
                ),
                rx.button(
                    rx.text("Cancel", size=default_button_text_size),
                    on_click=rx.redirect("/user"),
                    size=default_button_size,
                ),
            )
        )
    )


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
                                    width="200%",
                                    **{"data-testid": "user-name-input"},
                                ),
                                as_child=True,
                            ),
                            rx.form.message(
                                message_name_already_taken,
                                match="valueMissing",
                                force_match=State.invalid_new_user_name,
                                color=ERROR_MESSAGE_COLOUR,
                            ),
                        ),
                        rx.text("First name", weight="medium"),
                        rx.input(
                            placeholder="E.g. 'Robert' (required)",
                            name="first_name",
                            required=True,
                            width="100%",
                            **{"data-testid": "first-name-input"},
                        ),
                        rx.text("Last name", weight="medium"),
                        rx.input(
                            placeholder="E.g. 'Robertson' (required)",
                            name="last_name",
                            required=True,
                            width="100%",
                            **{"data-testid": "last-name-input"},
                        ),
                        rx.text("Phone number", weight="medium"),
                        rx.input(
                            placeholder="E.g. '+45 12345666' (required)",
                            name="phone_number",
                            required=True,
                            width="100%",
                            **{"data-testid": "phone-number-input"},
                        ),
                        rx.text("Email", weight="medium"),
                        rx.input(
                            placeholder="E.g. 'olivebranchelchorro@gmail.com' (required)",
                            name="email",
                            required=True,
                            type="email",
                            width="100%",
                            **{"data-testid": "email-input"},
                        ),
                        rx.text("Dietary preferences", weight="medium"),
                        rx.select(
                            [str(x) for x in Diet],
                            placeholder="Select a dietary preference",
                            name="diet",
                            required=True,
                            **{"data-testid": "diet-select"},
                        ),
                        rx.text("Allergies", weight="medium"),
                        rx.input(
                            placeholder="e.g. Peanuts, Shellfish (Anaphylaxis risk)",
                            name="allergies",
                            width="70%",
                            border_color="tomato",
                            **{"data-testid": ["allergies-input"]},
                        ),
                        rx.text(
                            "Are you currently staying at the Olive Branch?",
                            weight="medium",
                        ),
                        rx.radio_group.root(
                            rx.foreach(
                                ["Yes", "No"],
                                lambda x: rx.radio_group.item(
                                    x,
                                    value=x,
                                    **{"data-testid": f"radio-input-{x.lower()}"},
                                ),
                            ),
                            required=True,
                            name="current_guest",
                            default_value="Yes",
                            direction="row",
                        ),
                        rx.text("If this changes please notify reception."),
                        rx.spacer(),
                        rx.button(
                            rx.text("Submit", size=default_button_text_size),
                            type="submit",
                            size=default_button_size,
                            **{"data-testid": "user-submit-button"},
                        ),
                    ),
                    on_submit=State.submit_signup,
                    reset_on_submit=True,
                ),
                rx.button(
                    rx.text("Cancel", size=default_button_text_size),
                    on_click=State.redirect_to_homepage,
                    size=default_button_size,
                    color_scheme="red",
                ),
            ),
        ),
    )


def dinner_signup_page() -> rx.Component:
    prepaid_dinners_plural = rx.cond(State.remaining_prepaid_dinners_count > 1, "s", "")
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
                        on_change=State.set_dinner_signup_first_name,
                        **{"data-testid": f"dinner-signup-first-name"},
                    ),
                    rx.text("Last name of dinner guest", weight="bold"),
                    rx.input(
                        placeholder="Last name of dinner guest",
                        name="last_name",
                        default_value=State.current_user.last_name,
                        required=True,
                        on_change=State.set_dinner_signup_last_name,
                        **{"data-testid": f"dinner-signup-last-name"},
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
                        on_change=State.set_dinner_allergies,
                        **{"data-testid": f"dinner-signup-allergies"},
                    ),
                    rx.divider(),
                    rx.cond(
                        State.remaining_prepaid_dinners_count > 0,
                        rx.text.strong(
                            f"You currently have {State.remaining_prepaid_dinners_count} prepaid dinner{prepaid_dinners_plural} remaining."
                        ),
                    ),
                    rx.button(
                        rx.text("Register", size=default_button_text_size),
                        size=default_button_size,
                        on_click=[
                            State.set_order_request_id,
                            lambda: State.sign_guest_up_for_dinner(False),
                        ],
                        loading=State.is_order_request_loading,
                        **{"data-testid": f"dinner-signup-register"},
                    ),
                    rx.button(
                        rx.icon("credit-card"),
                        rx.text("Pay Now", size=default_button_text_size),
                        color_scheme="green",
                        size=default_button_size,
                        type="button",
                        loading=State.is_order_request_loading,
                        on_click=[
                            State.set_order_request_id,
                            lambda: State.sign_guest_up_for_dinner(True),
                        ],
                        **{"data-testid": f"dinner-signup-pay-now"},
                    ),
                    rx.dialog.root(
                        stripe_payment_dialog(
                            "dinner", State.admin_data["dinner_price"]
                        ),
                        open=State.ordered_item == "dinner",
                    ),
                    rx.button(
                        rx.text("Cancel", size=default_button_text_size),
                        on_click=rx.redirect("/user"),
                        size=default_button_size,
                        color_scheme="red",
                    ),
                ),
            )
        ),
        on_mount=State.set_dinner_signup_default_values,
    )


def late_dinner_signup_page() -> rx.Component:
    is_late_dinner_user_selected = State.late_dinner_user_nick_name != None
    user_selection_button_colour_scheme = "green"

    return rx.container(
        rx.center(
            rx.vstack(
                rx.form(
                    rx.vstack(
                        rx.heading("Late dinner signup", size=default_heading_size),
                        rx.hstack(
                            rx.cond(
                                is_late_dinner_user_selected,
                                rx.hstack(
                                    rx.text("User to pay:", size="5"),
                                    rx.text(
                                        State.late_dinner_user_nick_name,
                                        weight="bold",
                                        size="5",
                                        **{"data-testid": "late-signup-user-to-pay"},
                                    ),
                                ),
                            ),
                            rx.dialog.root(
                                rx.dialog.trigger(
                                    rx.button(
                                        rx.cond(
                                            is_late_dinner_user_selected,
                                            "Select another user",
                                            "Select a user to pay for this dinner sign-up",
                                        ),
                                        color_scheme=user_selection_button_colour_scheme,
                                        size=default_button_size,
                                        **{
                                            "data-testid": "late-signup-user-select-button"
                                        },
                                    )
                                ),
                                rx.dialog.content(
                                    rx.dialog.title(
                                        "Select a user to pay for this dinner sign-up"
                                    ),
                                    rx.scroll_area(
                                        rx.flex(
                                            rx.foreach(
                                                State.users,
                                                lambda user: rx.dialog.close(
                                                    user_button(
                                                        user.nick_name,
                                                        on_click=[
                                                            lambda: State.set_late_dinner_user_nick_name(
                                                                user.nick_name
                                                            ),
                                                            rx.set_value(
                                                                "full-name",
                                                                f"{user.first_name} {user.last_name}",
                                                            ),
                                                            rx.set_value(
                                                                "allergies",
                                                                user.allergies,
                                                            ),
                                                        ],
                                                        **{
                                                            "data-testid": f"late-signup-user-select-button-{user.nick_name}"
                                                        },
                                                    )
                                                ),
                                            ),
                                            padding="8px",
                                            spacing="4",
                                            style={"width": "max"},
                                            wrap="wrap",
                                        ),
                                        type="always",
                                        scrollbars="vertical",
                                        style={"height": "80vh"},
                                    ),
                                ),
                            ),
                            align="center",
                        ),
                        rx.input(
                            type="hidden",
                            display="none",
                            value=State.late_dinner_user_nick_name,
                            name="nick_name",
                        ),
                        rx.vstack(
                            rx.text("Full name of dinner guest", weight="bold"),
                            rx.input(
                                placeholder="Full name",
                                name="full_name",
                                required=True,
                                **{"data-testid": "late-signup-full-name-input"},
                                id="full-name",
                                disabled=~is_late_dinner_user_selected,
                            ),
                            rx.text("Dietary preferences", weight="bold"),
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Select a dietary preference",
                                    **{"data-testid": "late-signup-item-select"},
                                ),
                                rx.select.content(
                                    rx.foreach(
                                        [str(x) for x in Diet],
                                        lambda item: rx.select.item(
                                            item,
                                            value=item,
                                            **{
                                                "data-testid": "late-signup-item-option"
                                            },
                                        ),
                                    )
                                ),
                                name="diet",
                                value=State.late_dinner_diet,
                                required=True,
                                disabled=~is_late_dinner_user_selected,
                                on_change=State.set_late_dinner_diet,
                            ),
                            rx.text(
                                "Allergies",
                                weight="bold",
                            ),
                            rx.input(
                                name="allergies",
                                id="allergies",
                                disabled=~is_late_dinner_user_selected,
                                **{"data-testid": "late-signup-allergies"},
                            ),
                        ),
                        rx.hstack(
                            rx.button(
                                rx.text("Register", size=default_button_text_size),
                                type="submit",
                                size=default_button_size,
                                disabled=~is_late_dinner_user_selected
                                | State.late_dinner_diet
                                == "",
                                **{"data-testid": "late-signup-register-button"},
                            ),
                            rx.button(
                                rx.text(
                                    "Register and add another",
                                    size=default_button_text_size,
                                    **{
                                        "data-testid": "late-signup-register-and-add-another-button"
                                    },
                                ),
                                type="submit",
                                size=default_button_size,
                                disabled=~is_late_dinner_user_selected
                                | State.late_dinner_diet
                                == "",
                                on_click=State.handle_add_another_press_for_late_dinner_signup,
                            ),
                        ),
                    ),
                    on_submit=State.order_dinner_late,
                    reset_on_submit=True,
                ),
                rx.button(
                    rx.text("Cancel", size=default_button_text_size),
                    on_click=[
                        State.reset_late_dinner_user_nick_name,
                        rx.redirect("/admin/dinner"),
                    ],
                    size=default_button_size,
                    **{"data-testid": "late-signup-cancel-button"},
                ),
            )
        )
    )


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
                    on_change=State.set_breakfast_signup_first_name,
                    **{"data-testid": "breakfast-signup-first-name"},
                ),
                rx.text("Last name of breakfast guest *"),
                rx.input(
                    placeholder="Last name of breakfast guest",
                    default_value=State.current_user.last_name,
                    name="last_name",
                    on_change=State.set_breakfast_signup_last_name,
                    **{"data-testid": "breakfast-signup-last-name"},
                ),
                rx.text("Breakfast item *"),
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Select a breakfast item",
                        **{"data-testid": "breakfast-signup-item-select"},
                    ),
                    rx.select.content(
                        rx.foreach(
                            [str(x) for x in BreakfastMenuItem],
                            lambda item: rx.select.item(
                                f"{item} ({State.admin_data[item + '_price']}€)",
                                value=item,
                                **{"data-testid": "breakfast-signup-item-option"},
                            ),
                        )
                    ),
                    name="menu_item",
                    on_change=State.set_breakfast_signup_item,
                ),
                rx.text("Allergies"),
                rx.input(
                    name="allergies",
                    default_value=State.current_user.allergies,
                    on_change=State.set_breakfast_signup_allergies,
                    **{"data-testid": "breakfast-signup-allergies"},
                ),
                rx.button(
                    rx.text("Register", size=default_button_text_size),
                    size=default_button_size,
                    loading=State.is_order_request_loading,
                    on_click=[
                        State.set_order_request_id,
                        lambda: State.sign_guest_up_for_breakfast(False),
                    ],
                    **{"data-testid": "breakfast-signup-register"},
                ),
                rx.button(
                    rx.icon("credit-card"),
                    rx.text("Pay Now", size=default_button_text_size),
                    color_scheme="green",
                    size=default_button_size,
                    type="button",
                    loading=State.is_order_request_loading,
                    on_click=[
                        State.set_order_request_id,
                        lambda: State.sign_guest_up_for_breakfast(True),
                    ],
                    **{"data-testid": "breakfast-pay-now"},
                ),
                rx.dialog.root(
                    stripe_payment_dialog("breakfast", State.get_breakfast_price),
                    open=State.ordered_item == "breakfast",
                ),
                rx.button(
                    rx.text("Cancel", size=default_button_text_size),
                    on_click=rx.redirect("/user"),
                    size=default_button_size,
                ),
            )
        ),
        on_mount=State.set_breakfast_signup_default_values,
    )


def user_info_page() -> rx.Component:
    is_user_debt_0 = State.get_user_debt == 0

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

    return rx.container(
        rx.center(
            rx.vstack(
                rx.heading(
                    f"Hello {State.current_user.nick_name}", size=default_heading_size
                ),
                rx.button(
                    rx.text(f"Back to orders and items", size=default_button_text_size),
                    on_click=rx.redirect("/user"),
                    color_scheme="red",
                    size=default_button_size,
                ),
                rx.text(
                    "Note: new registrations may take a moment to show. "
                    "If you made a registration by mistake, please talk to the reception "
                    "and they will help correcting it.",
                    size=default_text_size,
                ),
                rx.text(
                    f"Total amount due: €{two_decimal_points(State.get_user_debt)}",
                    size=default_text_size,
                    weight="bold",
                    **{"data-testid": "total-amount-due"},
                ),
                rx.hstack(
                    rx.dialog.root(
                        rx.dialog.trigger(
                            rx.button(
                                rx.icon("euro"),
                                rx.text(
                                    "Pay tab",
                                    size=default_button_text_size,
                                    weight="bold",
                                ),
                                size=default_button_size,
                                color_scheme="yellow",
                                disabled=is_user_debt_0,
                                **{"data-testid": "pay-tab-button"},
                            )
                        ),
                        rx.cond(
                            State.is_closing_account == None,
                            rx.dialog.content(
                                rx.form(
                                    rx.vstack(
                                        rx.text(
                                            rx.cond(
                                                State.current_user.current_guest
                                                == True,
                                                "Are you leaving the Olive Branch?",
                                                "Are you closing your account?",
                                            ),
                                            weight="medium",
                                        ),
                                        rx.radio_group.root(
                                            rx.foreach(
                                                ["Yes", "No"],
                                                lambda x: rx.radio_group.item(
                                                    x,
                                                    value=x,
                                                    **{
                                                        "data-testid": f"radio-input-{x.lower()}"
                                                    },
                                                ),
                                            ),
                                            required=True,
                                            name="is_closing_account",
                                            default_value="Yes",
                                            direction="row",
                                        ),
                                        rx.hstack(
                                            rx.button(
                                                rx.text(
                                                    "Submit",
                                                    size=default_button_text_size,
                                                ),
                                                type="submit",
                                                size=default_button_size,
                                                **{"data-testid": "submit-button"},
                                            ),
                                            rx.dialog.close(
                                                rx.button(
                                                    "Close", size=default_button_size
                                                )
                                            ),
                                        ),
                                    ),
                                    on_submit=[
                                        State.handle_checkout_choice,
                                        lambda: State.generate_item_payment_qr(
                                            "tab", State.get_user_debt
                                        ),
                                    ],
                                )
                            ),
                            stripe_payment_dialog("tab", State.get_user_debt),
                        ),
                    ),
                    rx.text(
                        f"Pay your tab securely via Stripe. Please review your registrations below before paying.",
                        size=default_text_size,
                        opacity=rx.cond(is_user_debt_0, 0.3, 1),
                    ),
                    align="center",
                ),
                rx.cond(
                    is_user_debt_0,
                    rx.text(
                        "You have no orders to pay for! Please see reception if you wish to check out.",
                        size=default_text_size,
                    ),
                ),
                rx.text("Registrations:", size=default_text_size, weight="bold"),
                rx.scroll_area(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Time"),
                                rx.table.column_header_cell("Item"),
                                rx.table.column_header_cell("Quantity", align="right"),
                                rx.table.column_header_cell(
                                    "Unit Price", align="right"
                                ),
                                rx.table.column_header_cell("Total", align="right"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                State.current_user_orders_in_reverse_chronological_order,
                                show_row,
                            )
                        ),
                    ),
                    scrollbars="vertical",
                    style={"height": "70vh"},
                ),
            )
        )
    )


def admin() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.heading(f"Admin", size=default_heading_size),
                rx.button(
                    rx.text("Breakfast", size=default_button_text_size),
                    on_click=rx.redirect("/admin/breakfast"),
                    size=default_button_size,
                ),
                rx.button(
                    rx.text("Dinner", size=default_button_text_size),
                    on_click=rx.redirect("/admin/dinner"),
                    size=default_button_size,
                ),
            )
        )
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
        ),
        spacing="2",
    )


def show_signup(meal: Meal_Model):
    has_allergies = meal.allergies != ""
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
                rx.text(rx.cond(meal.served, "✅", "✖️"), size="8"),
                on_click=lambda: State.set_served(meal.meal_id, ~meal.served),
                color_scheme=rx.cond(meal.served, "green", "red"),
                size="4",
                **{"data-testid": "served-button"},
            )
        ),
        key=meal.meal_id,
        bg=rx.cond(has_allergies, "#FC281D20", "transparent"),
        **{"data-testid": "meal-row"},
    )


def admin_dinner() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.heading("Dinner", size=default_heading_size),
                rx.hstack(
                    admin_refresh_top_bar(),
                    rx.button(
                        rx.text("Late sign-up", size=default_button_text_size),
                        on_click=State.redirect_to_later_dinner_signup,
                        size=default_button_size,
                        **{"data-testid": "late-signup-button"},
                    ),
                    spacing="2",
                ),
                # Make the two columns share the available space evenly
                rx.hstack(
                    rx.vstack(
                        rx.text.strong(f"Total eating dinner: {State.dinner_count}"),
                        rx.text.strong(
                            f"Total served: {State.dinner_count_served}",
                            **{"data-testid": "total-served"},
                        ),
                        rx.text(f"Meat: {State.dinner_count_meat}"),
                        rx.text(f"Vegetarian: {State.dinner_count_vegetarian}"),
                        rx.text(f"Vegan: {State.dinner_count_vegan}"),
                        flex="1",
                    ),
                    rx.vstack(
                        rx.text.strong(
                            f"Guests eating dinner: {State.dinner_count_guests}"
                        ),
                        rx.text.strong(
                            f"Total served: {State.dinner_count_guests_served}",
                            **{"data-testid": "total-guests-served"},
                        ),
                        rx.text(f"Meat: {State.dinner_count_guests_meat}"),
                        rx.text(f"Vegetarian: {State.dinner_count_guests_vegetarian}"),
                        rx.text(f"Vegan: {State.dinner_count_guests_vegan}"),
                        flex="1",
                    ),
                    rx.vstack(
                        rx.text.strong(
                            f"Volunteers eating dinner: {State.dinner_count_volunteers}"
                        ),
                        rx.text.strong(
                            f"Total served: {State.dinner_count_volunteers_served}",
                            **{"data-testid": "total-volunteers-served"},
                        ),
                        rx.text(f"Meat: {State.dinner_count_volunteers_meat}"),
                        rx.text(
                            f"Vegetarian: {State.dinner_count_volunteers_vegetarian}"
                        ),
                        rx.text(f"Vegan: {State.dinner_count_volunteers_vegan}"),
                        flex="1",
                    ),
                    spacing="4",
                    justify="between",
                    width="100%",
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
                    rx.table.body(rx.foreach(State.todays_dinner_meals, show_signup)),
                    variant="surface",
                    size="3",
                ),
            )
        )
    )


def admin_breakfast() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.heading("Breakfast", size=default_heading_size),
                admin_refresh_top_bar(),
                rx.vstack(
                    rx.text.strong(f"Total eating breakfast: {State.breakfast_count}"),
                    rx.text(
                        f"Total served: {State.breakfast_count_served}",
                        **{"data-testid": "total-served"},
                    ),
                    flex="1",
                ),
                rx.scroll_area(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Name"),
                                rx.table.column_header_cell("Menu item"),
                                rx.table.column_header_cell("Allergies"),
                                rx.table.column_header_cell("Served"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(State.todays_breakfast_meals, show_signup)
                        ),
                        variant="surface",
                        size="3",
                    ),
                    type="always",
                    scrollbars="vertical",
                    style={"height": "80vh"},
                ),
            )
        )
    )


def admin_user_page() -> rx.Component:
    return rx.container(
        rx.center(
            rx.vstack(
                rx.heading("User information", size=default_heading_size),
                rx.button(
                    rx.text("Go back", size=default_button_text_size),
                    on_click=rx.redirect("/admin"),
                    size=default_button_size,
                ),
                rx.text(
                    f"Full name: {State.current_user.first_name} {State.current_user.last_name}"
                ),
                rx.text(f"Nick name: {State.current_user.nick_name}"),
                rx.text(f"Owes: {State.get_user_debt}€"),
            )
        )
    )
