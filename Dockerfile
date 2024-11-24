FROM python:3.9

WORKDIR /opt/app

COPY ./backend backend
COPY ./frontend frontend
COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["fastapi", "run", "backend/main.py", "--port", "9000"]
