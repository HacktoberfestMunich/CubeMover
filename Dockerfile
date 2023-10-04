FROM python:3.11.4

RUN mkdir /app

COPY ./CubeMover/* /app

ENTRYPOINT ["python", "/app/main.py"]
