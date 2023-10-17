from db.config import get_db, close_db

def add_user(user='User'):
  conn = get_db()
  cur = conn.cursor()
  cur = cur.execute("INSERT INTO users (id, guest_id) VALUES(NULL, ?)", [user])
  new_user = cur.execute("SELECT * FROM users WHERE id=?", [cur.lastrowid]).fetchone()
  conn.commit()
  return new_user

def check_user(id):
  conn = get_db().cursor()
  user = conn.execute("SELECT * FROM users WHERE id=?", [id]).fetchone()
  conn.close()
  return user