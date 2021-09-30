import requests
import json
import os
import base64

BASEURL = base64.b64decode("aHR0cDovL3JhZGlvLmdhcmRlbi9hcGkvYXJhL2NvbnRlbnQ=").decode("utf-8")

# modules for radio garden
def getChannels():
    container, idcontainer = [], []
    URL = BASEURL + "/favorites"
    with open("lib/stations.json", "r") as f: data = json.load(f)
    response = requests.post(url=URL, data=data).json()
    for i in response["data"]:
        container.append((i["title"], i["place"]["title"], i["country"]["title"]))
        idcontainer.append(i["id"])
    return container, idcontainer

def getListenUrl(id:str):
    URL = f"{BASEURL}/listen/{id}/channel.mp3"
    return URL

def searchRG(query:str):
    container = []
    idcontainer = []
    URL = f"{base64.b64decode('aHR0cDovL3JhZGlvLmdhcmRlbi9hcGkvc2VhcmNoP3E9').decode('utf-8')}{query}"
    response = requests.get(URL).json()
    for i in response["hits"]["hits"]:
        i = i["_source"]
        try:location = i["subtitle"]
        except KeyError: location = i["title"]
        title = i["title"]
        if i["type"] == "country":continue
        stid = i["url"].split("/")[-1]
        container.append((title, location, " "))
        idcontainer.append(stid)  
    return container, idcontainer

# modules for radio365
def fetchData():
    url = "https://live365.com/_next/data/6rVwQc0ex2Plg2edBQirB/index.json"
    response = requests.get(url).json()
    return response

def getStations(stype:int):
    response = fetchData()
    data = [response["pageProps"]['topStations'], response["pageProps"]['featuredStations']][stype]
    container = []
    idcontainer = []
    for i in data:
        genre = ""
        for j in i["genres"]:
            if stype == 0:genre+=f" | {j['name']}"
            else:genre+=f" | {j}"
        container.append((i["name"], i["description"], i["logo"], genre))
        if stype == 0:idcontainer.append(i["streamUrl"]["default"])
        else:idcontainer.append(i["streamUrl"])
    return container, idcontainer
