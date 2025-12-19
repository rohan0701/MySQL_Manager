from django.contrib import messages
from django.db import connection 
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
import mysql.connector
from mysql.connector import Error

def login(request):
    if request.method == "POST":
        pas = request.POST.get("p", "").strip()

        if pas=="":
            return render(request, "login.html", {"field_error": "Password is required."})
        
        try:
            conn = mysql.connector.connect(host="localhost",user="root",password=pas,database=None)

            if conn.is_connected():
                request.session["mysql_password"] = pas
                conn.close()
                return redirect("http://127.0.0.1:8000/home/")

        except Error as e:
            print("Error:", e)
            return render(request, "login.html", {"error": "Wrong password. Please try again."})

    return render(request, "login.html")

def home(request):
    return render(request, 'home.html')

def explore(request):
    return render(request,'explore.html')

def get_dbs(request):
    try:
        pas = request.session.get("mysql_password")

        conn = mysql.connector.connect(host="localhost", user="root", password=pas)
        c1 = conn.cursor()
        q = "SHOW DATABASES"
        c1.execute(q)
        
        dbs=[]
        for i in c1.fetchall():
            dbs.append(i[0])   
        conn.close()

    except Error as e:
        dbs = [f"Error: {e}"]

    return render(request, "explore.html", {"databases": dbs})

def create_dbs(request):
    dbs = []
    message = ""
    try:
        if request.method == "POST":
            pas = request.session.get("mysql_password")
            dbname = request.POST.get("db_name")

            conn = mysql.connector.connect(host="localhost", user="root", password=pas)
            c1 = conn.cursor()

            q = f"CREATE DATABASE {dbname}"
            c1.execute(q)

            message = f"Database '{dbname}' created successfully ✅"
            
            c1.execute("SHOW DATABASES")
            dbs = [i[0] for i in c1.fetchall()]

            conn.close()
    except Error as e:
        message = f"Error: {e}"

    return render(request, "explore.html", {"databases": dbs, "message": message})

def delete_dbs(request):
    dbs=[]
    del_message=""
    
    try:
        if request.method=="POST":
            dbname=request.POST.get("deldb")
            pas =request.session.get("mysql_password")
            
            conn = mysql.connector.connect(host="localhost", user="root", password=pas)
            c1 = conn.cursor()

            q=f"drop database {dbname}"
            c1.execute(q)
            del_message = f"Database '{dbname}' Deleted successfully ✅"
            
            c1.execute("SHOW DATABASES")
            dbs = [i[0] for i in c1.fetchall()]

            conn.close()
    except Error as e:
        message = f"Error: {e}"

    return render(request, "explore.html", {"databases": dbs, "message": del_message})

def work(request):
    return render(request,'work.html')

def select_db(request):
    select_db_name = ""  
    error_msg = ""
    
    if request.method == "POST":
        try:
            pas = request.session.get("mysql_password")
            name = request.POST.get("db_name")
            
            conn = mysql.connector.connect(host="localhost",user="root",password=pas,database=name)
    
            if conn.is_connected():
                request.session["current_db"]=name
                select_db_name = name
            
        except Error as e:
            error_msg = str(e)
            print("MySQL Error:", error_msg)
    
    context = {"selected_db": select_db_name,"error": error_msg}
    
    return render(request, 'work.html', context)

def show_tables(request):
    tables = []
    error_msg = None

    try:
        pas = request.session.get("mysql_password")
        db = request.session.get("current_db")
        
        conn = mysql.connector.connect(host="localhost",user="root",password=pas,database=db)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        conn.close()

    except Error as e:
        error_msg = str(e)
        print("MySQL Error:", error_msg)

    context = {"tables": tables,"selected_db": db,"error": error_msg}

    return render(request, 'work.html', context)



def view_table(request):
    table_structure = []
    table_data = []
    table_name = ""
    error_msg = None
    selected_db = request.session.get("current_db")

    if request.method == "POST":
        try:
            pas = request.session.get("mysql_password")
            db = request.session.get("current_db")
            table_name = request.POST.get("table_name")
            request.session["selected_table"] = table_name
            
            if not db:
                error_msg = "No database selected"
                context = {"error": error_msg, "selected_db": selected_db}
                return render(request, 'work.html', context)
            
            conn = mysql.connector.connect(host="localhost", user="root", password=pas, database=db)
            cursor = conn.cursor()
            
            # Get table structure
            cursor.execute(f"DESCRIBE {table_name}")
            structure_result = cursor.fetchall()
            
            # Format structure data
            for row in structure_result:
                table_structure.append({
                    'field': row[0],
                    'type': row[1],
                    'null': row[2],
                    'key': row[3],
                    'default': row[4] if row[4] is not None else 'NULL',
                    'extra': row[5]
                })
            
            # Get table data (limit to first 100 rows for performance)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
            columns = [desc[0] for desc in cursor.description]
            data_result = cursor.fetchall()
            
            # Format data
            for row in data_result:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = value if value is not None else 'NULL'
                table_data.append(row_dict)
            
            cursor.close()
            conn.close()
            
        except Error as e:
            error_msg = str(e)
            print("MySQL Error:", error_msg)

    context = {
        "table_structure": table_structure,
        "table_data": table_data,
        "table_name": table_name,
        "table_columns": [desc[0] for desc in cursor.description] if 'cursor' in locals() and table_data else [],
        "selected_db": selected_db,
        "error": error_msg
    }
    
    return render(request, 'table_view.html', context)

