"""Entry point for gunicorn and the Flask CLI.

    flask --app wsgi init-db
    flask --app wsgi seed-db
    flask --app wsgi create-admin
    flask --app wsgi run --debug
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
