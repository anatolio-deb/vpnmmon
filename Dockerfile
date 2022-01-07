FROM python:buster
WORKDIR /code
RUN apt update
COPY . .
RUN python3 -m pip install poetry
RUN python3 -m poetry export -o requirements.txt
RUN python3 -m pip install -r requirements.txt
