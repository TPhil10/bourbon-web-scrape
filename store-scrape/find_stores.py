import requests, watchtower, logging, os, sys, inspect
from pymysql import Error
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from db_conn import connect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('store scrape {}'.format(datetime.now().strftime("%a, %d %b %Y" )))
logger.addHandler(watchtower.CloudWatchLogHandler())

requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")
options.add_argument("--headless")
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 5)

mydb = connect()
cur = mydb.cursor()
cur.execute("truncate bourbon_stores")

for storenum in range(1,500): #no store number below 32
    with requests.Session() as s:
        response = s.get("https://www.abc.virginia.gov/stores/" + str(storenum))

        if response.status_code == 200:

            store = []

            driver.get("https://www.abc.virginia.gov/stores/" + str(storenum))

            elem_full_addr = wait.until(ec.presence_of_element_located((By.TAG_NAME, "address"))).text.replace('\n', ' ')
            elem_addr1 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[ng-bind-html="model.store.eAddress.shoppingCenter | asTrusted"]')))
            elem_addr2 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'span[ng-bind-html="model.store.eAddress.address1 | asTrusted"]')))
            elem_addr3 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'span[ng-bind-html="model.store.eAddress.address2 | asTrusted"]')))
            elem_city = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'span[ng-bind-html="model.store.eAddress.city.trim() | asTrusted"]')))
            elem_state = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'span[ng-bind-html="model.store.eAddress.state | asTrusted"]')))
            elem_zip = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'span[ng-bind-html="model.store.eAddress.zipcode | asTrusted"]')))

            store.extend([str(storenum), elem_full_addr, elem_addr1.text, elem_addr2.text, elem_addr3.text, elem_city.text, elem_state.text, elem_zip.text])

            store = tuple(store)

            try:

                insert_str = """INSERT INTO bourbon_stores VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                cur.execute(insert_str, store)
                mydb.commit()
                logger.info("{} Record inserted successfully into bourbon store table (Store Number {})".format(cur.rowcount, storenum))

            except Exception as error:
                logger.info("Failed to insert record into MySQL table {}".format(error))

        else:
            logger.info("Store {} doesn't exist".format(storenum))

if (connect().open):
    cur.close()
    mydb.close()
    logger.info("MySQL connection is closed")