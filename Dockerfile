FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY daaad/ daaad/

COPY .env .env

CMD [ "python", "-m", "daaad" ]