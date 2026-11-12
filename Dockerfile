FROM python:3.12-slim
WORKDIR /app
COPY motor.py casos.py ./
USER 65532:65532
ENTRYPOINT ["python", "-E", "-B", "-u", "/app/motor.py"]
