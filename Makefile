# Makefile

.PHONY: all format check validate test local-test
NSD_CONTROL_PORT ?= 8952

# Default target: runs format and check
all: validate test

# Format the code using ruff
format:
	ruff format --check --diff .

reformat-ruff:
	ruff format .

# Check the code using ruff
check:
	ruff check .

fix-ruff:
	ruff check . --fix

fix: reformat-ruff fix-ruff
	@echo "Updated code."

vulture:
	vulture . --exclude .venv,migrations,tests --make-whitelist

complexity:
	radon cc . -a -nc

xenon:
	xenon -b D -m B -a B .

pyright:
	pyright

test:
	pytest -m "not integration"

local-test:
	@set -eu; \
	mkdir -p tests/integration/runtime/certs; \
	mkdir -p tests/integration/runtime/state; \
	mkdir -p tests/integration/runtime/zones/dynamic; \
	trap 'NSD_CONTROL_PORT=$(NSD_CONTROL_PORT) docker compose -f docker-compose.integration.yml logs || true; NSD_CONTROL_PORT=$(NSD_CONTROL_PORT) docker compose -f docker-compose.integration.yml down -v || true' EXIT; \
	NSD_CONTROL_PORT=$(NSD_CONTROL_PORT) docker compose -f docker-compose.integration.yml up -d --build; \
	NSD_CONTROL_PORT=$(NSD_CONTROL_PORT) docker compose -f docker-compose.integration.yml exec -T nsd nsd-checkconf /etc/nsd/nsd.conf; \
	for i in $$(seq 1 60); do \
		if NSD_CONTROL_PORT=$(NSD_CONTROL_PORT) docker compose -f docker-compose.integration.yml exec -T nsd nsd-control -c /etc/nsd/nsd.conf status >/tmp/nsd-status.log 2>&1; then \
			break; \
		fi; \
		sleep 1; \
	done; \
	NSD_CONTROL_PORT=$(NSD_CONTROL_PORT) docker compose -f docker-compose.integration.yml exec -T nsd nsd-control -c /etc/nsd/nsd.conf status >/tmp/nsd-status.log 2>&1; \
	cat /tmp/nsd-status.log; \
	PYNSD_TEST_CONTROL_PORT=$(NSD_CONTROL_PORT) pytest -m integration tests/test_integration.py -v

# Validate the code (format + check)
validate: format check complexity pyright vulture
	@echo "Validation passed. Your code is ready to push."
