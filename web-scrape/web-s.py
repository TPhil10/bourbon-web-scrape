
import requests, csv, urllib3, watchtower, logging, pymysql, sys, os, inspect, time
import xml.etree.ElementTree as ET
from datetime import datetime
from emailer import emailer
import concurrent.futures

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from db_conn import connect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Inventory scrape {}'.format(datetime.now().strftime("%a, %d %b %Y" )))
logger.addHandler(watchtower.CloudWatchLogHandler())

requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

max_workers = 4

start_time = datetime.now()
logger.info("{} Running...".format(start_time.strftime('%m-%d-%Y %H:%M:%S')))

mydb = connect()
cur = mydb.cursor()

cur.execute("SELECT storeid FROM bourbon_stores")
storeResult = cur.fetchall()
cur.execute("SELECT productid FROM bourbon_desc")
prodResult = cur.fetchall()

url = 'https://www.abc.virginia.gov/webapi/inventory/storeNearby?storeNumber={}&productCode={}&mileRadius=999&storeCount=5&buffer=0'
url_list=[]
inventory = []

for store in storeResult:
    for product in prodResult:
        url_list.append(url.format(''.join(store) ,''.join(product) ))


# Retrieve a single page and report the url and contents
def load_url(url):

    time.sleep(1)
    try:
        with requests.get(url) as conn:
            return conn.content
    except requests.exceptions.RequestException as e:
        logger.info("Get called failed with: {}".format(e))
        return None
 
def parse_data(data):
    root = ET.fromstring(data)

    inv_list = []
    for child in root.findall("./products/products"):
        inv_list.append(child[0].text)
        for item in child[1]:
            if item.tag in ['storeId','PhoneNumber','quantity','longitude','latitude','distance']:
                if item.tag == 'PhoneNumber':
                    for phoneItem in item:
                        inv_list.append(phoneItem.text)
                elif item.tag == 'quantity':
                    inv_list.append(int(item.text))
                elif item.tag in ('longitude','latitude'):
                    if item.text is None: #Sometimes the long/lat values are deleted off their site
                        inv_list.append(item.text)
                    else:
                        inv_list.append(float(item.text))
                else: 
                    inv_list.append(item.text)

        formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        inv_list.append(formatted_date)

        if inv_list[2] > 0: #Remove any lists with 0 quantity
            inv_list = tuple(inv_list) 
        else:
            break

        try:
            insert_str = """INSERT INTO bourbon VALUES (null, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(insert_str, inv_list)
            mydb.commit()

        except Exception as error:
            logger.info("Failed to insert record into MySQL table {}".format(error))


with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_url = {executor.submit(load_url, url): url for url in url_list}
    for i, future in enumerate(concurrent.futures.as_completed(future_to_url), 1):
        try:
            data = future.result()

            if i % 500 == 0:
                time_diff = datetime.now() - start_time
                logger.info("Parsing url #: {} {} (Total time taken: {} seconds)".format(i, datetime.now().strftime('%m-%d-%Y %H:%M:%S'), time_diff.seconds ))

            parse_data(data)

        except Exception as exc:
            logger.info('{} generated an exception: {}'.format(future_to_url[future], exc))


            
if (connect().open):
    cur.close()
    mydb.close()
    logger.info("MySQL connection is closed")

logger.info("Download successful, sending emailer...")
emailer(logger)