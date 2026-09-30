# VehicleCare

A small Flask web app to track vehicles and their maintenance/service history.

## Features
- Add / view / update / delete vehicles
- Add / update / delete service records per vehicle
- Dashboard showing upcoming and overdue services
- `GET /api/vehicles` — JSON API
- `GET /health` — health check for uptime monitors / load balancers
- Current git commit shown in the site footer

## Tech stack
- Backend: Python + Flask
- Frontend: HTML + Bootstrap 5
- Storage: JSON file (`data/data.json`) — no database
- Tests: pytest
- Lint: flake8
- CI/CD: GitHub Actions
- Container: Docker
- Deployment: Render

## Project structure
```
vehiclecare/
├── app.py                  # Flask app (routes, data logic)
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .flake8
├── .gitignore
├── data/
│   └── data.json           # vehicle + service data
├── templates/               # Jinja2 HTML templates
├── static/css/style.css
├── tests/
│   └── test_app.py
└── .github/workflows/ci.yml # GitHub Actions pipeline
```

## Run locally
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Visit http://localhost:5000

## Run tests / lint
```bash
pytest -v
flake8 .
```

## Run with Docker
```bash
docker build --build-arg GIT_COMMIT=$(git rev-parse HEAD) -t vehiclecare .
docker run -p 5000:5000 vehiclecare
```

## Deploying to Render
1. Push this repo to GitHub (public).
2. On Render: **New +** → **Web Service** → connect the repo.
3. Environment: **Docker** (Render will use the Dockerfile automatically).
4. Render sets `PORT` automatically; the app already reads it via `os.environ.get("PORT")`.
5. (Optional) Add an environment variable `GIT_COMMIT` if you want a specific commit shown.
6. Deploy. Render gives you a live URL.

## Git workflow (for the assignment)
See the numbered checkpoints in the assistant's reply for exactly when to run
`git init`, `git add`, `git commit`, and `git push` while building this out.
