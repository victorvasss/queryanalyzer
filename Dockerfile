FROM python:3.9

WORKDIR /opt/app

COPY ./backend backend
COPY ./frontend frontend
COPY ./analysis_results analysis_results
COPY ./etalons etalons
COPY ./sql sql
COPY ./static static
COPY ./students_sql students_sql
COPY ./tmp tmp
COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8888

CMD ["fastapi", "run", "backend/main.py", "--port", "8888"]
