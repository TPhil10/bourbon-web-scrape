
import csv, boto3, io, watchtower, logging, sys, os, inspect
from pymysql import Error
from datetime import datetime

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from db_conn import connect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('product scrape {}'.format(datetime.now().strftime("%a, %d %b %Y" )))
logger.addHandler(watchtower.CloudWatchLogHandler())

region = 'us-east-1'

mydb = connect()
cur = mydb.cursor()
logger.info('Truncating bourbon description table...')
cur.execute("truncate bourbon_desc")

s3 = boto3.client('s3', region_name=region)
prod_list = s3.get_object(Bucket='bourbon-app', Key='product_list.csv')
csv_data = prod_list['Body'].read().decode('utf-8')

try:
    insert_str = """INSERT INTO bourbon_desc VALUES (%s, %s, %s, %s, %s, %s)"""

    buf = io.StringIO(csv_data)
    csv_dict = csv.DictReader(buf)

    for row in csv_dict:
        if row['Age'] == '':
            row['Age'] = None
        record = (row["Code"], row["Brand"], row["Size"], row["Age"], float(row["Proof"]), float(row["Price"].strip().replace('$','').replace(',','')))
        cur.execute(insert_str, record)
        mydb.commit()
        logger.info("{} Record inserted successfully into the product table".format(cur.rowcount))

except Error as error:
    logger.info("Failed to insert record into MySQL table {}".format(error))


if (connect().open):
    cur.close()
    mydb.close()
    logger.info("MySQL connection is closed")
