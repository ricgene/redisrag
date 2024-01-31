FROM python:3.9-slim

WORKDIR /app

COPY . .

WORKDIR /app/webapi

RUN pip install poetry

RUN poetry install

CMD ["sh", "entrypoint.sh"]