FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY *.py .

EXPOSE 5000

CMD ["python", "proxy_server.py"]

