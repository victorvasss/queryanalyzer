FROM python:3.9

WORKDIR /opt/app

RUN apt-get update && apt-get install -y \
    postgresql

RUN service postgresql start && \
    sleep 5 && \
    su postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD '237148';\"" && \
    su postgres -c "psql -c \"CREATE DATABASE course_work;\""

COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./analysis_results analysis_results
COPY ./backend backend
COPY ./etalons etalons
COPY ./frontend frontend
COPY ./sql sql
COPY ./static static
COPY ./students_sql students_sql
COPY ./tmp tmp

EXPOSE 8888

CMD service postgresql start && sleep 5 && fastapi run backend/main.py --port 8888
