FROM python:3.9-slim-bullseye

WORKDIR /app

COPY ./requirements.txt /app
RUN pip config --user set global.extra-index-url https://www.piwheels.org/simple
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8050 80

CMD [ "gunicorn", "--workers=5", "--threads=1", "-b 0.0.0.0:80", "index:server"]
