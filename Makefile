.PHONY: dev seed test build-frontend build-backend

dev:
	@echo "Starting ResQNet backend and frontend in parallel..."
	docker-compose up --build

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

seed:
	python scripts/seed_demo_data.py

test:
	cd backend && pytest tests/ -v

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
