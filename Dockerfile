# -----------------------------------------------------------------------------------
# Python-base stage sets up all shared env vars
FROM python:3.12-alpine AS python-base

# Metadata (author email)
LABEL author.email="mitkojenia@gmail.com"

# Metadata (author name)
LABEL author.name="Eugene Mitsko"

# Metadata
ARG SOURCE_VERSION
ARG SOURCE_DATE
ARG BUILD_DATE

# Important environment variables
ENV                                                                                 \
    # Force stdout and stderr streams to be unbuffered
    PYTHONUNBUFFERED=1                                                              \
    # Prevents python from creating .pyc files
    PYTHONDONTWRITEBYTECODE=1                                                       \
    # Disable pip cache
    PIP_NO_CACHE_DIR=0                                                              \
    # Disable periodically checking PyPI for a new version of pip
    PIP_DISABLE_PIP_VERSION_CHECK=1                                                 \
    # Set the default socket timeout
    PIP_DEFAULT_TIMEOUT=100                                                         \
    # Root of the project
    ROOT_DIR="/code"                                                                \
    # Make poetry to be installed into this location
    UV_INSTALL_DIR="/usr/local/bin"                                                 \
    # This is where requirements will live
    PYSETUP_PATH="/code/project"                                                    \
    # This is where venv will live
    VENV_PATH="/code/project/.venv"                                                 \
    #
    PATH="/code/project/.venv/bin:$PATH:$UV_INSTALL_DIR"                            \
    # Frontend static
    NODE_STATIC_PATH="/code/project/dist"                                           \
    # Backend static
    PYTHON_STATIC_PATH="/code/project/static/web"                                   \
    # Source version
    SOURCE_VERSION=${SOURCE_VERSION}                                                \
    # Source date
    SOURCE_DATE=${SOURCE_DATE}                                                      \
    # Build date
    BUILD_DATE=${BUILD_DATE}

# -----------------------------------------------------------------------------------
# Node-base stage sets up all shared env vars
FROM node:22-alpine AS node

# Important environment variables
ENV                                                                                 \
    # Root of the project
    ROOT_DIR="/code/project"

# Set workdir
WORKDIR $ROOT_DIR

# Install core deps
RUN                                                                                 \
    # Install build deps
    apk add --no-cache                                                              \
    # Git
	git                                                                             \
    # Curl
	curl                                                                            \
    # Udev
	udev &&                                                                         \
    # Upgrade
    apk upgrade &&                                                                 \
    # Install pnpm
	npm install -g pnpm

# Copy package files
COPY ./client/package.json ./client/pnpm-lock.yaml ./

# Install dependencies using npm
RUN pnpm install --frozen-lockfile

# Copy source code
COPY ./client .

# Build the application
RUN pnpm run build

# -----------------------------------------------------------------------------------
# Builder-base stage installs all necessary core deps
FROM python-base AS builder-base

# Install build dependencies
RUN                                                                                 \
    # Install build deps
    apk add --no-cache                                                              \
    # Install bash shell (better scripting support than default /bin/sh)
    bash                                                                            \
    # Install curl for downloading files and making HTTP requests
    curl                                                                            \
    # Install C compiler for compiling Python extensions
    gcc                                                                             \
    # Install musl-dev (standard C library headers) for Python C extensions
    musl-dev                                                                        \
    # Install PostgreSQL development libraries (for psycopg3, asyncpg, ...)
    postgresql-dev                                                                  \
    # Install Python3 development headers (for building Python modules)
    python3-dev

# Override default shell from sh to bash
SHELL ["/bin/bash", "-c"]

# -----------------------------------------------------------------------------------
# Poetry-base stage installs poetry, creates venv and installs project deps
FROM builder-base AS uv-base

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR $PYSETUP_PATH

# Copy project requirement files here to ensure they will be cached
COPY server/pyproject.toml server/uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv && uv sync --frozen --no-dev

# -----------------------------------------------------------------------------------
# Development stage is used during development / testing
FROM builder-base AS development

# Set working directory
WORKDIR $PYSETUP_PATH

# Copy uv binary
COPY --from=uv-base $UV_INSTALL_DIR/uv $UV_INSTALL_DIR/uv

# Copy virtual environment with all dependencies
COPY --from=uv-base $PYSETUP_PATH $PYSETUP_PATH

# Copy static files
COPY server/static ./static

