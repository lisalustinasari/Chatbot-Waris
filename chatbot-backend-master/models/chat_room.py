import sqlite3
from db.config import get_db

def create_room(name=None, user_id=None):
  conn = get_db()
  cur = conn.cursor()
  room = None
  try:
    cur.execute("INSERT INTO chat_room (chat_name, user_id) VALUES(?, ?)", [name, user_id])
    conn.commit()
    room = cur.execute("SELECT * FROM chat_room WHERE id=?", [cur.lastrowid]).fetchone()
  except sqlite3.Error as err:
    print(err.args)
    room = None
  
  cur.close()
  return room

def update_room(id, chat_name, user_id):
  conn = get_db()
  cur = conn.cursor()
  room = None
  try:
    cur.execute("UPDATE chat_room SET chat_name=?, user_id=? WHERE id=?", [id, chat_name, user_id])
    conn.commit()
    room = cur.execute("SELECT * FROM chat_room WHERE id=?", [id]).fetchone()
  except sqlite3.Error as err:
    print(err.args)
    room = None

  cur.close()
  return room

def get_room(id):
  conn = get_db()
  cur = conn.cursor()
  
  room = cur.execute("SELECT * FROM chat_room WHERE id=?", [id]).fetchone()
  return room

def get_room_user(user_id):
  conn = get_db()
  cur = conn.cursor()
  
  room = cur.execute("SELECT * FROM chat_room WHERE user_id=? ORDER BY id DESC", [user_id]).fetchone()
  return room

def get_rooms():
  conn = get_db()
  cur = conn.cursor()
  
  rooms = cur.execute("SELECT * FROM chat_room").fetchall()
  return rooms