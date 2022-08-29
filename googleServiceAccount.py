import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

PROJECT_ID = '116086635593352459139'

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']

def getCredentials():
    dirname = os.path.dirname(__file__)
    f = open(os.path.join(dirname, 'certificate.json'))
    info = json.load(f)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return creds
def getDriveService(creds):
    return build('drive', 'v3', credentials=creds)
def getDocService(creds):
    return build('docs', 'v1', credentials=creds)
