FROM python:3.7-slim

RUN apt update && apt install git g++ -y

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /
COPY run.py .

ENV NUM_WORKERS 1
ENV HOST 0.0.0.0

EXPOSE 8080

CMD ["python", "run.py"]

