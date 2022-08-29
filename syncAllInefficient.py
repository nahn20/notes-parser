import argparse
import os
from main import handleFile
import googleServiceAccount
import gitUtils

def enqueueAll(driveService, docService, path):
    for item in os.listdir(path):
        full = os.path.join(path, item)
        if os.path.isfile(full):
            mock_args = {
                'file': open(full, 'r'),
                'config': open('config.json', 'r'),
                'overwrite': True
            }
            handleFile(driveService, docService, mock_args)
        if os.path.isdir(full):
            if(item != '.git'):
                enqueueAll(driveService, docService, full)

def main():
    gitUtils.pull()

    creds = googleServiceAccount.getCredentials()
    driveService = googleServiceAccount.getDriveService(creds)
    docService = googleServiceAccount.getDocService(creds)

    enqueueAll(driveService, docService, "sync")
if __name__ == "__main__":
    main()
