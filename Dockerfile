FROM python:3.8.5-buster

WORKDIR /code
EXPOSE 80

RUN apt-get update && apt-get install -y python3-pandas

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY server.py .
COPY app/ app/
RUN python -m compileall .

CMD ["python", "server.py", "run"]
