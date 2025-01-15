import json
from datetime import datetime
import zipfile
from fastapi import FastAPI, File, Request, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse, RedirectResponse
import psycopg2
import os
from QueryAnalyzer import queryanalyzer
from fastapi.templating import Jinja2Templates
import csv

from QueryAnalyzer.queryanalyzer import DB_PARAMS


STUDENT_DIRECTORY_PATH = "./students_sql"
ETALON_DIRECTORY_PATH = "./etalons"
RESULTS_DIRECTORY_PATH = "./analysis_results"
STUDENT_DATA_FILE = ".\\analysis_results\\test.json"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='frontend')

# connection = psycopg2.connect(
#     dbname="course_work",
#     user="postgres",
#     password="237148",
#     host="localhost",
#     port="5432",
#     options="-c search_path=public"
# )
        
@app.get("/")
@app.get("/upload")
async def root(request: Request):
    return templates.TemplateResponse(name='upload.html', context={'request': request})

@app.post("/uploadfile")
async def upload_file(request: Request, file: UploadFile = File(...), dropdown: str = Form(...)):
    try:
        print(f"[+] Dropdown value: {dropdown}")  # Вывод выбранного значения
        DB_PARAMS["dbname"] = dropdown
        connection = psycopg2.connect(**DB_PARAMS)
        connection.autocommit = True
        contents = await file.read()
        print("[+] File uploaded success:", file.filename)
        content = contents.decode('utf-8')
        cursor = connection.cursor()
        cursor.execute(content)
        print("[+] Success execute query")
        if cursor.description:
            attrs = [description[0] for description in cursor.description]
            result = cursor.fetchall()
        else:
            attrs = []
            result = []
    except Exception as e:
        detail = "[!] Error: " + str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)
    finally:
        cursor.close()
        #connection.commit()
        connection.close()
    return templates.TemplateResponse(name='upload.html', context={'request': request, 'attr': attrs, 'result': result})


@app.post("/submit_text")
async def submit_text(request: Request, text: str = Form(...), dropdown: str = Form(...)):
    try:
        print(f"[+] Dropdown value: {dropdown}")  # Вывод выбранного значения
        DB_PARAMS["dbname"] = dropdown
        connection = psycopg2.connect(**DB_PARAMS)
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(text)
        print("[+] Success execute query")
        if cursor.description:
            attrs = [description[0] for description in cursor.description]
            result = cursor.fetchall()
        else:
            attrs = []
            result = []
    except Exception as e:
        detail = "[!] Error: " + str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)
    finally:
        cursor.close()
        #connection.commit()
        connection.close()
    return templates.TemplateResponse(name='upload.html', context={'request': request, 'attr': attrs, 'result': result})

@app.post("/upload_etalon")
async def upload_etalon(request: Request, file: UploadFile = File(...), dropdown: str = Form(...)):
    try:
        contents = await file.read()
        filename = file.filename
        print("[+] File uploaded success:", filename)
        content = contents.decode('utf-8')
        with open("etalons/"+dropdown+"_"+filename, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"[+] Success saved to etalons/{dropdown}_{filename}")
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)    
    return RedirectResponse(url="/etalons")

@app.post("/upload_result")
async def upload_result(request: Request, file: UploadFile = File(...), dropdown: str = Form(...), etalon: str = Form(...)):
    try:
        contents = await file.read()
        filename = file.filename
        print("[+] File uploaded success:", filename)

        if filename.endswith(".zip"):
            timestamp = datetime.now()
            formatted_timestamp = timestamp.strftime("%Y-%m-%d_%H-%M-%S")

            extraction_path = os.path.join("students_sql", formatted_timestamp)
            analysis_path = os.path.join("analysis_results", formatted_timestamp)

            zip_path = os.path.join("students_sql", filename)
            with open(zip_path, "wb") as zip_file:
                zip_file.write(contents)
            print(f"[+] ZIP file saved: {zip_path}")

            os.makedirs(extraction_path, exist_ok=True)
            print(f"[+] Created extraction directory: {extraction_path}")

            os.makedirs(analysis_path, exist_ok=True)
            print(f"[+] Created analysis directory: {analysis_path}")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extraction_path)
            print(f"[+] ZIP file extracted to: {extraction_path}")

            extracted_files = zip_ref.namelist()

            os.remove(zip_path)
            print(f"[+] ZIP file removed: {zip_path}")

            for extracted_file in extracted_files:
                file_path = os.path.join(extraction_path, extracted_file)
                if os.path.isfile(file_path):
                    print(f"[+] Analyzing file: {file_path}")
                    queryanalyzer.analyze(file_path, f"etalons/{etalon}", dropdown)
                else:
                    print(f"[!] Skipping non-file entry: {file_path}")
        # else:
            # content = contents.decode('utf-8')
            # with open(f"students_sql/{filename}", "w", encoding="utf-8") as sql_file:
            #     sql_file.write(content)
            # print(f"[+] Success saved to students_sql/{filename}")

            # queryanalyzer.analyze(f"students_sql/{filename}", f"etalons/{etalon}", dropdown)

    except zipfile.BadZipFile:
        detail = "[!] Error: Invalid ZIP file"
        print(detail)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        detail = "[!] Error: " + str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)

    return RedirectResponse(url="/results")

