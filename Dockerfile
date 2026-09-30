FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal on purpose
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bake the git commit into the image so the running app can show it in the footer.
# Pass it at build time: docker build --build-arg GIT_COMMIT=$(git rev-parse HEAD) -t vehiclecare .
ARG GIT_COMMIT=unknown
RUN echo "$GIT_COMMIT" > commit_sha.txt

ENV PORT=5000
EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]
