import psycopg2
import sqlparse
import time
import json
import os
import re

DB_PARAMS = {
    "dbname": "course_work",
    "user": "postgres",
    "password": "010716",
    "host": "localhost",
    "port": "5432",
    "options": "-c search_path=public"
}

def extract_tables_and_columns(query):
    tables = re.findall(r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', query)
    columns = re.findall(r'SELECT\s+(.*?)\s+FROM', query, re.DOTALL)
    columns = columns[0].split(',') if columns else []
    tables = [table.strip() for table in tables]
    columns = [column.strip() for column in columns]
    return tables, columns

def analyze(filename: str, reference_filename: str):
    import json
    from decimal import Decimal
    import sqlparse

    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError("Object of type Decimal is not JSON serializable")

    with open(filename, "r", encoding="utf-8") as file:
        sql_content = file.read()

    with open(reference_filename, "r", encoding="utf-8") as ref_file:
        reference_data = json.load(ref_file)

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

            query_score = 0
            recommendations = []

            try:
                cursor.execute(ref_query)
                reference_result = cursor.fetchall()

                cursor.execute(user_query)
                query_result = cursor.fetchall()

                completeness_check = False
                duplicates_check = False
                nulls_check = False
                # nulls_in_reference = 0
                # nulls_in_result = 0

                ref_tables, ref_columns = extract_tables_and_columns(ref_query)
                user_tables, user_columns = extract_tables_and_columns(user_query)

                tables_match = sorted(ref_tables) == sorted(user_tables)
                columns_match = sorted(ref_columns) == sorted(user_columns)

                if not tables_match or not columns_match:
                    query_score = 0
                    recommendations.append("Таблицы или столбцы не совпадают с эталоном. Проверьте FROM и SELECT.")
                else:
                    nulls_in_reference = sum(1 for row in reference_result for cell in row if cell is None)
                    nulls_in_result = sum(1 for row in query_result for cell in row if cell is None)
                    nulls_check = nulls_in_reference == nulls_in_result
                    completeness_check = len(set(reference_result)) == len(set(query_result))
                    duplicates_check = len(query_result) == len(set(query_result))

                    if completeness_check:
                        query_score += 1
                    else:
                        recommendations.append("Запрос возвращает не полный набор данных. Проверьте условия WHERE или LIMIT.")

                    if duplicates_check:
                        query_score += 1
                    else:
                        recommendations.append("В запросе обнаружены проблемы с дубликатами. Убедитесь, что используется DISTINCT, если нужно.")

                    if nulls_check:
                        query_score += 1
                    else:
                        recommendations.append("Число NULL-значений не совпадает. Проверьте, правильно ли обрабатываются отсутствующие значения.")

                check_result = {
                    "description": description,
                    "user_query": user_query,
                    "reference_query": ref_query,
                    "completeness": completeness_check,
                    "duplicates": duplicates_check,
                    "nulls_match": nulls_check,
                    "tables_match": tables_match,
                    "columns_match": columns_match,
                    "score": query_score,
                    "recommendations": recommendations,
                    "query_result": query_result,
                    "reference_result": reference_result
                }

                analyzed_data["checks"].append(check_result)
                analyzed_data["total_score"] += query_score

            except Exception as query_error:
                analyzed_data["recommendations"].append(
                    f"Error executing query: {query_error} for {description}"
                )

        cursor.close()
        conn.close()

    except Exception as e:
        analyzed_data["grade"] = "Failed"
        analyzed_data["recommendations"].append(f"Database connection or execution error: {e}")

    if not os.path.isdir("analysis_results"):
        os.mkdir("analysis_results")
    result_filename = filename.replace("students_sql", "analysis_results").replace(".sql", ".json")
    with open(result_filename, "w", encoding="utf-8") as result_file:
        json.dump(analyzed_data, result_file, indent=4, ensure_ascii=False, default=convert_decimal)
        print(f"[+] Analysis result saved to {result_filename}")