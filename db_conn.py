

import boto3
import json
import pymysql
import configparser

s3 = boto3.client('s3')
obj = s3.get_object(Bucket='bourbon-app', Key='config.ini')
config = configparser.ConfigParser()
config.read_string(obj['Body'].read().decode())

secrets_manager = boto3.client('secretsmanager')
rds_credentials = json.loads(
    secrets_manager.get_secret_value(SecretId=config['mysqlDB']['secretid'])['SecretString']
)

# Setup our mysql connection
connection_parameters = {
    'host': config['mysqlDB']['host'],
    'database': config['mysqlDB']['db'],
    'user': rds_credentials['username'],
    'password': rds_credentials['password']
}

def connect():
    return pymysql.connect(**connection_parameters)