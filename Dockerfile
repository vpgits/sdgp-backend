# # Use an official Python runtime as a parent image
# FROM python:3.11.7-slim

# # Set the working directory in the container
# WORKDIR /usr/src/app

# # Copy the current directory contents into the container at /usr/src/app
# COPY . .

# # Install RabbitMQ if needed (uncomment if necessary)
# # RUN apt-get update && apt-get install -y rabbitmq-server
# # RUN /bin/bash install_rabbitmq.sh
# # RUN apt-get update && / apt-get install rabbitmq-server -y

# # Install any needed packages specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# # Expose ports for Uvicorn and Flower
# EXPOSE 80
# EXPOSE 5555

# # Install Supervisor
# RUN apt-get update && apt-get install -y supervisor

# # Copy the Supervisor configuration file into the container
# COPY supervisord.conf /etc/supervisor/supervisord.conf

# # Start Supervisor to manage processes
# CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]