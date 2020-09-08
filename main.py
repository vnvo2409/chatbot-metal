from flask import Flask, request
import os
import json
import sql
import send

app = Flask(__name__)

NOTE_ID_STATUS = "_s_t_a_t_u_s_"
NOTE_NAME_STATUS_SEARCH = "_s_e_a_r_c_h_"
NOTE_NAME_SET_NAME_LATEST_NOTE = "_s_e_t_n_a_m_e_l_a_t_e_s_t_n_o_t_e_"


@app.route("/", methods=["GET"])
def webhook_get():
    mode = request.args.get("hub.mode")
    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and verify_token == os.getenv("VERIFY_TOKEN"):
        return challenge, 200
    else:
        return "verify token does not match", 403


@app.route("/", methods=["POST"])
def webhook_post():
    event = json.loads(request.data)
    if event["object"] != "page":
        return ""
    for entry in event["entry"]:
        process_messaging(entry["messaging"][0])
    return ""


def process_messaging(messaging):
    try:
        user_id = messaging["sender"]["id"]
        if "message" in messaging:
            message = messaging["message"]
            process_message(user_id, message)
        elif "postback" in messaging:
            postback = messaging["postback"]
            process_postback(user_id, postback)
    except Exception as exp:
        print(exp)
    finally:
        return ""


def process_postback(user_id, postback):
    payload = postback["payload"]
    if payload == "GET_STARTED":
        send.SendGenericMessage(
            user_id,
            {"text": "Send anything to save, reply to the message to give it a new!"},
        )
        with sql.db.connect() as conn:
            conn.execute(
                f"INSERT INTO chatbot_metal.notes (id, user_id ) VALUES ('{NOTE_ID_STATUS}' ,'{user_id}') "
            )
    elif payload == "SEARCH0":
        send.SendGenericMessage(
            user_id,
            {"text": "Enter the name you want to search"},
        )
        with sql.db.connect() as conn:
            conn.execute(
                f"UPDATE chatbot_metal.notes SET note_name = '{NOTE_NAME_STATUS_SEARCH}', note_content = '{payload}' WHERE id = '{NOTE_ID_STATUS}' AND user_id = '{user_id}'"
            )
    elif payload == "CANCEL_SEARCH":
        send.SendGenericMessage(
            user_id,
            {"text": "Search is cancel"},
        )
        with sql.db.connect() as conn:
            conn.execute(
                f"UPDATE chatbot_metal.notes SET note_name = NULL, note_content = NULL WHERE id = '{NOTE_ID_STATUS}' AND user_id = '{user_id}'"
            )
    elif payload == "SET_NAME_LATEST_NOTE":
        send.SendGenericMessage(
            user_id,
            {"text": "Enter the name for the latest note!"},
        )
        with sql.db.connect() as conn:
            note_id = conn.execute(
                f"SELECT id, created_at FROM chatbot_metal.notes WHERE user_id = '{user_id}' AND id != '{NOTE_ID_STATUS}' ORDER BY created_at DESC LIMIT 1"
            ).fetchone()[0]
            conn.execute(
                f"UPDATE chatbot_metal.notes SET note_name = '{NOTE_NAME_SET_NAME_LATEST_NOTE}', note_content = '{note_id}' WHERE id = '{NOTE_ID_STATUS}' AND user_id = '{user_id}'"
            )


def process_message(user_id, message):
    with sql.db.connect() as conn:
        status = conn.execute(
            f"SELECT note_name, note_content FROM chatbot_metal.notes WHERE id = '{NOTE_ID_STATUS}' AND user_id = '{user_id}'"
        ).fetchone()
        if status[0] is not None:
            process_status(user_id, status, message)
            return
    if "reply_to" in message:
        note_id = message["reply_to"]["mid"]
        note_name = message["text"]
        with sql.db.connect() as conn:
            conn.execute(
                f"UPDATE chatbot_metal.notes SET note_name = '{note_name}' WHERE id = '{note_id}' AND user_id = '{user_id}'"
            )
    else:
        note_id = message["mid"]
        note_content = message["text"]
        with sql.db.connect() as conn:
            conn.execute(
                f"INSERT INTO chatbot_metal.notes (id, user_id, note_content ) VALUES ('{note_id}' ,'{user_id}', '{note_content}') "
            )
            send.SendGenericMessage(user_id, {"text": "Saved!"})


def process_status(user_id, status, message):
    payload = message["quick_reply"]["payload"] if "quick_reply" in message else ""
    if payload.startswith("GETNOTE"):
        note_id = payload[len("PAYLOAD") :]
        with sql.db.connect() as conn:
            content = conn.execute(
                f"SELECT note_content FROM chatbot_metal.notes WHERE user_id = '{user_id}' AND id = '{note_id}'"
            ).fetchone()[0]
            send.SendGenericMessage(user_id, {"text": content})
    elif payload.startswith("SEARCH"):
        splits = payload.split(sep="#", maxsplit=1)
        offset = int(splits[0][len("SEARCH") :])
        pattern = splits[1]
        search(user_id, pattern, offset)
    elif status[0] == NOTE_NAME_STATUS_SEARCH:
        offset = 0
        pattern = message["text"]
        search(user_id, pattern, offset)
    elif status[0] == NOTE_NAME_SET_NAME_LATEST_NOTE:
        note_id = status[1]
        note_name = message["text"]
        with sql.db.connect() as conn:
            conn.execute(
                f"UPDATE chatbot_metal.notes SET note_name = '{note_name}' WHERE id = '{note_id}' AND user_id = '{user_id}'"
            )
            conn.execute(
                f"UPDATE chatbot_metal.notes SET note_name = NULL, note_content = NULL WHERE id = '{NOTE_ID_STATUS}' AND user_id = '{user_id}'"
            )


def search(user_id, pattern, offset):
    with sql.db.connect() as conn:
        notes = conn.execute(
            f"SELECT id, note_name FROM chatbot_metal.notes WHERE user_id = '{user_id}' AND note_name LIKE '%%{pattern}%%' AND note_name != '{NOTE_NAME_STATUS_SEARCH}' ORDER BY note_name LIMIT 11 OFFSET {offset}"
        ).fetchall()
        more_note = False
        if len(notes) == 11:
            more_note = True
            notes = notes[0:9]
        quick_replies_notes = []
        for note in notes:
            quick_replies_notes.append(
                {
                    "content_type": "text",
                    "title": note[1],
                    "payload": "GETNOTE" + note[0],
                }
            )
        if more_note:
            quick_replies_notes.append(
                {
                    "content_type": "text",
                    "title": "More notes",
                    "payload": "SEARCH" + str(offset + 10) + "#" + pattern,
                }
            )
        send.SendGenericMessage(
            user_id,
            {"text": "List of notes found", "quick_replies": quick_replies_notes},
        )


if __name__ == "__main__":
    app.run()
