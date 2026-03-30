# ------------------------------- INIT ------------------------------------

.RECIPEPREFIX := $() $()
SHELL := bash -O extglob

# ------------------------------- META ------------------------------------

SOURCE_VERSION = $(shell cat VERSION | tr -d '[:space:]')

SOURCE_DATE = $(shell TZ="Europe/Minsk"                                   \
    date -d "@$(shell git log -1 --format='%ct')" '+%Y-%m-%d %H:%M:%S %z')

BUILD_DATE = $(shell TZ="Europe/Minsk"                                    \
    date '+%Y-%m-%d %H:%M:%S %z')

# Run only of daemin.json is empty or not exists
# If it contains data you need to add
# "log_driver": "json-file" in main section and
# "labels-regex": "^.+" in log-opts section
init_docker_logging_driver:
    sudo sh -c 'echo "\
    {\n\
        \"log-driver\": \"json-file\",\n\
        \"log-opts\": {\n\
            \"labels-regex\": \"^.+\"\n\
        }\n\
    }\n" >> /etc/docker/daemon.json' && sudo systemctl restart docker

# ------------------------------- APP -----------------------------------

MANIFEST := -f docker-compose.yaml

build: docker-compose.yaml
    @docker compose -p kintree ${MANIFEST} build                         \
        --build-arg SOURCE_VERSION="$(SOURCE_VERSION)"                    \
        --build-arg SOURCE_DATE="$(SOURCE_DATE)"                          \
        --build-arg BUILD_DATE="$(BUILD_DATE)"

start: docker-compose.yaml
    @docker compose -p kintree ${MANIFEST} up

startd: docker-compose.yaml
    @docker compose -p kintree ${MANIFEST} up --detach

stop: docker-compose.yaml
    @docker compose -p kintree ${MANIFEST} down

restart: docker-compose.yaml
    @docker compose -p kintree ${MANIFEST} restart

logs:
    @docker compose -p kintree ${MANIFEST} logs -f


# ------------------------------- LINT ------------------------------------

black:
    black --check --config=server/pyproject.toml server/app

isort:
    isort --check-only --settings-file=server/pyproject.toml server/app

flake:
    flake8 --toml-config=server/pyproject.toml server/app

mypy:
    mypy --config-file=server/pyproject.toml server/app

eslint:
    cd client && pnpm run lint:eslint

types:
    cd client && pnpm run lint:types

lint:
    pre-commit run --config .pre-commit-config.yaml --all-files

# ------------------------------ TESTS ------------------------------------

test:
    @echo "Not implemented yet"

# -------------------------------------------------------------------------
