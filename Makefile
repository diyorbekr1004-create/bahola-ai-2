.PHONY: install backend frontend dev seed test lint docker-up docker-down clean

PY ?= python

install:
	$(PY) -m pip install -r backend/requirements.txt

backend:
	cd backend && $(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	$(PY) -m streamlit run frontend/streamlit_app.py --server.port 8501

dev:
	bash scripts/run_dev.sh

seed:
	$(PY) scripts/seed.py --reset

test:
	cd backend && $(PY) -m pytest -q

lint:
	$(PY) -m pyflakes backend/app frontend scripts

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v

clean:
	rm -rf exports/*.xlsx exports/*.docx exports/*.csv data.db backend/.pytest_cache
