FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e . \
 && playwright install --with-deps chromium

COPY evaluation ./evaluation
COPY tests ./tests

RUN useradd -m agent && mkdir -p /app/data && chown -R agent /app /ms-playwright
USER agent
ENV BA_HEADLESS=true

# docker run --rm --env-file .env -v $(pwd)/data:/app/data browser-agent run "your task"
ENTRYPOINT ["browser-agent"]