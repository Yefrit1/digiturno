# Digiturno System

## Features
- Customer ticket generation
- Real-time queue display
- Staff management interface
- Admin management interface
- Reports module

## Installation
- Install RabbitMQ and Erlang (versions used: RabbitMQ 4.0.7 and Erlang 27.3)
- Python 3.11.4
- Python requirements (versions used): b2sdk (2.8.1), pika (1.3.2), pyinstaller (6.12.0), PyQt5 (5.15.9), python-dotenv (1.0.0)
- Turn .py into .exe: Run cmd with the following for each .py file:
  pyinstaller --onefile --noconsole file_name.py

## .env structure
RABBITMQ_USER=YOUR_USER
RABBITMQ_PASS=YOUR_PASSWORD
LOCAL_IP=NETWORK_LOCAL_IP
PUBLIC_IP=NETWORK_PUBLIC_IP
PORT=5672 (default RabbitMQ port, change if needed)
B2_KEY_ID=BACKBLAZE_KEY_ID
B2_APP_KEY=BACKBLAZE_APP_KEY
B2_BUCKET=BACKBKLAZE_BUCKET_NAME

## Usage
- Run digiturnoPantalla on the 'server' device, where the DB will be stored.
- Run reporter in the background, that way report generation will be available all the time the server is on.
- Run digiturnoUsuario on some touch-screen device for the customers to use.
- Run digiturnoFuncionario on the staff's devices to manage turns.
- Run digiturnoAdmin on any device inside the server's network (or remotely, if firewall settings properly setup) to manage staff accounts.
- Run digiturnoReportes, same network logic as digiturnoAdmin, to get a turns information report for a certain date.
