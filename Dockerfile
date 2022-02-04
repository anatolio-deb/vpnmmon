FROM python:slim
RUN apt update
RUN apt install git traceroute -y
RUN git config --global user.email nikiforova693@gmail.com
RUN git config --global user.name anatolio-deb
WORKDIR /code
COPY . .
RUN pip install poetry
RUN poetry export -o requirements.txt --without-hashes --dev
RUN pip install -r requirements.txt