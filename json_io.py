import os, json
from pathlib import Path

def getJsonFile(name):
    workingDir = os.path.dirname(os.path.realpath(__file__)) + "/"
    if not Path(workingDir + name).is_file():
        raise ValueError("Missing " + name)
    try:
        with open(workingDir + name, "r") as f:
            return json.loads(f.read())
    except Exception as e:
        print("Failed to get file: " + name + " because of exception: " + str(e))
        raise e

def setJsonFile(name, text):
    workingDir = os.path.dirname(os.path.realpath(__file__)) + "/"
    try:
        with open(workingDir + name, "w+") as f:
            f.write(json.dumps(text))
    except Exception as e:
        print("Failed to write file: " + name + "because of exception: " + str(e))
        raise e
