FROM python:3

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY app.py .
COPY populate_db.py .
COPY faceit ./faceit
COPY necc ./necc
COPY database ./database

ARG workers=4
ENV WORKERS=${workers}

CMD gunicorn -w $WORKERS -b 0.0.0.0 app:app