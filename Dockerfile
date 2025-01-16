FROM python:3.11-alpine

COPY app.py /app.py
COPY nothanks /nothanks
COPY requirements.txt /requirements.txt

RUN pip install -r requirements.txt

CMD ["python", "app.py"]