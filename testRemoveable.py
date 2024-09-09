import requests
import pycurl
import json
import sys
from time import sleep
import certifi
import os
from urllib.parse import urlencode

from io import BytesIO

def removeKeys(d: dict, keys_to_remove: list):
    if isinstance(d, dict):
        return {k: removeKeys(v, keys_to_remove) for k, v in d.items() if k not in keys_to_remove}
    else:
        return d


if __name__ == "__main__":
    if (not os.path.exists("RequiredHeader.txt")):
        print("RequireHeader.txt not found")
        exit(-1)
    if (not os.path.exists("RemoveableKeys.txt")):
        print("RemoveableKeys.txt not found")
        exit(-1)

    if (len(sys.argv) == 1):
        file = open("examplecurl.sh")
    else:
        file = open(argv[1])


    lines = file.readlines()
    url = lines[0][6:-4]
    rawdata = lines[-1][14:-1]
    
    reqHeaders = []
    RemoveableKeys = []

    reqFile = open("RequiredHeader.txt")
    for ln in reqFile.readlines():
        reqHeaders.append(ln[:-1])
    
    rmFile = open("RemoveableKeys.txt")
    for ln in rmFile.readlines():
        RemoveableKeys.append(ln[:-1])
    
    dataJson:dict = json.loads(rawdata)
    rmdJson:dict = removeKeys(dataJson, RemoveableKeys)

    buffer = BytesIO()
    c = pycurl.Curl()

    c.setopt(c.URL, url)
    c.setopt(c.POST, 1)
    c.setopt(c.HTTPHEADER, reqHeaders)
    c.setopt(c.POSTFIELDS, json.dumps(rmdJson))
    c.setopt(c.CAINFO, certifi.where())
    c.setopt(c.WRITEDATA, buffer)
    c.perform()

    body = buffer.getvalue()
    if c.getinfo(pycurl.HTTP_CODE) != 200:
        print("Something was required")
    
    print(body.decode("utf-8"))

    