@app.post("/results_list")
@app.get("/results_list", response_class=HTMLResponse)
async def etalons_list(request: Request):
    try:
        files = os.listdir(RESULTS_DIRECTORY_PATH)
        # Создаем HTML-страницу со списком файлов и ссылками на их скачивание
        file_url_arr = []
        file_arr = []
        for file in files:
            file_url = f"/analysis_results/{file}"
            file_url_arr.append([file_url, file])
            #file_arr.append(file)
        return templates.TemplateResponse(name='results_list.html', context={'request': request, 'result': file_url_arr, 'files': file_arr})
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)

@app.get("/analysis_results/{filename}")
async def download_file(request: Request, filename: str):
    file_path = os.path.join(RESULTS_DIRECTORY_PATH, filename)
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")

@app.get("/download_result/{directory}/{filename}")
async def download_file(request: Request, directory: str, filename: str):
    file_path = os.path.join(RESULTS_DIRECTORY_PATH, directory)
    file_path = os.path.join(file_path, filename)
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
@app.get("/download_etalon/{filename}")
async def download_file(request: Request, filename: str):
    file_path = os.path.join(ETALON_DIRECTORY_PATH, filename)
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
@app.post("/etalons")
@app.get("/etalons")
async def get_pased_etalons(request: Request):
    files = os.listdir(ETALON_DIRECTORY_PATH)
    etalons_head = ['Эталон', 'Описание', 'Схема', 'Название файла', 'Скачать', 'Удалить']
    etalons_list = []
    for file in files:
        reference_data = {}
        with open(ETALON_DIRECTORY_PATH+"/"+file, "r", encoding="utf-8") as ref_file:
            reference_data = json.load(ref_file)
        for el in reference_data:
            parsed_etalon = []
            parsed_etalon.append(el)
            parsed_etalon.append(reference_data[el])
            dbs = await get_db_names(request)
            db_flag = 0
            for db in dbs:
                if db in file:
                    parsed_etalon.append(db)
                    parsed_etalon.append(file.replace(db + '_', ''))
                    db_flag = 1
                    break
            if not db_flag:
                parsed_etalon.append('')
                parsed_etalon.append(file)
            file_url = f"/download_etalon/{file}"
            parsed_etalon.append(file_url)
            file_url = f"/delete_etalon_via_link/{file}"
            parsed_etalon.append(file_url)
            etalons_list.append(parsed_etalon)
    return templates.TemplateResponse(name='etalons.html', context={'request': request, 'heads': etalons_head, 'etalons': etalons_list})

@app.post("/results")
@app.get("/results")
async def get_parsed_results(request: Request):
    all_files_and_dirs = [f for f in os.listdir(RESULTS_DIRECTORY_PATH) if os.path.isdir(os.path.join(RESULTS_DIRECTORY_PATH, f)) or os.path.isfile(os.path.join(RESULTS_DIRECTORY_PATH, f))]
    files = os.listdir(RESULTS_DIRECTORY_PATH)
    res_arr = []
    for tmp_dir in all_files_and_dirs:
        res_dir_arr = []
        dir_path = os.path.join(RESULTS_DIRECTORY_PATH, tmp_dir)
        if os.path.isdir(dir_path):
            files = os.listdir(dir_path)
        else:
            files = []
            files.append(dir_path)
        for file in files:
            results = {}
            with open(dir_path+"/"+file, "r", encoding="utf-8") as ref_file:
                results = json.load(ref_file)
                file_url_download = f"/download_result/{tmp_dir}/{file}"
                file_url_delete = f"/delete_result_via_link/{tmp_dir}/{file}"
                res_dir_arr.append([file.split('.')[0], results, file_url_download, file_url_delete])
        tmp = tmp_dir.split('_')
        tmp[0] = tmp[0].split('-')
        tmp = tmp[0][2] + '.' + tmp[0][1] + '.' + tmp[0][0] + ' ' + tmp[1].replace('-', ':')
        res_arr.append([tmp, res_dir_arr, f"/delete_result_dir_via_link/{tmp_dir}", f"/download_dir/{tmp_dir}", f"/download_csv/{tmp_dir}"])
    return templates.TemplateResponse(name='results_list.html', context={'request': request, 'results_dir': res_arr})

