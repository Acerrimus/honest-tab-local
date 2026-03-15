import reflex as rx


def user_button(*children, **kwargs):
    return rx.button(
        *children,
        font_size="1.5rem",
        padding="1.5rem 2rem",
        border_radius="0.5rem",
        **kwargs,
    )
