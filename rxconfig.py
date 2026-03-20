import reflex as rx

config = rx.Config(
    app_name="obhonesty",
    frontend_port=3000,
    backend_port=8000,
    db_url="postgresql://postgres:postgres@db:5432/reflex_db",
    frontend_url="http://app:3000",
    backend_url="http://app:8000",
    backend_host="0.0.0.0",
    cors_allowed_origins=["*"],
    vite_allowed_hosts=True,
)
