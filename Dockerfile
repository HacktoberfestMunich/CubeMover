FROM python:3.11.4

RUN mkdir /app

COPY ./CubeMover/* /app

# RUN --network=host python src/sample_client.py

ENTRYPOINT ["python", "/app/main.py"]