def create_table(request):
    if request.method == "POST":
        pas = request.session.get("mysql_password")
        db = request.session.get("current_db")
        table_name = request.POST.get("tableName")
        field_count = request.POST.get("fieldCount")

        
        # First step: user entered only table name & field count
        if field_count and not request.POST.get("fieldName1"):
            try:
                field_count = int(field_count)
            except ValueError:
                return HttpResponse("❌ Invalid number of fields.")

            return render(request, "create_table.html", {"field_range": range(1, field_count + 1),"table_name": table_name,"field_count": field_count})

        # Second step: user submitted field names and types
        elif request.POST.get("fieldName1"):
            try:
                field_count = int(request.POST.get("fieldCount"))
            except (ValueError, TypeError):
                return HttpResponse("❌ Field count missing or invalid.")

            fields = []
            for i in range(1, field_count + 1):
                fname = request.POST.get(f"fieldName{i}")
                ftype = request.POST.get(f"fieldType{i}")
                if not fname or not ftype:
                    return HttpResponse(f"❌ Missing name or type for field {i}.")
                fields.append(f"{fname} {ftype}")

            q = f"CREATE TABLE {table_name} ({', '.join(fields)})"

            try:
                conn = mysql.connector.connect(host="localhost", user="root", password=pas, database=db)
                c1 = conn.cursor()
                c1.execute(q)
                return HttpResponse(f"✅ Table '{table_name}' created successfully.")
            except Exception as e:
                return HttpResponse(f"❌ Error: {e}")

    # Initial GET request → show base form
    return render(request, "create_table.html", {"field_range": []})
def delete_table(request):
    pas = request.session.get("mysql_password")
    db = request.session.get("current_db")
    message = None  # default

    if request.method == "POST":   # ✅ only delete on POST
        name = request.POST.get("deltable")

        if not name:
            message = "❌ Please enter a table name."
        else:
            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password=pas,
                    database=db
                )
                c1 = conn.cursor()

                # ✅ safe table name with backticks
                query = f"DROP TABLE `{name}`"
                c1.execute(query)
                conn.commit()

                message = f"✅ Table '{name}' deleted successfully."
            except Error as e:
                message = f"❌ Error: {str(e)}"
            finally:
                if c1:
                    c1.close()
                if conn:
                    conn.close()
    return render(request, "delete_table.html", {"message": message})

def edit_table(request):   
    table_name = request.session.get("selected_table")
    db_name = request.session.get("selected_db") 

    context = {"table": table_name,}
    return render(request, "edit_table.html", context)


def insert(request):
    pas = request.session.get("mysql_password")
    dbname = request.session.get("current_db")
    table = request.session.get("selected_table")

    if request.method == "POST":
        records = request.POST.get("records")
        
        # STEP 1: User just entered record count
        if records and not request.POST.get("field_0_0"):
            try:
                records = int(records)
            except ValueError:
                return HttpResponse("❌ Invalid record count")

            # fetch columns
            conn = mysql.connector.connect(host="localhost", user="root", password=pas, database=dbname)
            c1 = conn.cursor()
            c1.execute(f"DESCRIBE {table}")
            columns = [col[0] for col in c1.fetchall()]
            conn.close()

            return render(request, "insert_records.html", {"table": table,"columns": columns,"records": range(records)})

        # STEP 2: User submitted actual values
        else:
            try:
                conn = mysql.connector.connect(host="localhost", user="root", password=pas, database=dbname)
                c1 = conn.cursor()

                # fetch columns again
                c1.execute(f"DESCRIBE {table}")
                columns = [col[0] for col in c1.fetchall()]

                records_to_insert = []
                i = 0
                while True:
                    row = []
                    row_has_data = False
                    for col in range(len(columns)):
                        field_value = request.POST.get(f"field_{i}_{col}")
                        if field_value not in [None, ""]:
                            row.append(field_value)
                            row_has_data = True
                        else:
                            row.append(None)
                    if not row_has_data:
                        break
                    records_to_insert.append(row)
                    i += 1

                if records_to_insert:
                    placeholders = ", ".join(["%s"] * len(columns))
                    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                    c1.executemany(query, records_to_insert)
                    conn.commit()
                    msg = f"✅ {len(records_to_insert)} record(s) inserted successfully into {table}!"
                else:
                    msg = "⚠️ No data provided."

                conn.close()
                return HttpResponse(msg)

            except Error as e:
                return HttpResponse(f"❌ MySQL Error: {e}")

    return render(request, "edit_table.html")

