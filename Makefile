.PHONY: dev-up dev-down blue-up green-up promote logs test fmt lint build load-test \
	create-venv activate-venv deactivate-venv

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

DEV_SERVICES=traefik app_blue redis_blue

dev-up:
	docker compose -f docker/compose.yml up -d $(DEV_SERVICES)

dev-down:
	docker compose -f docker/compose.yml down -v

blue-up:
	docker compose -f docker/compose.yml up -d traefik app_blue redis_blue
	echo "blue up"

green-up:
	docker compose -f docker/compose.yml up -d traefik app_green redis_green
	echo "green up"

promote:
	bash scripts/promote.sh

logs:
	bash -c 'COLOR=$$(grep -q "django-blue" docker/traefik/dynamic/active.yml && echo blue || echo green); docker compose -f docker/compose.yml logs -f app_$$COLOR'

test:
	pytest -q

fmt:
	ruff check --fix . || true
	black .

lint:
	ruff check .
	black --check .

build:
	docker build -f docker/Dockerfile -t django-ws:latest .

load-test: create-venv
	$(PIP) -q install websockets
	$(PY) scripts/load_test.py --host localhost --path /ws/chat/ --concurrency $${N:-6000}

test-session-resumption: create-venv
	$(PIP) -q install websockets
	$(PY) scripts/test_session_resumption.py

test-message-format: create-venv
	$(PIP) -q install websockets
	$(PY) scripts/test_message_format.py

test-sigterm: create-venv
	$(PIP) -q install websockets
	$(PY) scripts/test_sigterm_handling.py

cleanup-duplicates-preview:
	cd app && python ../scripts/cleanup_duplicate_messages.py --preview

cleanup-duplicates:
	cd app && python ../scripts/cleanup_duplicate_messages.py --cleanup

test-reconnect: create-venv
	$(PIP) -q install websockets
	$(PY) scripts/test_reconnect_functionality.py

test-broadcast: create-venv
	$(PIP) -q install websockets
	$(PY) scripts/test_broadcast.py

test-broadcast-api:
	bash scripts/test_broadcast_api.sh

test-graceful-shutdown: create-venv
	$(PIP) -q install websockets
	$(PY) scripts/test_sigterm_graceful.py

test-performance: create-venv
	$(PIP) -q install websockets
	$(PY) scripts/performance_test.py --concurrency 6000

create-venv:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PIP) -q install --upgrade pip

# Opens a new interactive shell with the venv activated. Type 'exit' to leave.
activate-venv: create-venv
	@. $(VENV)/bin/activate; \
	  echo "($(VENV)) active; type 'exit' to deactivate"; \
	  sh_name=$$(basename $$SHELL); \
	  if [ "$$sh_name" = "zsh" ]; then \
	    exec zsh -f -i; \
	  elif [ "$$sh_name" = "bash" ]; then \
	    exec bash --noprofile --norc -i; \
	  else \
	    exec $$SHELL -i; \
	  fi

# Informational: you cannot deactivate the parent shell from make.
deactivate-venv:
	@echo "If you used 'make activate-venv', type 'exit' to deactivate."
	@echo "If you manually activated, run: 'deactivate' in that shell."


