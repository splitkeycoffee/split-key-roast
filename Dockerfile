FROM python:2.7

WORKDIR /code
EXPOSE 80

COPY requirements.txt .
RUN pip2 install -r requirements.txt

COPY server.py .
COPY app/ app/
#RUN python2 -m compileall .

CMD ["python2", "-u", "server.py", "run"]
