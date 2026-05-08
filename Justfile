set dotenv-load := true

default:
    @just --list

compose args:
    podman compose {{ args }}

dev:
    code .
    podman compose up

up *args:
    podman compose up {{ args }}

down *args:
    podman compose down {{ args }}
    podman volume ls -q | grep -E '_[a-f0-9]{32,}$' | xargs -r podman volume rm

restart *args:
    podman compose restart {{ args }}

logs *args:
    podman compose logs -f {{ args }}

migrate:
    podman compose exec backend uv run python manage.py makemigrations
    podman compose exec backend uv run python manage.py migrate

backend:
    podman compose exec backend bash

worker:
    podman compose exec worker bash
