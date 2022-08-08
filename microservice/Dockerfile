FROM python:3.9-slim-bullseye

RUN mkdir /usr/src/app/
WORKDIR /usr/src/app/

COPY ./requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

COPY . /usr/src/app/

EXPOSE 5000 25 587
CMD ["python", "app.py"]