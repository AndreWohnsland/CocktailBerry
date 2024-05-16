FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update
RUN apt-get install -y build-essential curl
# Get Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

COPY ./requirements.txt /app
RUN pip config --user set global.extra-index-url https://www.piwheels.org/simple
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8080

CMD ["python", "main.py"]