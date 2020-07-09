import requests, csv, urllib3
import xml.etree.ElementTree as ET
from datetime import datetime
from ins_db import tbl_insert
from db_conn import connect

requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

inventory = []
url = 'https://www.abc.virginia.gov/webapi/inventory/mystore'

start_time = datetime.now()
print("{} Running...".format(start_time))

mydb = connect()
cur = mydb.cursor()

cur.execute("SELECT storeid FROM bourbon_stores")
storeResult = cur.fetchall()
cur.execute("SELECT productid FROM bourbon_desc")
prodResult = cur.fetchall()

for store in storeResult:
    with requests.Session() as s:
        inventory.clear()
        print("Downloading store #{}...".format(store[0]))
        for product in prodResult:

            params = (
                ('storeNumbers', store[0]),
                ('productCodes', product[0])
            )

            try:
                response = s.get(url,params=params, verify=False)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(err)
                break

            root = ET.fromstring(response.content)

            inv_list = []
            for child in root.findall("./products/products"):
                inv_list.append(child[0].text)
                for item in child[1].getchildren():
                    if item.tag == 'phoneNumber':
                        for phoneItem in item.getchildren():
                            inv_list.append(phoneItem.text)
                    else: 
                        inv_list.append(item.text)
                            
                inventory.append(inv_list)
                
        for l in inventory:
            for i in range(len(l)):
                if i == 2:
                    l[i] = 0 if int(l[i]) < 0 else int(l[i])
                elif i in (4,5):
                    l[i] = float(l[i])

        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

        for l in inventory:
            l.append(formatted_date)

        inventory = [tuple(i) for i in inventory] #comprehension
        end_time = datetime.now()
        print(end_time - start_time)
        cur.close()
        print("{} End of requests, starting database insert...".format(end_time))
        tbl_insert(inventory)
