FROM python:3.9

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install -y cloc

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
ENV PATH /root/.local/bin:$PATH
