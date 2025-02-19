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
      size="4"
    )
  return rx.container(
    rx.center(
      rx.vstack(
        rx.heading(
          "Welcome to the Olive Branch honest self-service",
          size=default_heading_size
        ),
        rx.hstack(
          rx.text("New here?", size=default_text_size),
          rx.button(
            rx.icon("user-plus"),
            rx.text("Sign up for self-service", size=default_button_text_size),
            color_scheme="green",
            on_click=rx.redirect("/signup")
          )
        ),
        rx.text(f"Find yourself and place an order", size=default_text_size),
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
      )
    )
  )


def user_page() -> rx.Component:
  def item_button(item: Item) -> rx.Component:
    title: str = f"{item.name} (€{two_decimal_points(item.price)})"
    return rx.dialog.root(
        rx.dialog.trigger(rx.button(
          rx.text(title, size=default_button_text_size),
          color_scheme='gray',
          size="4"
        )),
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
                  type="number"
                )
              ),
              rx.flex(
                rx.dialog.close(
                  rx.button("Register", type="submit")
                ), 
                rx.dialog.close(rx.button(f"Cancel")),
                spacing="3",
                justify="end" 
              ),
              on_submit=State.order_item
            ), 
            spacing="3"
          ),
        )
      )
  return rx.container(rx.center(rx.vstack(
    rx.heading(
      f"Hello {State.current_user.nick_name}", size=default_heading_size
    ),
    rx.button(
      rx.icon("list"),
      rx.text("View orders", size=default_button_text_size),
      on_click=rx.redirect("/info")
    ),
    rx.cond(
      State.breakfast_signup_available,
      rx.button(
        rx.icon("egg-fried"),
        rx.text(
          "Sign up for breakfast / packed lunch",
          size=default_button_text_size
        ),
        on_click=rx.redirect("/breakfast")
      ),
      rx.text(
        f"Breakfast sign-up closed "
        f"(last sign-up at {State.admin_data['breakfast_signup_deadline']})",
        size=default_text_size
      )
    ), 
    rx.cond(
      State.dinner_signup_available,
      rx.button(
        rx.icon("utensils"),
        rx.text("Sign up for dinner", size=default_button_text_size),
        on_click=rx.redirect("/dinner")
      ),
      rx.text(
        f"Dinner sign-up closed "
        f"(last sign-up at {State.admin_data['dinner_signup_deadline']}, "
        f"for late sign-ups, please ask the kitchen staff)",
        size=default_text_size
      )
    ),
    rx.text("Register an item", size=default_text_size), 
    rx.button(
      rx.icon("circle-plus"),
      rx.text("Custom item", size=default_button_text_size),
      on_click=rx.redirect("/custom_item")
    ),
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
      style={"height": "55vh"}
    ),
    rx.text("Remember when you are done to", size=default_text_size),
    rx.button(
      rx.icon("door-open"),
      rx.text("Log out", size=default_button_text_size),
      color_scheme="red",
      on_click=rx.redirect("/")
    ),
    rx.text("please :)", size=default_text_size)
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
          tax_categories,
          default_value=tax_categories[0],
          name="tax_category"
        ),
        rx.text("Comment"),
        rx.input(placeholder="optional", name="custom_item_description"),
        rx.button(
          rx.text("Register", size=default_button_text_size), type="submit"
        )
      ),
      on_submit=State.order_custom_item
    ),
    rx.button(
      rx.text("Cancel", size=default_button_text_size),
      on_click=rx.redirect("/user")
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
            rx.button(
              rx.text("Submit", size=default_button_text_size), type="submit"
            )
          ),
          on_submit=State.submit_signup,
          reset_on_submit=True
        ),
        rx.button(
          rx.text("Go back", size=default_button_text_size),
          on_click=rx.redirect("/")
        ),
      ),
    ),
  )

