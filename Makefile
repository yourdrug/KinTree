# ------------------------------- INIT ------------------------------------

.RECIPEPREFIX := $() $()
SHELL := bash -O extglob

# ------------------------------- META ------------------------------------

SOURCE_VERSION = $(shell cat VERSION | tr -d '[:space:]')

SOURCE_DATE = $(shell TZ="Europe/Minsk"                                   \
    date -d "@$(shell git log -1 --format='%ct')" '+%Y-%m-%d %H:%M:%S %z')

BUILD_DATE = $(shell TZ="Europe/Minsk"                                    \
    date '+%Y-%m-%d %H:%M:%S %z')

# ------------------------------- APP -----------------------------------

MANIFEST := -f docker-compose.yaml

build: docker-compose.yaml
    @docker compose -p kintree ${MANIFEST} build                         	\
        --build-arg SOURCE_VERSION="$(SOURCE_VERSION)"                    	\
        --build-arg SOURCE_DATE="$(SOURCE_DATE)"                          	\
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
