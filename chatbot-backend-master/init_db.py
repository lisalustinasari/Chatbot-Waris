import sqlite3

connection = sqlite3.connect('database.db')


with open('db/schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO users (guest_id) VALUES (?);", ['BOT'])

connection.commit()
connection.close()
