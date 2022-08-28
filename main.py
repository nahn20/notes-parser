import argparse
import os
import googleServiceAccount
import json
from pprint import pprint
import lineParser
import iso8601
import datetime

def isValidFile(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')  # return an open file handle

def getCleanName(path):
    base_name = os.path.basename(path)
    split_name = os.path.splitext(base_name)
    if(split_name[1] == '.nmd' or split_name[1] == '.txt'):
        return split_name[0]
    return base_name
def formatPath(path):
    head = os.path.split(path)[0]
    split = head.split('/')
    return split
def getFileId(driveService, rootFolder, path=[]):
    prev = rootFolder
    for item in path:
        dir_res = driveService.files().list(q=f"mimeType='application/vnd.google-apps.folder' and parents='{prev}' and name='{item}'").execute()
        if(len(dir_res['files']) == 0):
            file_res = driveService.files().list(q=f"mimeType='application/vnd.google-apps.document' and parents='{prev}' and name='{item}'").execute()
            if(len(file_res['files']) > 0):
                if(len(file_res['files']) > 1):
                    print("Warning: Duplicate files found")
                    print(path)
                return file_res['files'][0]['id']
            return False
        else:
            prev = dir_res['files'][0]['id']
    return False
def getOrCreateDoc(driveService, docService, rootFolder, path):
    arr_path = formatPath(path)
    arr_path.append(getCleanName(path))
    potentialId = getFileId(driveService, rootFolder, arr_path)
    if(potentialId):
        return potentialId
    return createDoc(docService, title=getCleanName(path))
def getOrCreateFolder(driveService, rootFolder, path=[]):
    if(path[0] == 'sync'):
        path.pop(0)
    prev = rootFolder
    for folder in path:
        res = driveService.files().list(q=f"mimeType='application/vnd.google-apps.folder' and parents='{prev}' and name='{folder}'").execute()
        if(len(res['files']) == 0):
            file_metadata = {
                'name': folder,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            res = driveService.files().create(body=file_metadata, fields='id').execute()
            moveToFolder(driveService, res['id'], prev)
            prev = res['id']
        else:
            prev = res['files'][0]['id']
    return prev
#Determines based on custom metadata if it's safe to overwrite file
def isSafeOverwrite(driveService, fileId):
    res = driveService.files().get(fileId=fileId, fields='modifiedTime,appProperties').execute()
    if('appProperties' not in res):
        return True
    expected_last_modified = iso8601.parse_date(res['appProperties']['lastTouched'])
    last_modified = iso8601.parse_date(res['modifiedTime'])
    diff_secs = (last_modified-expected_last_modified).total_seconds()
    if(abs(diff_secs) < 5):
        return True
    return False
def touch(driveService, fileId):
    driveService.files().update(fileId=fileId, body={
        'appProperties': {
            'lastTouched': datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
        }
    }).execute()
"""
Handles a single file whose path is specified in args
"""
def handleFile(driveService, docService, args):
    config = {}
    if(type(args) is not dict):
        args = vars(args)
    if(args.get('config')):
        config = json.load(args['config'])

    docId = getOrCreateDoc(driveService, docService, config['rootFolder'], args['file'].name)
    #docId = '1wf9GyXiBGgOExYTgfd0SyTUoDwUUfogw2WJ_8V32uP0'

    doc = docService.documents().get(documentId=docId).execute()
    destinationId = getOrCreateFolder(driveService, config['rootFolder'], formatPath(args['file'].name))
    moveToFolder(driveService, docId, destinationId)

    requests = []

    endIndex = doc['body']['content'][-1]['endIndex']-1
    safe_overwrite = isSafeOverwrite(driveService, docId)
    if(not safe_overwrite and args.get('overwrite')):
        print("[Unsafe Overwrite] Flag dictates overwrite anyways for file {}".format(doc['title']))
    if(not safe_overwrite and not args.get('overwrite')):
        print("[Unsafe Overwrite] Terminating for file {}".format(doc['title']))
    if((safe_overwrite or args.get('overwrite')) and endIndex > 1):
        requests.append({
            'deleteContentRange': {
                'range': {
                    'endIndex': endIndex,
                    'startIndex': 1
                }
            }
        })
        endIndex = 1
    else:
        return
    curIndex = endIndex

    for dirtyLine in args['file']:
        line = dirtyLine.rstrip()
        res = lineParser.parseLine(line+'\n', curIndex)
        curIndex = res['curIndex']
        requests += res['requests']

    if(len(requests) > 0):
        res = docService.documents().batchUpdate(documentId=docId, body={
            'requests': requests
        }).execute()
    touch(driveService, docId)
def moveToFolder(driveService, fileId, folderId):
    file = driveService.files().get(fileId=fileId, fields='parents').execute()

    previous_parents = ",".join(file.get('parents'))
    if(previous_parents == folderId):
        return

    file = driveService.files().update(
        fileId=fileId,
        addParents=folderId,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
def main():
    parser = argparse.ArgumentParser(description='A cool program.')
    parser.add_argument('file', help="input file path", type=lambda x: isValidFile(parser, x))
    parser.add_argument('--config', help="config file path", type=lambda x: isValidFile(parser, x))
    parser.add_argument('--upload', action=argparse.BooleanOptionalAction)
    parser.add_argument('--overwrite', action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    creds = googleServiceAccount.getCredentials()
    driveService = googleServiceAccount.getDriveService(creds)
    docService = googleServiceAccount.getDocService(creds)

    handleFile(driveService, docService, args)
def createDoc(service, title="Untitled Autogenerated Document"):
    doc = service.documents().create(body={
        'title': title
    }).execute()
    return doc.get('documentId')
if __name__ == "__main__":
    main()
