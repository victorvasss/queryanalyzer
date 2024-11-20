from fastapi import FastAPI, File, Request, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse
import psycopg2
import os
from QueryAnalyzer import queryanalyzer
from fastapi.templating import Jinja2Templates


DIRECTORY_PATH = "./students_sql"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='frontend')

connection = psycopg2.connect(
    dbname="course_work",
    user="postgres",
    password="237148",
    host="localhost",
    port="5432",
    options="-c search_path=public"
)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(name='index.html', context={'request': request})

@app.get("/upload")
async def root(request: Request):
    return templates.TemplateResponse(name='upload.html', context={'request': request})

@app.get("/upload_result")
async def root(request: Request):
    return templates.TemplateResponse(name='upload_result.html', context={'request': request})

@app.get("/console")
async def root(request: Request):
    return templates.TemplateResponse(name='console.html', context={'request': request})

@app.get("/etalons")
async def root(request: Request):
    return templates.TemplateResponse(name='etalons.html', context={'request': request})

@app.post("/uploadfile")
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        print("[+] File uploaded success:", file.filename)
        content = contents.decode('utf-8')
        cursor = connection.cursor()
        cursor.execute(content)
        print("[+] Success execute query")
        result = cursor.fetchall()
    except Exception as e:
        print("[!] Error:", e)
        raise HTTPException(status_code=500, detail="Error reading file")
    finally:
        cursor.close()
        connection.commit()
    return templates.TemplateResponse(name='upload.html', context={'request': request, 'result': result})

@app.post("/submit_text")
async def submit_text(request: Request, text: str = Form(...)):
    try:
        cursor = connection.cursor()
        cursor.execute(text)
        print("[+] Success execute query")
        result = cursor.fetchall()
    except Exception as e:
        print("[!] Error:", e)
        raise HTTPException(status_code=500, detail="Error reading file")
    finally:
        cursor.close()
        connection.commit()
    return templates.TemplateResponse(name='console.html', context={'request': request, 'result': result})

@app.post("/add_etalon")
async def submit_text(request: Request, text: str = Form(...)):
    try:
        filename = "common_etalon.json"
        with open("etalons/"+filename, "w", encoding="utf-8") as file:
            file.write(text)
        print(f"[+] Success saved to etalons/{filename}")
    except Exception as e:
        print("[!] Error:", e)
        raise HTTPException(status_code=500, detail="Error reading file")
    return templates.TemplateResponse(name='etalons.html', context={'request': request})


@app.post("/upload_result")
async def upload_result(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        filename = file.filename
        print("[+] File uploaded success:", filename)
        content = contents.decode('utf-8')
        with open("students_sql/"+filename, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"[+] Success saved to students_sql/{filename}")
        reference="test.sql"
        queryanalyzer.analyze("students_sql/"+filename, "etalons/"+reference)
    except Exception as e:
        print("[!] Error:", e)
        raise HTTPException(status_code=500, detail="Error reading file")
    return templates.TemplateResponse(name='upload_result.html', context={'request': request, 'result': content})

@app.get("/answers", response_class=HTMLResponse)
async def list_files(request: Request):
    try:
        files = os.listdir(DIRECTORY_PATH)
        # Создаем HTML-страницу со списком файлов и ссылками на их скачивание
        file_url_arr = []
        file_arr = []
        for file in files:
            file_url = f"/download/{file}"
            file_url_arr.append([file_url, file])
            #file_arr.append(file)
        print(file_url_arr)
        print(file_arr)
        return templates.TemplateResponse(name='answers.html', context={'request': request, 'result': file_url_arr, 'files': file_arr})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при получении списка файлов")

@app.get("/download/{filename}")
async def download_file(request: Request, filename: str):
    file_path = os.path.join(DIRECTORY_PATH, filename)
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")