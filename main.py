from keboola import docker

import ex.gmail.client as gmail
import ex.archive.processor as archive_processor
import logging
import json
import sys
import os.path
import shutil
from datetime import datetime




PAR_BUCKET = "kbc_bucket"
PAR_USER = "user"
PAR_QUERY = "q"
PAR_CLIENT_ID = "client_id"
PAR_CLIENT_SECRET = "#client_secret"
PAR_REFRESH_TOKEN = "#refresh_token"
PAR_FILE_MAPPING = "fileMapping"
PAR_SINCE_LAST = "sinceLast"
PAR_INCREMENTAL = "incremental"

KEY_SEPARATOR = "separator"
KEY_ENCLOSURE = "enclosure"
KEY_PREFIX = "prefix"
KEY_PKEY = "pkey"
KEY_TABLE_NAME = "tableName"
KEY_HEADER = "header"
KEY_LAST_RUN="lastRun"


DATA_PATH = '/data/'
PAR_OUT_TABLES_PATH = os.path.join(DATA_PATH, 'out', 'tables')
TEMP_FOLDER_PATH = os.path.join(DATA_PATH,'tmp')
MANDATORY_PARAMS = [PAR_BUCKET, PAR_USER, PAR_QUERY, PAR_FILE_MAPPING]


def validateConfig(dockerConfig):
    parameters = dockerConfig.get_parameters()
    for field in MANDATORY_PARAMS:
        if not parameters[field]:
            raise Exception('Missing mandatory configuration field: ' + field)
        if field == PAR_FILE_MAPPING:
            for mapp in parameters[field]:
                if not mapp.get(KEY_SEPARATOR):
                    raise Exception('Missing missing separator in mapping')
                if not mapp.get(KEY_PREFIX):
                    raise Exception('Missing missing prefix in mapping')


# #######  Common interface methods
def loadStateFile():
        base_dir = os.path.normpath(os.path.join(DATA_PATH, 'in'))        
        file_name = os.path.join(base_dir, 'state.json')
        lastState = None
        if os.path.isfile(file_name):
            with open(file_name) as lastStateFile:
                lastState = json.load(lastStateFile)
        return lastState


def writeLastState(lastRun):
        base_dir = os.path.normpath(os.path.join(DATA_PATH, 'out'))        
        file_name = os.path.join(base_dir, 'state.json')
        lastState = {
            KEY_LAST_RUN: lastRun
        }
        with open(file_name, 'w') as state_file:
            json.dump(lastState, state_file)


def write_table_manifest(
            file_name,
            destination,
            columns,
            delimiter=',',
            enclosure='"',
            primary_key=None,
            incremental = True):
        """
        Write manifest for output table Manifest is used for
        the table to be stored in KBC Storage.

        Args:
            file_name: Local file name of the CSV with table data.
            destination: String name of the table in Storage.
            primary_key: List with names of columns used for primary key.
        """
        primary_key = primary_key or []
        columns = columns or []
        increment = True if incremental else False
        manifest = {
            'destination': destination,
            'primary_key': primary_key,
            'columns' : columns,
            'incremental' : True,
            'delimiter': delimiter,
            "enclosure" : enclosure
        }
        with open(file_name + '.manifest', 'w') as manifest_file:
            json.dump(manifest, manifest_file)

# ##### Helper methods
def getUniquePrefixes(folderPath):
    files = []
    for i in os.listdir(folderPath):
        if os.path.isfile(os.path.join(folderPath,i)):
            files.append(i[0:i.find('_')])

    return set(files)


def removeHeaderFromFileAndMove(inputFile, outputFile, encoding):
    counter = 0
    with open(inputFile, 'r', encoding=encoding) as fin, open(outputFile, 'a', encoding='utf-8') as fout:
        for line in fin:
            if counter == 0: #skip header
                header = line
                pass
            else:
                if len(line) > 1:
                    fout.write(line)
            counter += 1
    return header;


def prepareSlicedTable(inputFileName, inputFolderPath, outputFolderPath, encoding, header):
    inputFile = inputFolderPath + os.sep + inputFileName
    outputFile = outputFolderPath + os.sep + inputFileName
    
    if not os.path.exists(outputFolderPath):
        os.makedirs(outputFolderPath)

    newHeader = header
    if not header:
        newHeader = removeHeaderFromFileAndMove(inputFile, outputFile, encoding)
    else:
        if os.path.isfile(outputFile):
            os.remove(outputFile)
        shutil.move(inputFile, outputFile)
    return newHeader


def processFilesWithPrefix(inputFolderPath, fileMapping, outputFolderPath, outBucket, encoding):
    files = []
    prefix = fileMapping.get(KEY_PREFIX)
    outputSlicedFolder = outputFolderPath + os.sep + fileMapping.get(KEY_PREFIX)
    header = fileMapping.get(KEY_HEADER).split(fileMapping.get(KEY_SEPARATOR))
    outPutTableName = fileMapping.get(KEY_TABLE_NAME) if fileMapping.get(KEY_TABLE_NAME) else prefix

    for i in os.listdir(inputFolderPath):
        if os.path.isfile(os.path.join(inputFolderPath,i)) and prefix in i:
            files.append(i)

    for file in files:
        prepareSlicedTable(file, inputFolderPath, outputSlicedFolder, encoding, header)
    # create manifest
    write_table_manifest(outputSlicedFolder, outBucket+'.'+outPutTableName, header, fileMapping.get(KEY_SEPARATOR), 
                         fileMapping.get(KEY_ENCLOSURE), fileMapping.get(KEY_PKEY), fileMapping.get(PAR_INCREMENTAL))



######### exec

cfg = docker.Config(DATA_PATH)

validateConfig(cfg)
params = cfg.get_parameters()

oauthData = cfg.get_oauthapi_data()
appSecret = cfg.get_oauthapi_appsecret()
appKey = cfg.get_oauthapi_appkey()

lastState = loadStateFile()
since = None
if lastState and params.get(PAR_SINCE_LAST) in ['True',1]:
    since = lastState.get(KEY_LAST_RUN)



try:
    gmailClient  =  gmail.Client(appKey, appSecret, oauthData.get('refresh_token'), params[PAR_USER], params[PAR_QUERY], logging)
    attachments = gmailClient.downloadAttachments(since)
except Exception as err:
    logging.error("Error extracting attachments from Gmail: " + str(err))
    sys.exit(1)

if attachments:
    try:
        unzipper = archive_processor.Processor(logging)
        unzippedFiles = unzipper.unzip(attachments,TEMP_FOLDER_PATH)
    except RuntimeError as err:
        logging.error("Error unzipping attachments!",err)
        sys.exit(1)
    
    
    for fileMapping in params.get(PAR_FILE_MAPPING):
        processFilesWithPrefix(TEMP_FOLDER_PATH, fileMapping, PAR_OUT_TABLES_PATH, params.get(PAR_BUCKET), 'utf-8')
else:
    logging.warning("No email with attachments found for query: " + params.get(PAR_QUERY) + ' and since: ' + since)

writeLastState(datetime.now().strftime("%Y/%m/%d"))

logging.info("Extraction finished successfully!")




