import json
import zipfile
from fastapi import FastAPI, File, Request, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse, RedirectResponse
import psycopg2
import os
from QueryAnalyzer import queryanalyzer
from fastapi.templating import Jinja2Templates


STUDENT_DIRECTORY_PATH = "./students_sql"
ETALON_DIRECTORY_PATH = "./etalons"
RESULTS_DIRECTORY_PATH = "./analysis_results"
STUDENT_DATA_FILE = ".\\analysis_results\\test.json"

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
    try:
        students_data = []
        files = os.listdir(RESULTS_DIRECTORY_PATH)
        for file in files:
            file = RESULTS_DIRECTORY_PATH + '/' + file
            with open(file, 'r') as file:
                data = json.load(file)
                students_data.append([file.name.split('/')[2], data['total_score'], data['recommendations']])
            print(students_data)

        return templates.TemplateResponse(name='index.html', context={'request': request, 'result': students_data})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
        

@app.get("/upload")
async def root(request: Request):
    return templates.TemplateResponse(name='upload.html', context={'request': request})

@app.get("/upload_result")
async def root(request: Request):
    return templates.TemplateResponse(name='upload_result.html', context={'request': request})

@app.get("/upload_etalon")
async def root(request: Request):
    return templates.TemplateResponse(name='upload_etalon.html', context={'request': request})

@app.get("/console")
async def root(request: Request):
    return templates.TemplateResponse(name='console.html', context={'request': request})

#@app.get("/etalons")
#async def root(request: Request):
#    return templates.TemplateResponse(name='etalons.html', context={'request': request})

@app.post("/uploadfile")
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        print("[+] File uploaded success:", file.filename)
        content = contents.decode('utf-8')
        cursor = connection.cursor()
        cursor.execute(content)
        print("[+] Success execute query")
        attrs = [description[0] for description in cursor.description] 
        result = cursor.fetchall()
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)
    finally:
        cursor.close()
        connection.commit()
    return templates.TemplateResponse(name='upload.html', context={'request': request, 'attr':attrs, 'result': result})

@app.post("/submit_text")
async def submit_text(request: Request, text: str = Form(...)):
    try:
        cursor = connection.cursor()
        cursor.execute(text)
        print("[+] Success execute query")
        attrs = [description[0] for description in cursor.description] 
        result = cursor.fetchall()
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)
    finally:
        cursor.close()
        connection.commit()
    return templates.TemplateResponse(name='upload.html', context={'request': request, 'attr':attrs, 'result': result})

@app.post("/add_etalon")
async def submit_text(request: Request, text: str = Form(...)):
    try:
        filename = "common_etalon.json"
        with open("etalons/"+filename, "w", encoding="utf-8") as file:
            file.write(text)
        print(f"[+] Success saved to etalons/{filename}")
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)
    return templates.TemplateResponse(name='etalons.html', context={'request': request})

@app.post("/upload_etalon")
async def upload_etalon(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        filename = file.filename
        print("[+] File uploaded success:", filename)
        content = contents.decode('utf-8')
        with open("etalons/"+filename, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"[+] Success saved to etalons/{filename}")
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)
    return templates.TemplateResponse(name='upload_etalon.html', context={'request': request, 'result': content})


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
        # TODO: имя эталона захардкожено... нужно добавить возможность его выбирать
        reference="common_etalon.json"
        queryanalyzer.analyze("students_sql/"+filename, "etalons/"+reference)
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)
    return templates.TemplateResponse(name='upload_result.html', context={'request': request, 'result': content})

@app.post("/answers")
@app.get("/answers", response_class=HTMLResponse)
async def list_files(request: Request):
    try:
        files = os.listdir(STUDENT_DIRECTORY_PATH)
        # Создаем HTML-страницу со списком файлов и ссылками на их скачивание
        file_url_arr = []
        file_arr = []
        for file in files:
            file_url = f"/download_student/{file}"
            file_url_arr.append([file_url, file])
            #file_arr.append(file)
        return templates.TemplateResponse(name='answers.html', context={'request': request, 'result': file_url_arr, 'files': file_arr})
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)

@app.post("/etalons_list")
@app.get("/etalons_list", response_class=HTMLResponse)
async def etalons_list(request: Request):
    try:
        files = os.listdir(ETALON_DIRECTORY_PATH)
        # Создаем HTML-страницу со списком файлов и ссылками на их скачивание
        file_url_arr = []
        file_arr = []
        for file in files:
            file_url = f"/download_etalon/{file}"
            file_url_arr.append([file_url, file])
            #file_arr.append(file)
        return templates.TemplateResponse(name='etalons_list.html', context={'request': request, 'result': file_url_arr, 'files': file_arr})
    except Exception as e:
        detail="[!] Error: "+str(e)
        print(detail)
        raise HTTPException(status_code=500, detail=detail)
    
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

