import psycopg2
import sqlparse
import time

DB_PARAMS = {
    "dbname": "course_work",
    "user": "postgres",
    "password": "1qaz@WSX",
    "host": "localhost",
    "port": "5432",
    "options": "-c search_path=public"
}

def analyze(filename: str, reference_filename: str):
    with open(filename, "r", encoding="utf-8") as file:
        sql_query = file.read()

    with open(reference_filename, "r", encoding="utf-8") as ref_file:
        reference_query = ref_file.read()

    parsed_query = sqlparse.parse(sql_query)
    analyzed_data = {
        "grade": "Executed",
        "recommendations": [],
        "score": 0,
        "checks": {}
    }

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        cursor.execute(reference_query)
        reference_result = cursor.fetchall()

        explain_query = f"EXPLAIN ANALYZE {sql_query}"
        cursor.execute(explain_query)
        explain_result = cursor.fetchall()

        cursor.execute(sql_query)
        query_result = cursor.fetchall()

        # null
        nulls_in_reference = sum(1 for row in reference_result for cell in row if cell is None)
        nulls_in_result = sum(1 for row in query_result for cell in row if cell is None)
        analyzed_data["checks"]["null_check"] = nulls_in_reference == nulls_in_result
        if analyzed_data["checks"]["null_check"]:
            analyzed_data["score"] += 1

        # дубликаты
        unique_rows_reference = len(set(reference_result))
        unique_rows_result = len(set(query_result))
        analyzed_data["checks"]["duplicates_check"] = unique_rows_reference == unique_rows_result
        if analyzed_data["checks"]["duplicates_check"]:
            analyzed_data["score"] += 1

        # полнота
        analyzed_data["checks"]["completeness_check"] = len(reference_result) == len(query_result)
        if analyzed_data["checks"]["completeness_check"]:
            analyzed_data["score"] += 1

        # если дубликаты и полнота минус то ноль баллов потому что нулл может и прошло но значит запрос неправильный
        if not analyzed_data["checks"]["completeness_check"] or not analyzed_data["checks"]["duplicates_check"]:
            analyzed_data["score"] = 0

        analyzed_data["execution_time"] = time.time() - time.time()
        analyzed_data["explain"] = explain_result

        cursor.close()
        conn.close()

    except Exception as e:
        analyzed_data["grade"] = "Failed"
        analyzed_data["recommendations"].append(f"Error executing query: {e}")

    result_filename = filename.replace("students_sql", "analysis_results")
    with open(result_filename, "w", encoding="utf-8") as result_file:
        for key, value in analyzed_data.items():
            result_file.write(f"{key}: {value}\n")
        print(f"[+] Analysis result saved to {result_filename}")