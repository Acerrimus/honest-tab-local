FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y unzip bash curl sqlite3
WORKDIR /app
COPY . .
RUN chmod +x requirements.bash
RUN ./requirements.bash
RUN reflex db init
CMD ["reflex", "run", "--loglevel", "debug"]
