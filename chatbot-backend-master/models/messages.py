import sqlite3
from db.config import get_db

def get_messages(room_id):
  conn = get_db()
  cur = conn.cursor()
  cur = cur.execute("SELECT * FROM messages WHERE chat_room_id=? ORDER BY created_at ASC", [room_id])
  messages = cur.fetchall()
  cur.close()
  return messages

def create_message(text: str, message_from='u', room_id=None):
  conn = get_db()
  cur = conn.cursor()
  message = None
  try:
    cur.execute("INSERT INTO messages (message_text, message_from, chat_room_id) VALUES(?, ?, ?)", [text, message_from, room_id])
    conn.commit()
    message = cur.execute("SELECT * FROM messages WHERE id=?", [cur.lastrowid]).fetchone()
  except sqlite3.Error as err:
    print(err.args)
  
  cur.close()
  return message

def create_messages(texts: list, message_from='u', room_id=None):
  conn = get_db()
  cur = conn.cursor()
  message = []
  data_insert = []
  for text in texts:
    data_insert.append((text, message_from, room_id))
  try:
    cur.executemany("INSERT INTO messages (message_text, message_from, chat_room_id) VALUES(?, ?, ?)", data_insert)
    conn.commit()
    message = cur.execute("SELECT * FROM messages WHERE chat_room_id=? AND message_from LIKE ? ORDER BY id DESC LIMIT ?", [room_id, message_from, cur.rowcount]).fetchall()
  except sqlite3.Error as err:
    print(err.args)
  
  conn.close()
  return message

def delete_message(id):
  conn = get_db()
  cur = conn.cursor()
  delete_message = False
  try:
    cur = cur.execute("DELETE FROM messages WHERE id=?", [id])
    conn.commit()
    delete_message = True
  except sqlite3.Error as err:
    print(err.args)
  
  cur.close()
  return delete_message

def formatted_message(message: dict):
  return {
    'id': message['id'],
    'message_text': message['message_text'],
    'message_from': message['message_from'],
    'created_at': message['created_at'].strftime("%a, %d %b %Y %H:%M:%S GMT"),
    'read_at': message['read_at'] if message['read_at'] != None else None,
    'chat_room_id': message['chat_room_id']
  }

def formatted_messages(messages: list):
  data = []
  for message in messages:
    data.append(formatted_message(message))

  return data