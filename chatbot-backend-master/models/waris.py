import sqlite3
import json
from db.config import get_db, close_db

def get_waris(id):
  conn = get_db()
  cur = conn.cursor()
  sql = "SELECT * FROM waris WHERE id=? LIMIT 1"
  db_exec = cur.execute(sql, [id])
  cur.close()
  return db_exec.fetchone()

def getCurrentWaris(id=None, user_id=None):
  conn = get_db()
  cur = conn.cursor()
  if id != None:
    data = cur.execute("SELECT * FROM waris WHERE id=? ORDER BY created_at DESC LIMIT 1", [id]).fetchone()
    return data if data else None
  elif user_id != None:
    data = cur.execute("SELECT * FROM waris WHERE user_id=? ORDER BY created_at DESC LIMIT 1", [user_id]).fetchone()
    return data if data else None

  cur.close()
  return None

def create_waris(user_id, pewaris, jk, harta, step=1):
  conn = get_db()
  cur = conn.cursor()
  sql = "INSERT INTO waris(user_id, pewaris, jk_pewaris, harta, step) VALUES(?,?,?,?,?)"
  added_id = None
  try:
    db_exec = cur.execute(sql, [user_id, pewaris, jk, harta, step])
    conn.commit()
    added_id = cur.lastrowid
  except sqlite3.Error as err:
    print(err.args)
    return None
  cur.close()
  return added_id

def deleteCurrentWaris(id):
  conn = get_db()
  cur = conn.cursor()
  try:
    data = cur.execute("DELETE FROM waris WHERE id=?", [id])
    conn.commit()
    return True
  except sqlite3.Error as err:
    print(err.args)
    return False
  

  cur.close()
  return None

def current_step(id=None, user_id=None):
  conn = get_db()
  cur = conn.cursor()
  if id != None:
    step = cur.execute("SELECT step FROM waris WHERE id=? ORDER BY created_at DESC LIMIT 1", [id]).fetchone()
    return step['step'] if step else 0
  elif user_id != None:
    step = cur.execute("SELECT step FROM waris WHERE user_id=? ORDER BY created_at DESC LIMIT 1", [user_id]).fetchone()
    return step['step'] if step else 0
  return 0

def current_substep(id=None, user_id=None):
  conn = get_db()
  cur = conn.cursor()
  if id != None:
    step = cur.execute("SELECT sub_step FROM waris WHERE id=? ORDER BY created_at DESC LIMIT 1", [id]).fetchone()
    return step['sub_step'] if step else 0
  elif user_id != None:
    step = cur.execute("SELECT sub_step FROM waris WHERE user_id=? ORDER BY created_at DESC LIMIT 1", [user_id]).fetchone()
    return step['sub_step'] if step else 0
  return 0

def setStep(id, step):
  conn = get_db()
  cur = conn.cursor()
  sql = "UPDATE waris SET step=? WHERE id=?"
  try:
    db_exec = cur.execute(sql, [step, id])
    conn.commit()
  except sqlite3.Error as err:
    print(err.args)
    return False
  cur.close()
  return True

def setSubStep(id, substep):
  conn = get_db()
  cur = conn.cursor()
  sql = "UPDATE waris SET sub_step=? WHERE id=?"
  try:
    db_exec = cur.execute(sql, [substep, id])
    conn.commit()
  except sqlite3.Error as err:
    print(err.args)
    return False
  cur.close()
  return True

# id, data: json format str
def setData(id: int, data):
  conn = get_db()
  cur = conn.cursor()
  sql = "UPDATE waris SET data=? WHERE id=?"
  try:
    db_exec = cur.execute(sql, [data, id])
    conn.commit()
  except sqlite3.Error as err:
    print(err.args)
    return False
  cur.close()
  return True

# id, data: json format str
def getData(id: int):
  conn = get_db()
  cur = conn.cursor()
  sql = "SELECT data FROM waris WHERE id=?"
  data = None
  try:
    db_exec = cur.execute(sql, [id])
    data = json.loads(db_exec.fetchone()['data'])
  except sqlite3.Error as err:
    print(err.args)
    return None
  cur.close()
  return data