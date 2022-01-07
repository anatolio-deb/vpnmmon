FROM ubuntu:latest
WORKDIR /code
RUN apt update
RUN apt install python3.9 python3-pip traceroute -y
COPY . .
RUN python3.9 -m pip install poetry
RUN python3.9 -m poetry export -o requirements.txt
RUN python3.9 -m pip install requirements.txt
