FROM python:3.13-slim-trixie

RUN mkdir /usr/src/app/
WORKDIR /usr/src/app/

COPY ./requirements.txt /usr/src/app/
RUN pip config --user set global.extra-index-url https://www.piwheels.org/simple \
  && python -m pip install --upgrade pip \
  && pip install -r requirements.txt

COPY . /usr/src/app/

EXPOSE 5000
CMD ["python", "app.py"]