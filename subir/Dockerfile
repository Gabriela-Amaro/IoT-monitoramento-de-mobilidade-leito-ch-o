FROM python:3.9-slim
WORKDIR /app
RUN pip install flask flask-sqlalchemy flask-socketio psycopg2-binary
COPY . .
CMD ["python", "app.py"]