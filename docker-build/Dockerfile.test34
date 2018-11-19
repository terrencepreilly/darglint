FROM python:3.4-alpine


RUN apk update && \
    apk add gcc \
            musl-dev \
            python3-dev


RUN python -m pip install -U pip && \
    python -m pip install pytest \
                          mypy \
                          typing


WORKDIR /code/
