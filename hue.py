import dotenv
from os import getenv
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from pprint import pprint
import json
import requests
import time
# threading pools
from concurrent.futures import ThreadPoolExecutor


dotenv.load_dotenv()

import json
from dotenv import load_dotenv
from os import getenv


def color_json_print(object):
    jtext = json.dumps(object, indent=2)
    ftext = highlight(jtext, lexer=JsonLexer(), formatter=TerminalFormatter())
    print(ftext)

BRIDGE_IP = getenv("BRIDGE_IP")
APP_ID = getenv("APP_ID")

# disable ssl warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Hue:

    SHORT = 0.1

    def __init__(self, bridge_ip, app_id):
        self.bridge_ip = bridge_ip
        self.app_id = app_id
        self.base_url = f"https://{self.bridge_ip}/clip/v2"

    def send(self, method, url, json_data=None, query_params=None, timeout=2):
        headers = {"hue-application-key": self.app_id}
        try:
            return requests.request(method, f"{self.base_url}{url}", headers=headers, json=json_data, params=query_params, verify=False, timeout=timeout)
        except requests.exceptions.Timeout:
            return False
    
    def get_lights(self):
        return self.send("GET", "/resource/light", None)
    
    def turn_light(self, light_id, on=True):
        return self.send("PUT", f"/resource/light/{light_id}", json_data={"on": {"on":on}, "dimming": {"brightness": 100 - 100*(not on)},  "dynamics": {"duration": 15}}, timeout=self.SHORT)

def party_mode(hue, lights, delay=0.3):
    with ThreadPoolExecutor(max_workers=6) as executor:
        for light in lights:
            print(f"Turning on light {light['metadata']['name']}")
            executor.submit(hue.turn_light, light["id"], False)
            time.sleep(delay)
        time.sleep(delay*2)
        for light in lights:
            executor.submit(hue.turn_light, light["id"], True)
            time.sleep(delay)

def alternate_half_lights(hue, lights, on=True):
    # select half of the lights and turn them off
    half = len(lights)//2
    with ThreadPoolExecutor(max_workers=len(lights)) as executor:
        for i in range(half):
            print(f"Turning {on} light {lights[i]['metadata']['name']}")
            executor.submit(hue.turn_light, lights[i]["id"], on)
        for i in range(half, len(lights)):
            print(f"Turning {on} light {lights[i]['metadata']['name']}")
            executor.submit(hue.turn_light, lights[i]["id"], not on)  
    
        

def main():
    hue = Hue(BRIDGE_IP, APP_ID)
    lights = hue.get_lights().json()['data']

    filtered_lights = list(filter(lambda light: light["metadata"]["name"].startswith("Wk spot"), lights))
    # color_json_print(list(filtered_lights))
    # sort by name
    filtered_lights.sort(key=lambda light: light["metadata"]["name"])
    # Turn off all lights
    for light in filtered_lights:
        hue.turn_light(light["id"], False)
        time.sleep(1)
    delay = 0.2
    while True:
        party_mode(hue, filtered_lights, delay)
    # color_json_print(list(map(lambda l: {"id":l['id'], "name": l['metadata']['name']}, filtered_lights)))

if __name__ == "__main__":
    main()