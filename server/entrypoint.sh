#!/bin/bash

set -e

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"

log_info() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    printf "${GREEN}[${timestamp}] INFO: $1${NC}\n"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    printf "${RED}[${timestamp}] ERROR: $1${NC}\n"
}

main() {
	export SERVICE_START_DATETIME=$(date --utc '+%Y-%m-%d %H:%M:%S%z')

	if [[ "$ENVIRONMENT" = "DEV" ]] ; then
		log_info "Running in DEVELOPMENT mode."
		alembic upgrade head
		cd app
	elif [[ "$ENVIRONMENT" = "TEST" ]] ; then
		log_info "Running in TESTING mode."
		alembic upgrade head
		cd app
	elif [[ "$ENVIRONMENT" = "PROD" ]] ; then
		log_info "Running in PRODUCTION mode."
		cd app
	else
		log_error "Evironment is not specified."
	fi

	log_info "Current working directory: '$(pwd)'"

	if [ $# -eq 0 ]; then
		log_error "Error. No arguments found. Finished."
		exit -1;
	else
		log_info "Command: '$*'"
		exec "$@"
	fi
}

main "$@"
