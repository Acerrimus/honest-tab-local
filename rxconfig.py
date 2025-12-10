import reflex as rx

config = rx.Config(
  app_name="obhonesty",
	frontend_port=3000,
	backend_port=8000,
	# backend_host="0.0.0.0",

	# api_url="http://192.168.0.105:8000",
	# deploy_url="http://192.168.0.105:3000",

	cors_allowed_origins=["*"],
)