@app.get("/download_result/{filename}")
async def download_file(request: Request, filename: str):
    file_path = os.path.join(RESULTS_DIRECTORY_PATH, filename)
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
    
@app.post("/delete_etalon/")
async def delete_etalon(request: Request, text: str = Form(...)):
    file_path = os.path.join(ETALON_DIRECTORY_PATH, text)
    if os.path.isfile(file_path):
        os.remove(file_path)        
        return RedirectResponse(url="/get_parsed_results")
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")

@app.post("/delete_result/")
async def delete_result(request: Request, text: str = Form(...)):
    file_path = os.path.join(RESULTS_DIRECTORY_PATH, text)
    if os.path.isfile(file_path):
        os.remove(file_path)        
        return RedirectResponse(url="/results_list")
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")

@app.post("/delete_answer/")
async def delete_answer(request: Request, text: str = Form(...)):
    file_path = os.path.join(STUDENT_DIRECTORY_PATH, text)
    if os.path.isfile(file_path):
        os.remove(file_path)         
        return RedirectResponse(url="/answers")
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
@app.get("/upload_zip")
async def upload_zip(request: Request):
    try:
        zip_file = RESULTS_DIRECTORY_PATH + "/results.zip"
        with zipfile.ZipFile(zip_file, "w") as myzip:
            files = os.listdir(RESULTS_DIRECTORY_PATH)
            for file in files:
                file = RESULTS_DIRECTORY_PATH + '/' + file
                myzip.write(file)

        return RedirectResponse(url="/results_list")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/etalons")
async def get_pased_etalons(request: Request):
    files = os.listdir(ETALON_DIRECTORY_PATH)
    # Создаем HTML-страницу со списком файлов и ссылками на их скачивание
    etalons_head = ['etalon', 'description', 'file_name', 'download_link', 'delete_link']
    etalons_list = []
    for file in files:
        reference_data = {}
        with open(ETALON_DIRECTORY_PATH+"/"+file, "r", encoding="utf-8") as ref_file:
            reference_data = json.load(ref_file)
        for el in reference_data:
            parsed_etalon = []
            parsed_etalon.append(el)
            parsed_etalon.append(reference_data[el])
            parsed_etalon.append(file)
            file_url = f"/download_etalon/{file}"
            parsed_etalon.append(file_url)
            file_url = f"/delete_etalon_via_link/{file}"
            parsed_etalon.append(file_url)
            etalons_list.append(parsed_etalon)
    return templates.TemplateResponse(name='etalons.html', context={'request': request, 'heads': etalons_head, 'etalons': etalons_list})

@app.get("/results")
async def get_parsed_results(request: Request):
    files = os.listdir(RESULTS_DIRECTORY_PATH)
    # Создаем HTML-страницу со списком файлов и ссылками на их скачивание
    results_head = ['filename', 'grade', 'recommendations', 'total_score', 'checks', 'download_link', 'delete_link']
    results_list = []
    for file in files:
        with open(RESULTS_DIRECTORY_PATH+"/"+file, "r", encoding="utf-8") as ref_file:
            parsed_results = [file]
            results = {}
            results = json.load(ref_file)
            for el in results:
                parsed_results.append(str(results[el]))
            file_url = f"/download_result/{file}"
            parsed_results.append(file_url)
            file_url = f"/delete_result_via_link/{file}"
            parsed_results.append(file_url)
            results_list.append(parsed_results)
    return templates.TemplateResponse(name='results_list.html', context={'request': request, 'heads': results_head, 'results_list': results_list})
        
@app.get("/delete_etalon_via_link/{filename}")
async def delete_etalon_via_link(request: Request, filename: str):
    file_path = os.path.join(ETALON_DIRECTORY_PATH, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
        return RedirectResponse(url="/etalons")
    else:
        raise HTTPException(status_code=404, detail="Файл не найден") 
        
@app.get("/delete_result_via_link/{filename}")
async def delete_result_via_link(request: Request, filename: str):
    file_path = os.path.join(RESULTS_DIRECTORY_PATH, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    file_path = os.path.join(STUDENT_DIRECTORY_PATH, filename.replace('.json', '.sql'))
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return RedirectResponse(url="/results")