@app.get("/download_dir/{directory}")
async def download_dir_via_link(request: Request, directory: str):
    file_path = os.path.join(RESULTS_DIRECTORY_PATH, directory)
    zip_fn = directory + '.zip'
    with zipfile.ZipFile(zip_fn, 'w') as zip_file:
        for item in os.listdir(file_path):
            zip_file.write(file_path + '/' + item)
    return FileResponse(zip_fn)

@app.get("/download_csv/{directory}")
def download_csv(request: Request, directory: str):
    data = {}
    file_path = os.path.join(RESULTS_DIRECTORY_PATH, directory)
    for item in os.listdir(file_path):
        tmp_file_path = os.path.join(file_path, item)
        with open(tmp_file_path, 'r', encoding='utf-8') as file:
            tmp_data = json.load(file)
            data[item] = tmp_data.get("total_score", None) 
    output_file = directory + '.csv'
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Запись заголовков
        writer.writerow(['Файл студента', 'Оценка'])
        # Запись данных
        for student, grade in data.items():
            writer.writerow([student, grade])
    return FileResponse(output_file)

@app.get("/delete_etalon_via_link/{filename}")
async def delete_etalon_via_link(request: Request, filename: str):
    file_path = os.path.join(ETALON_DIRECTORY_PATH, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
        return RedirectResponse(url="/etalons")
    else:
        raise HTTPException(status_code=404, detail="Файл не найден") 
        
@app.get("/delete_result_via_link/{directory}/{filename}")
async def delete_result_via_link(request: Request, directory: str, filename: str):
    dir_path = os.path.join(RESULTS_DIRECTORY_PATH, directory)
    file_path = os.path.join(dir_path, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    if os.path.isdir(dir_path):
        if len(os.listdir(dir_path)) == 0:
            os.rmdir(dir_path)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")

    dir_path = os.path.join(STUDENT_DIRECTORY_PATH, directory)
    file_path = os.path.join(dir_path, filename.replace('.json', '.sql'))
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    if os.path.isdir(dir_path):
        if len(os.listdir(dir_path)) == 0:
            os.rmdir(dir_path)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return RedirectResponse(url="/results")

@app.get("/delete_result_dir_via_link/{directory}")
async def delete_result_dir_via_link(request: Request, directory: str):
    file_path = os.path.join(RESULTS_DIRECTORY_PATH, directory)
    for item in os.listdir(file_path):
        item_path = os.path.join(file_path, item)
        try:
            if os.path.isfile(item_path):
                os.remove(item_path)
        except OSError as e:
            print(f"Ошибка при удалении {item}: {e}")
    if os.path.isdir(file_path):
        os.rmdir(file_path)    
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    file_path = os.path.join(STUDENT_DIRECTORY_PATH, directory)
    for item in os.listdir(file_path):
        item_path = os.path.join(file_path, item)
        try:
            if os.path.isfile(item_path):
                os.remove(item_path)
        except OSError as e:
            print(f"Ошибка при удалении {item}: {e}")
    if os.path.isdir(file_path):
        os.rmdir(file_path)    
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return RedirectResponse(url="/results")

@app.get("/get_db_names")
async def get_db_names(request: Request):
    query = "SELECT datname FROM pg_database WHERE datistemplate = false;"
    connection = psycopg2.connect(**DB_PARAMS)
    cursor = connection.cursor()
    cursor.execute(query)
    print("[+] Success execute query")
    result = cursor.fetchall()
    db_names = [el[0] for el in result]
    print(db_names)
    cursor.close()
    connection.close()
    return db_names

@app.post("/get_etalons_names")
@app.get("/get_etalons_names")
async def get_etalons_names(request: Request):
    files = os.listdir(ETALON_DIRECTORY_PATH)
    return files