def dinner_signup_page() -> rx.Component:
  return rx.container(rx.center(
    rx.vstack(
      rx.form(
        rx.vstack(
          rx.heading("Sign up for dinner", size=default_heading_size),
          rx.text(
            f"Note: you are signing up for todays dinner. "
            f"Sign up again tomorrow for tomorrows dinner. "
            f"Price per person is {State.admin_data['dinner_price']}€. "
            f"If you are signing up yourself, just write your own full name. "
            f"You can also sign up someone else on your tab, "
            f"in that case write the full name of the guest you are signing up."
          ),
          rx.text("First name of dinner guest", weight="bold"),
          rx.input(
            placeholder="First name of dinner guest",
            name="first_name",
            required=True
          ),
          rx.text("Last name of dinner guest", weight="bold"),
          rx.input(
            placeholder="Last name of dinner guest",
            name="last_name",
            required=True
          ),
          rx.text("Dietary preferences", weight="bold"),
          rx.select(
            ["Vegan", "Vegetarian", "Meat"],
            default_value="Vegan",
            name="diet"
          ),
          rx.text("Allergies", weight="bold"),
          rx.input(
            name="allergies"
          ),
          rx.button(
            rx.text("Register", size=default_button_text_size), type="submit"
          )
        ),
        on_submit=State.order_dinner
      ),
      rx.button(
        rx.text("Cancel", size=default_button_text_size),
        on_click=rx.redirect("/user")
      )
    )
  ))

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
            ["Vegan", "Vegetarian", "Meat"],
            default_value="Vegan",
            name="diet"
          ),
          rx.text("Allergies", weight="bold"),
          rx.input(
            name="allergies"
          ),
          rx.button(
            rx.text("Register", size=default_button_text_size),
            type="submit"
          )
        ),
        on_submit=State.order_dinner_late
      ),
      rx.button(
        rx.text("Cancel", size=default_button_text_size),
        on_click=rx.redirect("/admin/dinner")
      )
    )
  ))

def breakfast_signup_page() -> rx.Component:
  return rx.container(rx.center(
    rx.vstack(
      rx.form(
        rx.vstack(
          rx.heading("Sign up for breakfast", size=default_heading_size),
          rx.text(
            "Note: you are signing up for todays breakfast. "
            "Sign up again tomorrow for tomorrows breakfast."
          ),
          rx.spacer(),
          rx.text("First name of breakfast guest"),
          rx.input(
            placeholder="First name of breakfast guest",
            #default_value=State.current_user.full_name,
            name="first_name",
            required=True
          ),
          rx.text("Last name of breakfast guest"),
          rx.input(
            placeholder="Last name of breakfast guest",
            #default_value=State.current_user.full_name,
            name="last_name",
            required=True
          ),
          rx.text("Menu"),
          rx.select.root(
            rx.select.trigger(),
            rx.select.content(
              rx.foreach(
                breakfast_items,
                lambda item: rx.select.item(
                  f"{item} ({State.admin_data[item + "_price"]}€)",
                  value=item
                )
              )
            ),
            default_value=breakfast_items[0],
            name="menu_item"
          ),
          rx.text("Allergies"),
          rx.input(
            name="allergies"
          ),
          rx.button(
            rx.text("Register", size=default_button_text_size),
            type="submit"
          )
        ),
        on_submit=State.order_breakfast
      ),
      rx.button(
        rx.text("Cancel", size=default_button_text_size),
        on_click=rx.redirect("/user")
      )
    )
  ))


