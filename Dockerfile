FROM python:3.7

WORKDIR /code
EXPOSE 80

RUN apt-get update && apt-get install -y python3-pandas
RUN python -m ensurepip --upgrade

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY server.py .
COPY app/ app/
RUN python -m compileall .

CMD ["python", "-u", "server.py", "run"]
