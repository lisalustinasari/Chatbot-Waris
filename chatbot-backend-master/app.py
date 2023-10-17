from flask import Flask, request, session
from flask_socketio import SocketIO, join_room, leave_room
from db.config import close_db
from models import users, chat_room, messages, waris
from controllers import chatbot
from flask_cors import CORS
import json
from datetime import datetime, date, timedelta

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SECRET_KEY'] = 'eo31jdja9ffkm3klaj91ualgmjubn9A#_@+31'
app.config['DATABASE'] = 'database.db'

socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/", methods=["GET"])
def test_db():
  return "Welcome to API chatbot Waris"
  
@app.route("/guest/create", methods=["POST"])
def create_guest():
  # guest_id = id user
  guests = users.add_user()
  close_db()
  return {
    'guest_id': guests['id'],
    'guest_created': True
  }

@app.route("/guest/check", methods=["GET"])
def check_guest():
  # guest_id = id user
  guest_id = request.args.get('guest_id')
  guest_id = guest_id if guest_id else request.form['guest_id']
  if guest_id:
    guests = users.check_user(guest_id)
    close_db()
    if guests:
      return {
        'guest_id': guest_id,
        'guest_created': True
      }

  return {
    'guest_id': None,
    'guest_created': False
  }

@app.route("/chat-room", methods=["GET"])
def get_rooms():
  rooms = chat_room.get_rooms()
  close_db()

  return {
    "message": "get rooms success!!",
    "rooms": rooms
  }

@app.route("/chat-room/create", methods=["POST"])
def create_room():
  user_id = request.form['user_id']
  room = chat_room.create_room(user_id=user_id)
  close_db()
  if room:
    return {
      "message": "create room success!!",
      "room": room
    }
  else:
    return {
      "message": "create room failed!!"
    }, 400
  
@app.route("/chat-room/update/<id>", methods=["PUT"])
def update_room(id=None):
  chat_name = request.form['chat_name']
  user_id = request.form['user_id']
  room = chat_room.update_room(id, chat_name=chat_name, user_id=user_id)
  close_db()
  if room:
    return {
      "message": "update room success!!",
      "room": room
    }
  else:
    return {
      "message": "update room failed!!"
    }, 400

@app.route("/chat-room/room/<id>", methods=["GET"])
def get_room(id=None):
  room = chat_room.get_room(id)
  close_db()

  return {
    "message": "get rooms success!!",
    "room": room
  }

@app.route("/chat-room/room/user/<user_id>", methods=["GET"])
def get_room_user(user_id=None):
  room = chat_room.get_room_user(user_id)
  close_db()

  return {
    "message": "get rooms success!!",
    "room": room
  }

# message
@app.route("/messages/<room_id>", methods=["GET"])
def get_data_messages(room_id):
  msg = messages.get_messages(room_id)
  close_db()
  if msg != None:
    return {
      "message": "get messages success!!",
      "data_msgs": msg
    }
  else:
    return {
      "message": "get messages failed!!"
    }, 400

@app.route("/messages/create/<room_id>", methods=["POST"])
def create_messages(room_id):
  msg = request.form['message']
  # msg_from = request.form['message_from'] if request.form['message_from'] else 'u'
  message = messages.create_message(msg, 'u', room_id)
  if message != None:
    return {
      "message": "create messages success!!",
      "data_msg": message
    }
  else:
    return {
      "message": "create messages failed!!"
    }, 400

@app.route("/start-chat/<room_id>", methods=["GET"])
def start_message(room_id):
  # room = data['room_id']
  message = bot_reply(chatbot.welcome_chat(), room_id)
  return {
    "message": "Start chat",
    "data": message
  }

@socketio.on('connect', namespace='/chats')
def handle_connect():
  print('Connected')


@socketio.on('join', namespace='/chats')
def handle_join(data):
  user = data['user']
  room = data['room']
  session['user'] = user
  session['room'] = room
  join_room(room)
  print("{} join room.".format(user))
  socketio.send("{} join room.".format(user), namespace='/chats', to=room)
  

@socketio.on('leave', namespace='/chats')
def on_leave(data):
  user = data['user']
  room = data['room']
  session.pop('user')
  session.pop('room')
  leave_room(room)
  print("{} join room.".format(user))
  socketio.send("{} join room.".format(user), to=room, namespace='/chats')
  socketio.emit('start_message', {'room_id': room}, namespace='/chats', to=room)

@socketio.on('send_message', namespace='/chats')
def send_message(data):
  room = data['chat_room_id']
  message = data['message_text']
  step = waris.current_step(id=None, user_id=session['user'])
  substep= waris.current_substep(user_id=session['user'])
  if(session.get('start_hitung',False)):
    step = 0
    substep = 0
  reply_message = chatbot.bot_listener(message, room, step, substep)
  socketio.emit('reply_message', reply_message, namespace='/chats', to=room)
  # if step == 0 and isNewStep(step):
  #   newStep = waris.current_step(user_id=session['user'])
  #   reply_message = chatbot.bot_listener(message, room, newStep)
  #   socketio.emit('reply_message', reply_message, namespace='/chats', to=room)

def bot_reply(message, room_id):
  data_room = chat_room.get_room(room_id)
  reply = messages.create_message(text=message, message_from='b', room_id=room_id)
  return reply

def isNewStep(current_step):
  newStep = waris.current_step(user_id=session['user'])
  if current_step != newStep:
    return True
  else:
    return False

if __name__ == '__main__':
  socketio.run(app)


def serve():
  socketio.run(app)