def update_records(request):
    pas = request.session.get("mysql_password")
    dbname = request.session.get("current_db")
    table = request.session.get("selected_table")

    conn = None
    c1 = None
    try:
        conn = mysql.connector.connect(host="localhost", user="root", password=pas, database=dbname)
        c1 = conn.cursor(dictionary=True)
        
        pk_col = None
        c1.execute(f"SHOW KEYS FROM `{table}` WHERE Key_name = 'PRIMARY'")
        primary_key_info = c1.fetchone()
        if primary_key_info:
            pk_col = primary_key_info['Column_name']

        if request.method == "POST":
            row_indices = request.POST.getlist("row_indices")
            if not row_indices:
                return HttpResponse("No rows submitted for update.", status=400)
            
            conn.autocommit = False
            try:
                for row_index in row_indices:
                    columns = request.POST.getlist(f"row_{row_index}_columns")
                    
                    set_clause_parts = []
                    update_params = []
                    for col in columns:
                        new_value = request.POST.get(f"row_{row_index}_{col}")
                        processed_value = None if new_value in ["", "NULL"] else new_value
                        set_clause_parts.append(f"`{col}` = %s")
                        update_params.append(processed_value)
                    
                    set_clause = ", ".join(set_clause_parts)
                    
                    where_params = []
                    if pk_col:
                        original_pk_value = request.POST.get(f"original_row_{row_index}_pk")
                        where_clause = f"`{pk_col}` = %s"
                        where_params.append(original_pk_value)
                    else:
                        where_clause_parts = []
                        for col in columns:
                            original_value = request.POST.get(f"original_row_{row_index}_{col}")
                            processed_original_value = None if original_value in ["", "NULL"] else original_value
                            where_clause_parts.append(f"`{col}` <=> %s")
                            where_params.append(processed_original_value)
                        where_clause = " AND ".join(where_clause_parts)
                    
                    update_query = f"UPDATE `{table}` SET {set_clause} WHERE {where_clause}"
                    c1.execute(update_query, update_params + where_params)
                
                conn.commit()
                return HttpResponse("✅ Records updated successfully!")
            except Exception as e:
                conn.rollback()
                return HttpResponse(f"❌ Transaction failed. Error: {e}", status=500)
        else:
            c1.execute(f"SELECT * FROM `{table}` LIMIT 100")
            table_data = c1.fetchall()
            columns = [desc[0] for desc in c1.description]

            return render(request, "update_records.html", {"table_name": table,"table_columns": columns,"table_data": table_data,"selected_db": dbname,"pk_col": pk_col})

    except mysql.connector.Error as e:
        return HttpResponse(f"❌ MySQL Error: {e}", status=500)
    except Exception as e:
        return HttpResponse(f"❌ An unexpected server error occurred: {e}", status=500)
    finally:
        if c1:
            c1.close()
        if conn:
            conn.close()

def delete_record(request):
    pas = request.session.get("mysql_password")
    dbname = request.session.get("current_db")
    table = request.session.get("selected_table")

    conn = None
    c1 = None
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=pas,
            database=dbname
        )
        c1 = conn.cursor(dictionary=True)

        # Identify primary key column
        pk_col = None
        c1.execute(f"SHOW KEYS FROM `{table}` WHERE Key_name = 'PRIMARY'")
        primary_key_info = c1.fetchone()
        if primary_key_info:
            pk_col = primary_key_info['Column_name']

        if request.method == "POST":
            conn.autocommit = False
            try:
                if pk_col:
                    # Delete by primary key
                    pk_value = request.POST.get("pk_value")
                    delete_query = f"DELETE FROM `{table}` WHERE `{pk_col}` = %s"
                    c1.execute(delete_query, (pk_value,))
                else:
                    # No PK → delete using all column values
                    where_parts = []
                    where_params = []
                    for key, value in request.POST.items():
                        if key.startswith("col_"):
                            col = key.replace("col_", "")
                            processed_value = None if value in ["", "NULL"] else value
                            where_parts.append(f"`{col}` <=> %s")
                            where_params.append(processed_value)

                    where_clause = " AND ".join(where_parts)
                    delete_query = f"DELETE FROM `{table}` WHERE {where_clause} LIMIT 1"
                    c1.execute(delete_query, where_params)

                conn.commit()
                return redirect("/update_records/")  # back to update page
            except Exception as e:
                conn.rollback()
                return HttpResponse(f"❌ Delete failed. Error: {e}", status=500)

        return HttpResponse("Invalid request method", status=405)

    except mysql.connector.Error as e:
        return HttpResponse(f"❌ MySQL Error: {e}", status=500)
    except Exception as e:
        return HttpResponse(f"❌ Unexpected error: {e}", status=500)
    finally:
        if c1:
            c1.close()
        if conn:
            conn.close()