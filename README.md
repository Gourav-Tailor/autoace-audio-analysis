# AutoACE Audio Analysis

A Cookiecutter-style Django project scaffold for a local API-first application using Docker, PostgreSQL, Django REST Framework, pytest, Ruff, Black, pre-commit and GitHub Actions.

## Stack

- Django 5
- Django REST Framework
- PostgreSQL 16
- Docker Compose
- pytest
- Ruff
- Black
- pre-commit
- GitHub Actions

## Local development

```bash
cp .env.example .env
docker compose up --build
```

Then open:

http://localhost:8000

## Commands

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py test
pytest
ruff check .
black .
```

## Environment

Configuration is read from environment variables using django-environ. Keep `.env` out of version control.
