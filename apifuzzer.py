import requests
import pycurl
import json
import sys
from time import sleep
import certifi
import os
from urllib.parse import urlencode

from io import BytesIO

def parseHeaderAsDict(headerLns: list[str]) -> dict:
    out = {}
    for ln in headerLns:
        arg = ln[6:-4]
        colonIdx = arg.find(":")

        field = arg[:colonIdx]
        val = arg[colonIdx+1:]
        out[field] = val

    return out

def parseHeaderAsList(headerLns: list[str]) -> list[str]:
    out = []
    for ln in headerLns:
        out.append(ln[6:-4])
    
    return out

def printDictTree(aDict: dict, tabs: str = ""):
    if (type(aDict) != dict):
        return
    
    for key in list(aDict.keys()):
        print(tabs + key)
        printDictTree(aDict[key], tabs + f"|\t")

def treeDictTraverse(someDict: dict, travList: list):
    if travList == []:
        return someDict
    
    head: dict = someDict
    for key in travList:
        head = head[key]
    
    return head

def getKeys(d: dict) -> list:
    if type(d) != dict:
        return []
    
    out: list = list(d.keys())
    for key in list(d.keys()):
        out += getKeys(d[key])
    
    return out

def removeKeys(d: dict, keys_to_remove: list):
    if type(d) == dict:
        return {k: removeKeys(v, keys_to_remove) for k, v in d.items() if k not in keys_to_remove}
    else:
        return d

def removeKey(d: dict, key_to_remove: str):
    if type(d) == dict:
        return {k: removeKey(v, key_to_remove) for k, v in d.items() if k != key_to_remove}
    else:
        return d


# Quick and dirty script

# If you're using developer tools, use chrome.  It formats the copy as cURL requests more nicely
# See examplecurl.sh for what a curl script should look like
# Usage: python apifuzzer.py <Filename> 
if __name__ == "__main__":
    if (len(sys.argv) == 1):
        file = open("examplecurl.sh")
    else:
        file = open(argv[1])

    lines = file.readlines()

    url = lines[0][6:-4]

    headerLns = lines[1:-1]
    rawdata = lines[-1][14:-1]
    headLst = parseHeaderAsList(headerLns)
    

    #printDictTree(dataJson)
    
    reqHeaders = []

    # I use Pycurl over requests because Pycurl more closely replicates the behaviour of CPR which uses libcurl
    c = pycurl.Curl()

    # Check what headers are needed
    if (os.path.exists("RequiredHeader.txt")):
        reqFile = open("RequiredHeader.txt")
        for ln in reqFile.readlines():
            reqHeaders.append(ln[:-1])
        
        # Check if it's actually valid
        buffer = BytesIO()

        c.setopt(c.URL, url)
        c.setopt(c.POST, 1)
        c.setopt(c.HTTPHEADER, reqHeaders)
        c.setopt(c.POSTFIELDS, rawdata)
        c.setopt(c.CAINFO, certifi.where())
        c.setopt(c.WRITEDATA, buffer)
        c.perform()

        body = buffer.getvalue()
        if c.getinfo(pycurl.HTTP_CODE) != 200:
            print(f"http code: {c.getinfo(pycurl.HTTP_CODE)} | REQUIRED HEADERS NOT VALID")
            c.reset()
            exit(-1)
    else:
        for i in range(len(headLst)):
            buffer = BytesIO()

            c.setopt(c.URL, url)
            c.setopt(c.POST, 1)
            c.setopt(c.HTTPHEADER, headLst[:i] + headLst[i+1:])
            c.setopt(c.POSTFIELDS, rawdata)
            c.setopt(c.CAINFO, certifi.where())
            c.setopt(c.WRITEDATA, buffer)
            c.perform()

            body = buffer.getvalue()
            if c.getinfo(pycurl.HTTP_CODE) != 200:
                print(f"http code: {c.getinfo(pycurl.HTTP_CODE)} | header: {headLst[i]}")
                reqHeaders.append(headLst[i])
            
            c.reset()
        
        file = open("RequiredHeader.txt", "w+")
        for header in reqHeaders:
            file.write(header + "\n")
        file.close()
    


    dataJson:dict = json.loads(rawdata)
    dataJsonKeys = getKeys(dataJson)
    potentiallyRemoveableKeys = []

    # This makes an assumption that Google isn't sending any redundant data
    if (len(dataJsonKeys) > len(set(dataJsonKeys))):
        print("Precondition failed: Not all keys are unique")
        printDictTree(dataJson)
        exit(-1)
    
    # Not incredibly efficient, but this is something you run once.  
    # You could do something where you do some binary partitioning--i.e. you selectively remove half and see if it's okay if not remove half that and repeat
    for keyToRemove in dataJsonKeys:
        dictWithoutKey = removeKey(dataJson, keyToRemove)

        buffer = BytesIO()

        c.setopt(c.URL, url)
        c.setopt(c.POST, 1)
        c.setopt(c.HTTPHEADER, reqHeaders)
        c.setopt(c.POSTFIELDS, json.dumps(dictWithoutKey))
        c.setopt(c.CAINFO, certifi.where())
        c.setopt(c.WRITEDATA, buffer)
        c.perform()

        if c.getinfo(pycurl.HTTP_CODE) == 200:
            print(f"Removeable: {keyToRemove}")
            potentiallyRemoveableKeys.append(keyToRemove)
        
        c.reset()
    
    removeableFile = open("RemoveableKeys.txt", "w+")
    for key in potentiallyRemoveableKeys:
        removeableFile.write(key + "\n")
    
    removeableFile.close()