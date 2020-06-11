from db_conn import connect
import pymysql

def tbl_insert(data):
  try:
    mydb = connect()
    cur = mydb.cursor()

    insert_str = """INSERT INTO bourbon VALUES (null, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    cur.executemany(insert_str, data)
    mydb.commit()
    print(cur.rowcount, "Record inserted successfully into bourbon table")

  except Exception as error:
    print("Failed to insert record into MySQL table {}".format(error))

  finally:
    if (connect().open):
        cur.close()
        mydb.close()
        print("MySQL connection is closed")
