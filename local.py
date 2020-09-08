import requests
import os
import json

GRAPH_ENDPOINT = os.getenv("GRAPH_ENDPOINT")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")


def create_menu():
    res = requests.post(
        GRAPH_ENDPOINT + "/me/messenger_profile?access_token=" + PAGE_ACCESS_TOKEN,
        json={
            "get_started": {"payload": "GET_STARTED"},
            "greeting": [{"locale": "default", "text": "Hello {{user_full_name}}!"}],
            "persistent_menu": [
                {
                    "locale": "default",
                    "composer_input_disabled": False,
                    "call_to_actions": [
                        {
                            "type": "postback",
                            "title": "Search",
                            "payload": "SEARCH0",
                        },
                        {
                            "type": "postback",
                            "title": "Cancel search",
                            "payload": "CANCEL_SEARCH",
                        },
                        {
                            "type": "postback",
                            "title": "Set name latest note",
                            "payload": "SET_NAME_LATEST_NOTE",
                        },
                    ],
                }
            ],
        },
    )
    print(res.text)


if __name__ == "__main__":
    create_menu()
