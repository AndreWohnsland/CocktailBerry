FROM python:3.9-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8500 80

CMD [ "gunicorn", "--workers=5", "--threads=1", "-b 0.0.0.0:80", "index:server"]
