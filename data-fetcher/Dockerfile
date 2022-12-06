FROM arm32v7/python:3.11-slim-buster

LABEL maintainer "Christopher Meister-Paeslack <christopher.paeslack@gmail.com>"

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /

RUN apt-get update -y
RUN apt-get install python3 -y
RUN python3 -m pip install --upgrade pip
RUN apt-get install gcc python3-dev -y
RUN pip3 install -r /requirements.txt

COPY ./ ./

CMD ["python3", "./src/app.py"]
