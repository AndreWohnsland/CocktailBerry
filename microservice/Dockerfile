FROM python:3.9-slim-bullseye
RUN mkdir /usr/src/app/
COPY . /usr/src/app/
WORKDIR /usr/src/app/
EXPOSE 5000 25 587
RUN pip install -r requirements.txt
CMD ["python", "app.py"]