def user_info_page() -> rx.Component:
  def show_row(order: Order):
    return rx.table.row(
      rx.table.cell(order.time),
      rx.table.cell(order.item),
      rx.table.cell(f"{order.quantity}"),
      rx.table.cell(f"{order.price}€"),
      rx.table.cell(f"{order.total}€")
    )
  
  return rx.container(rx.center(rx.vstack(
    rx.heading(
      f"Hello {State.current_user.nick_name}", size=default_heading_size
    ),
    rx.button(
      rx.text(f"Back to orders and items", size=default_button_text_size),
      on_click=rx.redirect("/user")
    ),
		rx.text(
      "Note: new registrations may take a moment to show. "
      "If you made a registration by mistake, please talk to the reception "
      "and they will help correcting it.",
      size=default_text_size
		),
		rx.text("Your registrations:", size=default_text_size, weight="bold"),
		rx.scroll_area(
    	rx.table.root(
    	  rx.table.header(
    	    rx.table.row(
    	      rx.table.column_header_cell("Time"),
    	      rx.table.column_header_cell("Item"),
    	      rx.table.column_header_cell("Quantity"),
    	      rx.table.column_header_cell("Unit Price"),
    	      rx.table.column_header_cell("Total")
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
      on_click=State.redirect_to_admin_user_page(user)
    )
  return rx.container(rx.center(
    rx.vstack(
      rx.heading(f"Admin", size=default_heading_size),
      rx.button(
        rx.icon("refresh-cw"),
        rx.text("Reload", size=default_button_text_size),
        on_click=State.reload_sheet_data,
        color_scheme="green"
      ),
      rx.button(
        rx.text("Dinner", size=default_button_text_size),
        on_click=rx.redirect("/admin/dinner")
      ),
      rx.button(
        rx.text("Breakfast", size=default_button_text_size),
        on_click=rx.redirect("/admin/breakfast")
      ),
      rx.button(
        rx.text("Tax", size=default_button_text_size),
        on_click=rx.redirect("/admin/tax")
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
      on_click=rx.redirect("/admin")
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
      on_click=rx.redirect("/admin"), color_scheme="red"
    ),
    rx.button(
      rx.icon("refresh-cw"), rx.text("Reload", size=default_button_text_size),
      on_click=State.reload_sheet_data,
      color_scheme="green"
    ),
    spacing="2"
  )

def admin_dinner() -> rx.Component:
  def show_signup(signup: Order):
    return rx.table.row( 
      rx.table.cell(signup.receiver),
      rx.table.cell(signup.diet),
      rx.table.cell(signup.allergies),
      rx.table.cell(signup.comment)
    )

  return rx.container(rx.center(
    rx.vstack(
      rx.heading("Dinner", size=default_heading_size), 
      admin_refresh_top_bar(),
      rx.button(
        rx.text("Late sign-up", size=default_button_text_size),
        on_click=rx.redirect("/admin/late")
      ),
      rx.text(f"Total eating dinner: {State.dinner_count}"),
      rx.text(f"Vegan: {State.dinner_count_vegan}"),
      rx.text(f"Vegatarian: {State.dinner_count_vegetarian}"),
      rx.text(f"Meat: {State.dinner_count_meat}"),
      rx.table.root(
        rx.table.header(
          rx.table.row(
            rx.table.column_header_cell("Name"),
            rx.table.column_header_cell("Diet"),
            rx.table.column_header_cell("Allergies"),
            rx.table.column_header_cell("Volunteer"),
          )
        ),
        rx.table.body(
          rx.foreach(State.dinner_signups, show_signup)
        ),
        variant="surface",
        size="3"
      )
    )
  ))

def admin_breakfast() -> rx.Component:
  def show_signup(signup: Order):
    return rx.table.row( 
      rx.table.cell(signup.time),
      rx.table.cell(signup.receiver),
      rx.table.cell(signup.diet),
      rx.table.cell(signup.allergies)
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
              rx.table.column_header_cell("Diet"),
              rx.table.column_header_cell("Allergies")
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
      on_click=rx.redirect("/admin")
    ),
    rx.text(f"Full name: {State.current_user.first_name} {State.current_user.last_name}"),
    rx.text(f"Nick name: {State.current_user.nick_name}"),
    rx.text(f"Email: {State.current_user.email}"),
    rx.text(f"Phone: {State.current_user.phone_number}"),
    rx.text(f"Address: {State.current_user.address}"),
    rx.text(f"Owes: {State.get_user_debt}€")
  )))