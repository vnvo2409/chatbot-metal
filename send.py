import requests
import os
import json

GRAPH_ENDPOINT = os.getenv("GRAPH_ENDPOINT")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")


def SendGenericMessage(recipient_id, message):
    payload = {"recipient": {"id": recipient_id}, "message": message}
    res = requests.post(
        GRAPH_ENDPOINT + "/me/messages?access_token=" + PAGE_ACCESS_TOKEN,
        json=payload,
    )
    if res.status_code != requests.codes.ok:
        print(json.loads(res.content))
