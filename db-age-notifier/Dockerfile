FROM balenalib/aio-3288c-debian-python

LABEL maintainer "Christopher Meister-Paeslack <christopher.paeslack@gmail.com>"

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /

RUN apt-get update
RUN apt-get install python3
RUN python3 -m pip install --upgrade pip
RUN apt-get install gcc python3-dev
RUN pip3 install -r /requirements.txt

COPY ./ ./

CMD ["python3", "./src/app.py"]
