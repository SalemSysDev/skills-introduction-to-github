"""Entry point.

Development:  flask --app run run --debug
Production:   gunicorn -w 3 -b 127.0.0.1:8000 run:app
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
