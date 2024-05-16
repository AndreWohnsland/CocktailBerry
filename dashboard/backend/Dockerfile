FROM python:3.11-slim-bookworm

WORKDIR /app

COPY ./requirements.txt /app
RUN pip config --user set global.extra-index-url https://www.piwheels.org/simple
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8080

CMD ["python", "main.py"]