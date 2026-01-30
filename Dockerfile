# FROM ubuntu:22.04

# # Prevent interactive prompts during package install
# ENV DEBIAN_FRONTEND=noninteractive

# # Install basic dependencies (adjust as needed)
# RUN apt-get update && apt-get install -y \
#     bash \
#     curl \
#     git \
#     python3.12 \
#     python3-pip \
#     unzip \
#     && rm -rf /var/lib/apt/lists/*

# # Set working directory
# WORKDIR /app

# # Copy requirements script
# COPY . .

# # Make sure it is executable
# RUN chmod +x requirements.bash

# # Run dependency setup
# RUN ./requirements.bash

# # Default command
# CMD ["reflex", "run"]
FROM python:3.12-slim-bookworm

# # Prevent interactive prompts during package install
# ENV DEBIAN_FRONTEND=noninteractive

# # Install basic dependencies (adjust as needed)
# RUN apt-get update && apt-get install -y \
#     bash \
#     curl \
#     git \
#     python3.12 \
#     python3-pip \
#     unzip \
#     && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y unzip bash curl

# Set working directory
WORKDIR /app

# Copy requirements script
COPY . .

# Make sure it is executable
RUN chmod +x requirements.bash

# Run dependency setup
RUN ./requirements.bash

# Default command
CMD ["reflex", "run"]
