import psycopg2
import sqlparse
import time
import json
import os

DB_PARAMS = {
    "dbname": "course_work",
    "user": "postgres",
    "password": "237148",
    "host": "localhost",
    "port": "5432",
    "options": "-c search_path=public"
}

def analyze(filename: str, reference_filename: str):
    import json
    from decimal import Decimal
    import sqlparse

    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Преобразуем Decimal в float
        raise TypeError("Object of type Decimal is not JSON serializable")

    # Загружаем пользовательские запросы
    with open(filename, "r", encoding="utf-8") as file:
        sql_content = file.read()

    # Загружаем эталонные запросы
    with open(reference_filename, "r", encoding="utf-8") as ref_file:
        reference_data = json.load(ref_file)

    # Разбираем запросы из SQL-файла пользователя
    user_queries = sqlparse.split(sql_content)
    analyzed_data = {
        "grade": "Executed",
        "recommendations": [],
        "total_score": 0,
        "checks": []
    }

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        for user_query, (ref_query, description) in zip(user_queries, reference_data.items()):
            user_query = user_query.strip()
            # print(f"[DEBUG] Checking user query: {user_query}")
            # print(f"[DEBUG] Reference query: {ref_query}")

            query_score = 0

            try:
                cursor.execute(ref_query)
                reference_result = cursor.fetchall()
                # print(f"[DEBUG] Reference result: {reference_result}")

                cursor.execute(user_query)
                query_result = cursor.fetchall()
                # print(f"[DEBUG] Query result: {query_result}")

                nulls_in_reference = sum(1 for row in reference_result for cell in row if cell is None)
                nulls_in_result = sum(1 for row in query_result for cell in row if cell is None)
                completeness_check = len(reference_result) == len(query_result)
                duplicates_check = len(set(reference_result)) == len(set(query_result))

                if completeness_check and duplicates_check:
                    null_check = nulls_in_reference == nulls_in_result
                    if null_check:
                        query_score += 1
                else:
                    null_check = False  # если полнота или дубликаты по нулям то null не засчитываем

                if completeness_check:
                    query_score += 1
                if duplicates_check:
                    query_score += 1

                check_result = {
                    "description": description,
                    "user_query": user_query,
                    "reference_query": ref_query,
                    "completeness": completeness_check,
                    "duplicates": duplicates_check,
                    "nulls_match": null_check,
                    "score": query_score,
                    "query_result": query_result,
                    "reference_result": reference_result
                }

                analyzed_data["checks"].append(check_result)
                analyzed_data["total_score"] += query_score
                # print(f"[DEBUG] Check result: {check_result}")
            except Exception as query_error:
                analyzed_data["recommendations"].append(
                    f"Error executing query: {query_error} for {description}"
                )
                print(f"[!] Error executing query: {query_error}")

        cursor.close()
        conn.close()

    except Exception as e:
        analyzed_data["grade"] = "Failed"
        analyzed_data["recommendations"].append(f"Database connection or execution error: {e}")
        print(f"[!] Error: {e}")

    # Сохраняем результаты в JSON
    if not os.path.isfile("analysis_results"):
        os.mkdir("analysis_results")
    result_filename = filename.replace("students_sql", "analysis_results").replace(".sql", ".json")
    with open(result_filename, "w", encoding="utf-8") as result_file:
        json.dump(analyzed_data, result_file, indent=4, ensure_ascii=False, default=convert_decimal)
        print(f"[+] Analysis result saved to {result_filename}")