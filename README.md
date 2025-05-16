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

## Usage
- Run digiturnoPantalla on the 'server' device, where the DB will be stored.
- Run reporter in the background, that way report generation will be available all the time the server is on.
- Run digiturnoUsuario on some touch-screen device for the customers to use.
- Run digiturnoFuncionario on the staff's devices to manage turns.
- Run digiturnoAdmin on any device inside the server's network (or remotely, if firewall settings properly setup) to manage staff accounts.
- Run digiturnoReportes, same network logic as digiturnoAdmin, to get a turns information report for a certain date.

## Assets Setup

The following programs require these image files in the same directory:
- digiturnoPantalla:
  - `logoCoohem.png` (Organization logo)
- digiturnoUsuario:
  - `logoCoohem.png` (Organization logo)
  - `ok.png`
  - `delete.png`
  - `exit.png`
  - `clear.png`
  - `return.png`

Additionally, all programs require the .env file with the following structure:

- `RABBITMQ_USER=your_user`
- `RABBITMQ_PASS=your_password`  
- `LOCAL_IP=192.168.1.100`  
- `PUBLIC_IP=your.domain.com`  
- `PORT=5672` *(Default RabbitMQ port)*  
- `B2_KEY_ID=your_backblaze_key`  
- `B2_APP_KEY=your_backblaze_appkey`  
- `B2_BUCKET=your_bucket_name`  