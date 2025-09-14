import os
import json

minify = False

def minifyJsonFiles(rootDir="./assets"):
    for root, dirs, files in os.walk(rootDir):
        for infile in files:
            if infile.endswith(".json"):
                minifyExistingJson(root, infile)
def minifyExistingJson(root, infile):
    with open(os.path.join(root, infile), "r") as rf:
        data = json.load(rf)
        with open(os.path.join(root, infile), "w") as wf:
            json.dump(data, wf, separators=(',', ':'))

def dumpJson(data, f):
    json.dump(data, f, separators=(',', ':')) if minify else json.dump(data, f, indent=4)
