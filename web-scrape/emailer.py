from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import pymysql, csv, boto3, os, sys, inspect
from datetime import datetime

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from db_conn import connect

def emailer(logger):

    today = datetime.now().strftime("%Y-%m-%d")

    SENDER = "tim.j.phillips10@gmail.com"
    AWS_REGION = "us-east-1"
    SUBJECT = "The Bourbonhuntr - Bourbon Inventory - {}".format( datetime.now().strftime("%a, %d %b %Y") )
    ATTACHMENT = ["Bourbon Dump.csv"]
    BODY_TEXT = "Hello,\r\nPlease see the attached file for todays bourbon inventory."
    CHARSET = "utf-8"

    BODY_HTML = """\
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>The Bourbonhuntr</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    </head>
    <body style="margin: 0; padding: 0; background-color:#ececec">
        <table border="0" cellpadding="0" cellspacing="0" width="100%"> 
            <tr>
                <td style="padding: 10px 0 30px 0;">
                    <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border: 1px solid #cccccc; border-collapse: collapse;">
                        <tr>
                            <td align="center" bgcolor="#70bbd9" style="padding: 40px 0 30px 0; color: #153643; font-size: 28px; font-weight: bold; font-family: Arial, sans-serif;">
                                <img src="http://www.smythenet.com/icon/TheBourbonHuntr_Logo_v1.png">
                            </td>
                        </tr>
                        <tr>
                            <td bgcolor="#ffffff" style="padding: 40px 30px 40px 30px;">
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td style="color: #153643; font-family: Arial, sans-serif; font-size: 28px;">
                                            <center><b>Greetings from The Bourbonhuntr!!</b></center>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 20px 0 30px 0; color: #153643; font-family: Arial, sans-serif; font-size: 16px; line-height: 20px;">
                                            <center><b>Attached you will find today's bourbon inventory.</b></center>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td bgcolor="#000000">
                                <img src="http://www.smythenet.com/icon/bourbon.jpg" width="100%" height="175px">
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>"""

    query = (
    '''    select 
            bourbon.storeid,
            Concat(store_full_addr, ' ', store_city) as store_addr,
            bourbon.productid,
            description,
            quantity
        from bourbon
        inner join bourbon_desc
        on bourbon.productid = bourbon_desc.productid
        inner join bourbon_stores
        on bourbon.storeid = bourbon_stores.storeid
        where CAST(insert_dt AS DATE) = '{}'

    '''.format(today)
    )

    mydb = connect()

    with mydb.cursor() as cur:
        cur.execute(query)
        for row in cur:
            res = cur.fetchall()
                
            fp = open('Bourbon Dump.csv', 'w')
            myFile = csv.writer(fp)
            myFile.writerow(["As of {}".format(today)])
            myFile.writerow(["Store Number", "Store Address", "Product ID", "Description", "Quantity"])
            myFile.writerows(res)
            fp.close()


    # Create a new SES resource and specify a region.
    ses_client= boto3.client('ses',region_name=AWS_REGION)

    recipients = ses_client.list_identities(
    IdentityType = 'EmailAddress',
    MaxItems=10
    )

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT 

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    #Attachment part
    for attachment in ATTACHMENT:
        att = MIMEApplication(open(attachment, 'rb').read())
        att.add_header('Content-ID', '<{}>'.format(os.path.basename(attachment)))
        att.add_header('Content-Disposition','attachment',filename=os.path.basename(attachment))
        msg.attach(att)
    
    msg.attach(msg_body)

    try:
        #Provide the contents of the email.
        response = ses_client.send_raw_email(
            Source=SENDER,
            Destinations=recipients['Identities'],
            RawMessage={
                'Data':msg.as_string(),
            }
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        logger.info(e.response['Error']['Message'])
    else:
        logger.info("Email sent! Message ID: {}".format(response['MessageId']))
        os.remove('Bourbon Dump.csv')