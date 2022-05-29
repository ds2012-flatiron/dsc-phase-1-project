import os
import sys
import json
import gzip
import shutil

def convert_user_config_to_json(strUserConfigFile):
    """
    Converts user config file from readable flat format into JSON in one string format

    one madatory argument: location of user config file (./config/user_config.json)
    """
    # Reading data from config set up by user
    try: 
        fileUserConfig = open(strUserConfigFile, mode = 'r', encoding = 'utf-8')
        config = json.load(fileUserConfig)
    except OSError as err:
        print("OS error: {0}".format(err))
    fileUserConfig.close()
    # Write json config to the same folder as `user_config.json` location
    tplFolderFileSplit = os.path.split(strUserConfigFile)
    strJsonConfigFile  = os.path.join(tplFolderFileSplit[0],'config.json')
    
    # Writing data as a json dump
    try:
        fileJSON = open(strJsonConfigFile, mode = 'w', encoding = 'utf-8')
        json.dump(config, fileJSON)
    except OSError as err:
        print("OS error: {0}".format(err))
    fileJSON.close()

    return None

def load_json_config():
    """
    utility function 'load_json_config' loads file './config/config.json'
    which has been converted from 'user_config.json' file (editable format)
    via json.load() and json.dump()
    """
    # loading config from 
    try: 
        fileConfig = open('./config/config.json', mode = 'r', encoding = 'utf-8')
        config = json.load(fileConfig)
    except OSError as err:
        print("OS error: {0}".format(err))

    return config

def load_json_config_from_file(configFile):
    """
    utility function 'load_json_config' loads file './config/config.json'
    which has been converted from 'user_config.json' file (editable format)
    via json.load() and json.dump()
    
    Argument:
        `configFile` points to './config/config.json' from the location relative to
        the folder from where the function call is made.
    Example:
        if the function call is from folder './code/', then `configFile` must have value
        `./../config/config.json`
    """
    # File exists
    if not os.path.exists(configFile):
        raise FileNotFoundError
    # loading config from 
    try: 
        fileConfig = open(configFile, mode = 'r', encoding = 'utf-8')
        config = json.load(fileConfig)
    except OSError as err:
        print("OS error: {0}".format(err))

    return config


def check_file_exists(strFolder, strFile):
    dctReturnValue = {'file': '', 'exists': False}
    # construct the file location string 'strFileIn'
    strLoc = strFolder
    if strLoc.endswith('/'):
        strLoc += strFile
    else:
        strLoc += '/'
        strLoc += strFile
    if os.path.exists(strLoc):
        dctReturnValue['file'] = strLoc
        dctReturnValue['exists'] = True
    else:
        dctReturnValue['file'] = strLoc
    
    return dctReturnValue
    

def unzip_gz_file(strFileNameZip, strFileNameTxt, strFolderFrom, strFolderTo):
    """
    Takes one file 'strFileName' with .gz extension from folder 'strFolderFrom'
    and decompresses it to folder 'strFolderTo'
    Mandatory arguments:
    strFileNameZip -- compressed files with .gz extension
    strFileNameTxt -- decompressed file with a text file extension (.txt, .csv, .tsv)
    strFolderFrom -- compressed file source folder
    strFolderTo -- decompressed file destination folder
    """

    # construct the file location string 'strFileIn'
    dctFileExistsCheck = check_file_exists(strFolderFrom, strFileNameZip)
    if dctFileExistsCheck['exists']:
        strFileIn = dctFileExistsCheck['file']
    else:
        raise OSError(f"unable to open {dctFileExistsCheck['file']}")

    # main block of the function; 'check_file_exists' is used to create output file 
    # for decompressed data
    dctFileExistsCheck = check_file_exists(strFolderTo,strFileNameTxt)
    strFileOut = dctFileExistsCheck['file']
    
    try:
        with gzip.open(strFileIn, mode='rb') as fileGZ:
            with open(strFileOut, mode = 'wb') as fileTXT:
                shutil.copyfileobj(fileGZ, fileTXT)
    except OSError as err:
        print("OS error: {0}".format(err))

    return None

def generate_zipfilename_list_from_config(config):
    """
    This is a utility function to generate a flat list of .gz zipped files from
    'config' inputs. This function is specific to the structure of 'config'
    """
    lstReturnValue = list()
    dataFileKeys = list(map(lambda key: f"files-{key}", config['data-sources-keys']))
    for key in dataFileKeys:
        if type(config[key]['zip']) == dict:
            for item in config[key]['zip'].values():
                lstReturnValue.append(item)
        elif type(config[key]['zip']) == str:
                lstReturnValue.append((config[key]['zip']))
    
    return lstReturnValue