# Copy static files from node
COPY --from=node $NODE_STATIC_PATH $PYTHON_STATIC_PATH

# Install dev dependencies
RUN uv sync --frozen

# Container will listen this port
EXPOSE 8000

# -----------------------------------------------------------------------------------
# Testing stage is used for runtime
FROM python-base AS testing

# Install runtime dependencies
RUN                                                                                 \
    # Update CA certificates
    update-ca-certificates &&                                                       \
    # Install runtime dependencies
    apk add --no-cache                                                              \
    # Install bash shell (better scripting support than default /bin/sh)
    bash                                                                            \
    # Install curl for downloading files and making HTTP requests
    curl                                                                            \
    # Install libpq (required for psycopg3, asyncpg, ...)
    libpq

# Override default shell from sh to bash
SHELL ["/bin/bash", "-c"]

# Copy uv binary
COPY --from=uv-base $UV_INSTALL_DIR/uv $UV_INSTALL_DIR/uv

# Copy virtual environment with all dependencies
COPY --from=uv-base $PYSETUP_PATH $PYSETUP_PATH

# Create kintree group and user
RUN                                                                                 \
    # Create group named "kintree"
    addgroup -S -g 1001 kintree &&                                                 \
    # Create user named "kintree_user" and add it to group "kintree"
    adduser -S -u 1001 -G kintree kintree_user &&                                      \
    # Change the ownership of the workdir to the user "kintree_user"
    chown -R kintree_user:kintree_user $ROOT_DIR

# Switch to the non-root user "kintree_user"
USER kintree_user

# Set working directory
WORKDIR $PYSETUP_PATH

# Copy project files
COPY server/app ./app

# Copy meta file
COPY server/entrypoint.sh server/alembic.ini VERSION ./

# Copy static files
COPY server/static ./static

# Copy static files from node
COPY --from=node $NODE_STATIC_PATH $PYTHON_STATIC_PATH

# Run entrypoint
ENTRYPOINT [ "./entrypoint.sh" ]

# Run server
CMD [\
    "python",\
    "-m",\
    "uvicorn",\
    "main:create_app",\
    "--host", "0.0.0.0",\
    "--port", "8000",\
    "--proxy-headers",\
    "--forwarded-allow-ips", "*"\
]

# Container will listen this port
EXPOSE 8000

# -----------------------------------------------------------------------------------
# Production stage is used for runtime
FROM python-base AS production

# Install runtime dependencies
RUN                                                                                 \
    # Update CA certificates
    update-ca-certificates &&                                                       \
    # Install runtime dependencies
    apk add --no-cache                                                              \
    # Install bash shell (better scripting support than default /bin/sh)
    bash                                                                            \
    # Install curl for downloading files and making HTTP requests
    curl                                                                            \
    # Install libpq (required for psycopg3, asyncpg, ...)
    libpq

# Override default shell from sh to bash
SHELL ["/bin/bash", "-c"]

# Copy uv binary
COPY --from=uv-base $UV_INSTALL_DIR/uv $UV_INSTALL_DIR/uv

# Copy virtual environment with all dependencies
COPY --from=uv-base $PYSETUP_PATH $PYSETUP_PATH

# Create kintree group and user
RUN                                                                                 \
    # Create group named "kintree"
    addgroup -S -g 1001 kintree &&                                                 \
    # Create user named "kintree_user" and add it to group "kintree"
    adduser -S -u 1001 -G kintree kintree_user &&                                      \
    # Change the ownership of the workdir to the user "kintree_user"
    chown -R kintree_user:kintree_user $ROOT_DIR

# Switch to the non-root user "kintree_user"
USER kintree_user

# Set working directory
WORKDIR $PYSETUP_PATH

# Copy project files
COPY server/app ./app

# Copy meta file
COPY server/entrypoint.sh server/alembic.ini VERSION ./

# Copy static files
COPY server/static ./static

# Copy static files from node
COPY --from=node $NODE_STATIC_PATH $PYTHON_STATIC_PATH

# Run entrypoint
ENTRYPOINT [ "./entrypoint.sh" ]

# Run server
CMD [\
    "python",\
    "-m",\
    "uvicorn",\
    "main:create_app",\
    "--host", "0.0.0.0",\
    "--port", "8000",\
    "--proxy-headers",\
    "--forwarded-allow-ips", "*"\
]

# Container will listen this port
EXPOSE 8000
