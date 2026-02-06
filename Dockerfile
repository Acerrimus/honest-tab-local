FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y unzip bash curl
WORKDIR /app
COPY . .
RUN chmod +x requirements.bash
RUN ./requirements.bash
CMD ["reflex", "run", "--loglevel", "debug"]
