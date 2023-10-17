from re import sub
from this import d
from flask import session
from models import waris, chat_room, messages as msg_models
from flask_socketio import send, emit
import json

def bot_save_message(message, room_id):
  data_room = chat_room.get_room(room_id)
  reply = msg_models.create_message(text=message, message_from='b', room_id=room_id)
  return reply

def bot_save_messages(messages, room_id):
  # data = []
  # for message in messages:
  #   if message:
  #     data.append(bot_save_message(message, room_id))
  # print(messages)
  data = msg_models.create_messages(messages, 'b', room_id)
  data.sort(key=lambda x: x.get('id'))
  return data

def welcome_chat():
  message = "Assalamu'alaikum Wr. Wb<br/>Selamat datang di sistem chatbot waris!! Silahkan ketik /hitung untuk memulai perhitungan waris!!"
  return message

def bot_start_listener(msg):
  if msg == '/hitung':
    session['start_hitung'] = True
    session['waris'] = {
      'NAME': None,
      'JK': None,
      'HARTA': 0
    }
    # curWaris = waris.getCurrentWaris(user_id=session['user'])
    # if (curWaris is not None):
    #   waris.deleteCurrentWaris(curWaris['id'])

    return [getMsgInit('NAME')]
  else:
    return ["Bot tidak mengerti, masukkan jawaban yang valid!!"]

def bot_listener(msg, room_id, step=0, substep=0):
  msgs = bot_save_messages(bot_response(msg, step, substep), room_id)
  return msg_models.formatted_messages(msgs)

def reset():
  session.pop('waris')
  session.pop('start_hitung')
  session.pop('start_step')
  # curWaris = waris.getCurrentWaris(user_id=session['user'])
  # if (curWaris):
  #   waris.deleteCurrentWaris(curWaris['id'])
  return [welcome_chat()]

def getMsgInit(step):
  if step == 'NAME':
    session['start_step'] = 'NAME'
    return "Masukkan Nama Pewaris"
  elif step == 'JK':
    session['start_step'] = 'JK'
    return "Jenis kelamin pewaris? (L/P)"
  elif step == 'HARTA':
    session['start_step'] = 'HARTA'
    return "masukkan jumlah harta Al-Irts?<br>(harta yang sudah siap di bagi, telah di kurangi biaya pemakaman, hutang dan wasiat)"

# get chat next step, add step, and reset substep
def nextStep(current_step: int, id_waris):
  # id_waris = session['id_waris']
  current_step+=1
  if waris.setStep(id_waris, current_step):
    waris.setSubStep(id_waris, 0)
    return bot_response(None, step=current_step)
  else:
    return ["Terjadi kesalahan, tidak dapat lanjut ke tahap selanjutnya!!"]

# get chat next step, add step, and reset substep
def nextSubStep(current_substep: int, current_step: int, id_waris):
  # id_waris = session['id_waris']
  current_substep+=1
  if waris.setSubStep(id_waris, current_substep):
    return bot_response(None, step=current_step, substep=current_substep)
  else:
    return ["Terjadi kesalahan, tidak dapat lanjut ke tahap selanjutnya!!"]

def positive_answer(msg: str):
  valid_answer = ['Y', 'Ya', 'Punya']
  if(msg.lower() in [item.lower() for item in valid_answer]):
    return True
  else:
    return False

def negative_answer(msg: str):
  valid_answer = ['N', 'Tidak', 'Tidak Punya', 'Gak']
  if(msg.lower() in [item.lower() for item in valid_answer]):
    return True
  else:
    return False

def isInteger(msg):
  try:
    msg = int(msg)
    return True
  except:
    return False

def invalidResponse():
  return "Bot tidak mengerti, masukkan jawaban yang valid!!"

def bot_response(msg: str, step= 0, substep=0):
  response = []
  if (msg == '/hitung'):
    step = 0
    substep = 0
    return bot_start_listener(msg)
  if (step == 0):
    if(session.get('start_hitung', False)):
      if session['start_step'] == 'NAME':
        session['waris']['NAME'] = msg
        response.append(getMsgInit('JK'))
      elif session['start_step'] == 'JK':
        valid_answer_L = ['L', 'Laki-laki',  'pria']
        valid_answer_P = ['P', 'Perempuan', 'wanita']
        if msg.lower() in [x.lower() for x in valid_answer_L]:
          session['waris']['JK'] = 'L'
          response.append(getMsgInit('HARTA'))
        elif msg.lower() in [x.lower() for x in valid_answer_P]:
          session['waris']['JK'] = 'P'
          response.append(getMsgInit('HARTA'))
        else:
          response.append(invalidResponse())
          response.append(getMsgInit('JK'))
      elif session['start_step'] == 'HARTA':
        try:
          harta = float(msg)
          session['waris']['HARTA'] = harta

          data_waris = session['waris']
          waris_id = waris.create_waris(session['user'], data_waris['NAME'], data_waris['JK'], data_waris['HARTA'])
          current_waris = waris.getCurrentWaris(waris_id)
          session.pop('waris')
          session.pop('start_hitung')
          session.pop('start_step')
          session['id_waris'] = waris_id if waris_id else None
          next_step = nextStep(step, waris_id)
          if current_waris:
            text = "Start Hitung Waris<br>Nama: {}<br>Jenis Kelamin: {}<br>Harta: {}".format(current_waris['pewaris'], current_waris['jk_pewaris'], current_waris['harta'])
            response.append(text)
            response = response + next_step
          else:
            text = "Start Hitung Waris"
            response.append(text)
            response = response + next_step
          print(response)
        except ValueError:
          response.append("Bot tidak mengerti, masukkan jawaban yang valid!!")
          response.append(getMsgInit('HARTA'))
      return response
    # return bot_start_listener(msg)
  elif (step == 1):
    suami = False
    istri = 0
    anak_pr = 0
    anak_lk = 0
    ayah = False
    ibu = False
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    if substep == 0:
      res = nextSubStep(substep, step, current_waris['id'])
      response = response + res
      return response
    elif substep == 1:
      if (current_waris['jk_pewaris'] == 'P'):
        if msg is None:
          response.append("Apakah memiliki suami? (Y/N):")
          return response
        elif positive_answer(msg):
          suami = True
          data = {
            'suami': suami,
            'istri': istri
          }
          waris.setData(current_waris['id'], json.dumps(data))
          chat = nextSubStep(substep, step, current_waris['id'])
          response = response + chat
        elif negative_answer(msg):
          suami = False
          data = {
            'suami': suami,
            'istri': istri
          }
          waris.setData(current_waris['id'], json.dumps(data))
          chat = nextSubStep(substep, step, current_waris['id'])
          response = response + chat
        else:
          response.append(invalidResponse())
          response = response + bot_response(None, step, substep)
      elif current_waris['jk_pewaris'] == 'L':
        if msg is None:
          response.append("Masukan Jumlah Istri : (angka)")
        elif isInteger(msg):
          data = {
            'suami': suami,
          }
          data['istri'] = int(msg)
          waris.setData(current_waris['id'], json.dumps(data))
          response.extend(nextSubStep(substep, step, current_waris['id']))
        else:
          res = [invalidResponse()].extend(bot_response(None, step, substep))
          response = response + res
      else:
        return ["Maaf, anda diwajibkan mengisi jenis kelamin Muwwarits!"].append(welcome_chat())
			# exit()
    elif substep == 2:
      if msg is None:
        response.append("Masukan Jumlah anak perempuan kandung:<br>(angka)")
      elif isInteger(msg):
        data = json.loads(current_waris['data'])
        anak_pr = int(msg)
        data['anak_pr'] = anak_pr
        waris.setData(current_waris['id'], json.dumps(data))
        response = response + nextSubStep(substep, step, current_waris['id'])
      else:
        response = [invalidResponse()] + bot_response(None, step, substep)

      return response
    elif substep == 3:
      if msg is None:
        response = ["Masukan Jumlah anak laki-laki kandung<br>(angka)"]
      elif isInteger(msg):
        anak_lk = int(msg)
        data = json.loads(current_waris['data'])
        data['anak_lk'] = anak_lk
        waris.setData(current_waris['id'], json.dumps(data))
        response.extend(nextSubStep(substep, step, current_waris['id']))
      else:
        response.extend([invalidResponse()] + bot_response(None, step, substep))
      
      return response
    elif substep == 4:
      if msg is None:
        # response.append("apakah memiliki ayah kandung? (Y/N)")
        ayah = False
        data = json.loads(current_waris['data'])
        data['ayah'] = ayah
        waris.setData(current_waris['id'], json.dumps(data))
        response = response + nextSubStep(substep, step, current_waris['id'])
      # elif positive_answer(msg):
      #   ayah = True
      #   data = json.loads(current_waris['data'])
      #   data['ayah'] = ayah
      #   waris.setData(current_waris['id'], json.dumps(data))
      #   response = response + nextSubStep(substep, step, current_waris['id'])
      # elif negative_answer(msg):
      #   ayah = False
      #   data = json.loads(current_waris['data'])
      #   data['ayah'] = ayah
      #   waris.setData(current_waris['id'], json.dumps(data))
      #   response = response + nextSubStep(substep, step, current_waris['id'])
      else:
        response = response + [invalidResponse()] + bot_response(None, step, substep)

      return response
    elif substep == 5:
      if msg is None:
        # return ["apakah memiliki ibu kandung? (Y/N)"]
        ibu = False
        data = json.loads(current_waris['data'])
        data['ibu'] = ibu
        waris.setData(current_waris['id'], json.dumps(data))
        response += nextStep(step, current_waris['id'])
      # elif positive_answer(msg):
      #   ibu = True
      #   data = json.loads(current_waris['data'])
      #   data['ibu'] = ibu
      #   waris.setData(current_waris['id'], json.dumps(data))
      #   response += nextStep(step, current_waris['id'])
      # elif negative_answer(msg):
      #   ibu = False
      #   data = json.loads(current_waris['data'])
      #   data['ibu'] = ibu
      #   waris.setData(current_waris['id'], json.dumps(data))
      #   response += nextStep(step, current_waris['id'])
      else:
        response += [invalidResponse()] + bot_response(None, step, substep)
    # batas
    else:
      response.append(invalidResponse())
    
    return response
  elif step == 2:
    kakek = False
    nenek = False
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])
    if (data['ayah'] == False and data['ibu'] == False):
      if substep == 0:
        nextMsg = nextSubStep(substep, step, current_waris['id'])
        response += ["Tidak ada ahli waris ayah dan ibu, maka kakek dan nenek memiliki kesempatan untuk mendapatkan harta warisan jika mereka ada"] + nextMsg
      elif substep == 1:
        if msg is None:
          response += ["apakah memiliki kakek? (Y/N) "]
        elif positive_answer(msg):
          kakek=True
          data['kakek'] = kakek
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextSubStep(substep, step, current_waris['id'])
        elif negative_answer(msg):
          kakek=False
          data['kakek'] = kakek
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextSubStep(substep, step, current_waris['id'])
        else:
          response += [invalidResponse()] + bot_response(None, step, substep)
      elif substep == 2:
        if msg is None:
          response += ["masukkan jumlah nenek ? yang masih hidup baik dari ayah atau ibu <br>(angka)<br>Isi 0 jika tidak ada"]
        elif isInteger(msg):
          nenek=int(msg)
          data['nenek'] = nenek
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
        else:
          response += [invalidResponse()] + bot_response(None, step, substep)
    elif (data['ayah'] == False and data['ibu'] == True):
      if substep == 0:
        nextMsg = nextSubStep(substep, step, current_waris['id'])
        response += ["Tidak ada ahli waris ayah, maka kakek memiliki kesempatan untuk mendapatkan harta warisan jika mereka ada"] + nextMsg
      elif substep == 1:
        if msg is None:
          response += ["Apakah memiliki Kakek? (Y/N)"]
        elif positive_answer(msg):
          kakek=True
          data['kakek'] = kakek
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
        elif negative_answer(msg):
          kakek=False
          data['kakek'] = kakek
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
        else:
          response += [invalidResponse()] + bot_response(None, step, substep)
    elif (data['ayah'] == True and data['ibu'] == False):
      if substep == 0:
        nextMsg = nextSubStep(substep, step, current_waris['id'])
        response += ["Tidak ada ahli waris ibu, maka nenek memiliki kesempatan untuk mendapatkan harta warisan jika mereka ada <br><br>"] + nextMsg
      elif substep == 1:
        if msg is None:
          response += ["masukkan jumlah nenek ? yang masih hidup baik dari ayah atau ibu <br>(angka)<br>Isi 0 jika tidak ada"]
        elif isInteger(msg):
          nenek=int(msg)
          data['kakek'] = kakek
          data['nenek'] = nenek
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
        else:
          response += [invalidResponse()] + bot_response(None, step, substep)
    else:
      data['kakek'] = kakek
      data['nenek'] = nenek
      waris.setData(current_waris['id'], json.dumps(data))
      response += nextStep(step, current_waris['id'])
    #batas
    return response
  elif step == 3:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])
    if (data['anak_lk'] == 0 and data['anak_pr'] > 0):
      if (data['anak_pr'] == 1):
        if substep == 0:
          nextMsg = nextSubStep(substep, step, current_waris['id'])
          response += ["Tidak ada ahli waris anak kandung laki-laki, maka cucu laki-laki dan cucu perempuan dari anak kandung laki-laki memiliki kesempatan untuk mendapatkan harta warisan jika mereka ada"] + nextMsg
        elif substep == 1:
          if msg == None:
            response += ["Masukan Jumlah cucu perempuan dari turunan anak laki-laki : (angka)"]
          elif isInteger(msg):
            cucu_pr = int(msg)
            data['cucu_pr'] = cucu_pr
            waris.setData(current_waris['id'], json.dumps(data))
            response += nextSubStep(substep, step, current_waris['id'])
          else:
            response += [invalidResponse()] + bot_response(None, step, substep)
        elif substep == 2:
          if msg is None:
            response += ["Masukan Jumlah cucu laki-laki dari turunan anak laki-laki : (angka)"]
          elif isInteger(msg):
            cucu_lk = int(msg)
            data['cucu_lk'] = cucu_lk
            waris.setData(current_waris['id'], json.dumps(data))
            response += nextSubStep(substep, step, current_waris['id'])
          else:
            response += [invalidResponse()] + bot_response(None, step, substep)
        else:
          response += nextStep(step, current_waris['id'])
      elif (data['anak_pr'] > 1):
        if substep == 0:
          nextMsg = nextSubStep(substep, step, current_waris['id'])
          response += ["Cucu perempuan dari anak laki-laki dilewati karena termahjub oleh 2 anak perempuan atau lebih"] + nextMsg
        elif substep == 1:
          if msg is None:
            response += ["Masukan Jumlah cucu laki-laki dari turunan anak laki-laki : (angka)"]
          elif isInteger(msg):
            cucu_lk = int(msg)
            data['cucu_lk'] = cucu_lk
            waris.setData(current_waris['id'], json.dumps(data))
            response += nextSubStep(substep, step, current_waris['id'])
          else:
            response += [invalidResponse()] + bot_response(None, step, substep)
        else:
          response += nextStep(step, current_waris['id'])
      else:
        response += nextStep(step, current_waris['id'])
    elif (data['anak_lk'] == 0 and data['anak_pr'] == 0):
      if substep == 0:
        nextMsg = nextSubStep(substep, step, current_waris['id'])
        response += ["Tidak ada ahli waris anak kandung laki-laki, maka cucu laki-laki dan cucu perempuan dari anak kandung laki-laki memiliki kesempatan untuk mendapatkan harta warisan jika mereka ada"] + nextMsg
      elif substep == 1:
        if msg == None:
          response += ["Masukan Jumlah cucu perempuan dari turunan anak laki-laki : (angka)"]
        elif isInteger(msg):
          cucu_pr = int(msg)
          data['cucu_pr'] = cucu_pr
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextSubStep(substep, step, current_waris['id'])
        else:
          response += [invalidResponse()] + bot_response(None, step, substep)
      elif substep == 2:
        if msg == None:
          response += ["Masukan Jumlah cucu laki-laki dari turunan anak laki-laki : (angka)"]
        elif isInteger(msg):
          cucu_lk = int(msg)
          data['cucu_lk'] = cucu_lk
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
        else:
          response += [invalidResponse()] + bot_response(None, step, substep)
      else:
        response += nextStep(step, current_waris['id'])
    else:
      data['cucu_lk'] = 0
      data['cucu_pr'] = 0
      waris.setData(current_waris['id'], json.dumps(data))
      response += nextStep(step, current_waris['id'])

    return response
  elif step == 4:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])
    saudara_knd = data.get('saudara_knd', 0)
    saudari_knd = data.get('saudari_knd', 0)
    data['cucu_pr'] = data.get('cucu_pr', 0)
    if (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0):
      if substep == 0:
        response += ["Tidak ada ahli waris anak kandung ayah, kakek , anak kandung laki-laki, dan<br>cucu laki-laki maka saudara kandung dan saudari kandung memiliki <br>kesempatan untuk mendapatkan harta warisan jika mereka ada"]
        response += nextSubStep(substep, step, current_waris['id'])
      elif substep == 1:
        if msg is None:
          response += ["Masukan Jumlah saudari kandung : (angka)"]
        elif isInteger(msg):
          saudari_knd = int(msg)
          data['saudari_knd'] = saudari_knd
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextSubStep(substep, step, current_waris['id'])
        else:
          response += [invalidResponse()] + bot_response(None, step, substep)
      elif substep == 2:
        if msg is None:
          response += ["Masukan Jumlah saudara kandung : (angka)"]
        elif isInteger(msg):
          saudara_knd = int(msg)
          data['saudara_knd'] = saudara_knd
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextSubStep(substep, step, current_waris['id'])
        else:
          response += [invalidResponse()] + bot_response(None, step, substep)
      else:
        data['saudari_knd'] = saudari_knd
        data['saudara_knd'] = saudara_knd
        waris.setData(current_waris['id'], json.dumps(data))
        response += nextStep(step, current_waris['id'])
    else:
      data['saudari_knd'] = saudari_knd
      data['saudara_knd'] = saudara_knd
      waris.setData(current_waris['id'], json.dumps(data))
      response += nextStep(step, current_waris['id'])
    return response
  elif step == 5:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])
    data['cucu_pr'] = data.get('cucu_pr', 0)
    data['cucu_lk'] = data.get('cucu_lk', 0)
    data['anak_lk'] = data.get('anak_lk', 0)
    data['anak_pr'] = data.get('anak_pr', 0)
    data['saudari_knd'] = data.get('saudari_knd', 0)
    data['saudara_knd'] = data.get('saudara_knd', 0)
    saudara_seayah = data.get('saudara_seayah', 0)
    saudari_seayah = data.get('saudari_seayah', 0)
    saudara_seibu = data.get('saudara_seibu', 0)
    saudari_seibu = data.get('saudari_seibu', 0)

    if substep == 0:
      substep = 1
    if (data['kakek'] == False and data['ayah'] == False and data['anak_lk'] == 0 and data['cucu_lk'] == 0):
      if (data['cucu_pr'] == 0 and data['anak_pr'] == 0):
        if (data['saudari_knd'] == 0 and data['saudara_knd'] == 0):
          if substep == 1:
            if msg is None:
              response += ["Masukan Jumlah saudari seayah : (angka)"]
            elif isInteger(msg):
              saudari_seayah = int(msg)
              data['saudari_seayah'] = saudari_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 2:
            if msg is None:
              response += ["Masukan Jumlah saudara seayah : (angka)"]
            elif isInteger(msg):
              saudara_seayah = int(msg)
              data['saudara_seayah'] = saudara_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 3:
            if msg is None:
              response += ["Masukan Jumlah saudari seibu : (angka)"]
            elif isInteger(msg):
              saudari_seibu = int(msg)
              data['saudari_seibu'] = saudari_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 4:
            if msg is None:
              response += ["Masukan Jumlah saudara seibu : (angka)"]
            elif isInteger(msg):
              saudara_seibu = int(msg)
              data['saudara_seibu'] = saudara_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          else:
            response += nextStep(step, current_waris['id'])
        elif (data['saudari_knd'] == 1 and data['saudara_knd'] == 0):
          if substep == 1:
            if msg is None:
              response += ["Masukan Jumlah saudari seayah : (angka)"]
            elif isInteger(msg):
              saudari_seayah = int(msg)
              data['saudari_seayah'] = saudari_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 2:
            if msg is None:
              response += ["Masukan Jumlah saudara seayah : (angka)"]
            elif isInteger(msg):
              saudara_seayah = int(msg)
              data['saudara_seayah'] = saudara_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 3:
            if msg is None:
              response += ["Masukan Jumlah saudari seibu : (angka)"]
            elif isInteger(msg):
              saudari_seibu = int(msg)
              data['saudari_seibu'] = saudari_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 4:
            if msg is None:
              response += ["Masukan Jumlah saudara seibu : (angka)"]
            elif isInteger(msg):
              saudara_seibu = int(msg)
              data['saudara_seibu'] = saudara_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          else:
            response += nextStep(step, current_waris['id'])
        elif (data['saudari_knd'] == 0 and data['saudara_knd'] > 0):
          if substep == 1:
            if msg is None:
              response += ["Masukan Jumlah saudari seibu : (angka)"]
            elif isInteger(msg):
              saudari_seibu = int(msg)
              data['saudari_seibu'] = saudari_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 2:
            if msg is None:
              response += ["Masukan Jumlah saudara seibu : (angka)"]
            elif isInteger(msg):
              saudara_seibu = int(msg)
              data['saudara_seibu'] = saudara_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          else:
            response += nextStep(step, current_waris['id'])
        elif (data['saudari_knd'] > 0 and data['saudara_knd'] > 0):
          if substep == 1:
            if msg is None:
              response += ["Masukan Jumlah saudari seibu : (angka)"]
            elif isInteger(msg):
              saudari_seibu = int(msg)
              data['saudari_seibu'] = saudari_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 2:
            if msg is None:
              response += ["Masukan Jumlah saudara seibu : (angka)"]
            elif isInteger(msg):
              saudara_seibu = int(msg)
              data['saudara_seibu'] = saudara_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          else:
            response += nextStep(step, current_waris['id'])
        elif (data['saudari_knd'] > 1 and data['saudara_knd'] == 0):
          if substep == 1:
            nextMsg = nextSubStep(substep, step, current_waris['id'])
            response += ["Saudari Seayah termahjub karena adanya saudari kandung lebih dari satu orang"] + nextMsg
          elif substep == 2:
            if msg is None:
              response += ["Masukan Jumlah saudara seayah : (angka)"]
            elif isInteger(msg):
              saudara_seayah = int(msg)
              data['saudara_seayah'] = saudara_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 3:
            if msg is None:
              response += ["Masukan Jumlah saudari seibu : (angka)"]
            elif isInteger(msg):
              saudari_seibu = int(msg)
              data['saudari_seibu'] = saudari_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 4:
            if msg is None:
              response += ["Masukan Jumlah saudara seibu : (angka)"]
            elif isInteger(msg):
              saudara_seibu = int(msg)
              data['saudara_seibu'] = saudara_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          else:
            response += nextStep(step, current_waris['id'])
        else:
          data['saudara_seayah'] = saudara_seayah
          data['saudari_seayah'] = saudari_seayah
          data['saudara_seibu'] = saudara_seibu
          data['saudari_seibu'] = saudari_seibu
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
      elif (data['cucu_pr'] > 0 and data['anak_pr'] > 0):
        if (data['saudari_knd'] == 0 and data['saudara_knd'] == 0):
          if substep == 1:
            if msg is None:
              response += ["Masukan Jumlah saudari seayah : (angka)"]
            elif isInteger(msg):
              saudari_seayah = int(msg)
              data['saudari_seayah'] = saudari_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 2:
            if msg is None:
              response += ["Masukan Jumlah saudara seayah : (angka)"]
            elif isInteger(msg):
              saudara_seayah = int(msg)
              data['saudara_seayah'] = saudara_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          else:
            response += nextStep(step, current_waris['id'])
        else:
          data['saudara_seayah'] = saudara_seayah
          data['saudari_seayah'] = saudari_seayah
          data['saudara_seibu'] = saudara_seibu
          data['saudari_seibu'] = saudari_seibu
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
      elif (data['cucu_pr'] > 0 and data['anak_pr'] == 0):
        if (data['saudari_knd'] == 0 and data['saudara_knd'] == 0):
          if substep == 1:
            if msg is None:
              response += ["Masukan Jumlah saudari seayah : (angka)"]
            elif isInteger(msg):
              saudari_seayah = int(msg)
              data['saudari_seayah'] = saudari_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 2:
            if msg is None:
              response += ["Masukan Jumlah saudara seayah : (angka)"]
            elif isInteger(msg):
              saudara_seayah = int(msg)
              data['saudara_seayah'] = saudara_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              data['saudara_seayah'] = saudara_seayah
              data['saudari_seayah'] = saudari_seayah
              data['saudara_seibu'] = saudara_seibu
              data['saudari_seibu'] = saudari_seibu
              waris.setData(current_waris['id'], json.dumps(data))
              response += [invalidResponse()] + bot_response(None, step, substep)
          else:
            response += nextStep(step, current_waris['id'])
        else:
          data['saudara_seayah'] = saudara_seayah
          data['saudari_seayah'] = saudari_seayah
          data['saudara_seibu'] = saudara_seibu
          data['saudari_seibu'] = saudari_seibu
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
      elif (data['cucu_pr'] == 0 and data['anak_pr'] > 0):
        if (data['saudari_knd'] == 0 and data['saudara_knd'] == 0):
          if substep == 1:
            if msg is None:
              response += ["Masukan Jumlah saudari seayah : (angka)"]
            elif isInteger(msg):
              saudari_seayah = int(msg)
              data['saudari_seayah'] = saudari_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          elif substep == 2:
            if msg is None:
              response += ["Masukan Jumlah saudara seayah : (angka)"]
            elif isInteger(msg):
              saudara_seayah = int(msg)
              data['saudara_seayah'] = saudara_seayah
              waris.setData(current_waris['id'], json.dumps(data))
              response += nextSubStep(substep, step, current_waris['id'])
            else:
              response += [invalidResponse()] + bot_response(None, step, substep)
          else:
            data['saudara_seayah'] = saudara_seayah
            data['saudari_seayah'] = saudari_seayah
            data['saudara_seibu'] = saudara_seibu
            data['saudari_seibu'] = saudari_seibu
            waris.setData(current_waris['id'], json.dumps(data))
            response += nextStep(step, current_waris['id'])
        else:
          data['saudara_seayah'] = saudara_seayah
          data['saudari_seayah'] = saudari_seayah
          data['saudara_seibu'] = saudara_seibu
          data['saudari_seibu'] = saudari_seibu
          waris.setData(current_waris['id'], json.dumps(data))
          response += nextStep(step, current_waris['id'])
      else:
        data['saudara_seayah'] = saudara_seayah
        data['saudari_seayah'] = saudari_seayah
        data['saudara_seibu'] = saudara_seibu
        data['saudari_seibu'] = saudari_seibu
        waris.setData(current_waris['id'], json.dumps(data))
        response += nextStep(step, current_waris['id'])
    else:
      data['saudara_seayah'] = saudara_seayah
      data['saudari_seayah'] = saudari_seayah
      data['saudara_seibu'] = saudara_seibu
      data['saudari_seibu'] = saudari_seibu
      waris.setData(current_waris['id'], json.dumps(data))
      response += nextStep(step, current_waris['id'])
    
    return response
  elif step == 6:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])
    bagiansuami = 0
    bagianistri = 0
    # pewaris perempuan
    if (current_waris['jk_pewaris'] == "P"):
      if (data['suami'] == True):
        if (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
          bagiansuami = 0.5
          response += ["Bagian suami (1/2)"]
        elif (data['anak_pr'] > 0 or data['anak_lk'] > 0 or data['cucu_pr'] > 0 or data['cucu_lk'] > 0):
          bagiansuami = 0.25
          
          response += ["Bagian suami (1/4)"]
        else:
          bagiansuami = 0
          # response += nextStep(step, current_waris['id'])
      else:
        bagiansuami = 0
        # response += nextStep(step, current_waris['id'])
    # pewaris laki-laki
    elif (current_waris['jk_pewaris'] == "L"):
      if (data['istri'] == 0):
        bagianistri = 0
      else:
        if (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
          bagianistri = 0.25
          response += ["Bagian Istri (1/4)"]
        elif (data['anak_pr'] > 0 or data['anak_lk'] > 0 or data['cucu_pr'] > 0 or data['cucu_lk'] > 0):
          bagianistri = 0.125
          response += ["Bagian Istri (1/8)"]
        # else:
        #   response += nextStep(step, current_waris['id'])
    # else:
    #   response += nextStep(step, current_waris['id'])

    data['bagiansuami'] = bagiansuami
    data['bagianistri'] = bagianistri
    waris.setData(current_waris['id'], json.dumps(data))
    response += nextStep(step, current_waris['id'])
    return response
  elif step == 7:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])

    bagiananak_pr = data.get("bagiananak_pr", 0)
    bagiananak_lk = data.get("bagiananak_lk", 0)
    ############################# ANAK PEREMPUAN $ ANAK LAKI-LAKI ######################################################
    if (data['anak_pr'] == 1 and data['anak_lk'] == 0):
      bagiananak_pr = 0.5
      response += ["Bagian anak perempuan (1/2)"]
    elif (data['anak_pr'] > 1 and data['anak_lk'] == 0):
      bagiananak_pr = 0.6
      response += ["Bagian anak perempuan (2/3)"]
    elif (data['anak_pr'] > 0 and data['anak_lk'] > 0):
      bagiananak_pr = "sisa"
      bagiananak_lk = "sisa"
      response += ["Bagian anak perempuan (sisa)", "Bagian anak laki-laki (sisa)"]
    elif (data['anak_lk'] >= 1):
      bagiananak_lk = "sisa"
      response += ["Bagian anak laki-laki (sisa)"]
    
    data['bagiananak_pr'] = bagiananak_pr
    data['bagiananak_lk'] = bagiananak_lk
    waris.setData(current_waris['id'], json.dumps(data))
    response += nextStep(step, current_waris['id'])

    return response
  elif step == 8:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])
    bagianayah = 0
    bagiansisa = ""
    bagiankakek = 0
    bagiansisakakek = ""
    ############################ AYAH #################################################################
    if (data['ayah'] == True):
      if (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
        bagianayah = "sisa"
        bagiansisa = ""
        response += ["Bagian ayah (sisa)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
        bagianayah = 0.16
        bagiansisa = "+sisa"
        response += [f"Bagian ayah (1/6) {bagiansisa}"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
        bagianayah = 0.16
        bagiansisa = "+sisa"
        response += [f"Bagian ayah (1/6) {bagiansisa}"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
        bagianayah = 0.16
        bagiansisa = "+sisa"
        response += [f"Bagian ayah (1/6) {bagiansisa}"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] > 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] > 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0):
        bagianayah = 0.16
        bagiansisa = ""
        response += ["Bagian ayah (1/6)"]
    else:
      bagianayah = 0
    ############################### KAKEK #################################################################
    if (bagianayah == 0):
      if (data['kakek'] == True):
        if (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
          bagiankakek = "sisa"
          bagiansisakakek = ""
          response += [f"Bagian kakek (sisa)"]
        elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek {bagiankakek}"]
        elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
          bagiankakek = 0.16
          bagiansisakakek = "+sisa"
          response += [f"Bagian kakek (1/6) {bagiansisakakek}"]
        elif (data['anak_pr'] > 0 and data['anak_lk'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
          bagiankakek = 0.16
          bagiansisakakek = "+sisa"
          response += [f"Bagian kakek (1/6) {bagiansisakakek}"]
        elif (data['anak_pr'] > 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
          bagiankakek = 0.16
          bagiansisakakek = "+sisa"
          response += [f"Bagian kakek (1/6) {bagiansisakakek}"]
        elif (data['anak_pr'] > 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] > 0 and data['anak_lk'] > 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] > 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] > 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] > 0 and data['anak_lk'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] == 0 and data['anak_lk'] > 0 and data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
        elif (data['anak_pr'] > 0 and data['anak_lk'] > 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0):
          bagiankakek = 0.16
          bagiansisakakek = ""
          response += [f"Bagian kakek (1/6)"]
      else:
        bagiankakek = 0
    else:
      bagiankakek = 0
    data['bagianayah'] = bagianayah
    data['bagiansisa'] = bagiansisa
    data['bagiankakek'] = bagiankakek
    data['bagiansisakakek'] = bagiansisakakek
    waris.setData(current_waris['id'], json.dumps(data))
    response += nextStep(step, current_waris['id'])

    return response
  elif step == 9:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])

    data['nenek'] = data.get('nenek', 0)
    bagianibu = data.get('bagianibu', 0)
    bagiansisaibu = data.get('bagiansisaibu', "")
    bagiannenek = data.get('bagiannenek', 0)
    ######################### IBU ##################################################################################################
    if (data['ibu'] == True):
      if (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudari_knd'] == 1 and data['saudara_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
        bagianibu = 0.33
        bagiansisaibu = ""
        response += [f"Bagian ibu (1/3)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudari_knd'] == 0 and data['saudara_knd'] == 1 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
        bagianibu = 0.33
        bagiansisaibu = ""
        response += [f"Bagian ibu (1/3)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudari_knd'] == 0 and data['saudara_knd'] == 0 and data['saudari_seayah'] == 1 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
        bagianibu = 0.33
        bagiansisaibu = ""
        response += [f"Bagian ibu (1/3)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudari_knd'] == 0 and data['saudara_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 1 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
        bagianibu = 0.33
        bagiansisaibu = ""
        response += [f"Bagian ibu (1/3)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudari_knd'] == 0 and data['saudara_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 1 and data['saudara_seibu'] == 0):
        bagianibu = 0.33
        bagiansisaibu = ""
        response += [f"Bagian ibu (1/3)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudari_knd'] == 0 and data['saudara_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 1):
        bagianibu = 0.33
        bagiansisaibu = ""
        response += [f"Bagian ibu (1/3)"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudari_knd'] == 0 and data['saudara_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
        bagianibu = 0.33
        bagiansisaibu = "*sisa"
        response += [f"Bagian ibu (1/3) {bagiansisaibu}"]
      elif (data['anak_pr'] > 0 or data['anak_lk'] > 0 or data['cucu_pr'] > 0 or data['cucu_lk'] > 0 or data['saudari_knd'] > 0 or data['saudara_knd'] > 0 or data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0 or data['saudari_seibu'] > 0 or data['saudara_seibu'] > 0):
        bagianibu = 0.16
        bagiansisaibu = ""
        response += [f"Bagian ibu (1/6)"]
      if (data['nenek'] < 3 and data['nenek'] != 0):
        if (data['ibu'] == True):
          bagiannenek = "termahjub"
          response += [f"bagian nenek  {bagiannenek}"]
    else:
      bagianibu = 0
      bagiannenek = 0
    ############################### NENEK #####################################################################
      if (bagianibu == 0):
        if (data['nenek'] > 0):
          bagiannenek = 0.16
          response += [f"bagian nenek (1/6)"]
    
    data['bagianibu'] = bagianibu
    data['bagiansisaibu'] = bagiansisaibu
    data['bagiannenek'] = bagiannenek
    waris.setData(current_waris['id'], json.dumps(data))
    response += nextStep(step, current_waris['id'])

    return response
  elif step == 10:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])
    bagiancuculk = data.get("bagiancuculk", 0)
    bagiancucupr = data.get("bagiancucupr", 0)
    ################################ CUCU PEREMPUAN & CUCU LAKI-LAKI ################################################################
    if (data['cucu_pr'] >= 1 and data['cucu_lk'] >= 1):
      if (data['anak_pr'] == 0 and data['anak_lk'] >= 1):
        bagiancucupr = "termahjub"
        response += [f"bagian cucu perempuan {bagiancucupr}"]
        bagiancuculk = "termahjub"
        response += [f"bagian cucu laki-laki {bagiancuculk}"]
      elif (data['anak_pr'] > 1 and data['anak_lk'] == 0):
        bagiancucupr = "termahjub"
        response += [f"bagian cucu perempuan {bagiancucupr}"]
        bagiancuculk = "sisa"
        response += [f"bagian cucu laki-laki {bagiancuculk}"]
      elif (data['anak_pr'] == 0 and data['anak_lk'] == 0):
        bagiancucupr = "sisa"
        bagiancuculk = "sisa"
        response += [f"bagian cucu perempuan {bagiancucupr}"]
        response += [f"bagian cucu laki-laki {bagiancuculk}"]
      elif (data['anak_pr'] == 1 and data['anak_lk'] == 0):
        bagiancucupr = "sisa"
        bagiancuculk = "sisa"
        response += [f"bagian cucu perempuan {bagiancucupr}"]
        response += [f"bagian cucu laki-laki {bagiancuculk}"]
      elif (data['anak_pr'] > 0 and data['anak_lk'] > 0):
        bagiancucupr = "termahjub"
        bagiancuculk = "termahjub"
        response += [f"bagian cucu perempuan {bagiancucupr}"]
        response += [f"bagian cucu laki-laki {bagiancuculk}"]
    elif (data['cucu_pr'] == 0 and data['cucu_lk'] >= 1):
      if (data['anak_lk'] >= 1 and data['anak_pr'] == 0):
        bagiancuculk = "termahjub"
        response += [f"bagian cucu laki-laki {bagiancuculk}"]
      elif (data['anak_lk'] == 0 and data['anak_pr'] == 0):
        bagiancuculk = "sisa"
        response += [f"bagian cucu laki-laki {bagiancuculk}"]
      elif (data['anak_pr'] >= 1 and data['anak_lk'] == 0):
        bagiancuculk = "sisa"
        response += [f"bagian cucu laki-laki {bagiancuculk}"]
    elif (data['cucu_pr'] == 1 and data['cucu_lk'] == 0):
      if (data['anak_lk'] == 0 and data['anak_pr'] == 0):
        bagiancucupr = 0.5  # 1/2
        response += [f"bagian cucu perempuan (1/2)"]
      elif (data['anak_lk'] >= 1 and data['anak_pr'] == 0):
        bagiancucupr = 0.5  # 1/2
        response += [f"bagian cucu perempuan (1/2)"]
      elif (data['anak_lk'] == 0 and data['anak_pr'] == 1):
        bagiancucupr = 0.16  # 1/6
        response += [f"bagian cucu perempuan (1/6)"]
      elif (data['anak_lk'] == 0 and data['anak_pr'] > 1):
        bagiancucupr = "termahjub"
        response += [f"bagian cucu perempuan {bagiancucupr}"]
    elif (data['cucu_pr'] > 1 and data['cucu_lk'] == 0):
      if (data['anak_lk'] >= 1 and data['anak_pr'] == 0):
        bagiancucupr = "termahjub"
        response += [f"bagian cucu perempuan {bagiancucupr}"]
      elif (data['anak_lk'] == 0 and data['anak_pr'] == 0):
        bagiancucupr = 0.6  # 2/3
        response += [f"bagian cucu perempuan (2/3)"]
      elif (data['anak_lk'] == 0 and data['anak_pr'] == 1):
        bagiancucupr = 0.16  # 1/6
        response += [f"bagian cucu perempuan (1/6)"]
      elif (data['anak_lk'] == 0 and data['anak_pr'] > 1):
        bagiancucupr = "termahjub"
        response += [f"bagian cucu perempuan {bagiancucupr}"]
    
    data['bagiancuculk'] = bagiancuculk
    data['bagiancucupr'] = bagiancucupr
    waris.setData(current_waris['id'], json.dumps(data))
    response += nextStep(step, current_waris['id'])
    return response
  elif step == 11:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])

    bagiansaudariknd = data.get("bagiansaudariknd", "")
    bagiansaudaraknd = data.get("bagiansaudaraknd", "")
    ###################### SAUDARI KANDUNG #######################################################
    if (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] == 0 and data['cucu_lk'] == 0):
      if (data['saudari_knd'] > 0 and data['saudara_knd'] > 0):
        bagiansaudariknd = "sisa"
        bagiansaudaraknd = "sisa"
        response += [f"bagian Saudari kandung {bagiansaudariknd}"]
        response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
      elif (data['saudari_knd'] == 1 and data['saudara_knd'] == 0):
        if (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudariknd = 0.5  # 1/2
          response += [f"bagian Saudari kandung (1/2)"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudariknd = "sisa"
          response += [f"bagian Saudari kandung {bagiansaudariknd}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudariknd = "sisa"
          response += [f"bagian Saudari kandung {bagiansaudariknd}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudariknd = "sisa"
          response += [f"bagian Saudari kandung {bagiansaudariknd}"]
      elif (data['saudari_knd'] > 1 and data['saudara_knd'] == 0):
        if (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudariknd = 0.6  # 2/3
          response += [f"bagian Saudari kandung (2/3)"]
        elif (data['anak_pr'] == 1 and data['cucu_pr'] == 1):
          bagiansaudariknd = "sisa"
          response += [f"bagian Saudari kandung {bagiansaudariknd}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudariknd = "sisa"
          response += [f"bagian Saudari kandung {bagiansaudariknd}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudariknd = "sisa"
          response += [f"bagian Saudari kandung {bagiansaudariknd}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudariknd = "sisa"
          response += [f"bagian Saudari kandung {bagiansaudariknd}"]
      elif (data['saudari_knd'] == 0 and data['saudara_knd'] > 0):
        if (data['anak_pr'] > 0 and data['cucu_pr'] > 0):
          bagiansaudaraknd = "sisa"
          response += [f"bagian saudara kandung {bagiansaudaraknd}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] > 0):
          bagiansaudaraknd = "sisa"
          response += [f"bagian saudara kandung {bagiansaudaraknd}"]
        elif (data['anak_pr'] > 0 and data['cucu_pr'] == 0):
          bagiansaudaraknd = "sisa"
          response += [f"bagian saudara kandung {bagiansaudaraknd}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudaraknd = "sisa"
          response += [f"bagian saudara kandung {bagiansaudaraknd}"]
    elif (data['ayah'] == True or data['kakek'] == True or data['anak_lk'] > 0 or data['cucu_lk'] > 0):
      if (data['saudari_knd'] > 0 and data['saudara_knd'] > 0):
        bagiansaudariknd = "termahjub"
        bagiansaudaraknd = "termahjub"
        response += [f"bagian Saudari kandung {bagiansaudariknd}"]
        response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
      elif (data['saudari_knd'] > 0 and data['saudara_knd'] == 0):
        bagiansaudariknd = "termahjub"
        response += [f"bagian Saudari kandung {bagiansaudariknd}"]
      elif (data['saudari_knd'] == 0 and data['saudara_knd'] > 0):
        bagiansaudaraknd = "termahjub"
        response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
    # elif (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] == 0 and data['cucu_lk'] > 0):
    #     if (data['saudari_knd'] > 0 and data['saudara_knd'] > 0):
    #         bagiansaudariknd = "termahjub"
    #         bagiansaudaraknd = "termahjub"
    #         response += [f"bagian Saudari kandung {bagiansaudariknd}"]
    #         response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
    #     elif (data['saudari_knd'] > 0 and data['saudara_knd'] == 0):
    #         bagiansaudariknd = "termahjub"
    #         response += [f"bagian Saudari {bagiansaudariknd}"]
    #     elif (data['saudari_knd'] == 0 and data['saudara_knd'] > 0):
    #         bagiansaudaraknd = "termahjub"
    #         response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
    # elif (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] > 0 and data['cucu_lk'] > 0):
    #     if (data['saudari_knd'] > 0 and data['saudara_knd'] > 0):
    #         bagiansaudariknd = "termahjub"
    #         bagiansaudaraknd = "termahjub"
    #         response += [f"bagian Saudari kandung {bagiansaudariknd}"]
    #         response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
    #     elif (data['saudari_knd'] > 0 and data['saudara_knd'] == 0):
    #         bagiansaudariknd = "termahjub"
    #         response += [f"bagian Saudari kandung {bagiansaudariknd}"]
    #     elif (data['saudari_knd'] == 0 and data['saudara_knd'] > 0):
    #         bagiansaudaraknd = "termahjub"
    #         response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
    # elif (data['ayah'] == True and data['kakek'] == True and data['anak_lk'] > 0 and data['cucu_lk'] > 0):
    #     if (data['saudari_knd'] > 0 and data['saudara_knd'] > 0):
    #         bagiansaudariknd = "termahjub"
    #         bagiansaudaraknd = "termahjub"
    #         response += [f"bagian Saudari kandung {bagiansaudariknd}"]
    #         response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
    #     elif (data['saudari_knd'] > 0 and data['saudara_knd'] == 0):
    #         bagiansaudariknd = "termahjub"
    #         response += [f"bagian Saudari kandung {bagiansaudariknd}"]
    #     elif (data['saudari_knd'] == 0 and data['saudara_knd'] > 0):
    #         bagiansaudaraknd = "termahjub"
    #         response += [f"bagian Saudara kandung {bagiansaudaraknd}"]
    
    data['bagiansaudaraknd'] = bagiansaudaraknd
    data['bagiansaudariknd'] = bagiansaudariknd
    waris.setData(current_waris['id'], json.dumps(data))

    response += nextStep(step, current_waris['id'])
    return response
  elif step == 12:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])

    bagiansaudaraseayah = data.get("bagiansaudaraseayah", "")
    bagiansaudariseayah = data.get("bagiansaudariseayah", "")
    bagiansaudaraseibu = data.get("bagiansaudaraseibu", "")
    bagiansaudariseibu = data.get("bagiansaudariseibu", "")

    ###################################### SAUDARI SEAYAH ##############################################################
    if (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0):
      if (data['saudari_seayah'] > 0 and data['saudara_seayah'] > 0 and data['saudari_knd'] == 0):
        if (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "sisa"
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "sisa"
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "sisa"
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "sisa"
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seyah {bagiansaudaraseayah}"]
      elif (data['saudari_seayah'] > 0 and data['saudara_seayah'] > 0 and data['saudari_knd'] == 1):
        if (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "termahjub"
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "termahjub"
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "termahjub"
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "sisa"
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
      elif (data['saudari_seayah'] > 0 and data['saudara_seayah'] > 0 and data['saudari_knd'] > 1):
        if (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "termahjub"
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "termahjub"
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "termahjub"
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "termahjub"
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
      elif (data['saudari_seayah'] == 1 and data['saudara_seayah'] == 0 and data['saudari_knd'] == 0):
        if (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudariseayah = 0.5  # 1/2
          response += [f"bagian Saudari seayah (1/2)"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
      elif (data['saudari_seayah'] > 1 and data['saudara_seayah'] == 0 and data['saudari_knd'] == 0):
        if (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudariseayah = 0.6  # 2/3
          response += [f"bagian Saudari seayah (2/3)"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "sisa"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
      elif (data['saudari_seayah'] >= 1 and data['saudara_seayah'] == 0 and data['saudari_knd'] == 1):
        if (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudariseayah = 0.16  # 1/6
          response += [f"bagian Saudari seayah (1/6)"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudariseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudariseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
      elif (data['saudari_seayah'] >= 1 and data['saudara_seayah'] == 0 and data['saudari_knd'] > 1):
        if (data['anak_pr'] >= 0 and data['cucu_pr'] >= 0):
          bagiansaudariseayah = "termahjub"
          response += [f"bagian Saudari seayah {bagiansaudariseayah}"]
      ######### SAUDARA SEAYAH ############################
      elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] >= 1 and data['saudari_knd'] == 0):
        if (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudaraseayah = "sisa"
          response += [f"bagian Saudara seayah {bagiansaudaraseayah}"]
      elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] >= 1 and data['saudari_knd'] >= 1):
        if (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
        if (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
          bagiansaudaraseayah = "sisa"
          response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
        elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
        if (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
          bagiansaudaraseayah = "termahjub"
          response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
      # elif (data['saudari_seayah'] >= 1 and data['saudara_seayah'] >= 1 and data['saudari_knd'] == 0):
      #     if (data['anak_pr'] >= 1 and data['cucu_pr'] >= 1):
      #         bagiansaudariseayah = "sisa"
      #         bagiansaudaraseayah = "sisa"
      #         response += [f"bagian saudari seayah {bagiansaudariseayah}"]
      #         response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
      #     elif (data['anak_pr'] >= 1 and data['cucu_pr'] == 0):
      #         bagiansaudariseayah = "sisa"
      #         bagiansaudaraseayah = "sisa"
      #         response += [f"bagian saudari seayah {bagiansaudariseayah}"]
      #         response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
      #     elif (data['anak_pr'] == 0 and data['cucu_pr'] >= 1):
      #         bagiansaudariseayah = "sisa"
      #         bagiansaudaraseayah = "sisa"
      #         response += [f"bagian saudari seayah {bagiansaudariseayah}"]
      #         response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
      #     elif (data['anak_pr'] == 0 and data['cucu_pr'] == 0):
      #         bagiansaudariseayah = "sisa"
      #         bagiansaudaraseayah = "sisa"
      #         response += [f"bagian saudari seayah {bagiansaudariseayah}"]
      #         response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
    elif (data['ayah'] == True or data['kakek'] == True or data['anak_lk'] >= 1 or data['cucu_lk'] >= 1 or data['saudara_knd'] >= 1):
      if (data['saudari_seayah'] >= 1 and data['saudara_seayah'] >= 1):
        bagiansaudariseayah = "termahjub"
        bagiansaudaraseayah = "termahjub"
        response += [f"bagian saudari seayah {bagiansaudariseayah}"]
        response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
      elif (data['saudari_seayah'] >= 1 and data['saudara_seayah'] == 0):
        bagiansaudariseayah = "termahjub"
        response += [f"bagian saudari seayah {bagiansaudariseayah}"]
      elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] >= 1):
        bagiansaudaraseayah = "termahjub"
        response += [f"bagian saudara seayah {bagiansaudaraseayah}"]
    ###################################### SAUDARI SEIBU ##############################################################
    if (data['ayah'] == False and data['kakek'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
      if (data['saudari_seibu'] > 1 and data['saudara_seibu'] > 1):
        bagiansaudariseibu = 0.16
        bagiansaudaraseibu = 0.16
        response += [f"bagian saudari seibu (1/6)"]
        response += [f"bagian saudara seibu (1/6)"]
      elif (data['saudari_seibu'] == 1 and data['saudara_seibu'] == 1):
        bagiansaudariseibu = 0.16
        bagiansaudaraseibu = 0.16
        response += [f"bagian saudari seibu (1/6)"]
        response += [f"bagian saudara seibu (1/6)"]
      elif (data['saudari_seibu'] == 1 and data['saudara_seibu'] > 1):
        bagiansaudariseibu = 0.16
        bagiansaudaraseibu = 0.16
        response += [f"bagian saudari seibu (1/6)"]
        response += [f"bagian saudara seibu (1/6)"]
      elif (data['saudari_seibu'] > 1 and data['saudara_seibu'] == 1):
        bagiansaudariseibu = 0.16
        bagiansaudaraseibu = 0.16
        response += [f"bagian saudari seibu (1/6)"]
        response += [f"bagian saudara seibu (1/6)"]
      elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] == 1):
        bagiansaudaraseibu = 0.16
        response += [f"bagian saudara seibu (1/6)"]
      elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] > 1):
        bagiansaudaraseibu = 0.3
        response += [f"bagian saudara seibu (1/3)"]
      elif (data['saudari_seibu'] == 1 and data['saudara_seibu'] == 0):
        bagiansaudariseibu = 0.16
        response += [f"bagian saudari seibu (1/6)"]
      elif (data['saudari_seibu'] > 1 and data['saudara_seibu'] == 0):
        bagiansaudariseibu = 0.3
        response += [f"bagian saudari seibu (1/3)"]
    elif (data['ayah'] == True or data['kakek'] == True or data['anak_pr'] >= 0 or data['anak_lk'] >= 0 or data['cucu_pr'] >= 0 or data['cucu_lk'] >= 0):
      if (data['saudari_seibu'] >= 1 and data['saudara_seibu'] >= 1):
        bagiansaudariseibu = "termahjub"
        bagiansaudaraseibu = "teermahjub"
        response += [f"bagian saudari seibu {bagiansaudariseibu}"]
        response += [f"bagian saudara seibu {bagiansaudaraseibu}"]
      elif (data['saudari_seibu'] >= 1 and data['saudara_seibu'] == 0):
        bagiansaudariseibu = "termahjub"
        response += [f"bagian saudari seibu  {bagiansaudariseibu}"]
      elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] >= 1):
        bagiansaudaraseibu = "termahjub"
        response += [f"bagian saudara seibu {bagiansaudaraseibu}"]

    data['bagiansaudaraseayah'] = bagiansaudaraseayah
    data['bagiansaudariseayah'] = bagiansaudariseayah
    data['bagiansaudaraseibu'] = bagiansaudaraseibu
    data['bagiansaudariseibu'] = bagiansaudariseibu
    waris.setData(current_waris['id'], json.dumps(data))

    response += nextStep(step, current_waris['id'])

    return response
  elif step == 13:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])

    ##################### Asal Masalah #################################
    asalmasalah = data['asalmasalah'] if 'asalmasalah' in data else 0
    masuk = data['masuk'] if 'masuk' in data else ""
    masuk0 = data.get("masuk0", "")
    masuk2 = data.get("masuk2", "")
    sisa = data['sisa'] if 'sisa' in data else 0
    tampil = data['tampil'] if 'tampil' in data else ""
    hitung = data['hitung'] if 'hitung' in data else ""
    suami = data.get('suami', False)
    istri = data.get('istri', 0)
    ayah = data.get('ayah', False)
    ibu = data.get('ibu', False)
    kakek = data.get('kakek', False)
    nenek = data.get('nenek', 0)
    cucu_pr = data.get('cucu_pr', 0)
    anak_pr = data.get('anak_pr', 0)
    cucu_lk = data.get('cucu_lk', 0)
    anak_lk = data.get('anak_lk', 0)
    saudara_knd = data.get('saudara_knd', 0)
    saudari_knd = data.get('saudari_knd', 0)
    saudara_seayah = data.get('saudara_seayah', 0)
    saudari_seayah = data.get('saudari_seayah', 0)
    saudara_seibu = data.get('saudara_seibu', 0)
    saudari_seibu = data.get('saudari_seibu', 0)
    bagianibu = data.get("bagianibu", 0)
    bagiansuami = data.get("bagiansuami", 0)
    bagianistri = data.get("bagianistri", 0)
    bagianibu = data.get("bagianibu", 0)
    bagianayah = data.get("bagianayah", 0)
    bagiankakek = data.get("bagiankakek", 0)
    bagiannenek = data.get("bagiannenek", 0)
    bagiananakpr = data.get("bagiananakpr", 0)
    bagiananaklk = data.get("bagiananaklk", 0)
    bagiancuculk = data.get("bagiancuculk", 0)
    bagiancucupr = data.get("bagiancucupr", 0)
    bagiansaudaraknd = data.get("bagiansaudaraknd", 0)
    bagiansaudariknd = data.get("bagiansaudariknd", 0)
    bagiansaudaraseayah = data.get("bagiansaudaraseayah", 0)
    bagiansaudariseayah = data.get("bagiansaudariseayah", 0)
    bagiansaudaraseibu = data.get("bagiansaudaraseibu", 0)
    bagiansaudariseibu = data.get("bagiansaudariseibu", 0)
    bagiansisaibu = data.get("bagiansisaibu", "")
    jumlahasalmasalah = data.get("jumlahasalmasalah", 0)
    totalasalmasalah = data.get("totalasalmasalah", 0)
    asalmasalah_suami = data.get("asalmasalah_suami", 0)
    asalmasalah_istri = data.get("asalmasalah_istri", 0)
    asalmasalah_ibu = data.get("asalmasalah_ibu", 0)
    asalmasalah_ayah = data.get("asalmasalah_ayah", 0)
    asalmasalah_nenek = data.get("asalmasalah_nenek", 0)
    asalmasalah_kakek = data.get("asalmasalah_kakek", 0)
    asalmasalah_anaklk = data.get("asalmasalah_anaklk", 0)
    asalmasalah_anakpr = data.get("asalmasalah_anakpr", 0)
    asalmasalah_cuculk = data.get("asalmasalah_cuculk", 0)
    asalmasalah_cucupr = data.get("asalmasalah_cucupr", 0)
    asalmasalah_saudara_knd = data.get("asalmasalah_saudara_knd", 0)
    asalmasalah_saudari_knd = data.get("asalmasalah_saudari_knd", 0)
    asalmasalah_saudara_seayah = data.get("asalmasalah_saudara_seayah", 0)
    asalmasalah_saudari_seayah = data.get("asalmasalah_saudari_seayah", 0)
    asalmasalah_saudara_seibu = data.get("asalmasalah_saudara_seibu", 0)
    asalmasalah_saudari_seibu = data.get("asalmasalah_saudari_seibu", 0)

    ## pembagian
    if (current_waris['jk_pewaris'] == 'L'):
      if (data['bagianistri'] == 0.125):
        if (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] == 0 and data['cucu_lk'] == 0):
          if (data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
            if (data['ibu'] == False and data['nenek'] == 0):
              if (data['anak_pr'] == 1 and data['cucu_pr'] == 0):
                asalmasalah = 8
              elif (data['anak_pr'] == 0 and data['cucu_pr'] == 1):
                asalmasalah = 8
              else:
                asalmasalah = 24
            else:
              asalmasalah = 24
          elif (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
            if (data['ibu'] == False and data['nenek'] == 0):
              if (data['anak_pr'] == 1 and data['cucu_pr'] == 0):
                asalmasalah = 8
              elif (data['anak_pr'] == 0 and data['cucu_pr'] == 1):
                asalmasalah = 8
              else:
                asalmasalah = 24
            else:
              asalmasalah = 24
          else:
            asalmasalah = 8
            if(data['ibu'] == False and data['nenek'] == 0):
              masuk2 = "anakpr"
        else:
          if (data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0 and data['anak_pr'] > 1):
              asalmasalah = 24
            else:
              asalmasalah = 8
          else:
            asalmasalah = 24
      elif (data['bagianistri'] == 0.25):
        if (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
          response += [f"Asal Masalah Awal 4 Menjadi {asalmasalah}"]
        elif (data['kakek'] == True and data['nenek'] > 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 12
        else:
          if (data['ayah'] == True and data['nenek'] > 0 and data['kakek'] == False and data['ibu'] == False):
            asalmasalah = 12
          else:
            if (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] > 0):
              if (data['ibu'] == False and data['nenek'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudara_seibu'] == 0 and data['saudari_seibu'] == 0):
                asalmasalah = 4
              else:
                asalmasalah = 12
            else:
              if (data['saudari_knd'] > 1 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seibu'] == 0 and data['saudari_seibu'] == 0):
                if (data['ibu'] == False and data['nenek'] == 0):
                  asalmasalah = 4
                else:
                  asalmasalah = 12
              else:
                if (data['ibu'] == False and data['nenek'] > 0 and data['saudari_knd'] == 1 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudara_seibu'] == 0 and data['saudari_seibu'] == 0):
                  asalmasalah = 4
                elif (data['ibu'] == False and data['nenek'] > 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 1 and data['saudara_seayah'] == 0 and data['saudara_seibu'] == 0 and data['saudari_seibu'] == 0):
                  asalmasalah = 4
                else:
                  if (data['nenek'] == 0 and data['ibu'] == False):
                    if (data['saudari_knd'] > 1 and data['saudara_seayah'] > 0):
                      asalmasalah = 12
                    else:
                      if(data['saudari_seibu'] > 0 or data['saudara_seibu'] > 0):
                        if(data['saudara_seibu'] == 0 and data['saudari_seibu'] == 1 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0):
                          if(data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            masuk = "saudari-sibu"
                            asalmasalah = 4
                        elif(data['saudara_seibu'] == 1 and data['saudari_seibu'] == 1 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0):
                          if(data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            masuk = "saudari-sibu"
                            asalmasalah = 4
                        elif(data['saudara_seibu'] == 1 and data['saudari_seibu'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0):
                          if(data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            masuk = "saudari-sibu"
                            asalmasalah = 4
                        elif(data['saudara_seibu'] == 0 and data['saudari_seibu'] > 1 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0):
                          if(data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            masuk = "saudari-sibu"
                            asalmasalah = 4
                        elif(data['saudara_seibu'] > 1 and data['saudari_seibu'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0):
                          if(data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            masuk = "saudari-sibu"
                            asalmasalah = 4   
                        elif(data['saudara_seibu'] == 1 and data['saudari_seibu'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 1 and data['saudari_seayah'] == 0):
                          if(data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            asalmasalah = 4
                        elif(data['saudara_seibu'] == 0 and data['saudari_seibu'] == 1 and data['saudara_knd'] == 0 and data['saudari_knd'] == 1 and data['saudari_seayah'] == 0):
                          if(data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            asalmasalah = 4
                        elif(data['saudara_seibu'] == 1 and data['saudari_seibu'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 1):
                          if(data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            asalmasalah = 4   
                            tampil = "ubah"
                        elif(data['saudara_seibu'] == 0 and data['saudari_seibu'] == 1 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 1):
                          if(data['saudara_seayah'] > 0):
                            asalmasalah = 12
                          else:
                            asalmasalah = 4   
                            tampil = "ubah"
                        else:
                          if(data['saudara_knd'] == 0 and data['saudari_knd'] == 0):
                            if(data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                              asalmasalah = 12
                            else:
                              asalmasalah = 4
                              masuk = "saudari-sibu" 
                          else:
                            asalmasalah = 12
                      else:
                        asalmasalah = 4
                  else:
                    if (data['ayah'] == False and data['kakek'] == False and data['ibu'] == True and data['saudari_knd'] == 0 and data['saudara_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seibu'] == 0 and data['saudari_seibu'] == 0):
                      asalmasalah = 4
                    else:
                      if (data['ayah'] == False and data['kakek'] == False and data['ibu'] == True and data['saudari_knd'] == 0 and data['saudara_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] >= 0 and data['saudara_seibu'] >= 0):
                        asalmasalah = 4
                        masuk = "saudari-sibu"
                      elif (data['ayah'] == False and data['kakek'] == False and data['nenek'] > 0 and data['saudari_knd'] == 0 and data['saudara_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] >= 0 and data['saudara_seibu'] >= 0):
                        asalmasalah = 4
                        masuk = "saudari-sibu"
                      else:
                        asalmasalah = 12
      elif (data['bagianistri'] == 0):
        if (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == True and data['ibu'] == True and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 3
        # data['ayah']
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == True and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
        # data['ibu']
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == True and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == True and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] >= 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] >= 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 3
        # data['kakek']
        elif (data['kakek'] == True and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
        # data['nenek']
        elif (data['kakek'] == False and data['nenek'] > 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
        # cucupr
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] > 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah_cucupr = (1 * data['cucu_pr'])
          asalmasalah = asalmasalah_cucupr
          masuk = "cucu1"
        # cuculk
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] > 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah_cuculk = (1 * data['cucu_lk'])
          asalmasalah = asalmasalah_cuculk
        # cuculk and cucu pr
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] > 0 and data['cucu_pr'] > 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah_cucupr = (1 * data['cucu_pr'])
          asalmasalah_cuculk = (2 * data['cucu_lk'])
          asalmasalah = asalmasalah_cucupr + asalmasalah_cuculk
        # anak pr cucu pr saudara kandung
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] >= 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] >= 0 and data['saudara_knd'] >= 0 and data['saudari_knd'] >= 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['anak_pr'] == 0 and data['cucu_pr'] == 1):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 2
          elif (data['anak_pr'] == 0 and data['cucu_pr'] > 1):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 3
          elif (data['anak_pr'] == 1 and data['cucu_pr'] == 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 2
              masuk = "saudari3"
          elif (data['anak_pr'] > 1 and data['cucu_pr'] == 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 3
            else:
              asalmasalah = 3
              masuk = "anakprk1"
          elif (data['anak_pr'] == 1 and data['cucu_pr'] > 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 6
              masuk = "saudari3"
          elif(data['anak_pr'] == 0 and data['cucu_pr'] == 0):
            if (data['saudari_knd'] > 0 and data['saudara_knd'] == 0):
              asalmasalah_saudari_knd = (1 * data['saudari_knd'])
              asalmasalah = asalmasalah_saudari_knd
              masuk = "saudari0"
            elif (data['saudari_knd'] == 0 and data['saudara_knd'] > 0):
              asalmasalah_saudara_knd = (1 * data['saudara_knd'])
              asalmasalah = asalmasalah_saudara_knd
            elif (data['saudari_knd'] > 0 and data['saudara_knd'] > 0):
              asalmasalah_saudari_knd = (1 * data['saudari_knd'])
              asalmasalah_saudara_knd = (2 * data['saudara_knd'])
              asalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_knd
        # anak pr cucu pr saudara kandung
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] >= 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] >= 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] >= 0 and data['saudara_seayah'] >= 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['anak_pr'] == 0 and data['cucu_pr'] == 1):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 2
          elif (data['anak_pr'] == 0 and data['cucu_pr'] > 1):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 3
          elif (data['anak_pr'] == 1 and data['cucu_pr'] == 0):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 2
              masuk = "saudari3"
          elif (data['anak_pr'] > 1 and data['cucu_pr'] == 0):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 3
          elif (data['anak_pr'] == 1 and data['cucu_pr'] > 0):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 6
              masuk = "saudari3"
          elif(data['anak_pr'] == 0 and data['cucu_pr'] == 0):
            if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
              asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
              asalmasalah = asalmasalah_saudari_seayah
              masuk = "saudari0"
            elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] > 0):
              asalmasalah_saudara_seayah = (1 * data['saudara_seayah'])
              asalmasalah = asalmasalah_saudara_seayah
            elif (data['saudari_seayah'] > 0 and data['saudara_seayah'] > 0):
              asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
              asalmasalah_saudara_seayah = (2 * data['saudara_seayah'])
              asalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudara_seayah
        # batas
        elif (data['kakek'] == True and data['nenek'] > 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 6
        elif (data['kakek'] == True and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == True and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 3
        elif (data['kakek'] == False and data['nenek'] > 0 and data['ayah'] == True and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 6
        # anak laki dan anak perempuan
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] >= 0 and data['anak_lk'] >= 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['anak_pr'] > 0 and data['anak_lk'] == 0):
            asalmasalah_anakpr = (1 * data['anak_pr'])
            asalmasalah = asalmasalah_anakpr
          elif (data['anak_pr'] == 0 and data['anak_lk'] > 0):
            asalmasalah_anaklk = (1 * data['anak_lk'])
            asalmasalah = asalmasalah_anaklk
          elif (data['anak_pr'] > 0 and data['anak_lk'] > 0):
            asalmasalah_anakpr = (1 * data['anak_pr'])
            asalmasalah_anaklk = (2 * data['anak_lk'])
            asalmasalah = asalmasalah_anakpr + asalmasalah_anaklk
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudari_seayah'] >= 0 and data['saudara_seayah'] >= 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
            asalmasalah = 6
          else:
            asalmasalah = 2
        # saudara saudari saayah
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] >= 0 and data['saudara_seayah'] >= 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
            asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
            asalmasalah = asalmasalah_saudari_seayah
          elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] > 0):
            asalmasalah_saudara_seayah = (1 * data['saudara_seayah'])
            asalmasalah = asalmasalah_saudara_seayah
          elif (data['saudari_seayah'] > 0 and data['saudara_seayah'] > 0):
            asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
            asalmasalah_saudara_seayah = (2 * data['saudara_seayah'])
            asalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudara_seayah
        # saudara saudari sibu
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] >= 0 and data['saudara_seibu'] >= 0):
          if (data['saudari_seibu'] > 0 and data['saudara_seibu'] == 0):
            masuk = "saudari6"
            if(data['saudari_seibu'] > 1):
              asalmasalah = 3
            else:
              asalmasalah = 6
          elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] > 0):
            masuk = "saudari6"
            if(data['saudara_seibu'] > 1):
              asalmasalah = 3
            else:
              asalmasalah = 6
          elif (data['saudari_seibu'] > 0 and data['saudara_seibu'] > 0):
            masuk = "saudari6"
            asalmasalah = 6
        else:
          asalmasalah = 6
    elif (current_waris['jk_pewaris'] == 'P'):
      if (data['bagiansuami'] == 0.5):
        if (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
          response += [f"Asal Masalah Awal 2 Menjadi {asalmasalah}"]
        elif (data['kakek'] == True and data['nenek'] > 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 6
        else:
          if (data['ayah'] == True and data['nenek'] > 0 and data['kakek'] == False and data['ibu'] == False):
            asalmasalah = 6
          else:
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              if (data['saudari_knd'] > 1 and data['saudara_knd'] == 0):
                if (data['ibu'] == False and data['nenek'] == 0):
                  if (data['saudara_seayah'] > 0):
                    asalmasalah = 6
                  else:
                    asalmasalah = 6
                else:
                  asalmasalah = 6
              else:
                if (data['ibu'] == False and data['nenek'] == 0):
                  if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
                    asalmasalah = 6
                  else:
                    if(data['saudari_seibu'] > 0 or data['saudara_seibu'] > 0):
                      asalmasalah = 6
                    else:
                      asalmasalah = 2
                else:
                  asalmasalah = 6
            else:
              if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                if (data['saudari_seayah'] > 1 and data['saudara_seayah'] == 0):
                  if (data['ibu'] == False and data['nenek'] == 0):
                    asalmasalah = 6
                  else:
                    asalmasalah = 6
                else:
                  if (data['ibu'] == False and data['nenek'] == 0):
                    if(data['saudara_seibu'] > 0 or data['saudari_seibu'] > 0):
                      asalmasalah = 6
                    else:
                      asalmasalah = 2
                  else:
                    asalmasalah = 6
              else:
                if(data['saudari_seibu'] > 0 or data['saudara_seibu'] > 0):
                  if(data['nenek'] > 0 and data['saudari_seibu'] == 1 and data['saudara_seibu'] == 0):
                    asalmasalah = 2
                    masuk = "saudari-sibu"
                  elif(data['nenek'] > 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 1):
                    asalmasalah = 2
                    masuk = "saudari-sibu"
                  else:
                    if(data['ibu'] == False and data['nenek'] == 0):
                      asalmasalah = 2
                      masuk = "saudari-sibu"
                    else:
                      asalmasalah = 6
                else:
                  asalmasalah = 2
      elif (data['bagiansuami'] == 0.25):
        if (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] == 0):
          if (data['ibu'] == True and data['anak_pr'] > 1):
            asalmasalah = 12
          elif (data['nenek'] > 0 and data['anak_pr'] > 1):
            asalmasalah = 12
          else:
            if (data['ibu'] == True and data['nenek'] == 0 and data['anak_pr'] == 1 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
              asalmasalah = 12
            elif (data['ibu'] == False and data['nenek'] > 0 and data['anak_pr'] == 1 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
              asalmasalah = 12
            else:
              if (data['anak_pr'] > 1):
                if (data['ibu'] == False and data['nenek'] == 0 and data['cucu_lk'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudara_seayah'] == 0):
                  asalmasalah = 4
                else:
                  asalmasalah = 12
              else:
                if (data['cucu_lk'] > 0 or data['cucu_pr'] > 0):
                  if (data['cucu_pr'] == 1 and data['cucu_lk'] == 0):
                    if (data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
                      if (data['ibu'] == False and data['nenek'] == 0 and data['anak_pr'] == 1):
                        asalmasalah = 12
                      else:
                        asalmasalah = 4
                    else:
                      if (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                        if (data['ibu'] == False and data['nenek'] == 0 and data['anak_pr'] == 1):
                          asalmasalah = 12
                        else:
                          asalmasalah = 4
                      else:
                        asalmasalah = 4
                  else:
                    if(data['ibu'] == False and data['nenek'] == 0 and data['cucu_lk'] == 0):
                      asalmasalah = 4 
                    else:
                      asalmasalah = 12
                else:
                  if (data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
                    if (data['ibu'] == False and data['nenek'] == 0):
                      asalmasalah = 4
                    else:
                      asalmasalah = 12
                  else:
                    if (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                      if (data['ibu'] == False and data['nenek'] == 0):
                        asalmasalah = 4
                      else:
                        asalmasalah = 12
                    else:
                      asalmasalah = 4
        else:
          if (data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0):
            asalmasalah = 4
          else:
            asalmasalah = 12
      elif (data['bagiansuami'] == 0):
        if (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == True and data['ibu'] == True and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 3
        # data['ayah']
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == True and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
        # data['ibu']
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == True and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == True and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] >= 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] >= 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 3
        # data['kakek']
        elif (data['kakek'] == True and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
        # data['nenek']
        elif (data['kakek'] == False and data['nenek'] > 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 1
        # cucupr
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] > 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah_cucupr = (1 * data['cucu_pr'])
          asalmasalah = asalmasalah_cucupr
          masuk = "cucu1"
        # cuculk
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] > 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah_cuculk = (1 * data['cucu_lk'])
          asalmasalah = asalmasalah_cuculk
        # cuculk and cucu pr
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] > 0 and data['cucu_pr'] > 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah_cucupr = (1 * data['cucu_pr'])
          asalmasalah_cuculk = (2 * data['cucu_lk'])
          asalmasalah = asalmasalah_cucupr + asalmasalah_cuculk
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] >= 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] >= 0 and data['saudara_knd'] >= 0 and data['saudari_knd'] >= 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['anak_pr'] == 0 and data['cucu_pr'] == 1):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 2
          elif (data['anak_pr'] == 0 and data['cucu_pr'] > 1):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 3
          elif (data['anak_pr'] == 1 and data['cucu_pr'] == 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 2
              masuk = "saudari3"
          elif (data['anak_pr'] > 1 and data['cucu_pr'] == 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 3
            else :
              asalmasalah = 3
              masuk = "anakprk1"
          elif (data['anak_pr'] == 1 and data['cucu_pr'] > 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              asalmasalah = 6
              masuk = "saudari3"
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] >= 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] >= 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] >= 0 and data['saudara_seayah'] >= 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['anak_pr'] == 0 and data['cucu_pr'] == 1):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 2
          elif (data['anak_pr'] == 0 and data['cucu_pr'] > 1):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 3
          elif (data['anak_pr'] == 1 and data['cucu_pr'] == 0):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 2
              masuk = "saudari3"
          elif (data['anak_pr'] > 1 and data['cucu_pr'] == 0):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 3
          elif (data['anak_pr'] == 1 and data['cucu_pr'] > 0):
            if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
              asalmasalah = 6
              masuk = "saudari3"
        elif (data['kakek'] == True and data['nenek'] > 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 6
        elif (data['kakek'] == True and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == True and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 3
        elif (data['kakek'] == False and data['nenek'] > 0 and data['ayah'] == True and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          asalmasalah = 6
        # anak laki dan perempuan
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] >= 0 and data['anak_lk'] >= 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['anak_pr'] > 0 and data['anak_lk'] == 0):
            asalmasalah_anakpr = (1 * data['anak_pr'])
            asalmasalah = asalmasalah_anakpr
          elif (data['anak_pr'] == 0 and data['anak_lk'] > 0):
            asalmasalah_anaklk = (1 * data['anak_lk'])
            asalmasalah = asalmasalah_anaklk
          elif (data['anak_pr'] > 0 and data['anak_lk'] > 0):
            asalmasalah_anakpr = (1 * data['anak_pr'])
            asalmasalah_anaklk = (2 * data['anak_lk'])
            asalmasalah = asalmasalah_anakpr + asalmasalah_anaklk
        # saudara saudari kandung
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] >= 0 and data['saudari_knd'] >= 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['saudari_knd'] > 0 and data['saudara_knd'] == 0):
            asalmasalah_saudari_knd = (1 * data['saudari_knd'])
            asalmasalah = asalmasalah_saudari_knd
            masuk = "saudari0"
          elif (data['saudari_knd'] == 0 and data['saudara_knd'] > 0):
            asalmasalah_saudara_knd = (1 * data['saudara_knd'])
            asalmasalah = asalmasalah_saudara_knd
          elif (data['saudari_knd'] > 0 and data['saudara_knd'] > 0):
            asalmasalah_saudari_knd = (1 * data['saudari_knd'])
            asalmasalah_saudara_knd = (2 * data['saudara_knd'])
            asalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_knd
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudari_seayah'] >= 0 and data['saudara_seayah'] >= 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
            asalmasalah = 6
          else:
            asalmasalah = 2
        # saudara saudari saayah
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] >= 0 and data['saudara_seayah'] >= 0 and data['saudari_seibu'] == 0 and data['saudara_seibu'] == 0):
          if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
            asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
            asalmasalah = asalmasalah_saudari_seayah
          elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] > 0):
            asalmasalah_saudara_seayah = (1 * data['saudara_seayah'])
            asalmasalah = asalmasalah_saudara_seayah
          elif (data['saudari_seayah'] > 0 and data['saudara_seayah'] > 0):
            asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
            asalmasalah_saudara_seayah = (2 * data['saudara_seayah'])
            asalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudara_seayah
        # saudara saudari seibu
        elif (data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['cucu_pr'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seibu'] >= 0 and data['saudara_seibu'] >= 0):
          if (data['saudari_seibu'] > 0 and data['saudara_seibu'] == 0):
            masuk = "saudari6"
            if(data['saudari_seibu'] > 1):
              asalmasalah = 3
            else:
              asalmasalah = 6
          elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] > 0):
            masuk = "saudari6"
            if(data['saudara_seibu'] > 1):
              asalmasalah = 3
            else:
              asalmasalah = 6
          elif (data['saudari_seibu'] > 0 and data['saudara_seibu'] > 0):
            masuk = "saudari6"
            asalmasalah = 6
        else:
          asalmasalah = 6
    
    response += [f"Asal Masalah : {asalmasalah}"]

    ####################### Penghitungan Asal Masalah ###########################
    # asal masalah suami
    if (suami == True):
        if (cucu_lk > 0 or cucu_pr > 0):
            hitungasalmasalah_suami = (asalmasalah / 4) * 1
            asalmasalah_suami = int(hitungasalmasalah_suami)
            response.append(
                f"Tampil Siham Masalah Suami : {asalmasalah_suami}")
        elif (anak_lk > 0 or anak_pr > 0):
            hitungasalmasalah_suami = (asalmasalah / 4) * 1
            asalmasalah_suami = int(hitungasalmasalah_suami)
            response.append(
                f"Tampil Siham Masalah Suami : {asalmasalah_suami}")
        elif (cucu_pr == 0 and anak_pr == 0 and anak_lk == 0 and anak_pr == 0):
            if (kakek == False and nenek == 0 and ayah == False and ibu == False and saudara_knd == 0 and saudari_knd == 0 and saudari_seayah == 0 and saudara_seayah == 0 and saudari_seibu == 0 and saudara_seibu == 0):
                asalmasalah_suami = 1
                response.append(
                    f"Tampil Siham Masalah Suami : {asalmasalah_suami}")
            else:
                hitungasalmasalah_suami = (asalmasalah / 2) * 1
                asalmasalah_suami = int(hitungasalmasalah_suami)
                response.append(
                    f"Tampil Siham Masalah Suami : {asalmasalah_suami}")
    else:
        asalmasalah_suami = 0

    # asal masalah istri
    if (istri > 0):
        if (cucu_lk > 0 or cucu_pr > 0):
            hitungasalmasalah_istri = (asalmasalah / 8) * 1
            asalmasalah_istri = int(hitungasalmasalah_istri)
            response.append(
                f"Tampil Siham Masalah Istri : {asalmasalah_istri}")
        elif (anak_lk > 0 or anak_pr > 0):
            hitungasalmasalah_istri = (asalmasalah / 8) * 1
            asalmasalah_istri = int(hitungasalmasalah_istri)
            response.append(
                f"Tampil Siham Masalah Istri : {asalmasalah_istri}")
        elif (cucu_pr == 0 and anak_pr == 0 and anak_lk == 0 and anak_pr == 0):
            if (kakek == False and nenek == 0 and ayah == False and ibu == False and saudara_knd == 0 and saudari_knd == 0 and saudari_seayah == 0 and saudara_seayah == 0 and saudari_seibu == 0 and saudara_seibu == 0):
                asalmasalah_istri = 1
                response.append(
                    f"Tampil Siham Masalah Istri : {asalmasalah_istri}")
            else:
                hitungasalmasalah_istri = (asalmasalah / 4) * 1
                asalmasalah_istri = int(hitungasalmasalah_istri)
                response.append(
                    f"Tampil Siham Masalah Istri : {asalmasalah_istri}")
    else:
        asalmasalah_istri = 0

    # asal masalah ibu
    if (ibu == True):
        if (bagianibu == 0.33 and bagiansisaibu == "*sisa"):
            asalmasalah_ibu = 1
            response.append(f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
        elif (bagianibu == 0.33 and bagiansisaibu == ""):
            if (masuk == "saudari-sibu"):
                hitungasalmasalah_ibu = (6 / 3) * 1
                asalmasalah_ibu = int(hitungasalmasalah_ibu)
            else:
                hitungasalmasalah_ibu = (asalmasalah / 3) * 1
                asalmasalah_ibu = int(hitungasalmasalah_ibu)
                response.append(
                    f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
        else:
            if (current_waris['jk_pewaris'] == 'L'):
                if (ayah == False and kakek == False and anak_lk == 0 and cucu_lk == 0 and saudara_knd == 0):
                    if (saudari_knd > 1):
                        hitungasalmasalah_ibu = (asalmasalah / 6) * 1
                        asalmasalah_ibu = int(hitungasalmasalah_ibu)
                        response.append(
                            f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                    elif (saudari_knd == 0):
                        if (cucu_pr == 0 and anak_pr == 0):
                            if (saudara_seayah > 0 or saudari_seayah > 0):
                                hitungasalmasalah_ibu = (asalmasalah / 6) * 1
                                asalmasalah_ibu = int(hitungasalmasalah_ibu)
                                print(
                                    f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                            else:
                                if (saudari_seibu > 0 or saudara_seibu > 0):
                                    hitungasalmasalah_ibu = (6 / 6) * 1
                                    asalmasalah_ibu = int(
                                        hitungasalmasalah_ibu)
                                    if (istri == 0):
                                        response.append(
                                            f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                                else:
                                    asalmasalah_ibu = 1
                                    response.append(
                                        f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                        else:
                            hitungasalmasalah_ibu = (asalmasalah / 6) * 1
                            asalmasalah_ibu = int(hitungasalmasalah_ibu)
                            response.append(
                                f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                    else:
                        if (cucu_pr == 0 and anak_pr == 0):
                            if (saudara_seayah > 0 or saudari_seayah > 0):
                                hitungasalmasalah_ibu = (asalmasalah / 6) * 1
                                asalmasalah_ibu = int(hitungasalmasalah_ibu)
                                print(
                                    f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                            else:
                                if (saudari_seibu > 0 or saudara_seibu > 0):
                                    hitungasalmasalah_ibu = (
                                        asalmasalah / 6) * 1
                                    asalmasalah_ibu = int(
                                        hitungasalmasalah_ibu)
                                    response.append(
                                        f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                                else:
                                    asalmasalah_ibu = 1
                                    print(
                                        f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                        else:
                            hitungasalmasalah_ibu = (asalmasalah / 6) * 1
                            asalmasalah_ibu = int(hitungasalmasalah_ibu)
                            response.append(
                                f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                else:
                    hitungasalmasalah_ibu = (asalmasalah / 6) * 1
                    asalmasalah_ibu = int(hitungasalmasalah_ibu)
                    response.append(
                        f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
            elif (current_waris['jk_pewaris'] == 'P'):
                if (suami == True and bagiansuami == 0.25 and asalmasalah == 4):
                    asalmasalah_ibu = 1
                    response.append(
                        f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                else:
                    if (suami == False and anak_pr == 0 and anak_lk == 0):
                        asalmasalah_ibu = 1
                        response.append(
                            f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
                    else:
                        hitungasalmasalah_ibu = (asalmasalah / 6) * 1
                        asalmasalah_ibu = int(hitungasalmasalah_ibu)
                        response.append(
                            f"Tampil Siham Masalah Ibu : {asalmasalah_ibu}")
    else:
        asalmasalah_ibu = 0

    # asal masalah nenek
    if (nenek > 0 and bagiannenek != "termahjub"):
        if (ayah == False and kakek == False and anak_lk == 0 and anak_pr == 0 and cucu_lk == 0 and cucu_pr == 0 and saudara_knd == 0 and saudari_knd == 0 and saudara_seayah == 0 and saudari_seayah == 0 and saudara_seibu == 0 and saudari_seibu == 0):
            asalmasalah_nenek = 1
            response.append(
                f"Tampil Siham Masalah Nenek : {asalmasalah_nenek}")
        else:
            if (current_waris['jk_pewaris'] == 'L'):
                if (istri == 0 and anak_pr == 0 and anak_lk == 0):
                    asalmasalah_nenek = 1
                    response.append(
                        f"Tampil Siham Masalah Nenek : {asalmasalah_nenek}")
                else:
                    if (bagiansaudariknd != "termahjub" and saudari_knd == 1 and saudara_knd == 0 and cucu_pr == 0):
                        if (anak_pr > 0):
                            hitungasalmasalah_nenek = (asalmasalah / 6) * 1
                            asalmasalah_nenek = int(hitungasalmasalah_nenek)
                        else:
                            if (saudari_seayah > 0 or saudara_seayah > 0):
                                hitungasalmasalah_nenek = (asalmasalah / 6) * 1
                                asalmasalah_nenek = int(
                                    hitungasalmasalah_nenek)
                            elif (saudari_seibu > 0 or saudara_seibu > 0):
                                hitungasalmasalah_nenek = (asalmasalah / 6) * 1
                                asalmasalah_nenek = int(
                                    hitungasalmasalah_nenek)
                            else:
                                asalmasalah_nenek = 1
                        if (masuk != "saudari-sibu"):
                            response.append(
                                f"Tampil Siham Masalah Nenek : {asalmasalah_nenek}")
                    else:
                        if (asalmasalah == 4 and bagianIstri == 0.25):
                            asalmasalah_nenek = 1
                        else:
                            hitungasalmasalah_nenek = (asalmasalah / 6) * 1
                            asalmasalah_nenek = int(hitungasalmasalah_nenek)
                        response.append(
                            f"Tampil Siham Masalah Nenek : {asalmasalah_nenek}")
            elif (current_waris['jk_pewaris'] == 'P'):
                if (suami == True and bagiansuami == 0.25 and asalmasalah == 4):
                    asalmasalah_nenek = 1
                    response.append(
                        f"Tampil Siham Masalah Nenek : {asalmasalah_nenek}")
                else:
                    if (suami == False and anak_pr == 0 and anak_lk == 0):
                        asalmasalah_nenek = 1
                        response.append(
                            f"Tampil Siham Masalah Nenek : {asalmasalah_nenek}")
                    else:
                        if (masuk == "saudari-sibu"):
                            hitungasalmasalah_nenek = (6 / 6) * 1
                            asalmasalah_nenek = int(hitungasalmasalah_nenek)
                        else:
                            hitungasalmasalah_nenek = (asalmasalah / 6) * 1
                            asalmasalah_nenek = int(hitungasalmasalah_nenek)
                            response.append(
                                f"Tampil Siham Masalah Nenek : {asalmasalah_nenek}")
    else:
        asalmasalah_nenek = 0

    # asal masalah ayah
    if (ayah == True):
        if (bagianayah == "sisa"):
            if (current_waris['jk_pewaris'] == 'P'):
                if (suami == False):
                    if (ibu == False and nenek > 0):
                        asalmasalah_ayah = 1
                    else:
                        if (nenek == 0 and kakek == False and ibu == False):
                            asalmasalah_ayah = 1
                        else:
                            asalmasalah_ayah = 2
                else:
                    if (suami == True):
                        if (ibu == False and kakek == False and nenek == 0):
                            asalmasalah_ayah = 1
                        else:
                            asalmasalah_ayah = 2
                    else:
                        asalmasalah_ayah = 1
                if (ibu == True and asalmasalah_ayah == 2):
                    response.append(
                        f"Tampil Siham Masalah Ayah : {asalmasalah_ayah}")
                elif (ibu == True and asalmasalah_ayah == 1):
                    response.append(
                        f"Tampil Siham Masalah Ayah : {asalmasalah_ayah}")
            else:
                if (istri == 0):
                    if (ibu == False and nenek > 0):
                        asalmasalah_ayah = 1
                    else:
                        if (nenek == 0 and kakek == False and ibu == False):
                            asalmasalah_ayah = 1
                        else:
                            asalmasalah_ayah = 2
                else:
                    if (istri > 0):
                        if (ibu == False and kakek == False and nenek == 0):
                            asalmasalah_ayah = 1
                        else:
                            asalmasalah_ayah = 2
                    else:
                        asalmasalah_ayah = 1
                if (ibu == True and asalmasalah_ayah == 2):
                    response.append(
                        f"Tampil Siham Masalah Ayah : {asalmasalah_ayah}")
                elif (ibu == True and asalmasalah_ayah == 1):
                    response.append(
                        f"Tampil Siham Masalah Ayah : {asalmasalah_ayah}")
        else:
            hitungasalmasalah_ayah = (asalmasalah / 6) * 1
            asalmasalah_ayah = int(hitungasalmasalah_ayah)
            response.append(f"Tampil Siham Masalah Ayah : {asalmasalah_ayah}")
    else:
        asalmasalah_ayah = 0
    # asal masalah kakek
    if (kakek == True):
        if (bagiankakek == "sisa"):
            if (current_waris['jk_pewaris'] == 'L'):
                if (istri > 0 and ibu == True):
                    asalmasalah_kakek = 2
                    response.append(
                        f"Tampil Siham Masalah Kakek : {asalmasalah_kakek}")
                else:
                    if (istri == 0 and anak_pr == 0 and anak_lk == 0):
                        if (ibu == False and nenek > 0):
                            asalmasalah_kakek = 1
                        else:
                            if (nenek == 0 and ayah == False and ibu == False):
                                asalmasalah_kakek = 1
                            else:
                                asalmasalah_kakek = 2
                    else:
                        if (istri > 0):
                            if (ibu == False and ayah == False and nenek == 0):
                                asalmasalah_kakek = 1
                            else:
                                asalmasalah_kakek = 2
                        else:
                            asalmasalah_kakek = 1
                    if (ibu == True and asalmasalah_ayah == 2):
                        response.append(
                            f"Tampil Siham Masalah Kakek : {asalmasalah_kakek}")
                    elif (ibu == True and asalmasalah_ayah == 1):
                        response.append(
                            f"Tampil Siham Masalah Kakek : {asalmasalah_kakek}")
            elif (current_waris['jk_pewaris'] == 'P'):
                if (suami == True and ibu == True and nenek == 0):
                    asalmasalah_kakek = 2
                    response.append(
                        f"Tampil Siham Masalah Kakek : {asalmasalah_kakek}")
                elif (suami == True and ibu == False and nenek > 0):
                    asalmasalah_kakek = 2
                else:
                    if (suami == False and anak_pr == 0 and anak_lk == 0):
                        if (ibu == False and nenek > 0):
                            asalmasalah_kakek = 1
                        else:
                            if (nenek == 0 and ayah == False and ibu == False):
                                asalmasalah_kakek = 1
                            else:
                                asalmasalah_kakek = 2
                    else:
                        if (suami == True):
                            if (ibu == False and ayah == False and nenek == 0):
                                asalmasalah_kakek = 1
                            else:
                                asalmasalah_kakek = 2
                        else:
                            asalmasalah_kakek = 1
                    response.append(
                        f"Tampil Siham Masalah Kakek : {asalmasalah_kakek}")
        else:
            hitungasalmasalah_kakek = (asalmasalah / 6)*1
            asalmasalah_kakek = int(hitungasalmasalah_kakek)
            response.append(
                f"Tampil Siham Masalah Kakek : {asalmasalah_kakek}")
    else:
        asalmasalah_kakek = 0

    #################################### Hitung Asal Masalah ###################################
    # tanpa anak
    if (data['anak_lk'] == 0 and data['anak_pr'] == 0):
      asalmasalah_anakpr = 0
      asalmasalah_anaklk = 0
      # mengambil nilai asal masalah suami/istri
      if (data['suami'] == True):
        ambil_asalmasalah = asalmasalah_suami
      else:
        ambil_asalmasalah = asalmasalah_istri
      # batas mendapatkan nilai
      # totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_ibu + asalmasalah_nenek + asalmasalah_kakek
      asalmasalah_cucupr = 0
      asalmasalah_cuculk = 0
      asalmasalah_saudara_knd = 0
      asalmasalah_saudari_knd = 0
      asalmasalah_saudara_seayah = 0
      asalmasalah_saudari_seayah = 0
      asalmasalah_saudara_seibu = 0
      asalmasalah_saudari_seibu = 0
      if (data['suami'] == False and data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 1 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seibu'] == 0 and data['saudari_seibu'] == 0):
        asalmasalah_cucupr = 1
      else:
        if (data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
          if (current_waris['jk_pewaris'] == 'L'):
            if (data['cucu_pr'] < 2 and data['cucu_pr'] > 0):
              if (data['kakek'] == False and data['ayah'] == False):
                if (masuk != "cucu1"):
                  # baru
                  if (data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
                    hitungasalmasalah_cucupr = (
                      asalmasalah / 2) * 1
                    asalmasalah_cucupr = int(
                      hitungasalmasalah_cucupr)
                  else:
                    if (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                      hitungasalmasalah_cucupr = (
                        asalmasalah / 2) * 1
                      asalmasalah_cucupr = int(
                        hitungasalmasalah_cucupr)
                    else:
                      hitungasalmasalah_cucupr = (6 / 2) * 1
                      asalmasalah_cucupr = int(
                        hitungasalmasalah_cucupr)
                  response.append(
                    f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
              else:
                hitungasalmasalah_cucupr = (asalmasalah / 2) * 1
                asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                response.append(
                  f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
            else:
              if (data['kakek'] == False and data['ayah'] == False):
                if (masuk != "cucu1"):
                  # baru
                  if (data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
                    hitungasalmasalah_cucupr = (
                      asalmasalah / 3) * 2
                    asalmasalah_cucupr = int(
                      hitungasalmasalah_cucupr)
                  else:
                    if (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                      hitungasalmasalah_cucupr = (
                        asalmasalah / 3) * 2
                      asalmasalah_cucupr = int(
                        hitungasalmasalah_cucupr)
                    else:
                      hitungasalmasalah_cucupr = (6 / 3) * 2
                      asalmasalah_cucupr = int(
                        hitungasalmasalah_cucupr)
                  response.append(
                    f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
              else:
                hitungasalmasalah_cucupr = (asalmasalah / 3) * 2
                asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                response.append(
                  f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
          elif (current_waris['jk_pewaris'] == 'P'):
            if (data['suami'] == True):
              if (asalmasalah == 4):
                if (data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
                  hitungasalmasalah_cucupr = (asalmasalah / 2) * 1
                  asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                  response.append(
                    f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
                else:
                  if (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                    hitungasalmasalah_cucupr = (
                      asalmasalah / 2) * 1
                    asalmasalah_cucupr = int(
                      hitungasalmasalah_cucupr)
                    response.append(
                      f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
                  else:
                    hitungasalmasalah_cucupr = (6 / 2) * 1
                    asalmasalah_cucupr = int(
                      hitungasalmasalah_cucupr)
                    response.append(
                      f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
              else:
                if (data['cucu_pr'] < 2 and data['cucu_pr'] > 0):
                  hitungasalmasalah_cucupr = (asalmasalah / 2) * 1
                  asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                  response.append(
                    f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
                else:
                  hitungasalmasalah_cucupr = (asalmasalah / 3) * 2
                  asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                  response.append(
                    f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
            else:
              if (masuk != "cucu1"):
                if (data['cucu_pr'] < 2 and data['cucu_pr'] > 0):
                  hitungasalmasalah_cucupr = (asalmasalah / 2) * 1
                  asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                  response.append(
                    f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
                else:
                  hitungasalmasalah_cucupr = (asalmasalah / 3) * 2
                  asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                  response.append(
                    f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
        elif (data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
          if (data['anak_pr'] > 0 and data['anak_pr'] < 2):
            asalmasalah_cucupr = (1 * data['cucu_pr'])
          asalmasalah_cuculk = (2 * data['cucu_lk'])
        elif (data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
          if (data['saudara_knd'] == 0):
            # conditional
            # if (masuk == "saudari-sibu"):
            #     hitungasalmasalah_saudari_seibu = (6 / 6) * 1
            #     asalmasalah_saudari_seibu = int(hitungasalmasalah_saudari_seibu)
            if (data['saudari_knd'] == 1):
              if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0 and asalmasalah != 4):
                if (bagiansaudariseayah != "termahjub"):
                  hitungasalmasalah_saudari_seayah = (
                    asalmasalah / 6) * 1
                  asalmasalah_saudari_seayah = int(
                    hitungasalmasalah_saudari_seayah)
                  response.append(
                    f"Tampil Siham Masalah Saudari Seayah : {asalmasalah_saudari_seayah}")
              if (bagiansaudariknd != "termahjub"):
                if (asalmasalah == 4):
                  if (data['ibu'] == False and data['nenek'] == 0):
                    if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
                      hitungasalmasalah_saudari_seayah = (
                        6 / 6) * 1
                      asalmasalah_saudari_seayah = int(
                        hitungasalmasalah_saudari_seayah)
                      hitungasalmasalah_saudari_knd = (6 / 2) * 1
                      asalmasalah_saudari_knd = int(
                        hitungasalmasalah_saudari_knd)
                      response.append(
                        f"Tampil Siham Masalah Saudari Seayah : {asalmasalah_saudari_seayah}")
                    elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0):
                      if(data['saudari_seibu'] > 0 or data['saudara_seibu'] > 0):
                        if (bagiansaudariseibu == 0.16):
                          hitungasalmasalah_saudari_seibu = (6 / 6) * 1
                        else:
                          hitungasalmasalah_saudari_seibu = (6 / 3) * 1
                        if (bagiansaudaraseibu == 0.3):
                          hitungasalmasalah_saudara_seibu = (6 / 3) * 1
                        else:
                          hitungasalmasalah_saudara_seibu = ( 6 / 6) * 1
                        asalmasalah_saudari_seibu = int( hitungasalmasalah_saudari_seibu)
                        asalmasalah_saudara_seibu = int(hitungasalmasalah_saudara_seibu)
                        # saudari kandung
                        if(data['saudari_knd'] == 1):
                          hitungasalmasalah_saudari_knd = (6 / 2) * 1
                          asalmasalah_saudari_knd = int(hitungasalmasalah_saudari_knd)
                        tampil = "ubah"
                      else:
                        asalmasalah_saudari_knd = 1
                    else:
                      hitungasalmasalah_saudari_knd = (
                        asalmasalah / 2) * 1
                      asalmasalah_saudari_knd = int(
                        hitungasalmasalah_saudari_knd)
                      response.append(
                        f"Tampil Siham Masalah Saudari Kandung : {asalmasalah_saudari_knd}")
                  else:
                    hitungasalmasalah_saudari_knd = (6 / 2) * 1
                    asalmasalah_saudari_knd = int(
                      hitungasalmasalah_saudari_knd)
                    response.append(
                      f"Tampil Siham Masalah Saudari Kandung : {asalmasalah_saudari_knd}")
                else:
                  if (masuk != "saudari0"):
                    if (data['saudari_seibu'] > 0 and data['saudara_seibu'] == 0):
                      if (bagiansaudariseibu == 0.16):
                        hitungasalmasalah_saudari_seibu = (
                          asalmasalah / 6) * 1
                      else:
                        hitungasalmasalah_saudari_seibu = (
                          asalmasalah / 3) * 1
                      asalmasalah_saudari_seibu = int(
                        hitungasalmasalah_saudari_seibu)
                      response.append(
                        f"Tampil Siham Masalah Saudari Sibu : {asalmasalah_saudari_seibu}")
                    elif (data['saudari_seibu'] > 0 and saudara_seibu > 0):
                      if (bagiansaudariseibu == 0.16):
                        hitungasalmasalah_saudari_seibu = (
                          asalmasalah / 6) * 1
                      else:
                        hitungasalmasalah_saudari_seibu = (
                          asalmasalah / 3) * 1
                      if (bagiansaudaraseibu == 0.3):
                        hitungasalmasalah_saudara_seibu = (
                          asalmasalah / 3) * 1
                      else:
                        hitungasalmasalah_saudara_seibu = (
                          asalmasalah / 6) * 1
                      asalmasalah_saudari_seibu = int(
                        hitungasalmasalah_saudari_seibu)
                      asalmasalah_saudara_seibu = int(
                        hitungasalmasalah_saudara_seibu)
                      response.append(
                        f"Tampil Siham Masalah Saudari Sibu : {asalmasalah_saudari_seibu}")
                      response.append(
                        f"Tampil Siham Masalah Saudara Sibu : {asalmasalah_saudara_seibu}")
                    elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] > 0):
                      if (bagiansaudaraseibu == 0.3):
                        hitungasalmasalah_saudara_seibu = (
                          asalmasalah / 3) * 1
                      else:
                        hitungasalmasalah_saudara_seibu = (
                          asalmasalah / 6) * 1
                      asalmasalah_saudara_seibu = int(
                        hitungasalmasalah_saudara_seibu)
                      response.append(
                        f"Tampil Siham Masalah Saudara Sibu : {asalmasalah_saudara_seibu}")
                    hitungasalmasalah_saudari_knd = (
                      asalmasalah / 2) * 1
                    asalmasalah_saudari_knd = int(
                      hitungasalmasalah_saudari_knd)
                    response.append(
                      f"Tampil Siham Masalah Saudari Kandung : {asalmasalah_saudari_knd}")
            elif (data['saudari_knd'] > 1):
              if (bagiansaudariknd != "termahjub"):
                # if(asalmasalah == 4):
                #     hitungasalmasalah_saudari_knd = (6 / 2) * 1
                #     asalmasalah_saudari_knd = int(hitungasalmasalah_saudari_knd)
                #     response.append("Tampil Siham Masalah Saudari Kandung : {asalmasalah_saudari_knd}")
                # else:
                if (masuk != "saudari0"):
                  if (data['saudari_seibu'] > 0 and data['saudara_seibu'] == 0):
                    if (bagiansaudariseibu == 0.16):
                      hitungasalmasalah_saudari_seibu = (
                        asalmasalah / 6) * 1
                    else:
                      hitungasalmasalah_saudari_seibu = (
                        asalmasalah / 3) * 1
                    asalmasalah_saudari_seibu = int(
                      hitungasalmasalah_saudari_seibu)
                    response.append(
                      f"Tampil Siham Masalah Saudari Sibu : {asalmasalah_saudari_seibu}")
                  elif (data['saudari_seibu'] > 0 and data['saudara_seibu'] > 0):
                    if (bagiansaudariseibu == 0.16):
                      hitungasalmasalah_saudari_seibu = (
                        asalmasalah / 6) * 1
                    else:
                      hitungasalmasalah_saudari_seibu = (
                        asalmasalah / 3) * 1
                    if (bagiansaudaraseibu == 0.3):
                      hitungasalmasalah_saudara_seibu = (
                        asalmasalah / 3) * 1
                    else:
                      hitungasalmasalah_saudara_seibu = (
                        asalmasalah / 6) * 1
                    asalmasalah_saudari_seibu = int(
                      hitungasalmasalah_saudari_seibu)
                    asalmasalah_saudara_seibu = int(
                      hitungasalmasalah_saudara_seibu)
                    response.append(
                      f"Tampil Siham Masalah Saudari Sibu : {asalmasalah_saudari_seibu}")
                    response.append(
                      f"Tampil Siham Masalah Saudara Sibu : {asalmasalah_saudara_seibu}")
                  elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] > 0):
                    if (bagiansaudaraseibu == 0.3):
                      hitungasalmasalah_saudara_seibu = (
                        asalmasalah / 3) * 1
                    else:
                      hitungasalmasalah_saudara_seibu = (
                        asalmasalah / 6) * 1
                    asalmasalah_saudara_seibu = int(
                      hitungasalmasalah_saudara_seibu)
                    response.append(
                      f"Tampil Siham Masalah Saudara Sibu : {asalmasalah_saudara_seibu}")
                  hitung = "saudari2"
                  hitungasalmasalah_saudari_knd = (
                    asalmasalah / 3) * 2
                  asalmasalah_saudari_knd = int(
                    hitungasalmasalah_saudari_knd)
                  response.append(
                    f"Tampil Siham Masalah Saudari Kandung : {asalmasalah_saudari_knd}")
            else:
              if (data['saudara_seayah'] == 0 and data['saudari_seayah'] == 1):
                if (asalmasalah == 4):
                  if (data['ibu'] == False and data['nenek'] == 0):
                    if(data['saudari_seibu'] > 0 or data['saudara_seibu'] > 0):
                      hitungasalmasalah_saudari_seayah = (6 / 2) * 1
                      asalmasalah_saudari_seayah = int(hitungasalmasalah_saudari_seayah)
                    else:
                      asalmasalah_saudari_seayah = 1
                  else:
                    hitungasalmasalah_saudari_seayah = (6 / 2) * 1
                    asalmasalah_saudari_seayah = int(hitungasalmasalah_saudari_seayah)
                else:
                  hitungasalmasalah_saudari_seayah = (
                    asalmasalah / 2) * 1
                  asalmasalah_saudari_seayah = int(
                    hitungasalmasalah_saudari_seayah)
                  response.append(
                    f"Tampil Siham Masalah Saudari Seayah : {asalmasalah_saudari_seayah}")
              elif (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 1):
                hitungasalmasalah_saudari_seayah = (asalmasalah / 3) * 2
                asalmasalah_saudari_seayah = int(
                  hitungasalmasalah_saudari_seayah)
                response.append(
                  f"Tampil Siham Masalah Saudari Seayah : {asalmasalah_saudari_seayah}")
              if (data['saudari_seibu'] > 0 and data['saudara_seibu'] == 0):
                if (bagiansaudariseibu == 0.16):
                  if(asalmasalah == 4):
                    hitungasalmasalah_saudari_seibu = (6 / 6) * 1
                  elif(asalmasalah == 2):
                    hitungasalmasalah_saudari_seibu = (6 / 6) * 1
                  else:
                    hitungasalmasalah_saudari_seibu = (asalmasalah / 6) * 1
                else:
                  if(asalmasalah == 4):
                    hitungasalmasalah_saudari_seibu = (6 / 3) * 1
                  elif(asalmasalah == 2):
                    hitungasalmasalah_saudari_seibu = (6 / 3) * 1
                  else:
                    hitungasalmasalah_saudari_seibu = (asalmasalah / 3) * 1
                asalmasalah_saudari_seibu = int(hitungasalmasalah_saudari_seibu)
                if(masuk != "saudari-sibu"):
                  if(asalmasalah != 4):
                    response.append(
                      f"Tampil Siham Masalah Saudari Sibu : {asalmasalah_saudari_seibu}")
              elif (data['saudari_seibu'] > 0 and data['saudara_seibu'] > 0):
                if (bagiansaudariseibu == 0.16):
                  if(asalmasalah == 4):
                    hitungasalmasalah_saudari_seibu = (6 / 6) * 1
                  elif(asalmasalah == 2):
                    hitungasalmasalah_saudari_seibu = (6 / 6) * 1
                  else:
                    hitungasalmasalah_saudari_seibu = (asalmasalah / 6) * 1
                else:
                  if(asalmasalah == 4):
                    hitungasalmasalah_saudari_seibu = (6 / 3) * 1
                  elif(asalmasalah == 2):
                    hitungasalmasalah_saudari_seibu = (6 / 3) * 1
                  else:
                    hitungasalmasalah_saudari_seibu = (asalmasalah / 3) * 1
                if (bagiansaudaraseibu == 0.3):
                  if(asalmasalah == 4):
                    hitungasalmasalah_saudara_seibu = (6 / 3) * 1
                  elif(asalmasalah == 2):
                    hitungasalmasalah_saudara_seibu = (6 / 3) * 1
                  else:
                    hitungasalmasalah_saudara_seibu = (asalmasalah / 3) * 1
                else:
                  if(asalmasalah == 4):
                    hitungasalmasalah_saudara_seibu = (6 / 6) * 1
                  elif(asalmasalah == 2):
                    hitungasalmasalah_saudara_seibu = (6 / 6) * 1
                  else:
                    hitungasalmasalah_saudara_seibu = (asalmasalah / 6) * 1
                asalmasalah_saudari_seibu = int(
                  hitungasalmasalah_saudari_seibu)
                asalmasalah_saudara_seibu = int(
                  hitungasalmasalah_saudara_seibu)
                if(masuk != "saudari-sibu"):
                  if(asalmasalah != 4):
                    response.append(
                      f"Tampil Siham Masalah Saudari Sibu : {asalmasalah_saudari_seibu}")
                    response.append(
                      f"Tampil Siham Masalah Saudara Sibu : {asalmasalah_saudara_seibu}")
              elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] > 0):
                if (bagiansaudaraseibu == 0.3):
                  if(asalmasalah == 4):
                    hitungasalmasalah_saudara_seibu = (6 / 3) * 1
                  elif(asalmasalah == 2):
                    hitungasalmasalah_saudara_seibu = (6 / 3) * 1
                  else:
                    hitungasalmasalah_saudara_seibu = (asalmasalah / 3) * 1
                else:
                  if(asalmasalah == 4):
                    hitungasalmasalah_saudara_seibu = (6 / 6) * 1
                  elif(asalmasalah == 2):
                    hitungasalmasalah_saudara_seibu = (6 / 6) * 1
                  else:
                    hitungasalmasalah_saudara_seibu = (asalmasalah / 6) * 1
                asalmasalah_saudara_seibu = int(
                  hitungasalmasalah_saudara_seibu)
                if(masuk != "saudari-sibu"):
                  if(asalmasalah != 4):
                    response.append(
                      f"Tampil Siham Masalah Saudara Sibu : {asalmasalah_saudara_seibu}")
          else:
            if (data['saudari_seibu'] > 0 and data['saudara_seibu'] == 0):
              if (bagiansaudariseibu == 0.16):
                hitungasalmasalah_saudari_seibu = (asalmasalah / 6) * 1
              else:
                hitungasalmasalah_saudari_seibu = (asalmasalah / 3) * 1
              asalmasalah_saudari_seibu = int(
                hitungasalmasalah_saudari_seibu)
              if(masuk != "saudari-sibu"):
                response.append(
                  f"Tampil Siham Masalah Saudari Sibu : {asalmasalah_saudari_seibu}")
            elif (data['saudari_seibu'] > 0 and data['saudara_seibu'] > 0):
              if (bagiansaudariseibu == 0.16):
                hitungasalmasalah_saudari_seibu = (asalmasalah / 6) * 1
              else:
                hitungasalmasalah_saudari_seibu = (asalmasalah / 3) * 1
              if (bagiansaudaraseibu == 0.3):
                hitungasalmasalah_saudara_seibu = (asalmasalah / 3) * 1
              else:
                hitungasalmasalah_saudara_seibu = (asalmasalah / 6) * 1
              asalmasalah_saudari_seibu = int(
                hitungasalmasalah_saudari_seibu)
              asalmasalah_saudara_seibu = int(
                hitungasalmasalah_saudara_seibu)
              if(masuk != "saudari-sibu"):
                response.append(
                  f"Tampil Siham Masalah Saudari Sibu : {asalmasalah_saudari_seibu}")
                response.append(
                  f"Tampil Siham Masalah Saudara Sibu : {asalmasalah_saudara_seibu}")
            elif (data['saudari_seibu'] == 0 and data['saudara_seibu'] > 0):
              if (bagiansaudaraseibu == 0.3):
                hitungasalmasalah_saudara_seibu = (asalmasalah / 3) * 1
              else:
                hitungasalmasalah_saudara_seibu = (asalmasalah / 6) * 1
              asalmasalah_saudara_seibu = int(
                hitungasalmasalah_saudara_seibu)
              if(masuk != "saudari-sibu"):
                response.append(
                  f"Tampil Siham Masalah Saudara Sibu : {asalmasalah_saudara_seibu}")
      if (current_waris['jk_pewaris'] == "L"):
        if (data['istri'] == 0 and data['ibu'] == True):
          if (data['cucu_lk'] > 0):
            totalasalmasalah = ambil_asalmasalah + \
              asalmasalah_ibu + asalmasalah_ayah + asalmasalah_kakek
          else:
            if (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              if (data['cucu_pr'] > 0):
                totalasalmasalah = asalmasalah_ibu + asalmasalah_cucupr
              else:
                masuk = "saudari1"
                totalasalmasalah = asalmasalah_ibu + asalmasalah_cucupr + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              if (data['cucu_pr'] > 0):
                totalasalmasalah = asalmasalah_ibu + asalmasalah_cucupr
              else:
                masuk = "saudari1"
                totalasalmasalah = asalmasalah_ibu + asalmasalah_cucupr + asalmasalah_saudari_seayah
            # tanpa saudara kandung tanpa saudara sayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudara_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
            # saudari kandung, saudari sibu , saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            # saudari sayah, saudari sibu , saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            # saudari knd, saudari sayah, saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            # saudari kandung, saudara sayah, saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            # sauadari kandung, saudara sayah , saudari sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            #saudara sayah , saudari sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            #saudara sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd
            else:
              if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                totalasalmasalah = asalmasalah_ibu + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
              else:
                totalasalmasalah = asalmasalah_ibu + asalmasalah_ayah + asalmasalah_kakek + asalmasalah_cucupr
        elif (data['istri'] == 0 and data['nenek'] > 0):
          if (data['cucu_lk'] > 0):
            totalasalmasalah = asalmasalah_nenek + asalmasalah_ayah + asalmasalah_kakek
          else:
            if (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              if (data['cucu_pr'] > 0):
                totalasalmasalah = asalmasalah_nenek + asalmasalah_cucupr
              else:
                masuk = "saudari1"
                totalasalmasalah = asalmasalah_nenek + \
                  asalmasalah_cucupr + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              if (data['cucu_pr'] > 0):
                totalasalmasalah = asalmasalah_nenek + asalmasalah_cucupr
              else:
                masuk = "saudari1"
                totalasalmasalah = asalmasalah_nenek + \
                  asalmasalah_cucupr + asalmasalah_saudari_seayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd
            # tanpa saudara kandung tanpa saudara sayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudara_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
            # saudari kandung, saudari sibu , saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek+ asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            # saudari sayah, saudari sibu , saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            # saudari knd, saudari sayah, saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            # saudari kandung, saudara sayah, saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            # sauadari kandung, saudara sayah , saudari sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            #saudara sayah , saudari sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            #saudara sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd
            else:
              if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                totalasalmasalah = asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
              else:
                totalasalmasalah = asalmasalah_nenek + asalmasalah_ayah + asalmasalah_kakek + asalmasalah_cucupr
        else:
          # data['ibu']
          if (data['istri'] > 0 and data['ayah'] == False and data['kakek'] == False and data['ibu'] == True and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu
            else:
              if (data['saudara_knd'] == 0 and data['saudari_knd'] > 0):
                if (data['saudari_knd'] == 1):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                  else:
                    if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_knd + \
                          asalmasalah_saudari_seibu + asalmasalah_saudara_seibu + asalmasalah_saudari_seayah
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                          asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                      masuk = "saudari2"
                      hitung = "saudari2"
                    else:
                      if (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                          asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                        masuk = "saudari2"
                        hitung = "saudari2"
                      else:
                        if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                          totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                            asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                        else:
                          totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_knd
                else:
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                  else:
                    if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                        asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                      masuk = "saudari2"
                      hitung = "saudari2"
                    else:
                      masuk = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + \
                        asalmasalah_ibu + asalmasalah_saudari_knd
              elif (data['saudara_knd'] > 0 and data['saudari_knd'] == 0):
                if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                else:
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
              elif (data['saudara_knd'] > 0 and data['saudari_knd'] > 0):
                if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                    asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                else:
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
              else:
                if (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                  else:
                    if (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0):
                      if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                          asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                        masuk = "saudari2"
                      else:
                        totalasalmasalah = ambil_asalmasalah + \
                          asalmasalah_ibu + asalmasalah_saudari_seayah
                        masuk = "saudari2"
                    else:
                      if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu
                else:
                  totalasalmasalah = ambil_asalmasalah
          # data['kakek']
          elif (data['istri'] == 0 and data['ayah'] == False and data['kakek'] == True and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek
            else:
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + asalmasalah_cucupr
          elif (data['istri'] > 0 and data['ayah'] == False and data['kakek'] == True and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek
            else:
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + asalmasalah_cucupr
          # data['ayah']
          elif (data['istri'] == 0 and data['ayah'] == True and data['kakek'] == False and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah
            else:
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_cucupr
          elif (data['istri'] > 0 and data['ayah'] == True and data['kakek'] == False and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah
            else:
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_cucupr
          # data['nenek']
          elif (data['istri'] > 0 and data['ayah'] == False and data['kakek'] == False and data['ibu'] == False and data['nenek'] > 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah
            else:
              if (data['saudara_knd'] > 0 and data['saudari_knd'] > 0):
                if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                else:
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
              elif (data['saudara_knd'] == 0 and data['saudari_knd'] > 1):
                if (data['cucu_pr'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                else:
                  if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                    masuk = "saudari2"
                    hitung = "saudari2"
                  else:
                    masuk = "saudari2"
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek + asalmasalah_saudari_knd
              elif (data['saudara_knd'] > 0 and data['saudari_knd'] == 0):
                if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                else:
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
              elif (data['saudara_knd'] == 0 and data['saudari_knd'] == 1):
                if (data['cucu_pr'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                else:
                  if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                    if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_knd + \
                        asalmasalah_saudari_seibu + asalmasalah_saudara_seibu + asalmasalah_saudari_seayah
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + \
                        asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                    masuk = "saudari2"
                    hitung = "saudari2"
                  else:
                    if (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0):
                      hitung = "saudari2"
                      masuk = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                    elif (data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0):
                      totalasalmasalah = ambil_asalmasalah + \
                        asalmasalah_saudari_knd + asalmasalah_nenek
                      hitung = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah
              else:
                if (data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0):
                  if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                elif (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 1):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                  else:
                    if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                      masuk = "saudari2"
                    else:
                      masuk = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek + asalmasalah_saudari_seayah
                elif (data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0):
                  if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                elif (data['saudara_seayah'] == 0 and data['saudari_seayah'] == 1):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                  else:
                    if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                      masuk = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah
                else:
                  totalasalmasalah = ambil_asalmasalah
          # data['istri']
          elif (data['istri'] > 0 and data['ayah'] == False and data['kakek'] == False and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah
            else:
              if (data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
                if (data['saudari_knd'] == 1 and data['saudara_knd'] == 0):
                  if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
                    if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                      hitung = "saudari2"
                      masuk = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah
                      hitung = "saudari4"
                      tampil = "ubah"
                  elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0):
                    if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      if(asalmasalah == 4):
                        totalasalmasalah = ambil_asalmasalah
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                        masuk = "saudari2"
                        hitung = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr
                  else:
                    if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                      hitung = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                      if(totalasalmasalah > asalmasalah):
                        masuk = "saudari2"
                    else:
                      hitung = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd
                else:
                  if (data['saudara_seayah'] > 0):
                    if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                      hitung = "saudari2"
                      masuk = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd
                  else:
                    if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                      if(data['saudara_knd'] == 0 and data['saudari_knd'] > 1):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu 
                        hitung = "saudari2"
                        masuk = "saudari2"
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu 
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr
              else:
                if (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                  if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                    if(data['saudara_seayah'] == 0):
                      if(saudara_seibu == 1 and data['saudari_seibu'] == 0 and data['saudari_seayah'] == 1):
                        totalasalmasalah = ambil_asalmasalah
                        masuk = "saudari1"
                      elif(saudara_seibu == 0 and data['saudari_seibu'] == 1 and data['saudari_seayah'] == 1):
                        totalasalmasalah = ambil_asalmasalah
                        masuk = "saudari1"
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu 
                        masuk = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu 
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr
                else:
                  if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                    totalasalmasalah = ambil_asalmasalah
                  else:
                    totalasalmasalah = ambil_asalmasalah
          # data['ayah'] dan data['ibu']
          elif (data['istri'] > 0 and data['ayah'] == True and data['kakek'] == False and data['ibu'] == True and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_ibu
            else:
              if (data['cucu_pr'] > 0):
                totalasalmasalah = ambil_asalmasalah + \
                  asalmasalah_ayah + asalmasalah_ibu + asalmasalah_cucupr
              else:
                totalasalmasalah = ambil_asalmasalah
          # data['ayah'] dan data['nenek']
          elif (data['istri'] > 0 and data['ayah'] == True and data['kakek'] == False and data['ibu'] == False and data['nenek'] > 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_nenek
            else:
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + \
                asalmasalah_nenek + asalmasalah_cucupr
          # data['kakek'] dan data['nenek']
          elif (data['istri'] > 0 and data['ayah'] == False and data['kakek'] == True and data['ibu'] == False and data['nenek'] > 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + asalmasalah_nenek
            else:
              if (bagiankakek == "sisa"):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_cucupr
              else:
                totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + \
                  asalmasalah_nenek + asalmasalah_cucupr
          # data['kakek'] dan data['ibu']
          elif (data['istri'] > 0 and data['ayah'] == False and data['kakek'] == True and data['ibu'] == True and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + asalmasalah_ibu
            else:
              totalasalmasalah = ambil_asalmasalah + \
                asalmasalah_kakek + asalmasalah_ibu + asalmasalah_cucupr
          else:
            if (data['cucu_lk'] > 0):
              if (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_cuculk = (1 * data['cucu_lk'])
                response.append("Tampil Siham Masalah Cucu Laki-Laki : 1")
                totalasalmasalah = asalmasalah_cuculk
              elif (data['istri'] == 0 and data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] > 0 and data['cucu_pr'] > 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and saudara_seibu == 0 and saudara_seibu == 0):
                asalmasalah_cucupr = (1 * data['cucu_pr'])
                asalmasalah_cuculk = (2 * data['cucu_lk'])
                response.append("Tampil Siham Masalah Cucu Laki-Laki : 2")
                response.append("Tampil Siham Masalah Cucu Perempuan : 1")
                totalasalmasalah = asalmasalah_cucupr + asalmasalah_cuculk
              else:
                totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek
            else:
              # cucu pr
              if (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_cucupr = (1 * data['cucu_pr'])
                response.append("Tampil Siham Masalah Cucu Perempuan : 1")
                totalasalmasalah = asalmasalah_cucupr
              # saudara dan saudari kandung
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudari_knd = (1 * data['saudari_knd'])
                response.append("Tampil Siham Masalah Saudari Kandung : 1")
                totalasalmasalah = asalmasalah_saudari_knd
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudara_knd = (1 * data['saudara_knd'])
                response.append("Tampil Siham Masalah Saudara Kandung : 1")
                totalasalmasalah = asalmasalah_saudara_knd
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudara_knd = (2 * data['saudara_knd'])
                asalmasalah_saudari_knd = (1 * data['saudari_knd'])
                response.append("Tampil Siham Masalah Saudara Kandung : 2")
                response.append("Tampil Siham Masalah Saudari Kandung : 1")
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_knd
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] >= 0 and data['saudari_seayah'] >= 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                if (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0):
                  totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                  masuk = "saudari5"
                else:
                  totalasalmasalah = asalmasalah_saudari_knd
                  hitung = "saudari2"
              # batas saudara dan saudari kandung
              # saudara dan saudari sayah
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
                response.append("Tampil Siham Masalah Saudari Seayah : 1")
                totalasalmasalah = asalmasalah_saudari_seayah
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudara_seayah = (1 * data['saudara_seayah'])
                response.append("Tampil Siham Masalah Saudara Seayah : 1")
                totalasalmasalah = asalmasalah_saudara_seayah
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudara_seayah = (2 * data['saudara_seayah'])
                asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
                response.append("Tampil Siham Masalah Saudari Seayah : 1")
                response.append("Tampil Siham Masalah Saudara Seayah : 2")
                totalasalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudara_seayah
              # batas saudara dan saudari sayah
              # saudara dan saudari seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] > 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu > 0 and data['saudari_seibu'] == 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu > 0 and data['saudari_seibu'] > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              # saudari kandung, saudari sibu , saudara sibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              # saudara kandung, saudari sibu , saudara sibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              # saudara kandung, saudari kandung, saudari sibu , saudara sibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              # saudari sayah, saudari sibu , saudara sibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              # saudari knd, saudari sayah, saudari sibu, saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
                if(totalasalmasalah < asalmasalah):
                  masuk = "saudari6"
                else:
                  hitung = "saudari2"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
                if(totalasalmasalah < asalmasalah):
                  masuk = "saudari6"
                else:
                  hitung = "saudari2"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                if(totalasalmasalah < asalmasalah):
                  masuk = "saudari6"
                else:
                  hitung = "saudari2"
              # saudari kandung, saudara sayah, saudari sibu, saudara sibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu
                hitung = "saudari2"
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_seibu
                hitung = "saudari2"
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                hitung = "saudari2"
              # saudari kandung, saudara sayah , saudari sayah dan saudari sibu, saudara sibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu
                hitung = "saudari2"
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_seibu
                hitung = "saudari2"
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                hitung = "saudari2"
              #saudara sayah , saudari sayah dan saudari sibu, saudara sibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              #saudara sayah dan saudari sibu, saudara sibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['istri'] == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              else:
                totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_cucupr
      else:
        if (data['suami'] == False and data['ibu'] == True):
          if (data['cucu_lk'] > 0):
            totalasalmasalah = asalmasalah_ibu + asalmasalah_ayah + asalmasalah_kakek
          else:
            if (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              if (data['cucu_pr'] > 0):
                totalasalmasalah = asalmasalah_ibu + asalmasalah_cucupr
              else:
                masuk = "saudari1"
                totalasalmasalah = asalmasalah_ibu + asalmasalah_cucupr + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              if (data['cucu_pr'] > 0):
                totalasalmasalah = asalmasalah_ibu + asalmasalah_cucupr
              else:
                masuk = "saudari1"
                totalasalmasalah = asalmasalah_ibu + asalmasalah_cucupr + asalmasalah_saudari_seayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudara_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
            # saudari kandung, saudari sibu , saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            # saudari sayah, saudari sibu , saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            # saudari knd, saudari sayah, saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            # saudari kandung, saudara sayah, saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            # sauadari kandung, saudara sayah , saudari sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            #saudara sayah , saudari sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            #saudara sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            else:
              if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                totalasalmasalah = asalmasalah_ibu + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
              else:
                totalasalmasalah = asalmasalah_ibu + asalmasalah_ayah + asalmasalah_kakek + asalmasalah_cucupr
        elif (data['suami'] == False and data['nenek'] > 0):
          if (data['cucu_lk'] > 0):
            totalasalmasalah = asalmasalah_nenek + asalmasalah_ayah + asalmasalah_kakek
          else:
            if (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              if (data['cucu_pr'] > 0):
                totalasalmasalah = asalmasalah_nenek + asalmasalah_cucupr
              else:
                masuk = "saudari1"
                totalasalmasalah = asalmasalah_nenek + \
                  asalmasalah_cucupr + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              if (data['cucu_pr'] > 0):
                totalasalmasalah = asalmasalah_nenek + asalmasalah_cucupr
              else:
                masuk = "saudari1"
                totalasalmasalah = asalmasalah_nenek + \
                  asalmasalah_cucupr + asalmasalah_saudari_seayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + \
                asalmasalah_saudari_knd + asalmasalah_saudari_seayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd
            # tanpa saudara kandung tanpa saudara sayah
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudara_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu == 0):
              masuk = "saudari1"
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
            # saudari kandung, saudari sibu , saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek+ asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            # saudari sayah, saudari sibu , saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
              elif(totalasalmasalah < asalmasalah):
                masuk = "saudari1"
            # saudari knd, saudari sayah, saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            # saudari kandung, saudara sayah, saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            # sauadari kandung, saudara sayah , saudari sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            #saudara sayah , saudari sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            #saudara sayah dan saudari sibu, saudara sibu
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            elif (data['ayah'] == False and data['kakek'] == False and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
              totalasalmasalah = asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              if(totalasalmasalah > asalmasalah):
                hitung = "saudari2"
                masuk = "saudari2"
            else:
              if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                totalasalmasalah = asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
              else:
                totalasalmasalah = asalmasalah_nenek + asalmasalah_ayah + asalmasalah_kakek + asalmasalah_cucupr
        else:
          if (data['suami'] == False and data['ayah'] == False and data['kakek'] == True and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = asalmasalah_kakek
            else:
              totalasalmasalah = asalmasalah_kakek + asalmasalah_cucupr
          elif (data['suami'] == True and data['ayah'] == False and data['kakek'] == True and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek
            else:
              if (bagiankakek == "sisa"):
                totalasalmasalah = ambil_asalmasalah
              else:
                totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + asalmasalah_cucupr
          # data['suami']
          elif (data['suami'] == True and data['ayah'] == False and data['kakek'] == False and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah
            else:
              if (data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
                if (data['saudara_knd'] > 0):
                  if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr
                else:
                  if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0 and data['saudari_knd'] == 1):
                    if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                      masuk = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                    hitung = "saudari2"
                  else:
                    if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_knd + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                      hitung = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_saudari_knd
                  masuk = "saudari2"
              else:
                if (data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
                  if (data['saudara_seayah'] > 0):
                    if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr
                  else:
                    if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                      masuk = "saudari2"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_saudari_seayah
                      masuk = "saudari2"
                else:
                  totalasalmasalah = ambil_asalmasalah
          # data['ibu']
          elif (data['suami'] == True and data['ayah'] == False and data['kakek'] == False and data['ibu'] == True and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu
            else:
              if (data['saudara_knd'] == 0 and data['saudari_knd'] > 0):
                if (data['saudari_knd'] == 1):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                  else:
                    if (data['saudari_seayah'] > 0 and data['saudara_seayah'] == 0):
                      if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                        asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                          asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                      masuk = "saudari2"
                      hitung = "saudari2"
                    elif (data['saudari_seayah'] == 0 and data['saudara_seayah'] > 0):
                      if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                        masuk = "saudari2"
                        hitung = "saudari2"
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_knd
                        masuk = "saudari2"
                    else:
                      if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu 
                        hitung = "saudari2"
                        masuk = "saudari2"
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_knd
                else:
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                  else:
                    if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      masuk = "saudari2"
                      hitung = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                    else:
                      masuk = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu + asalmasalah_saudari_knd
              elif (data['saudara_knd'] > 0 and data['saudari_knd'] == 0):
                if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                else:
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
              elif (data['saudara_knd'] > 0 and data['saudari_knd'] > 0):
                if (data['saudari_seibu'] > 0 or saudara_seibu > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                else:
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
              else:
                if (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0):
                  if (data['saudari_seayah'] == 1):
                    if (data['cucu_pr'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                    else:
                      if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                        masuk = "saudari2"
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seayah
                  else:
                    if (data['cucu_pr'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                    else:
                      if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                        masuk = "saudari2"
                      else:
                        masuk = "saudari2"
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + \
                          asalmasalah_ibu + asalmasalah_saudari_seayah
                elif (data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0):
                  if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                elif (data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0):
                  if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_ibu
                else:
                  if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                    masuk = "saudari2"
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                  else:
                    if(data['cucu_pr'] > 0):
                      if(data['cucu_pr'] == 1):
                        totalasalmasalah = ambil_asalmasalah
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_cucupr
                    else:
                      totalasalmasalah = ambil_asalmasalah
          elif (data['suami'] == False and data['ayah'] == True and data['kakek'] == False and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = asalmasalah_ayah
            else:
              totalasalmasalah = asalmasalah_ayah + asalmasalah_cucupr
          elif (data['suami'] == True and data['ayah'] == True and data['kakek'] == False and data['ibu'] == False and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah
            else:
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_cucupr
          elif (data['suami'] == True and data['ayah'] == False and data['kakek'] == False and data['ibu'] == False and data['nenek'] > 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek
            else:
              if (data['saudara_knd'] > 0 and data['saudari_knd'] > 0):
                if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                else:
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
              elif (data['saudara_knd'] == 0 and data['saudari_knd'] > 0):
                if (data['cucu_pr'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                else:
                  if (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0):
                    if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                      masuk = "saudari2"
                      hitung = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                    else:
                      masuk = "saudari2"
                      hitung = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                  else:
                    if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                      masuk = "saudari2"
                      hitung = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                    else:
                      masuk = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_knd
              elif (data['saudara_knd'] > 0 and data['saudari_knd'] == 0):
                if(saudara_seibu > 0 or data['saudari_seibu'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                else:
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
              else:
                # sayah
                if (data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0):
                  if(data['saudari_seibu'] > 0 or saudara_seibu > 0) : 
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                elif (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                  else:
                    if(data['saudari_seibu'] > 0 or saudara_seibu > 0) : 
                      masuk = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                    else:
                      masuk = "saudari2"
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek + asalmasalah_saudari_seayah
                elif (data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0):
                  if(data['saudari_seibu'] > 0 or saudara_seibu > 0) : 
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_nenek
                else:
                  if (data['cucu_pr'] == 1):
                    totalasalmasalah = ambil_asalmasalah
                  elif (data['cucu_pr'] == 0):
                    if(data['saudari_seibu'] > 0 or saudara_seibu > 0):
                      if(data['saudari_seibu'] == 1 and saudara_seibu == 0):
                        totalasalmasalah = ambil_asalmasalah
                      elif(data['saudari_seibu'] == 0 and saudara_seibu == 1):
                        totalasalmasalah = ambil_asalmasalah
                      else:
                        totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_cucupr
          elif (data['suami'] == True and data['ayah'] == True and data['kakek'] == False and data['ibu'] == True and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_ibu
            else:
              if (data['cucu_pr'] > 0):
                totalasalmasalah = ambil_asalmasalah + \
                  asalmasalah_ayah + asalmasalah_ibu + asalmasalah_cucupr
              else:
                totalasalmasalah = ambil_asalmasalah
          elif (data['suami'] == True and data['ayah'] == False and data['kakek'] == True and data['ibu'] == True and data['nenek'] == 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + asalmasalah_ibu
            else:
              if (data['cucu_pr'] > 0):
                totalasalmasalah = ambil_asalmasalah + \
                  asalmasalah_kakek + asalmasalah_ibu + asalmasalah_cucupr
              else:
                totalasalmasalah = ambil_asalmasalah
          # data['ayah'] dan data['nenek']
          elif (data['suami'] == True and data['ayah'] == True and data['kakek'] == False and data['ibu'] == False and data['nenek'] > 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_nenek
            else:
              if (data['cucu_pr'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + \
                  asalmasalah_nenek + asalmasalah_cucupr
              else:
                if (bagianayah == "sisa"):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek
                else:
                  totalasalmasalah = ambil_asalmasalah
          # data['kakek'] dan data['nenek']
          elif (data['suami'] == True and data['ayah'] == False and data['kakek'] == True and data['ibu'] == False and data['nenek'] > 0):
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + asalmasalah_nenek
            else:
              if (data['cucu_pr'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_kakek + \
                  asalmasalah_nenek + asalmasalah_cucupr
              else:
                if (bagiankakek == "sisa"):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek
                else:
                  totalasalmasalah = ambil_asalmasalah
          else:
            if (data['cucu_lk'] > 0):
              if (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] > 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_cuculk = (1 * data['cucu_lk'])
                response.append("Tampil Siham Masalah Cucu Laki-Laki : 1")
                totalasalmasalah = asalmasalah_cuculk
              elif (data['istri'] == False and data['kakek'] == False and data['nenek'] == 0 and data['ayah'] == False and data['ibu'] == False and data['anak_pr'] == 0 and data['anak_lk'] == 0 and data['cucu_lk'] > 0 and data['cucu_pr'] > 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudari_seayah'] == 0 and data['saudara_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_cucupr = (1 * data['cucu_pr'])
                asalmasalah_cuculk = (2 * data['cucu_lk'])
                response.append("Tampil Siham Masalah Cucu Laki-Laki : 2")
                response.append("Tampil Siham Masalah Cucu Perempuan : 1")
                totalasalmasalah = asalmasalah_cucupr + asalmasalah_cuculk
              else:
                totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek
            else:
              # cucupr
              if (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] > 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_cucupr = (1 * data['cucu_pr'])
                response.append("Tampil Siham Masalah Cucu Perempuan : 1")
                totalasalmasalah = asalmasalah_cucupr
              # saudara dan saudari kandung
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudari_knd = (1 * data['saudari_knd'])
                response.append("Tampil Siham Masalah Saudari Kandung : 1")
                totalasalmasalah = asalmasalah_saudari_knd
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudara_knd = (1 * data['saudara_knd'])
                response.append("Tampil Siham Masalah Saudara Kandung : 1")
                totalasalmasalah = asalmasalah_saudara_knd
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudara_knd = (2 * data['saudara_knd'])
                asalmasalah_saudari_knd = (1 * data['saudari_knd'])
                response.append("Tampil Siham Masalah Saudara Kandung : 2")
                response.append("Tampil Siham Masalah Saudari Kandung : 1")
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_knd
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] >= 0 and data['saudari_seayah'] >= 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                if (data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0):
                  totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                  masuk = "saudari5"
                else:
                  totalasalmasalah = asalmasalah_saudari_knd
                  hitung = "saudari2"
              # batas saudara dan saudari kandung
              # saudara dan saudari sayah
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
                response.append("Tampil Siham Masalah Saudari Seayah : 1")
                totalasalmasalah = asalmasalah_saudari_seayah
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudara_seayah = (1 * data['saudara_seayah'])
                response.append("Tampil Siham Masalah Saudara Seayah : 1")
                totalasalmasalah = asalmasalah_saudara_seayah
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and saudara_seibu == 0 and data['saudari_seibu'] == 0):
                asalmasalah_saudara_seayah = (2 * data['saudara_seayah'])
                asalmasalah_saudari_seayah = (1 * data['saudari_seayah'])
                response.append("Tampil Siham Masalah Saudara Seayah : 2")
                response.append("Tampil Siham Masalah Saudari Seayah : 1")
                totalasalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudara_seayah
              # batas saudara dan saudari sayah
              # saudara dan saudari seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu == 0 and data['saudari_seibu'] > 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu > 0 and data['saudari_seibu'] == 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and saudara_seibu > 0 and data['saudari_seibu'] > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              # batas saudara dan saudari sibu
              # saudari kandung, saudari sibu , saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              # saudara kandung, saudari sibu , saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              # saudara kandung, saudari kandung, saudari sibu , saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              # saudari sayah, saudari sibu , saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                if(totalasalmasalah > asalmasalah):
                  hitung = "saudari2"
                  masuk = "saudari2"
                elif(totalasalmasalah < asalmasalah):
                  masuk = "saudari1"
              # saudari knd, saudari sayah, saudari sibu, saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
                if(totalasalmasalah < asalmasalah):
                  masuk = "saudari6"
                else:
                  hitung = "saudari2"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
                if(totalasalmasalah < asalmasalah):
                  masuk = "saudari6"
                else:
                  hitung = "saudari2"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] == 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                if(totalasalmasalah < asalmasalah):
                  masuk = "saudari6"
                else:
                  hitung = "saudari2"
              # saudari kandung, saudara sayah, saudari sibu, saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu
                hitung = "saudari2"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_seibu
                hitung = "saudari2"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                hitung = "saudari2"
              # saudari kandung, saudara sayah , saudari sayah dan saudari sibu, saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu
                hitung = "saudari2"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudara_seibu
                hitung = "saudari2"
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] > 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                hitung = "saudari2"
              #saudara sayah , saudari sayah dan saudari sibu, saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] > 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              #saudara sayah dan saudari sibu, saudara sibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu == 0):
                totalasalmasalah = asalmasalah_saudari_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] == 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudara_seibu
              elif (data['suami'] == False and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0 and data['anak_lk'] == 0 and data['anak_pr'] == 0 and data['cucu_pr'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] == 0 and data['saudari_knd'] == 0 and data['saudara_seayah'] > 0 and data['saudari_seayah'] == 0 and data['saudari_seibu'] > 0 and saudara_seibu > 0):
                totalasalmasalah = asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
              #sibu baru 
              else:
                totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_cucupr
      sisa = asalmasalah - totalasalmasalah
      if (current_waris['jk_pewaris'] == "L"):
        if (asalmasalah_cucupr == 16):
          if (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['saudara_knd'] > 0 or data['saudari_knd'] > 0):
            jumlahasalmasalah = asalmasalah
          else:
            if (data['ayah'] == False and data['kakek'] == False and data['anak_lk'] == 0 and data['cucu_lk'] == 0 and data['saudara_seayah'] > 0 or data['saudari_seayah'] > 0):
              jumlahasalmasalah = asalmasalah
            else:
              jumlahasalmasalah = totalasalmasalah
        else:
          if (data['ayah'] == False and data['kakek'] == False):
            if (data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
              if (data['saudari_knd'] > 0):
                jumlahasalmasalah = asalmasalah
              else:
                if (data['saudara_knd'] > 0):
                  jumlahasalmasalah = asalmasalah
                else:
                  if (data['saudari_seayah'] > 0):
                    jumlahasalmasalah = asalmasalah
                  else:
                    if (data['saudara_seayah'] > 0):
                      jumlahasalmasalah = asalmasalah
                    else:
                      jumlahasalmasalah = totalasalmasalah
            elif (data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
              if (masuk == "saudari2"):
                jumlahasalmasalah = totalasalmasalah
              else:
                if (bagianibu == 0.33 and bagiansisaibu == ""):
                  if (data['saudara_knd'] == 0):
                    if (data['istri'] > 0):
                      if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                        jumlahasalmasalah = asalmasalah
                      else:
                        jumlahasalmasalah = totalasalmasalah
                    else:
                      jumlahasalmasalah = asalmasalah
                  else:
                    jumlahasalmasalah = asalmasalah
                else:
                  if (masuk == "saudari-sibu"):
                    jumlahasalmasalah = totalasalmasalah
                  else:
                    jumlahasalmasalah = asalmasalah
            else:
              jumlahasalmasalah = asalmasalah
          else:
            jumlahasalmasalah = asalmasalah
      else:
        if (asalmasalah_cucupr == 16):
          jumlahasalmasalah = totalasalmasalah
        else:
          if (data['ayah'] == False and data['kakek'] == False):
            if (data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
              if (data['saudari_knd'] > 0):
                if (totalasalmasalah > asalmasalah):
                  jumlahasalmasalah = totalasalmasalah
                else:
                  jumlahasalmasalah = asalmasalah
              else:
                if (data['saudara_knd'] > 0):
                  if (totalasalmasalah > asalmasalah):
                    jumlahasalmasalah = totalasalmasalah
                  else:
                    jumlahasalmasalah = asalmasalah
                else:
                  if (data['saudari_seayah'] > 0):
                    if (totalasalmasalah > asalmasalah):
                      jumlahasalmasalah = totalasalmasalah
                    else:
                      jumlahasalmasalah = asalmasalah
                  else:
                    if (data['saudara_seayah'] > 0):
                      if (totalasalmasalah > asalmasalah):
                        jumlahasalmasalah = totalasalmasalah
                      else:
                        jumlahasalmasalah = asalmasalah
                    else:
                      jumlahasalmasalah = totalasalmasalah
            elif (data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
              if (masuk == "saudari2"):
                jumlahasalmasalah = totalasalmasalah
              else:
                if (bagianibu == 0.33 and bagiansisaibu == ""):
                  if (data['saudara_knd'] == 0):
                    if (data['suami'] == True):
                      if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                        jumlahasalmasalah = asalmasalah
                      else:
                        jumlahasalmasalah = totalasalmasalah
                    else:
                      jumlahasalmasalah = asalmasalah
                  else:
                    jumlahasalmasalah = asalmasalah
                else:
                  if (masuk == "saudari-sibu"):
                    jumlahasalmasalah = totalasalmasalah
                  else:
                    jumlahasalmasalah = asalmasalah
            else:
              jumlahasalmasalah = asalmasalah
          else:
            if (data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
              jumlahasalmasalah = totalasalmasalah
            else:
              jumlahasalmasalah = asalmasalah
    elif (data['anak_pr'] > 0 and data['anak_lk'] == 0):
      # asal masalah anak perempuan lebih dari 1 dan tanpa anak laki-laki
      if (data['anak_pr'] > 1 and data['anak_lk'] == 0):
        if (current_waris['jk_pewaris'] == "L"):
          if (data['ayah'] == False and data['kakek'] == False and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              hitungasalmasalah_anakpr = (asalmasalah / 3) * 2
              asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 3) * 2
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                hitungasalmasalah_anakpr = (6 / 3) * 2
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          else:
            hitungasalmasalah_anakpr = (asalmasalah / 3) * 2
            asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          if(masuk2 == "anakpr" ):
            response.append("Tampil Siham Masalah Anak Perempuan : 1")
          else:
            if(masuk == "anakprk1"):
              asalmasalah_anakpr = 2
              response.append(f"Tampil Siham Masalah Anak Perempuan : {asalmasalah_anakpr}")
            else:
              response.append(f"Tampil Siham Masalah Anak Perempuan : {asalmasalah_anakpr}")
        elif (current_waris['jk_pewaris'] == "P"):
          if (data['ayah'] == False and data['kakek'] == False and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
            if (data['ibu'] == True):
              hitungasalmasalah_anakpr = (asalmasalah / 3) * 2
              asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            elif (data['nenek'] > 0):
              hitungasalmasalah_anakpr = (asalmasalah / 3) * 2
              asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 3) * 2
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 3) * 2
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (6 / 3) * 2
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          else:
            hitungasalmasalah_anakpr = (asalmasalah / 3) * 2
            asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          if(masuk2 == "anakpr" ):
            response.append("Tampil Siham Masalah Anak Perempuan : 1")
          else:
            if(masuk == "anakprk1"):
              asalmasalah_anakpr = 2
              response.append(f"Tampil Siham Masalah Anak Perempuan : {asalmasalah_anakpr}")
            else:
              response.append(f"Tampil Siham Masalah Anak Perempuan : {asalmasalah_anakpr}")
      elif (data['anak_pr'] == 1 and data['anak_lk'] == 0):
        if (current_waris['jk_pewaris'] == "L"):
          if (data['ayah'] == False and data['ibu'] == True and data['kakek'] == False and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
              asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                hitungasalmasalah_anakpr = (6 / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          elif (data['ibu'] == False and data['ayah'] == False and data['kakek'] == False and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
            if (data['nenek'] > 0):
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (6 / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (2 / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          elif (data['ibu'] == False and data['ayah'] == False and data['kakek'] == False and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
            if (data['nenek'] > 0):
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (6 / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (6 / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          elif (data['ibu'] == True and data['ayah'] == False and data['kakek'] == False and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
              asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                hitungasalmasalah_anakpr = (6 / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          else:
            hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
            asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          if(masuk2 == "anakpr" ):
            response.append("Tampil Siham Masalah Anak Perempuan : 1")
          else:
            response.append(f"Tampil Siham Masalah Anak Perempuan : {asalmasalah_anakpr}")
        elif (current_waris['jk_pewaris'] == "P"):
          if (data['ayah'] == False and data['ibu'] == True and data['kakek'] == False and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
            if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
              hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
              asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                hitungasalmasalah_anakpr = (6 / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          elif (data['ibu'] == False and data['ayah'] == False and data['kakek'] == False and data['cucu_pr'] == 0 and data['cucu_lk'] == 0):
            if (data['nenek'] > 0):
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (6 / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (2 / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          elif (data['ibu'] == False and data['ayah'] == False and data['kakek'] == False and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
            if (data['nenek'] > 0):
              if (data['suami'] == True):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                    hitungasalmasalah_anakpr = (
                      asalmasalah / 2) * 1
                    asalmasalah_anakpr = int(
                      hitungasalmasalah_anakpr)
                  else:
                    hitungasalmasalah_anakpr = (6 / 2) * 1
                    asalmasalah_anakpr = int(
                      hitungasalmasalah_anakpr)
            else:
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (6 / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          elif (data['ibu'] == True and data['ayah'] == False and data['kakek'] == False and data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
            if (data['suami'] == True):
              hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
              asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
            else:
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
              else:
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
                else:
                  hitungasalmasalah_anakpr = (6 / 2) * 1
                  asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          else:
            hitungasalmasalah_anakpr = (asalmasalah / 2) * 1
            asalmasalah_anakpr = int(hitungasalmasalah_anakpr)
          response.append(
            f"Tampil Siham Masalah Anak Perempuan : {asalmasalah_anakpr}")
      elif (data['anak_pr'] == 0):
        asalmasalah_anakpr = 0
      # pemabagian siham cucu lk and cucu perempuan
      asalmasalah_cucupr = 0
      asalmasalah_cuculk = 0
      if (data['cucu_pr'] > 0 and data['cucu_lk'] == 0):
        if (data['anak_pr'] > 0 and data['anak_pr'] < 2):
          if (current_waris['jk_pewaris'] == "L"):
            hitungasalmasalah_cucupr = (asalmasalah / 6) * 1
            asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
            response.append(
              f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
          elif (current_waris['jk_pewaris'] == "P"):
            if (data['suami'] == True):
              if (asalmasalah == 4):
                hitungasalmasalah_cucupr = (6 / 6) * 1
                asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                response.append(
                  f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
              else:
                hitungasalmasalah_cucupr = (asalmasalah / 6) * 1
                asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
                response.append(
                  f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
            else:
              hitungasalmasalah_cucupr = (asalmasalah / 6) * 1
              asalmasalah_cucupr = int(hitungasalmasalah_cucupr)
              response.append(
                f"Tampil Siham Masalah Cucu Perempuan : {asalmasalah_cucupr}")
      elif (data['cucu_pr'] > 0 and data['cucu_lk'] > 0):
        if (data['anak_pr'] > 0 and data['anak_pr'] < 2):
          asalmasalah_cucupr = (1 * data['cucu_pr'])
        else:
          asalmasalah_cucupr = 0
        asalmasalah_cuculk = (2 * data['cucu_lk'])
      # totalasalmasalah dengan anak perempuan tanpa anak lk
      # mengambil nilai asal masalah data['suami']/data['istri']
      if (data['suami'] == True):
        ambil_asalmasalah = asalmasalah_suami
      else:
        ambil_asalmasalah = asalmasalah_istri
      if (data['ayah'] == False and data['kakek'] == False):
        if (current_waris['jk_pewaris'] == "P"):
          if (data['ibu'] == True and data['nenek'] == 0):
            if (data['anak_pr'] > 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                  asalmasalah_anakpr + asalmasalah_cucupr
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr
                  masuk = "saudari3"
                elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr
                  masuk = "saudari3"
                else:
                  if (data['suami'] == True):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr + asalmasalah_ibu
                  else:
                    totalasalmasalah = asalmasalah_ibu + asalmasalah_anakpr
            elif (data['anak_pr'] == 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                  asalmasalah_nenek + asalmasalah_anakpr
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                      asalmasalah_anakpr + asalmasalah_cucupr
                    if (data['suami'] == False):
                      masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr
                    masuk = "saudari3"
                elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                      asalmasalah_anakpr + asalmasalah_cucupr
                    if (data['suami'] == False):
                      masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr
                    masuk = "saudari3"
                else:
                  if (data['suami'] == True):
                    if (data['cucu_pr'] > 0):
                      totalasalmasalah = ambil_asalmasalah + \
                        asalmasalah_anakpr + asalmasalah_cucupr + asalmasalah_ibu
                    else:
                      totalasalmasalah = ambil_asalmasalah
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                      asalmasalah_anakpr + asalmasalah_cucupr
            else:
              totalasalmasalah = ambil_asalmasalah
          elif (data['ibu'] == False and data['nenek'] > 0):
            if (data['anak_pr'] > 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr + \
                  asalmasalah_nenek + asalmasalah_cucupr
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
                  masuk = "saudari3"
                elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
                  masuk = "saudari3"
                else:
                  if (data['suami'] == True):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr + asalmasalah_nenek
                  else:
                    totalasalmasalah = asalmasalah_nenek + asalmasalah_anakpr
            elif (data['anak_pr'] == 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                  asalmasalah_nenek + asalmasalah_anakpr
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + \
                      asalmasalah_anakpr + asalmasalah_cucupr
                    if (data['suami'] == False):
                      masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
                    masuk = "saudari3"
                elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + \
                      asalmasalah_anakpr + asalmasalah_cucupr
                    if (data['suami'] == False):
                      masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
                    masuk = "saudari3"
                else:
                  if (data['suami'] == True):
                    if (data['cucu_pr'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr + \
                        asalmasalah_cucupr + asalmasalah_nenek
                    else:
                      totalasalmasalah = ambil_asalmasalah
                  else:
                    totalasalmasalah = asalmasalah_nenek + asalmasalah_anakpr + asalmasalah_cucupr
                # if(data['suami'] == True):
                #     if(data['cucu_pr'] > 0):
                #         totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr + asalmasalah_cucupr + asalmasalah_nenek
                #     else:
                #         totalasalmasalah = ambil_asalmasalah
                # else :
                #     totalasalmasalah = asalmasalah_anakpr + asalmasalah_nenek + asalmasalah_cucupr
                  # totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_nenek + asalmasalah_anakpr + asalmasalah_cucupr
            else:
              totalasalmasalah = ambil_asalmasalah
          elif (data['ibu'] == False and data['nenek'] == 0):
            if (data['anak_pr'] > 1):
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                masuk = "saudari3"
              elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                masuk = "saudari3"
              else:
                if (data['cucu_lk'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                else:
                  totalasalmasalah = ambil_asalmasalah
            elif (data['anak_pr'] == 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
              else:
                if (data['suami'] == 'y'):
                  if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                    if (data['cucu_pr'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_anakpr
                      masuk = "saudari3"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                      masuk = "saudari3"
                  elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                    if (data['cucu_pr'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_anakpr
                      masuk = "saudari3"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                      masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah
                else:
                  totalasalmasalah = asalmasalah_anakpr + asalmasalah_cucupr
            else:
              totalasalmasalah = ambil_asalmasalah
          else:
            # menghilangkan hitung asalmasalah cucu perempuan ketika ada cucu laki-laki
            # bagian cucu perempuan dipindakhkan ke bagian sisa
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_ibu + \
                asalmasalah_anakpr + asalmasalah_nenek + asalmasalah_kakek
            else:
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_ibu + \
                asalmasalah_anakpr + asalmasalah_nenek + asalmasalah_kakek + asalmasalah_cucupr
        elif (current_waris['jk_pewaris'] == "L"):
          if (data['ibu'] == True and data['nenek'] == 0):
            if (data['anak_pr'] > 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_ibu + \
                  asalmasalah_anakpr + asalmasalah_nenek + asalmasalah_kakek + asalmasalah_cucupr
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr
                  masuk = "saudari3"
                elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr
                  masuk = "saudari3"
                else:
                  if (data['istri'] > 0):
                    totalasalmasalah = ambil_asalmasalah
                  else:
                    totalasalmasalah = asalmasalah_ibu + asalmasalah_anakpr
            elif (data['anak_pr'] == 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                  asalmasalah_nenek + asalmasalah_anakpr
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                      asalmasalah_anakpr + asalmasalah_cucupr
                    masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr
                    masuk = "saudari3"
                elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + \
                      asalmasalah_anakpr + asalmasalah_cucupr
                    masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr
                    masuk = "saudari3"
                else:
                  if (data['istri'] > 0):
                    totalasalmasalah = ambil_asalmasalah
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_ibu + asalmasalah_anakpr + asalmasalah_cucupr
            else:
              totalasalmasalah = ambil_asalmasalah
          elif (data['ibu'] == False and data['nenek'] > 0):
            if (data['anak_pr'] > 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_anakpr + \
                  asalmasalah_nenek + asalmasalah_kakek + asalmasalah_cucupr
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
                  masuk = "saudari3"
                if (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
                  masuk = "saudari3"
                else:
                  if (data['istri'] > 0):
                    totalasalmasalah = ambil_asalmasalah
                  else:
                    totalasalmasalah = asalmasalah_nenek + asalmasalah_anakpr
            elif (data['anak_pr'] == 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
              else:
                if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + \
                      asalmasalah_anakpr + asalmasalah_cucupr
                    masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
                    masuk = "saudari3"
                elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                  if (data['cucu_pr'] > 0):
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + \
                      asalmasalah_anakpr + asalmasalah_cucupr
                    masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah + asalmasalah_nenek + asalmasalah_anakpr
                    masuk = "saudari3"
                else:
                  if (data['istri'] > 0):
                    totalasalmasalah = ambil_asalmasalah
                  else:
                    totalasalmasalah = asalmasalah_nenek + asalmasalah_anakpr + asalmasalah_cucupr
            else:
              totalasalmasalah = ambil_asalmasalah
          elif (data['ibu'] == False and data['nenek'] == 0):
            if (data['anak_pr'] > 1):
              if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                masuk = "saudari3"
              elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                masuk = "saudari3"
              else:
                totalasalmasalah = ambil_asalmasalah
            elif (data['anak_pr'] == 1):
              if (data['cucu_lk'] > 0):
                totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
              else:
                if (data['istri'] > 0):
                  if (data['saudari_knd'] > 0 or data['saudara_knd'] > 0):
                    if (data['cucu_pr'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_anakpr
                      masuk = "saudari3"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                      masuk = "saudari3"
                  elif (data['saudari_seayah'] > 0 or data['saudara_seayah'] > 0):
                    if (data['cucu_pr'] > 0):
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_cucupr + asalmasalah_anakpr
                      masuk = "saudari3"
                    else:
                      totalasalmasalah = ambil_asalmasalah + asalmasalah_anakpr
                      masuk = "saudari3"
                  else:
                    totalasalmasalah = ambil_asalmasalah
                else:
                  totalasalmasalah = asalmasalah_anakpr + asalmasalah_cucupr
            else:
              totalasalmasalah = ambil_asalmasalah
          else:
            # menghilangkan hitung asalmasalah cucu perempuan ketika ada cucu laki-laki
            # bagian cucu perempuan dipindakhkan ke bagian sisa
            if (data['cucu_lk'] > 0):
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_ibu + \
                asalmasalah_anakpr + asalmasalah_nenek + asalmasalah_kakek
            else:
              totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + asalmasalah_ibu + \
                asalmasalah_anakpr + asalmasalah_nenek + asalmasalah_kakek + asalmasalah_cucupr
      else:
        if (data['cucu_lk'] > 0):
          totalasalmasalah = ambil_asalmasalah + \
            asalmasalah_ayah + asalmasalah_ibu + asalmasalah_anakpr + \
            asalmasalah_nenek + asalmasalah_kakek
        else:
          totalasalmasalah = ambil_asalmasalah + \
            asalmasalah_ayah + asalmasalah_ibu + asalmasalah_anakpr + \
            asalmasalah_nenek + asalmasalah_kakek + asalmasalah_cucupr
      sisa = asalmasalah - totalasalmasalah
      if (masuk == "saudari3"):
        if (totalasalmasalah > asalmasalah):
          jumlahasalmasalah = totalasalmasalah
        else:
          jumlahasalmasalah = asalmasalah
      else:
        jumlahasalmasalah = totalasalmasalah
    elif (data['anak_pr'] > 0 and data['anak_lk'] > 0):
      asalmasalah_anakpr = (1 * data['anak_pr'])
      asalmasalah_anaklk = (2 * data['anak_lk'])
      # response.append(f"Tampil Siham Masalah Anak Laki-Laki: {asalmasalah_anaklk}")
      # response.append(f"Tampil Siham Masalah Anak Perempuan: {asalmasalah_anakpr}")
      
      if (data['suami'] == True):
        ambil_asalmasalah = asalmasalah_suami
      else:
        ambil_asalmasalah = asalmasalah_istri
      totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + \
        asalmasalah_ibu + asalmasalah_nenek + asalmasalah_kakek
      sisa = asalmasalah - totalasalmasalah
      jumlahasalmasalah = sisa + totalasalmasalah
    elif (data['anak_lk'] > 0 and data['anak_pr'] == 0):
      asalmasalah_anakpr = 0
      
      if (data['suami'] == True):
        ambil_asalmasalah = asalmasalah_suami
      else:
        ambil_asalmasalah = asalmasalah_istri
      if (ambil_asalmasalah == 0 and data['ayah'] == False and data['ibu'] == False and data['kakek'] == False and data['nenek'] == 0):
        totalasalmasalah = asalmasalah_anaklk
      else:
        totalasalmasalah = ambil_asalmasalah + asalmasalah_ayah + \
          asalmasalah_ibu + asalmasalah_nenek + asalmasalah_kakek
      sisa = asalmasalah - totalasalmasalah
      jumlahasalmasalah = sisa + totalasalmasalah
    else:
      # mengambil nilai asal masalah suami/istri
      if (data['suami'] == True):
        ambil_asalmasalah = asalmasalah_suami
      else:
        ambil_asalmasalah = asalmasalah_istri
      # batas mendapatkan nilai
      totalasalmasalah = ambil_asalmasalah + \
        asalmasalah_ayah + asalmasalah_ibu + asalmasalah_nenek
      sisa = asalmasalah - totalasalmasalah
      jumlahasalmasalah = sisa + totalasalmasalah

    #################################### Batas Hitung Asal Masalah ###################################
    data['asalmasalah'] = asalmasalah
    data['jumlahasalmasalah'] = jumlahasalmasalah
    data['totalasalmasalah'] = totalasalmasalah
    data['sisa'] = sisa
    data['tampil'] = tampil
    data['hitung'] = hitung
    data['masuk'] = masuk
    data['masuk0'] = masuk0
    data['masuk2'] = masuk2
    data['asalmasalah_suami'] = asalmasalah_suami
    data['asalmasalah_istri'] = asalmasalah_istri
    data['asalmasalah_ibu'] = asalmasalah_ibu
    data['asalmasalah_ayah'] = asalmasalah_ayah
    data['asalmasalah_kakek'] = asalmasalah_kakek
    data['asalmasalah_nenek'] = asalmasalah_nenek
    data['asalmasalah_anakpr'] = asalmasalah_anakpr
    data['asalmasalah_anaklk'] = asalmasalah_anaklk
    data['asalmasalah_cucupr'] = asalmasalah_cucupr
    data['asalmasalah_cuculk'] = asalmasalah_cuculk
    data['asalmasalah_saudara_knd'] = asalmasalah_saudara_knd
    data['asalmasalah_saudari_knd'] = asalmasalah_saudari_knd
    data['asalmasalah_saudara_seayah'] = asalmasalah_saudara_seayah
    data['asalmasalah_saudari_seayah'] = asalmasalah_saudari_seayah
    data['asalmasalah_saudara_seibu'] = asalmasalah_saudara_seibu
    data['asalmasalah_saudari_seibu'] = asalmasalah_saudari_seibu

    waris.setData(current_waris['id'], json.dumps(data))
    response += nextStep(step, current_waris['id'])

    print(data)
    return response
  elif step == 14:
    current_waris = waris.getCurrentWaris(user_id=session['user'])
    data = json.loads(current_waris['data'])

    harta = current_waris['harta']
    masuk = data.get('masuk', "")
    masuk0 = data.get('masuk0', "")
    masuk2 = data.get('masuk2', "")
    suami = data.get('suami', False)
    istri = data.get('istri', 0)
    ayah = data.get('ayah', False)
    ibu = data.get('ibu', False)
    kakek = data.get('kakek', False)
    nenek = data.get('nenek', 0)
    cucu_pr = data.get('cucu_pr', 0)
    anak_pr = data.get('anak_pr', 0)
    cucu_lk = data.get('cucu_lk', 0)
    anak_lk = data.get('anak_lk', 0)
    saudara_knd = data.get('saudara_knd', 0)
    saudari_knd = data.get('saudari_knd', 0)
    saudara_seayah = data.get('saudara_seayah', 0)
    saudari_seayah = data.get('saudari_seayah', 0)
    saudara_seibu = data.get('saudara_seibu', 0)
    saudari_seibu = data.get('saudari_seibu', 0)
    tampil = data.get('tampil', "")
    hitung = data.get('hitung', "")
    jumlahasalmasalah = data['jumlahasalmasalah']
    totalasalmasalah = data.get("totalasalmasalah", 0)
    asalmasalah = data['asalmasalah']
    asalmasalah_suami = data.get("asalmasalah_suami", 0)
    asalmasalah_istri = data.get("asalmasalah_istri", 0)
    asalmasalah_ibu = data.get("asalmasalah_ibu", 0)
    asalmasalah_ayah = data.get("asalmasalah_ayah", 0)
    asalmasalah_nenek = data.get("asalmasalah_nenek", 0)
    asalmasalah_kakek = data.get("asalmasalah_kakek", 0)
    asalmasalah_anaklk = data.get("asalmasalah_anaklk", 0)
    asalmasalah_anakpr = data.get("asalmasalah_anakpr", 0)
    asalmasalah_cuculk = data.get("asalmasalah_cuculk", 0)
    asalmasalah_cucupr = data.get("asalmasalah_cucupr", 0)
    asalmasalah_saudara_knd = data.get("asalmasalah_saudara_knd", 0)
    asalmasalah_saudari_knd = data.get("asalmasalah_saudari_knd", 0)
    asalmasalah_saudara_seayah = data.get("asalmasalah_saudara_seayah", 0)
    asalmasalah_saudari_seayah = data.get("asalmasalah_saudari_seayah", 0)
    asalmasalah_saudara_seibu = data.get("asalmasalah_saudara_seibu", 0)
    asalmasalah_saudari_seibu = data.get("asalmasalah_saudari_seibu", 0)
    sisa = data.get('sisa', 0)
    bagiansuami = data.get("bagiansuami", 0)
    bagianistri = data.get("bagianistri", 0)
    bagianibu = data.get("bagianibu", 0)
    bagianayah = data.get("bagianayah", 0)
    bagiankakek = data.get("bagiankakek", 0)
    bagiannenek = data.get("bagiannenek", 0)
    bagiananakpr = data.get("bagiananakpr", 0)
    bagiananaklk = data.get("bagiananaklk", 0)
    bagiancuculk = data.get("bagiancuculk", 0)
    bagiancucupr = data.get("bagiancucupr", 0)
    bagiansaudaraknd = data.get("bagiansaudaraknd", 0)
    bagiansaudariknd = data.get("bagiansaudariknd", 0)
    bagiansaudaraseayah = data.get("bagiansaudaraseayah", 0)
    bagiansaudariseayah = data.get("bagiansaudariseayah", 0)
    bagiansaudaraseibu = data.get("bagiansaudaraseibu", 0)
    bagiansaudariseibu = data.get("bagiansaudariseibu", 0)
    bagiansisa = data.get("bagiansisa", "")
    bagiansisakakek = data.get("bagiansisakakek", "")
    bagianibu = data.get("bagianibu", 0)
    bagiansisaibu = data.get("bagiansisaibu", "")
    
    teks_hasil = f"Perhitungan Waris <br>Pewaris : {current_waris['pewaris']}<br>Jenis Kelamin : {current_waris['jk_pewaris']}<br><br>"

    if (jumlahasalmasalah == asalmasalah):
      response += [f"Jumlah Siham : {int(totalasalmasalah)}"]
      if (current_waris['jk_pewaris'] == "L"):
        if (istri == 0 and cucu_pr == 0 and anak_pr == 0 and masuk == "saudari1"):
          hitung = "saudari1"
          response += [f"Asal masalah awal : {int(asalmasalah)}<br>" + \
            f"Asal Masalah Menjadi : {int(totalasalmasalah)}<br>" + \
            "Asal Masalah Sisa : 0"]
        elif (istri == 0 and cucu_pr == 0 and anak_pr == 0 and masuk == "saudari5"):
          hitung = "saudari5"
          response += [f"Asal masalah awal : {int(asalmasalah)}<br>" +\
            f"Asal Masalah Menjadi : {int(totalasalmasalah)}<br>" +\
            "Asal Masalah Sisa : 0"]
        elif (istri == 0 and cucu_pr == 0 and anak_pr == 0 and masuk == "saudari6"):
          hitung = "saudari6"
          response += [f"Asal masalah awal : {int(asalmasalah)}<br>" + \
            f"Asal Masalah Menjadi : {int(totalasalmasalah)}<br>" + \
            "Asal Masalah Sisa : 0"]
        else:
          response += [f"Asal Masalah Sisa: {int(sisa)}"]
      else:
        if (sisa < 0):
          response += [f"Asal Masalah Menjadi : {int(totalasalmasalah)}<br>" + \
            "Asal Masalah Sisa : 0"]
        else:
          if (suami == False and cucu_pr == 0 and anak_pr == 0 and masuk == "saudari1"):
            hitung = "saudari1"
            response += [f"asal masalah awal : {int(asalmasalah)}<br>" +\
              f"Asal Masalah Menjadi : {int(totalasalmasalah)}<br>" +\
              "Asal Masalah Sisa : 0"]
          elif (suami == False and cucu_pr == 0 and anak_pr == 0 and masuk == "saudari5"):
            hitung = "saudari5"
            response += [f"asal masalah awal : {int(asalmasalah)}<br>" + \
              f"Asal Masalah Menjadi : {int(totalasalmasalah)}<br>" + \
              "Asal Masalah Sisa : 0"]
          elif (suami == False and cucu_pr == 0 and anak_pr == 0 and masuk == "saudari6"):
            hitung = "saudari6"
            response += [f"Asal masalah awal : {int(asalmasalah)}<br>" + \
              f"Asal Masalah Menjadi : {int(totalasalmasalah)}<br>" + \
              "Asal Masalah Sisa : 0"]
          else:
            response += [f"Asal Masalah Sisa: {int(sisa)}"]
      # antisipasi Zero division
      # penghitungan bagian suami / istri
      if (suami == True):
        if (asalmasalah_suami == 0):
          finalbagiansuami = 0
          ambil_bagian_harta = finalbagiansuami
        else:
          suku_bagian_suami = harta / asalmasalah
          finalbagiansuami = (asalmasalah_suami * suku_bagian_suami)
          ambil_bagian_harta = finalbagiansuami
      else:
        if (asalmasalah_istri == 0):
          finalbagianistri = 0
          ambil_bagian_harta = finalbagianistri
        else:
          suku_bagian_istri = harta / asalmasalah
          finalbagianistri = (asalmasalah_istri * suku_bagian_istri)
          ambil_bagian_harta = finalbagianistri
      # batas penghitungan bagian suami / istri
      # bagiananakpr
      if (asalmasalah_anakpr == 0):
        finalbagiananakpr = 0
      else:
        suku_bagian_anak_pr = harta / asalmasalah
        finalbagiananakpr = (asalmasalah_anakpr * suku_bagian_anak_pr)
      # perhitungan bagian nenek
      if (asalmasalah_nenek != 0):
        if (ayah == False and kakek == False and anak_lk == 0 and anak_pr == 0 and cucu_lk == 0 and cucu_pr == 0 and saudara_knd == 0 and saudari_knd == 0 and saudara_seayah == 0 and saudari_seayah == 0 and saudara_seibu == 0 and saudari_seibu == 0):
          sisa_harta_nenek = harta - ambil_bagian_harta
          finalbagiannenek = asalmasalah_nenek * sisa_harta_nenek
        else:
          sisa_harta = harta - ambil_bagian_harta
          if (ayah == False and kakek == False and anak_pr == 0 and anak_lk == 0 and cucu_lk == 0 and cucu_pr == 0 and saudara_knd == 0):
            if (saudari_knd > 0):
              if (saudari_seayah == 0 and saudara_seayah == 0):
                if(saudara_seibu > 0 or saudari_seibu > 0):
                  asalmasalah_sisa = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                  finalbagiannenek = (sisa_harta * asalmasalah_nenek) / int(asalmasalah_sisa)
                else:
                  tampil = "ubah"
                  asalmasalah_sisa = asalmasalah_nenek + asalmasalah_saudari_knd
                  finalbagiannenek = (sisa_harta * asalmasalah_nenek) / int(asalmasalah_sisa)
              else:
                if (hitung == "saudari1"):
                  asalmasalah_sisa = asalmasalah_nenek + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                  finalbagiannenek = (sisa_harta * asalmasalah_nenek) / int(asalmasalah_sisa)
                else:
                  finalbagiannenek = (asalmasalah_nenek * harta) / jumlahasalmasalah
                  hitung = "saudari2"
            else:
              if (saudari_seayah > 0 and saudara_seayah == 0):
                if(hitung == "saudari1"):
                  asalmasalah_sisa = asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                else:
                  tampil = "ubah"
                  if (saudari_seibu > 0 or saudara_seibu > 0):
                    asalmasalah_sisa = asalmasalah_nenek + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                  else :
                    asalmasalah_sisa = asalmasalah_nenek + asalmasalah_saudari_seayah
                finalbagiannenek = (sisa_harta * asalmasalah_nenek) / int(asalmasalah_sisa)
              else:
                if(saudari_seibu > 0 or saudara_seibu > 0):
                  if(hitung == "saudari1"):
                    asalmasalah_sisa = asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                    finalbagiannenek = (sisa_harta * asalmasalah_nenek) / int(asalmasalah_sisa)
                  else:
                    finalbagiannenek = (asalmasalah_nenek * harta) / jumlahasalmasalah
                else:
                  finalbagiannenek = (asalmasalah_nenek * harta) / jumlahasalmasalah
          else:
            finalbagiannenek = (asalmasalah_nenek * harta) / jumlahasalmasalah
      else:
        finalbagiannenek = 0
      # perhitungan bagian ibu
      if (asalmasalah_ibu == 0):
        finalbagianibu = 0
      else:
        sisa_harta = harta - ambil_bagian_harta
        if (bagiansisaibu == "*sisa"):
          if (ayah == True):
            asalmasalah_sisa = asalmasalah_ibu + asalmasalah_ayah
            suku_bagian = sisa_harta / asalmasalah_sisa
            finalbagianibu = asalmasalah_ibu * suku_bagian
          elif (kakek == True):
            asalmasalah_sisa = asalmasalah_ibu + asalmasalah_kakek
            suku_bagian = sisa_harta / asalmasalah_sisa
            finalbagianibu = asalmasalah_ibu * suku_bagian
          else:
            finalbagianibu = sisa_harta
        else:
          if (ayah == False and kakek == False and anak_pr == 0 and anak_lk == 0 and ibu == True and cucu_lk == 0 and cucu_pr == 0 and saudara_knd == 0):
            if (saudari_knd > 0):
              if (saudari_seayah == 0 and saudara_seayah == 0):
                if(saudara_seibu > 0 or saudari_seibu > 0):
                  asalmasalah_sisa = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                  finalbagianibu = (sisa_harta * asalmasalah_ibu) / int(asalmasalah_sisa)
                else:
                  tampil = "ubah"
                  asalmasalah_sisa = asalmasalah_ibu + asalmasalah_saudari_knd
                  finalbagianibu = (sisa_harta * asalmasalah_ibu) / int(asalmasalah_sisa)
              else:
                if (hitung == "saudari1"):
                  asalmasalah_sisa = asalmasalah_ibu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah
                  finalbagianibu = (sisa_harta * asalmasalah_ibu) / int(asalmasalah_sisa)
                else:
                  finalbagianibu = (asalmasalah_ibu * harta) / jumlahasalmasalah
                  hitung = "saudari2"
            else:
              if (saudara_seayah > 0):
                finalbagianibu = (asalmasalah_ibu * harta) / jumlahasalmasalah
              else:
                if(saudari_seibu > 0 or saudara_seibu > 0):
                  if(hitung == "saudari1"):
                    if(saudari_seayah > 0):
                      asalmasalah_sisa = asalmasalah_ibu + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                    else:
                      asalmasalah_sisa = asalmasalah_ibu + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
                    finalbagianibu = (sisa_harta * asalmasalah_ibu) / int(asalmasalah_sisa)
                  else:
                    finalbagianibu = (asalmasalah_ibu * harta) / jumlahasalmasalah
                else:
                  tampil = "ubah"
                  asalmasalah_sisa = asalmasalah_ibu + asalmasalah_saudari_seayah
                  finalbagianibu = (sisa_harta * asalmasalah_ibu) / int(asalmasalah_sisa)
          # elif(ayah == False  and kakek == False and anak_pr > 1 and ibu == True and cucu_lk == 0):
          #     tampil = "ubah"
          #     asalmasalah_sisa = asalmasalah_ibu + asalmasalah_anakpr
          #     sisa_harta = harta - ambil_bagian_harta
          #     finalbagianibu = (sisa_harta * asalmasalah_ibu) / int(asalmasalah_sisa)
          else:
            finalbagianibu = (asalmasalah_ibu * harta) / jumlahasalmasalah
      # penghitungan bagian ayah / kakek
      if (asalmasalah_kakek == 0):
        finalbagiankakek = 0
      else:
        finalbagiankakek = (asalmasalah_kakek * harta) / jumlahasalmasalah
      # ayah
      if (asalmasalah_ayah == 0):
        finalbagianayah = 0
        sisa_harta_ayah = 0
      else:
        if (bagianayah == "sisa" and bagiansisa == ""):
          # old
          sisa_harta = harta - ambil_bagian_harta
          # sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek
          if (suami == False and nenek > 0):
            sisa_harta = harta - ambil_bagian_harta - finalbagiannenek
            asalmasalah_sisa = asalmasalah_ibu + asalmasalah_ayah
          else:
            sisa_harta = harta - ambil_bagian_harta
            asalmasalah_sisa = asalmasalah_ibu + asalmasalah_ayah + asalmasalah_nenek
          suku_bagian = sisa_harta / asalmasalah_sisa
          finalbagianayah = suku_bagian * asalmasalah_ayah
          sisa_harta_ayah = 0
        elif (bagianayah == 0.16 and bagiansisa == "+sisa"):
          harta_cucupr = (asalmasalah_cucupr * harta) / jumlahasalmasalah
          finalbagianayah = (asalmasalah_ayah * harta) / jumlahasalmasalah
          sisa_harta_ayah = harta - ambil_bagian_harta - finalbagianayah - \
            finalbagianibu - finalbagiannenek - harta_cucupr - finalbagiananakpr
          if (sisa_harta_ayah <= 0):
            sisa_harta_ayah = 0.0
        else:
          sisa_harta_ayah = 0
          finalbagianayah = (asalmasalah_ayah * harta) / jumlahasalmasalah
      # batas penghitungan bagian ayah/kakek
      # batas antisipasi Zero division error
      if (current_waris['jk_pewaris'] == "L"):
        if (hitung != "saudari1" or hitung != "saudari5" or masuk != "saudari6"):
          if (tampil == "ubah"):
            if (saudari_knd == 1 and nenek > 0):
              asalmasalah_ubah = asalmasalah_nenek + asalmasalah_saudari_knd
              teks = f"Siham Saudari Kandung: {asalmasalah_saudari_knd}<br>"
              teks += f"Siham Nenek : {asalmasalah_nenek}<br>"
              teks += f"Asal Masalah Awal : 6<br>"
              teks += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              response += [teks]
              
            elif (saudari_knd == 1 and ibu == True):
              asalmasalah_ubah = asalmasalah_ibu + asalmasalah_saudari_knd
              teks = f"Siham Saudari Kandung : {asalmasalah_saudari_knd}"
              teks += f"Siham Ibu : {asalmasalah_ibu}<br>"
              teks += f"Asal Masalah Awal : 6<br>"
              teks += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              response += [teks]
            elif (saudari_seayah == 1 and nenek > 0):
              asalmasalah_ubah = asalmasalah_nenek + asalmasalah_saudari_seayah
              teks = f"Siham Saudari Sayah: {asalmasalah_saudari_seayah}<br>"
              teks += f"Siham Nenek : {asalmasalah_nenek}<br>"
              teks += f"Asal Masalah Awal : 6<br>"
              teks += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              response += [teks]
            elif (saudari_knd == 1 and saudari_seayah > 0):
              asalmasalah_ubah = asalmasalah_saudari_knd + asalmasalah_saudari_seayah
              teks= f"Siham Saudari Kandung : {asalmasalah_saudari_knd}<br>"
              teks += f"Siham Saudari Sayah: {asalmasalah_saudari_seayah}<br>"
              teks += f"Asal Masalah Awal : 6<br>"
              teks += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              response += [teks]
            elif (saudari_knd == 1 and saudari_seibu == 1):
              asalmasalah_ubah = asalmasalah_saudari_knd + asalmasalah_saudari_seibu
              teks = f"Siham Saudari Kandung : {asalmasalah_saudari_knd}<br>"
              teks += f"Siham Saudari Sibu : {asalmasalah_saudari_seibu}<br>"
              teks += f"Asal Masalah Awal : 6<br>"
              teks += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              hitung = "saudari6"
              response += [teks]
            elif (saudari_knd == 1 and saudara_seibu == 1):
              asalmasalah_ubah = asalmasalah_saudari_knd + asalmasalah_saudara_seibu
              teks = "Siham Saudari Kandung : {asalmasalah_saudari_knd}<br>"
              teks += "Siham Saudara Sibu : {asalmasalah_saudara_seibu}<br>"
              teks += "Asal Masalah Awal : 6<br>"
              teks += "Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              hitung = "saudari6"
              response += [teks]
            elif (saudari_seayah == 1 and saudari_seibu == 1):
              asalmasalah_ubah = asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
              teks = "Siham Saudari Sayah : {asalmasalah_saudari_seayah}<br>"
              teks += "Siham Saudari Sibu : {asalmasalah_saudari_seibu}<br>"
              teks += "Asal Masalah Awal : 6<br>"
              hitung = "saudari6"
              teks += "Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              response += [teks]
            elif (saudari_seayah == 1 and saudara_seibu == 1):
              asalmasalah_ubah = asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
              teks = "Siham Saudari Sayah : {asalmasalah_saudari_seayah}<br>"
              teks += "Siham Saudara Sibu : {asalmasalah_saudara_seibu}<br>"
              teks += "Asal Masalah Awal : 6<br>"
              teks += "Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              hitung = "saudari6"
              response += [teks]
        else:
          response += [f"Asal Masalah Sisa : {int(sisa)}"]
      if (suami == True):
        teks_hasil += f"Bagian Harta Suami : {round(finalbagiansuami, 2)}<br>"
      else:
        # tampil bagian istri jika lebih 1 harta per istri
        if (istri > 1):
          bagi_harta_istri = finalbagianistri / istri
          teks_hasil += f"Bagian Harta Istri : {round(finalbagianistri , 2)}<br>"
          j = 1
          while j <= istri:
            teks_hasil += f"Harta Untuk Istri Ke- {j} = {round(bagi_harta_istri, 2)}<br>"
            j += 1
        else:
          if (istri != 0):
            teks_hasil += f"Bagian Harta Istri : {round(finalbagianistri, 2)}<br>"
      if (ayah == True):
        if (bagiansisa == "+sisa"):
          teks_hasil += f"Bagian Harta Ayah 1/6 + Sisa : {round(finalbagianayah, 2)} + {round(sisa_harta_ayah, 2)}<br>"
          teks_hasil += f"Jumlah Harta Ayah : {round(finalbagianayah + sisa_harta_ayah, 2)}<br>"
        else:
          teks_hasil += f"Bagian Harta Ayah : {round(finalbagianayah, 2)}<br>"
      if (ibu == True):
        teks_hasil += f"Bagian Harta Ibu : {round(finalbagianibu, 2)}<br>"
      if (nenek > 1):
        bagi_harta_nenek = finalbagiannenek / nenek
        teks_hasil += f"Bagian Harta Nenek : {round(finalbagiannenek, 2)}<br>"
        j = 1
        while j <= nenek:
          teks_hasil += f"Harta Untuk Nenek Ke- {j} = {round(bagi_harta_nenek, 2)}<br>"
          j += 1
      else:
        if (nenek != 0):
          teks_hasil += f"Bagian Harta Nenek : {round(finalbagiannenek, 2)}<br>"
      sisa_harta_kakek = 0
      if (kakek == True):
        if (bagiankakek == "sisa" and bagiansisakakek == ""):
          if (current_waris['jk_waris'] == "L"):
            if (istri > 0 and ibu == True):
              sisa_harta_kakek = harta - ambil_bagian_harta
              asalmasalah_sisa = asalmasalah_ibu + asalmasalah_kakek
            elif (istri > 0 and nenek > 0):
              sisa_harta_kakek = harta - ambil_bagian_harta - finalbagiannenek
              asalmasalah_sisa = asalmasalah_kakek
            elif (istri == 0 and nenek > 0):
              sisa_harta_kakek = harta - finalbagiannenek
              asalmasalah_sisa = asalmasalah_kakek
            elif (istri == 0 and ibu == True):
              sisa_harta_kakek = harta - finalbagianibu
              asalmasalah_sisa = asalmasalah_kakek
            else:
              sisa_harta_kakek = harta - ambil_bagian_harta
              asalmasalah_sisa = asalmasalah_kakek
          elif (current_waris['jk_waris'] == "P"):
            if (suami == True and ibu == True):
              sisa_harta_kakek = harta - ambil_bagian_harta
              asalmasalah_sisa = asalmasalah_ibu + asalmasalah_kakek
            elif (suami == True and nenek > 0):
              sisa_harta_kakek = harta - ambil_bagian_harta - finalbagiannenek
              asalmasalah_sisa = asalmasalah_kakek
            elif (suami == False and nenek > 0):
              sisa_harta_kakek = harta - finalbagiannenek
              asalmasalah_sisa = asalmasalah_kakek
            elif (suami == False and ibu == True):
              sisa_harta_kakek = harta - finalbagianibu
              asalmasalah_sisa = asalmasalah_kakek
            else:
              sisa_harta_kakek = harta - ambil_bagian_harta
              asalmasalah_sisa = asalmasalah_kakek
          suku_bagian = sisa_harta_kakek / asalmasalah_sisa
          finalbagiankakek = suku_bagian * asalmasalah_kakek
        elif (bagiankakek == 0.16 and bagiansisakakek == "+sisa"):
          harta_cucupr = (asalmasalah_cucupr * harta) / jumlahasalmasalah
          finalbagiankakek = (asalmasalah_kakek * harta) / jumlahasalmasalah
          sisa_harta_kakek = harta - ambil_bagian_harta - finalbagiankakek - \
            finalbagianibu - finalbagiannenek - harta_cucupr - finalbagiananakpr
        # tampil harta kakek
        if (bagiansisakakek == "+sisa"):
          if (sisa_harta_kakek <= 0):
            sisa_harta_kakek = 0.0
          teks_hasil += f"Bagian Harta Kakek 1/6 + sisa: {round(finalbagiankakek, 2)} + {round(sisa_harta_kakek, 2)}<br>"
          teks_hasil += f"Jumlah Harta Kakek : {round(finalbagiankakek + sisa_harta_kakek, 2)}<br>"
        else:
          teks_hasil += f"Bagian Harta Kakek : {round(finalbagiankakek, 2)}<br>"
      # bagian harta anak laki dan perempuan
      if (anak_pr > 0 or anak_lk > 0):
        if (anak_pr > 0 and anak_lk == 0):
          if (masuk != "saudari3"):
            asalmasalah_anakpr = (1 * anak_pr)
            asalmasalah_sisa = asalmasalah_anakpr
            harta_cucupr = (asalmasalah_cucupr * harta) / jumlahasalmasalah
            # sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu
            sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
              finalbagianibu - finalbagiannenek - finalbagiankakek - harta_cucupr
            teks_hasil += f"Sisa Harta : {round(sisa_harta, 2)}<br>"
            suku_bagian = sisa_harta / asalmasalah_sisa
            sisa_harta_anak_pr = (1 * suku_bagian)
            bagianharta_anak_pr = sisa_harta_anak_pr * anak_pr
          else:
            bagianharta_anak_pr = (
              asalmasalah_anakpr * harta) / jumlahasalmasalah
            sisa_harta_anak_pr = bagianharta_anak_pr / anak_pr
          teks_hasil += f"Harta Anak Perempuan : {round(bagianharta_anak_pr, 2)}<br>"
          # pembagian harta per anak perempuan
          if (anak_pr > 1):
            k = 1
            while k <= anak_pr:
              teks_hasil += f"Harta Untuk Anak Perempuan {k} = {round(sisa_harta_anak_pr, 2)}<br>"
              k += 1
        elif (anak_lk > 0 and anak_pr == 0):
          asalmasalah_anaklk = (1 * anak_lk)
          asalmasalah_sisa = asalmasalah_anaklk
          sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
            finalbagianibu - finalbagiannenek - finalbagiankakek
          teks_hasil += f"Sisa Harta : {round(sisa_harta, 2)}<br>"
          suku_bagian = sisa_harta / asalmasalah_sisa
          sisa_harta_anak_lk = (1 * suku_bagian)
          bagianharta_anak_lk = sisa_harta_anak_lk * anak_lk
          teks_hasil += f"Harta Anak Laki-Laki : {round(bagianharta_anak_lk, 2)}<br>"
          # pembagian harta per anak laki-laki
          if (anak_lk > 1):
            j = 1
            while j <= anak_lk:
              teks_hasil += f"Harta Untuk Anak Laki - Laki {j} = {round(sisa_harta_anak_lk, 2)}<br>"
              j += 1
        elif (anak_lk > 0 and anak_lk > 0):
          asalmasalah_anaklk = (2 * anak_lk)
          asalmasalah_anakpr = (1 * anak_pr)
          asalmasalah_sisa = asalmasalah_anaklk + asalmasalah_anakpr
          sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
            finalbagianibu - finalbagiannenek - finalbagiankakek
          teks_hasil += f"Sisa Harta : {round(sisa_harta, 2)}<br>"
          suku_bagian = sisa_harta / asalmasalah_sisa
          sisa_harta_anak_pr = (1 * suku_bagian)
          sisa_harta_anak_lk = (2 * suku_bagian)
          bagianharta_anak_pr = sisa_harta_anak_pr * anak_pr
          bagianharta_anak_lk = sisa_harta_anak_lk * anak_lk
          teks_hasil += f"Harta Anak Perempuan : {round(bagianharta_anak_pr, 2)}<br>"
          # pembagian harta per anak perempuan
          if (anak_pr > 1):
            i = 1
            while i <= anak_pr:
              teks_hasil += f"Harta Untuk Anak Perempuan {i} = {round(sisa_harta_anak_pr, 2)}<br>"
              i += 1
          # pembagian harta per anak laki-laki
          teks_hasil += f"Harta Anak Laki-Laki : {round(bagianharta_anak_lk, 2)}<br>"
          if (anak_lk > 1):
            j = 1
            while j <= anak_lk:
              teks_hasil += f"Harta Untuk Anak Laki - Laki {j} = {round(sisa_harta_anak_lk, 2)}<br>"
              j += 1
      # bagianharta cucu
      if (cucu_pr > 0 or cucu_lk > 0):
        if (cucu_pr > 0 and cucu_lk == 0):
          if (ayah == False and kakek == False and anak_lk == 0 and saudara_knd > 0 or saudari_knd > 0):
            bagianharta_cucu_pr = (
              asalmasalah_cucupr * harta) / jumlahasalmasalah
            sisa_harta_cucu_pr = bagianharta_cucu_pr / cucu_pr

          else:
            if (ayah == False and kakek == False and anak_lk == 0 and saudara_knd == 0 and saudari_knd == 0 and saudara_seayah > 0 or saudari_seayah > 0):
              bagianharta_cucu_pr = (
                asalmasalah_cucupr * harta) / jumlahasalmasalah
              sisa_harta_cucu_pr = bagianharta_cucu_pr / cucu_pr
            else:
              asalmasalah_cucupr = (1 * cucu_pr)
              asalmasalah_sisa = asalmasalah_cucupr
              # sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu
              if (kakek == True and ayah == False):
                sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu - \
                  finalbagiannenek - finalbagiankakek - sisa_harta_kakek - finalbagiananakpr
              else:
                sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu - \
                  finalbagiannenek - finalbagiankakek - sisa_harta_ayah - finalbagiananakpr
              if (sisa_harta <= 0):
                sisa_harta_cucu_pr = 0.0
                bagianharta_cucu_pr = 0.0
              else:
                suku_bagian = sisa_harta / asalmasalah_sisa
                sisa_harta_cucu_pr = (1 * suku_bagian)
                bagianharta_cucu_pr = sisa_harta_cucu_pr * cucu_pr
                teks_hasil += f"Sisa Harta : {round(sisa_harta, 2)}<br>"
          # pembagian harta per cucu perempuan
          if (bagiancucupr != "termahjub"):
            teks_hasil += f"Harta Cucu Perempuan : {round(bagianharta_cucu_pr, 2)}<br>"
            if (cucu_pr > 1):
              k = 1
              while k <= cucu_pr:
                teks_hasil += f"Harta Untuk Cucu Perempuan {k} = {round(sisa_harta_cucu_pr, 2)}<br>"
                k += 1
        elif (cucu_lk > 0 and cucu_pr == 0):
          asalmasalah_cuculk = (1 * cucu_lk)
          asalmasalah_sisa = asalmasalah_cuculk
          sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
            finalbagianibu - finalbagiannenek - finalbagiankakek - finalbagiananakpr
          if (sisa_harta <= 0):
            sisa_harta_cucu_lk = 0.0
            bagianharta_cucu_lk = 0.0
          else:
            teks_hasil += f"Sisa Harta : {round(sisa_harta, 2)}<br>"
            suku_bagian = sisa_harta / asalmasalah_sisa
            sisa_harta_cucu_lk = (1 * suku_bagian)
            bagianharta_cucu_lk = sisa_harta_cucu_lk * cucu_lk

          # pembagian harta per cucu laki-laki
          if (bagiancuculk != "termahjub"):
            teks_hasil += f"Harta Cucu Laki-Laki : {round(bagianharta_cucu_lk, 2)}<br>"
            if (cucu_lk > 1):
              j = 1
              while j <= cucu_lk:
                teks_hasil += f"Harta Untuk Cucu Laki - Laki {j} =  {round(sisa_harta_cucu_lk, 2)}<br>"
                j += 1
        elif (cucu_lk > 0 and cucu_lk > 0):
          asalmasalah_cuculk = (2 * cucu_lk)
          asalmasalah_cucupr = (1 * cucu_pr)
          asalmasalah_sisa = asalmasalah_cuculk + asalmasalah_cucupr
          sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
            finalbagianibu - finalbagiannenek - finalbagiankakek - finalbagiananakpr
          if (sisa_harta <= 0):
            sisa_harta_cucu_lk = 0.0
            bagianharta_cucu_lk = 0.0
            sisa_harta_cucu_pr = 0.0
            bagianharta_cucu_pr = 0.0
          else:
            teks_hasil += f"Sisa Harta : {round(sisa_harta, 2)}<br>"
            suku_bagian = sisa_harta / asalmasalah_sisa
            sisa_harta_cucu_pr = (1 * suku_bagian)
            sisa_harta_cucu_lk = (2 * suku_bagian)
            bagianharta_cucu_pr = sisa_harta_cucu_pr * cucu_pr
            bagianharta_cucu_lk = sisa_harta_cucu_lk * cucu_lk

          # pembagian harta per cucu perempuan
          if (bagiancucupr != "termahjub"):
            teks_hasil += f"Harta Cucu Perempuan : {round(bagianharta_cucu_pr, 2)}<br>"
            if (cucu_pr > 1):
              i = 1
              while i <= cucu_pr:
                teks_hasil += f"Harta Untuk Cucu Perempuan {i} = {round(sisa_harta_cucu_pr, 2)}<br>"
                i += 1
          # pembagian harta per cucu laki-laki
          if (bagiancuculk != "termahjub"):
            teks_hasil += f"Harta Cucu Laki-Laki : {round(bagianharta_cucu_lk, 2)}<br>"
            if (cucu_lk > 1):
              j = 1
              while j <= cucu_lk:
                teks_hasil += f"Harta Untuk Cucu Laki - Laki {j} = {round(sisa_harta_cucu_lk, 2)}<br>"
                j += 1
      else:
        bagianharta_cucu_pr = 0
        bagianharta_cucu_lk = 0
      # saudara sibu dan saudari sibu
      bagianharta_saudari_sibu = 0
      bagianharta_saudara_sibu = 0
      if (saudara_seibu > 0 and saudari_seibu == 0):
        bagianharta_saudari_sibu = 0
        if (bagiansaudaraseibu != "termahjub"):
          if (hitung == "saudari1"):
            sisa_harta = harta
            if(ibu == True):
              asalmasalah_ortu = asalmasalah_ibu
            elif(nenek > 0):
              asalmasalah_ortu = asalmasalah_nenek
            else:
              asalmasalah_ortu = 0
            if(saudari_knd > 0):
              asalmasalah_sisa = asalmasalah_ortu + asalmasalah_saudara_seibu + asalmasalah_saudari_knd
            elif(saudari_seayah > 0):
              asalmasalah_sisa = asalmasalah_ortu + asalmasalah_saudara_seibu + asalmasalah_saudari_seayah
            else:
              asalmasalah_sisa = asalmasalah_ortu + asalmasalah_saudara_seibu
            bagianharta_saudara_sibu = (asalmasalah_saudara_seibu * sisa_harta) / int(asalmasalah_sisa)
            finalbagiansaudarasibu = bagianharta_saudara_sibu / saudara_seibu
          elif (hitung == "saudari6"):
            sisa_harta = harta - ambil_bagian_harta
            asalmasalah_sisa = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu
            bagianharta_saudara_sibu = (asalmasalah_saudara_seibu * sisa_harta) / int(asalmasalah_sisa)
            finalbagiansaudarasibu = bagianharta_saudara_sibu / saudara_seibu
          else:
            asalmasalah_saudara = asalmasalah_saudara_seibu
            suku_bagian_saudara = harta / jumlahasalmasalah
            bagianharta_saudara_sibu = (asalmasalah_saudara * suku_bagian_saudara)
            finalbagiansaudarasibu = bagianharta_saudara_sibu / saudara_seibu
          teks_hasil += f"Harta Saudara Seibu : {round(bagianharta_saudara_sibu, 2)}<br>"
          if (saudara_seibu > 1):
            j = 1
            while j <= saudara_seibu:
              teks_hasil += f"Harta Untuk Saudara Seibu {j} = {round(finalbagiansaudarasibu, 2)}<br>"
              j += 1
      elif (saudara_seibu == 0 and saudari_seibu > 0):
        bagianharta_saudara_sibu = 0
        if (bagiansaudariseibu != "termahjub"):
          if (hitung == "saudari1"):
            sisa_harta = harta
            if(ibu == True):
              asalmasalah_ortu = asalmasalah_ibu
            elif(nenek > 0):
              asalmasalah_ortu = asalmasalah_nenek
            else:
              asalmasalah_ortu = 0
            if(saudari_knd > 0):
              asalmasalah_sisa = asalmasalah_ortu + asalmasalah_saudari_seibu + asalmasalah_saudari_knd
            elif(saudari_seayah > 0):
              asalmasalah_sisa = asalmasalah_ortu + asalmasalah_saudari_seibu + asalmasalah_saudari_seayah
            else:
              asalmasalah_sisa = asalmasalah_ortu + asalmasalah_saudari_seibu
            bagianharta_saudari_sibu = (asalmasalah_saudari_seibu * sisa_harta) / int(asalmasalah_sisa)
            finalbagiansaudarisibu = bagianharta_saudari_sibu / saudari_seibu
          elif (hitung == "saudari6"):
            sisa_harta = harta - ambil_bagian_harta
            asalmasalah_sisa = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu
            bagianharta_saudari_sibu = (asalmasalah_saudari_seibu * sisa_harta) / int(asalmasalah_sisa)
            finalbagiansaudarisibu = bagianharta_saudari_sibu / saudari_seibu
          else:
            asalmasalah_saudara = asalmasalah_saudari_seibu
            suku_bagian_saudari = harta / jumlahasalmasalah
            bagianharta_saudari_sibu = (asalmasalah_saudara * suku_bagian_saudari)
            finalbagiansaudarisibu = bagianharta_saudari_sibu / saudari_seibu
          teks_hasil += f"Harta Saudari Sibu : {round(bagianharta_saudari_sibu, 2)}<br>"
          if (saudari_seibu > 1):
            j = 1
            while j <= saudari_seibu:
              teks_hasil += f"Harta Untuk Saudari Sibu {j} = {round(finalbagiansaudarisibu, 2)}<br>"
              j += 1
      elif (saudara_seibu > 0 and saudari_seibu > 0):
        if (bagiansaudaraseibu != "termahjub" and bagiansaudariseibu != "termahjub"):
          hitung_jumlah_saudara = saudara_seibu + saudari_seibu
          if (hitung_jumlah_saudara > 2):
            if(masuk == "saudari1"):
              harta_sibu = harta / totalasalmasalah
            elif(masuk == "saudari6"):
              harta_sibu = harta / totalasalmasalah
            else:
              harta_sibu = harta / jumlahasalmasalah
            hitung_saudara = asalmasalah_saudara_seibu * harta_sibu
            hitung_saudari = asalmasalah_saudari_seibu * harta_sibu
            proses_hitung = hitung_saudara + hitung_saudari
            suku_bagian_saudara = proses_hitung / hitung_jumlah_saudara
            bagianharta_saudari_sibu = saudari_seibu * suku_bagian_saudara
            bagianharta_saudara_sibu = saudara_seibu * suku_bagian_saudara
          else:
            if(masuk == "saudari1"):
              suku_bagian_saudara = harta / totalasalmasalah
            elif(masuk == "saudari6"):
              suku_bagian_saudara = harta / totalasalmasalah
            else:
              suku_bagian_saudara = harta / jumlahasalmasalah
            bagianharta_saudari_sibu = asalmasalah_saudari_seibu * suku_bagian_saudara
            bagianharta_saudara_sibu = asalmasalah_saudara_seibu * suku_bagian_saudara
          finalbagiansaudarisibu = bagianharta_saudari_sibu / saudari_seibu
          finalbagiansaudarasibu = bagianharta_saudara_sibu / saudara_seibu
          
          teks_hasil += f"Harta Saudari Seibu : {round(bagianharta_saudari_sibu, 2)}<br/>"
          if (saudari_seibu > 1):
            i = 1
            while i <= saudari_seibu:
              teks_hasil += f"Harta Untuk Saudari Seibu {i} = {round(finalbagiansaudarisibu, 2)}<br/>"
              i += 1
          teks_hasil += f"Harta Saudara Seibu : {round(bagianharta_saudara_sibu, 2)}<br>"
          if (saudara_seibu > 1):
            j = 1
            while j <= saudara_seibu:
              teks_hasil += f"Harta Untuk Saudara Seibu {j} = {round(finalbagiansaudarasibu, 2)}<br/>"
              j += 1
      # saudara kandung dan saudari kandung
      if (saudara_knd > 0 and saudari_knd == 0):
        bagianharta_saudari_knd = 0
        if (bagiansaudaraknd != "termahjub"):
          
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - \
            finalbagiannenek - bagianharta_cucu_pr - finalbagiananakpr - \
            bagianharta_saudara_sibu - bagianharta_saudari_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara_knd = (1 * saudara_knd)
          asalmasalah_saudara = asalmasalah_saudara_knd
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudaraknd = (1 * suku_bagian_saudara)
          bagianharta_saudara_knd = finalbagiansaudaraknd * saudara_knd
          teks_hasil += f"Harta Saudara Kandung : {round(bagianharta_saudara_knd, 2)}<br>"
          if (saudara_knd > 1):
            j = 1
            while j <= saudara_knd:
              teks_hasil += f"Harta Untuk Saudara Kandung {j} = {round(finalbagiansaudaraknd, 2)}<br>"
              j += 1
      elif (saudara_knd == 0 and saudari_knd > 0):
        bagianharta_saudara_knd = 0
        if (bagiansaudariknd != "termahjub"):
          if (hitung == "saudari1"):
            if (ibu == False and nenek > 0):
              asalmasalah_ortu = asalmasalah_nenek
            else:
              asalmasalah_ortu = asalmasalah_ibu
            asalmasalah_sisa = asalmasalah_ortu + asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
            bagianharta_saudari_knd = (
              asalmasalah_saudari_knd * harta) / int(asalmasalah_sisa)
            finalbagiansaudariknd = bagianharta_saudari_knd / saudari_knd
          elif (hitung == "saudari2"):
            bagianharta_saudari_knd = (
              asalmasalah_saudari_knd * harta) / jumlahasalmasalah
            finalbagiansaudariknd = bagianharta_saudari_knd / saudari_knd
          elif (hitung == "saudari4"):
            sisa_harta = harta - ambil_bagian_harta
            bagianharta_saudari_knd = (
              asalmasalah_saudari_knd * sisa_harta) / asalmasalah_ubah
            finalbagiansaudariknd = bagianharta_saudari_knd / saudari_knd
          elif (hitung == "saudari5"):
            asalmasalah_sisa = asalmasalah_saudari_knd + asalmasalah_saudari_seayah
            bagianharta_saudari_knd = (
              asalmasalah_saudari_knd * harta) / int(asalmasalah_sisa)
            finalbagiansaudariknd = bagianharta_saudari_knd / saudari_knd
          elif (hitung == "saudari6"):
            asalmasalah_sisa = asalmasalah_saudari_knd + asalmasalah_saudari_seayah + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
            bagianharta_saudari_knd = (asalmasalah_saudari_knd * harta) / int(asalmasalah_sisa)
            finalbagiansaudariknd = bagianharta_saudari_knd / saudari_knd
          else:
            sisa_harta = harta - ambil_bagian_harta - finalbagianibu - \
              finalbagiannenek - bagianharta_cucu_pr - finalbagiananakpr - bagianharta_saudara_sibu - bagianharta_saudari_sibu
            if (sisa_harta <= 0):
              sisa_harta = 0
            asalmasalah_saudari_knd = (1 * saudari_knd)
            asalmasalah_saudara = asalmasalah_saudari_knd
            suku_bagian_saudari = sisa_harta / asalmasalah_saudara
            finalbagiansaudariknd = (1 * suku_bagian_saudari)
            bagianharta_saudari_knd = finalbagiansaudariknd * saudari_knd
          
          teks_hasil += f"Harta Saudari Kandung : {round(bagianharta_saudari_knd, 2)}<br>"
          if (saudari_knd > 1):
            j = 1
            while j <= saudari_knd:
              teks_hasil += f"Harta Untuk Saudari Kandung {j} = {round(finalbagiansaudariknd, 2)}<br>"
              j += 1
      elif (saudara_knd > 0 and saudari_knd > 0):
        if (bagiansaudaraknd != "termahjub" and bagiansaudariknd != "termahjub"):
          
          asalmasalah_saudari_knd = (1 * saudari_knd)
          asalmasalah_saudara_knd = (2 * saudara_knd)
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - \
            finalbagiannenek - bagianharta_cucu_pr - finalbagiananakpr - \
            bagianharta_saudara_sibu - bagianharta_saudari_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara = asalmasalah_saudara_knd + asalmasalah_saudari_knd
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudariknd = (1 * suku_bagian_saudara)
          finalbagiansaudaraknd = (2 * suku_bagian_saudara)
          bagianharta_saudari_knd = finalbagiansaudariknd * saudari_knd
          bagianharta_saudara_knd = finalbagiansaudaraknd * saudara_knd
          teks_hasil += f"Harta Saudari Kandung : {round(bagianharta_saudari_knd, 2)}<br>"
          if (saudari_knd > 1):
            i = 1
            while i <= saudari_knd:
              teks_hasil += f"Harta Untuk Saudari Kandung {i} = {round(finalbagiansaudariknd, 2)}<br>"
              i += 1
          
          teks_hasil += f"Harta Saudara Kandung : {round(bagianharta_saudara_knd, 2)}<br>"
          if (saudara_knd > 1):
            j = 1
            while j <= saudara_knd:
              teks_hasil += f"Harta Untuk Saudara Kandung {j} = {round(finalbagiansaudaraknd, 2)}<br>"
              j += 1
      elif (saudara_knd == 0 and saudari_knd == 0):
        bagianharta_saudari_knd = 0
        bagianharta_saudara_knd = 0
      # saudara sayah dan saudari sayah
      bagianharta_saudara_sayah = 0
      bagianharta_saudari_sayah = 0
      if (saudara_seayah > 0 and saudari_seayah == 0):
        if (bagiansaudaraseayah != "termahjub"):
          
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek - \
            bagianharta_cucu_pr - finalbagiananakpr - bagianharta_saudari_knd - bagianharta_saudari_sibu - bagianharta_saudara_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara_seayah = (1 * saudara_seayah)
          asalmasalah_saudara = asalmasalah_saudara_seayah
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudaraseayah = (1 * suku_bagian_saudara)
          bagianharta_saudara_sayah = finalbagiansaudaraseayah * saudara_seayah
          teks_hasil += f"Harta Saudara Seayah : {round(bagianharta_saudara_sayah, 2)}<br/>"
          if (saudara_seayah > 1):
            j = 1
            while j <= saudara_seayah:
              teks_hasil += f"Harta Untuk Saudara Seayah {j} = {round(finalbagiansaudaraseayah, 2)}<br/>"
              j += 1
      elif (saudara_seayah == 0 and saudari_seayah > 0):
        if (bagiansaudariseayah != "termahjub"):
          
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek - \
            bagianharta_cucu_pr - finalbagiananakpr - bagianharta_saudari_knd - bagianharta_saudara_sibu - bagianharta_saudari_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudari_seayah = (1 * saudari_seayah)
          asalmasalah_saudara = asalmasalah_saudari_seayah
          suku_bagian_saudari = sisa_harta / asalmasalah_saudara
          finalbagiansaudarisayah = (1 * suku_bagian_saudari)
          bagianharta_saudari_sayah = finalbagiansaudarisayah * saudari_seayah
          teks_hasil += f"Harta Saudari Seayah : {round(bagianharta_saudari_sayah, 2)}<br>"
          if (saudari_seayah > 1):
            j = 1
            while j <= saudari_seayah:
              teks_hasil += f"Harta Untuk Saudari Seayah {j} = {round(finalbagiansaudarisayah, 2)}<br>"
              j += 1
      elif (saudara_seayah > 0 and saudari_seayah > 0):
        if (bagiansaudaraseayah != "termahjub" and bagiansaudariseayah != "termahjub"):
          
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek - \
            bagianharta_cucu_pr - finalbagiananakpr - bagianharta_saudari_knd - bagianharta_saudara_sibu - bagianharta_saudari_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudari_seayah = (1 * saudari_seayah)
          asalmasalah_saudara_seayah = (2 * saudara_seayah)
          asalmasalah_saudara = asalmasalah_saudara_seayah + asalmasalah_saudari_seayah
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudarisayah = (1 * suku_bagian_saudara)
          finalbagiansaudaraseayah = (2 * suku_bagian_saudara)
          bagianharta_saudari_sayah = finalbagiansaudarisayah * saudari_seayah
          bagianharta_saudara_sayah = finalbagiansaudaraseayah * saudara_seayah
          teks_hasil += f"Harta Saudari Seayah : {round(bagianharta_saudari_sayah, 2)}<br>"
          if (saudari_seayah > 1):
            i = 1
            while i <= saudari_seayah:
              teks_hasil += f"Harta Untuk Saudari Seayah {i} = {round(finalbagiansaudarisayah, 2)}<br>"
              i += 1
          
          teks_hasil += f"Harta Saudara Seayah : {round(bagianharta_saudara_sayah, 2)}<br>"
          if (saudara_seayah > 1):
            j = 1
            while j <= saudara_seayah:
              teks_hasil += f"Harta Untuk Saudara Seayah {j} = {round(finalbagiansaudaraseayah, 2)}<br>"
              j += 1
        else:
          
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek - \
            bagianharta_cucu_pr - finalbagiananakpr - bagianharta_saudari_knd - bagianharta_saudara_sibu - bagianharta_saudari_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara_seayah = (1 * saudara_seayah)
          asalmasalah_saudara = asalmasalah_saudara_seayah
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudaraseayah = (1 * suku_bagian_saudara)
          bagianharta_saudara_sayah = finalbagiansaudaraseayah * saudara_seayah
          teks_hasil += f"Harta Saudara Seayah : {round(bagianharta_saudara_sayah, 2)}<br>"
          if (saudara_seayah > 1):
            j = 1
            while j <= saudara_seayah:
              teks_hasil += f"Harta Untuk Saudara Seayah {j} = {round(finalbagiansaudaraseayah, 2)}<br>"
              j += 1
    elif (jumlahasalmasalah > asalmasalah):
      response += [f"Jumlah Siham : {int(totalasalmasalah)}"]
      if (sisa > 0):
        response.append(f"Asal Masalah Sisa: {int(sisa)}")
      sisa_harta = 0
      suku_bagian = harta / jumlahasalmasalah
      if (suami == True):
        if (asalmasalah_suami == 0):
          finalbagiansuami = 0
          ambil_bagian_harta = finalbagiansuami
        else:
          finalbagiansuami = (asalmasalah_suami * harta) / jumlahasalmasalah
          ambil_bagian_harta = finalbagiansuami
      else:
        if (asalmasalah_istri == 0):
          finalbagianistri = 0
          ambil_bagian_harta = finalbagianistri
        else:
          finalbagianistri = (asalmasalah_istri * harta) / jumlahasalmasalah
          ambil_bagian_harta = finalbagianistri
      if (asalmasalah_ibu == 0):
        finalbagianibu = 0
      else:
        if (bagiansisaibu == "*sisa"):
          sisa_harta = harta - ambil_bagian_harta
          if (ayah == True):
            asalmasalah_sisa = asalmasalah_ibu + asalmasalah_ayah
            suku_bagian = sisa_harta / asalmasalah_sisa
            finalbagianibu = asalmasalah_ibu * suku_bagian
          else:
            finalbagianibu = sisa_harta
        else:
          finalbagianibu = (asalmasalah_ibu * harta) / jumlahasalmasalah
      # perhitungan bagian nenek lebih
      # old
      # if(asalmasalah_nenek != 0):
      #     if(ayah == False and kakek =="0" and anak_lk == 0 and anak_pr == 0 and cucu_lk == 0 and cucu_pr == 0 and saudara_knd == 0 and saudari_knd == 0 and saudara_seayah == 0 and saudari_seayah == 0 and saudara_seibu == 0 and saudari_seibu == 0):
      #         sisa_harta_nenek = harta - ambil_bagian_harta
      #         finalbagiannenek = asalmasalah_nenek * sisa_harta_nenek
      #     else:
      #         finalbagiannenek = (asalmasalah_nenek * harta) / asalmasalah
      # else:
      #     finalbagiannenek = 0

      # new
      if (asalmasalah_nenek == 0):
        finalbagiannenek = 0
      else:
        finalbagiannenek = (asalmasalah_nenek * harta) / jumlahasalmasalah
      # penghitungan bagian ayah / kakek
      if (asalmasalah_kakek == 0):
        finalbagiankakek = 0
      else:
        if (bagiankakek == "sisa"):
          sisa_harta = harta - ambil_bagian_harta
          asalmasalah_sisa = asalmasalah_ibu + asalmasalah_kakek
          suku_bagian = sisa_harta / asalmasalah_sisa
          
          response.append("Asal Masalah Sisa " + asalmasalah_sisa + "<br>")
          response.append("Suku Bagian " + suku_bagian + "<br>")
          finalbagiankakek = suku_bagian * asalmasalah_kakek
        else:
          finalbagiankakek = (asalmasalah_kakek * harta) / jumlahasalmasalah

      if (asalmasalah_ayah == 0):
        finalbagianayah = 0
      else:
        if (bagianayah == "sisa"):
          sisa_harta = harta - ambil_bagian_harta
          asalmasalah_sisa = asalmasalah_ibu + asalmasalah_ayah
          suku_bagian = sisa_harta / asalmasalah_sisa
          
          response.append("Asal Masalah Sisa " + asalmasalah_sisa + "<br>")
          response.append("Suku Bagian " + suku_bagian + "<br>")
          finalbagianayah = suku_bagian * asalmasalah_ayah
        else:
          finalbagianayah = (asalmasalah_ayah * harta) / jumlahasalmasalah
      # batas penghitungan bagian ayah/kakek
      if (asalmasalah_anakpr == 0):
        finalbagiananakpr = 0
      else:
        finalbagiananakpr = (asalmasalah_anakpr * suku_bagian)
      
      response.append(f"Asal Masalah Awal : {int(asalmasalah)}<br>")
      response.append(f"Asal Masalah Menjadi : {int(jumlahasalmasalah)}<br>")
      # cucu perempuan
      # bagian cucu laki dan cucu perempuan
      finalbagiancucupr = 0
      finalbagiancuculk = 0
      sisa_cucu = 0
      cucu = ""
      if (cucu_pr > 0 and cucu_lk == 0):
        finalbagiancuculk = 0
        cucu = "kondisi1"
        if (bagiancucupr != "termahjub"):
          if (cucu_pr > 0 and anak_pr > 0):
            if (ayah == False and kakek == False):
              if (ibu == True):
                asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr + asalmasalah_ibu
              else:
                if (nenek > 0):
                  asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr + asalmasalah_nenek
                else:
                  asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr
              sisa_harta_cucu_pr = harta - ambil_bagian_harta
              suku_bagian_cucu = sisa_harta_cucu_pr / asalmasalah_sisa
            else:
              suku_bagian_cucu = harta / jumlahasalmasalah
            finalbagiancucupr = asalmasalah_cucupr * suku_bagian_cucu
            # sisa_harta_cucu_pr = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu - finalbagiannenek - finalbagiankakek
          else:
            finalbagiancucupr = asalmasalah_cucupr * suku_bagian
        else:
          finalbagiancucupr = 0
      elif (cucu_pr == 0 and cucu_lk > 0):
        if (bagiancuculk != "termahjub"):
          cucu = "kondisi2"
          sisa_harta_cucu = harta - ambil_bagian_harta - finalbagiananakpr - \
            finalbagianayah - finalbagiankakek - finalbagianibu - finalbagiannenek
          if (sisa_harta_cucu <= 0):
            sisa_harta_cucu_lk = 0
            finalbagiancuculk = 0
          else:
            sisa_harta_cucu_lk = (1 * sisa_harta_cucu)
            finalbagiancuculk = sisa_harta_cucu_lk * cucu_lk
        else:
          finalbagiancuculk = 0
        sisa_cucu = finalbagiancuculk

      elif (cucu_pr > 0 and cucu_lk > 0):
        cucu = "kondisi3"
        asalmasalah_sisa_cucu = asalmasalah_cucupr + asalmasalah_cuculk
        sisa_harta_cucu = harta - ambil_bagian_harta - finalbagiananakpr - \
          finalbagianayah - finalbagiankakek - finalbagianibu - finalbagiannenek
        if (sisa_harta_cucu <= 0):
          sisa_harta_cucu = 0
        else:
          sisa_harta_cucu = sisa_harta_cucu
        suku_bagian_cucu = sisa_harta_cucu / asalmasalah_sisa_cucu
        sisa_harta_cucu_pr = (1 * suku_bagian_cucu)
        sisa_harta_cucu_lk = (2 * suku_bagian_cucu)
        if (bagiancucupr != "termahjub"):
          finalbagiancucupr = sisa_harta_cucu_pr * cucu_pr
        else:
          finalbagiancucupr = 0
        if (bagiancuculk != "termahjub"):
          finalbagiancuculk = sisa_harta_cucu_lk * cucu_lk
        else:
          finalbagiancuculk = 0
        sisa_cucu = finalbagiancucupr + finalbagiancuculk

      # batas cucu perempuan
      if (suami == True):
        teks_hasil += f"Bagian Harta Suami : {round(finalbagiansuami, 2)}<br>"
      else:
        # tampil bagian istri jika lebih 1 harta per istri
        if (istri > 1):
          bagi_harta_istri = finalbagianistri / istri
          teks_hasil += f"Bagian Harta Istri : {round(finalbagianistri, 2)}<br>"
          j = 1
          while j <= istri:
            teks_hasil += f"Harta Untuk Istri Ke- {j} = {bagi_harta_istri}<br>"
            j += 1
        else:
          if (istri != 0):
            teks_hasil += f"Bagian Harta Istri : {round(finalbagianistri , 2)}<br>"
      if (bagianayah == 0.16 and bagiansisa == "+sisa"):
        teks_hasil += f"Bagian Harta Ayah 1/6 + sisa: {round(finalbagianayah, 2)} + {round(sisa_harta, 2)}<br>"
        teks_hasil += f"Harta untuk ayah =  {round(finalbagianayah + sisa_harta, 2)}<br>"
      else:
        if (ayah == True):
          teks_hasil += f"Bagian Harta Ayah : {round(finalbagianayah, 2)}<br>"
      if (ibu == True):
        teks_hasil += f"Bagian Harta Ibu : {round(finalbagianibu, 2)}<br>"
      if (nenek > 1):
        bagi_harta_nenek = finalbagiannenek / nenek
        teks_hasil += f"Bagian Harta Nenek : {round(finalbagiannenek, 2)}<br>"
        j = 1
        while j <= nenek:
          teks_hasil += f"Harta Untuk Nenek Ke- {j} = {round(bagi_harta_nenek, 2)}<br>"
          j += 1
      else:
        if (nenek != 0):
          teks_hasil += f"Bagian Harta Nenek : {round(finalbagiannenek, 2)}<br>"
      # tampil bagian kakek
      if (kakek == True):
        if (bagiankakek == "sisa" and bagiansisakakek == ""):
          if (current_waris['jk_pewaris'] == 'L'):
            if (istri > 0 and ibu == True):
              sisa_harta_kakek = harta - ambil_bagian_harta
              asalmasalah_sisa = asalmasalah_ibu + asalmasalah_kakek
            elif (istri > 0 and nenek > 0):
              sisa_harta_kakek = harta - ambil_bagian_harta - finalbagiannenek
              asalmasalah_sisa = asalmasalah_kakek
            elif (istri == 0 and nenek > 0):
              sisa_harta_kakek = harta - finalbagiannenek
              asalmasalah_sisa = asalmasalah_kakek
            elif (istri == 0 and ibu == True):
              sisa_harta_kakek = harta - finalbagianibu
              asalmasalah_sisa = asalmasalah_kakek
            else:
              sisa_harta_kakek = harta - ambil_bagian_harta
              asalmasalah_sisa = asalmasalah_kakek
          elif (current_waris['jk_pewaris'] == 'P'):
            if (suami == True and ibu == True):
              sisa_harta_kakek = harta - ambil_bagian_harta
              asalmasalah_sisa = asalmasalah_ibu + asalmasalah_kakek
            elif (suami == True and nenek > 0):
              sisa_harta_kakek = harta - ambil_bagian_harta - finalbagiannenek
              asalmasalah_sisa = asalmasalah_kakek
            elif (suami == False and nenek > 0):
              sisa_harta_kakek = harta - finalbagiannenek
              asalmasalah_sisa = asalmasalah_kakek
            elif (suami == False and ibu == True):
              sisa_harta_kakek = harta - finalbagianibu
              asalmasalah_sisa = asalmasalah_kakek
            else:
              sisa_harta_kakek = harta - ambil_bagian_harta
              asalmasalah_sisa = asalmasalah_kakek
          suku_bagian = sisa_harta_kakek / asalmasalah_sisa
          finalbagiankakek = suku_bagian * asalmasalah_kakek
          teks_hasil += f"Bagian Harta Kakek : {round(finalbagiankakek, 2)}<br>"
        elif (bagiankakek == 0.16 and bagiansisakakek == "+sisa"):
          teks_hasil += f"Bagian Harta Kakek 1/6 + sisa: {round(finalbagiankakek, 2)} + {round(sisa_harta ,2)}<br>"
          teks_hasil += f"Harta untuk kakek =  {round(finalbagiankakek + sisa_harta, 2)}<br>"
        else:
          teks_hasil += f"Bagian Harta Kakek : {round(finalbagiankakek, 2)}<br>"
      if (anak_pr > 0 and anak_lk == 0):
        asalmasalah_anakpr = (1 * anak_pr)
        asalmasalah_sisa = asalmasalah_anakpr
        # batas ambil bagian suami / istri
        # sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu
        sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
          finalbagianibu - finalbagiannenek - finalbagiankakek - finalbagiancucupr
        teks_hasil += f"Sisa Harta : {round(sisa_harta , 2)}<br>"
        suku_bagian = sisa_harta / asalmasalah_sisa
        sisa_harta_anak_pr = (1 * suku_bagian)
        bagianharta_anak_pr = sisa_harta_anak_pr * anak_pr
        teks_hasil += f"Harta Anak Perempuan : {round(bagianharta_anak_pr ,2)}<br>"
        # pembagian harta per anak perempuan
        if (anak_pr > 1):
          k = 1
          while k <= anak_pr:
            teks_hasil += f"Harta Untuk Anak Perempuan {k} = {round(sisa_harta_anak_pr, 2)}<br>"
            k += 1
      elif (anak_lk > 0 and anak_pr == 0):
        asalmasalah_anaklk = (1 * anak_lk)
        asalmasalah_sisa = asalmasalah_anaklk
        # batas ambil bagian suami / istri
        # sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu
        sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
          finalbagianibu - finalbagiannenek - finalbagiankakek
        teks_hasil += f"Sisa Harta : {round(sisa_harta, 2)}<br>"
        suku_bagian = sisa_harta / asalmasalah_sisa
        sisa_harta_anak_lk = (1 * suku_bagian)
        bagianharta_anak_lk = sisa_harta_anak_lk * anak_lk
        teks_hasil += f"Harta Anak Laki-Laki : {round(bagianharta_anak_lk, 2)}<br>"
        # pembagian harta per anak laki-laki
        if (anak_lk > 1):
          j = 1
          while j <= anak_lk:
            teks_hasil += f"Harta Untuk Anak Laki - Laki {j} = {round(sisa_harta_anak_lk, 2)}<br>"
            j += 1
      elif (anak_lk > 0 and anak_pr > 0):
        asalmasalah_anaklk = (2 * anak_lk)
        asalmasalah_anakpr = (1 * anak_pr)
        asalmasalah_sisa = asalmasalah_anaklk + asalmasalah_anakpr
        # ambil bagian suami jika ada jika tidak ada ambil bagian istri
        if (suami == True):
          ambil_bagian_harta = finalbagiansuami
        else:
          ambil_bagian_harta = finalbagianistri
        # batas ambil bagian suami / istri
        # sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu
        sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
          finalbagianibu - finalbagiannenek - finalbagiankakek
        teks_hasil += f"Sisa Harta : {round(sisa_harta, 2)}<br>"
        suku_bagian = sisa_harta / asalmasalah_sisa
        sisa_harta_anak_pr = (1 * suku_bagian)
        sisa_harta_anak_lk = (2 * suku_bagian)
        bagianharta_anak_pr = sisa_harta_anak_pr * anak_pr
        bagianharta_anak_lk = sisa_harta_anak_lk * anak_lk
        teks_hasil += f"Harta Anak Perempuan : {round(bagianharta_anak_pr, 2)}<br>"
        teks_hasil += f"Harta Anak Laki-Laki : {round(bagianharta_anak_lk, 2)}<br>"
        # pembagian harta per anak perempuan
        if (anak_pr > 1):
          i = 1
          while i <= anak_pr:
            teks_hasil += f"Harta Untuk Anak Perempuan {i} = {round(sisa_harta_anak_pr, 2)}<br>"
            i += 1
        # pembagian harta per anak laki-laki
        if (anak_lk > 1):
          j = 1
          while j <= anak_lk:
            teks_hasil += f"Harta Untuk Anak Laki - Laki {j} = {round(sisa_harta_anak_lk, 2)}<br>"
            j += 1
      # # bagian harta cucu pr
      # if(cucu_pr > 0):
      #     print(f"Bagian Harta Cucu Perempuan : {int(finalbagiancucupr)}")
      #     if(finalbagiancucupr == 0):
      #         sisa_harta_cucu_pr = 0
      #     else:
      #         sisa_harta_cucu_pr = finalbagiancucupr / cucu_pr
      #     # pembagian harta per cucu perempuan
      #     if(cucu_pr > 1):
      #         i = 1
      #         while i <= cucu_pr:
      #             print("Harta Untuk Cucu Perempuan ", i, " = ", sisa_harta_cucu_pr)
      #             i += 1
      # bagian harta cucu pr
      if (cucu == "kondisi1"):
        if (bagiancucupr != "termahjub"):
          teks_hasil += f"Bagian Harta Cucu Perempuan : {round(finalbagiancucupr, 2)}<br>"
          if (finalbagiancucupr == 0):
            sisa_harta_cucu_pr = 0
          else:
            sisa_harta_cucu_pr = finalbagiancucupr / cucu_pr
          # pembagian harta per cucu perempuan
          if (cucu_pr > 1):
            i = 1
            while i <= cucu_pr:
              teks_hasil += f"Harta Untuk Cucu Perempuan {i} = {round(sisa_harta_cucu_pr, 2)}<br>"
              i += 1
      elif (cucu == "kondisi2"):
        # pembagian harta per cucu laki-laki
        if (bagiancuculk != "termahjub"):
          teks_hasil += f"Harta Cucu Laki-Laki : {round(finalbagiancuculk, 2)}<br>"
          if (cucu_lk > 1):
            j = 1
            while j <= cucu_lk:
              teks_hasil += f"Harta Untuk Cucu Laki - Laki {j} = {round(sisa_harta_cucu_lk, 2)}<br>"
              j += 1
      elif (cucu == "kondisi3"):
        # pembagian harta per cucu perempuan
        if (bagiancucupr != "termahjub"):
          teks_hasil += f"Harta Cucu Perempuan : {round(finalbagiancucupr, 2)}<br>"
          if (cucu_pr > 1):
            i = 1
            while i <= cucu_pr:
              teks_hasil += f"Harta Untuk Cucu Perempuan {i} = {sisa_harta_cucu_pr}<br>"
              i += 1
        # pembagian harta per cucu laki-laki
        if (bagiancuculk != "termahjub"):
          teks_hasil += f"Harta Cucu Laki-Laki : {round(finalbagiancuculk, 2)}<br>"
          if (cucu_lk > 1):
            j = 1
            while j <= cucu_lk:
              teks_hasil += f"Harta Untuk Cucu Laki - Laki {j} = {round(sisa_harta_cucu_lk, 2)}<br>"
              j += 1
      bagianharta_saudara_sibu = 0
      bagianharta_saudari_sibu = 0
      # saudara sibu dan saudari sibu
      if (saudara_seibu > 0 and saudari_seibu == 0):
        if (bagiansaudaraseibu != "termahjub"):
          if (masuk == "saudari-sibu"):
            asalmasalah_saudara_seibu = 1
          asalmasalah_saudara = asalmasalah_saudara_seibu
          suku_bagian_saudara = harta / jumlahasalmasalah
          bagianharta_saudara_sibu = asalmasalah_saudara_seibu * suku_bagian_saudara
          finalbagiansaudarasibu = (bagianharta_saudara_sibu / saudara_seibu)
          teks_hasil += f"Harta Saudara Seibu : {round(bagianharta_saudara_sibu, 2)}<br>"
          if (saudara_seibu > 1):
            j = 1
            while j <= saudara_seibu:
              teks_hasil += f"Harta Untuk Saudara Seibu {j} = {round(finalbagiansaudarasibu, 2)}<br>"
              j += 1
      elif (saudara_seibu == 0 and saudari_seibu > 0):
        if (bagiansaudariseibu != "termahjub"):
          if (masuk == "saudari-sibu"):
            asalmasalah_saudari_seibu = 1
          asalmasalah_saudara = asalmasalah_saudari_seibu
          suku_bagian_saudari = harta / jumlahasalmasalah
          bagianharta_saudari_sibu = asalmasalah_saudari_seibu * suku_bagian_saudari
          finalbagiansaudarisibu = (bagianharta_saudari_sibu / saudari_seibu)
          teks_hasil += f"Harta Saudari Sibu : {round(bagianharta_saudari_sibu, 2)}<br>"
          if (saudari_seibu > 1):
            j = 1
            while j <= saudari_seibu:
              teks_hasil += "Harta Untuk Saudari Sibu " + j +" = " + round(finalbagiansaudarisibu, 2) + "<br>"
              j += 1
      elif (saudara_seibu > 0 and saudari_seibu > 0):
        if (bagiansaudaraseibu != "termahjub" and bagiansaudariseibu != "termahjub"):
          hitung_jumlah_saudara = saudara_seibu + saudari_seibu
          if (hitung_jumlah_saudara > 2):
            harta_sibu = harta / jumlahasalmasalah
            hitung_saudara = asalmasalah_saudari_seibu * harta_sibu
            hitung_saudari = asalmasalah_saudari_seibu * harta_sibu
            proses_hitung = hitung_saudara + hitung_saudari
            suku_bagian_saudara = proses_hitung / hitung_jumlah_saudara
            bagianharta_saudari_sibu = saudari_seibu * suku_bagian_saudara
            bagianharta_saudara_sibu = saudara_seibu * suku_bagian_saudara
          else:
            suku_bagian_saudara = harta / jumlahasalmasalah
            bagianharta_saudari_sibu = asalmasalah_saudari_seibu * suku_bagian_saudara
            bagianharta_saudara_sibu = asalmasalah_saudara_seibu * suku_bagian_saudara
          finalbagiansaudarisibu = bagianharta_saudari_sibu / saudari_seibu
          finalbagiansaudarasibu = bagianharta_saudara_sibu / saudara_seibu
          
          teks_hasil += f"Harta Saudari Seibu : {round(bagianharta_saudari_sibu, 2)}<br>"
          if (saudari_seibu > 1):
            i = 1
            while i <= saudari_seibu:
              teks_hasil += f"Harta Untuk Saudari Seibu {i} = {round(finalbagiansaudarisibu, 2)}<br>"
              i += 1
          teks_hasil += f"Harta Saudara Seibu : {round(bagianharta_saudara_sibu, 2)}<br>"
          if (saudara_seibu > 1):
            j = 1
            while j <= saudara_seibu:
              teks_hasil += f"Harta Untuk Saudara Seibu {j} = {round(finalbagiansaudarasibu, 2)}<br>"
              j += 1
      # harta saudara kandung dan saudari kandung
      bagianharta_saudara_knd = 0
      bagianharta_saudari_knd = 0
      if (saudara_knd > 0 and saudari_knd == 0):
        if (bagiansaudaraknd != "termahjub"):
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - \
            finalbagiannenek - finalbagiancucupr - finalbagiananakpr
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara_knd = (1 * saudara_knd)
          asalmasalah_saudara = asalmasalah_saudara_knd
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudaraknd = (1 * suku_bagian_saudara)
          bagianharta_saudara_knd = finalbagiansaudaraknd * saudara_knd
          teks_hasil += f"Harta Saudara Kandung : {round(bagianharta_saudara_knd, 2)}<br>"
          if (saudara_knd > 1):
            j = 1
            while j <= saudara_knd:
              teks_hasil += f"Harta Untuk Saudara Kandung {j} = {round(finalbagiansaudaraknd, 2)}<br>"
              j += 1
      elif (saudara_knd == 0 and saudari_knd > 0):
        if (bagiansaudariknd != "termahjub"):
          if (hitung == "saudari2"):
            bagianharta_saudari_knd = (
              asalmasalah_saudari_knd * harta) / jumlahasalmasalah
            finalbagiansaudariknd = bagianharta_saudari_knd / saudari_knd
          else:
            sisa_harta = harta - ambil_bagian_harta - finalbagianibu - \
              finalbagiannenek - finalbagiancucupr - finalbagiananakpr
            asalmasalah_saudari_knd = (1 * saudari_knd)
            asalmasalah_saudara = asalmasalah_saudari_knd
            suku_bagian_saudari = sisa_harta / asalmasalah_saudara
            finalbagiansaudariknd = (1 * suku_bagian_saudari)
            bagianharta_saudari_knd = finalbagiansaudariknd * saudari_knd
          teks_hasil += f"Harta Saudari Kandung : {round(bagianharta_saudari_knd, 2)}<br/>"
          if (saudari_knd > 1):
            j = 1
            while j <= saudari_knd:
              teks_hasil += f"Harta Untuk Saudari Kandung {j} = {round(finalbagiansaudariknd, 2)}<br>"
              j += 1
      elif (saudara_knd > 0 and saudari_knd > 0):
        if (bagiansaudaraknd != "termahjub" and bagiansaudariknd != "termahjub"):
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - \
            finalbagiannenek - finalbagiancucupr - finalbagiananakpr
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudari_knd = (1 * saudari_knd)
          asalmasalah_saudara_knd = (2 * saudara_knd)
          asalmasalah_saudara = asalmasalah_saudara_knd + asalmasalah_saudari_knd
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudariknd = (1 * suku_bagian_saudara)
          finalbagiansaudaraknd = (2 * suku_bagian_saudara)
          bagianharta_saudari_knd = finalbagiansaudariknd * saudari_knd
          bagianharta_saudara_knd = finalbagiansaudaraknd * saudara_knd
          teks_hasil += f"Harta Saudari Kandung : {round(bagianharta_saudari_knd, 2)}<br/>"
          if (saudari_knd > 1):
            i = 1
            while i <= saudari_knd:
              teks_hasil += f"Harta Untuk Saudari Kandung {i} = {round(finalbagiansaudariknd, 2)}<br/>"
              i += 1
          teks_hasil += f"Harta Saudara Kandung : {round(bagianharta_saudara_knd, 2)}<br/>"
          if (saudara_knd > 1):
            j = 1
            while j <= saudara_knd:
              teks_hasil += f"Harta Untuk Saudara Kandung {j} = {round(finalbagiansaudaraknd, 2)}<br/>"
              j += 1
      # saudara dan saudari sayah
      bagianharta_saudari_sayah = 0
      bagianharta_saudara_sayah = 0
      if (saudara_seayah > 0 and saudari_seayah == 0):
        if (bagiansaudaraseayah != "termahjub"):
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek - \
            finalbagiancucupr - finalbagiananakpr - bagianharta_saudari_knd - \
            bagianharta_saudari_sibu - bagianharta_saudara_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara_seayah = (1 * saudara_seayah)
          asalmasalah_saudara = asalmasalah_saudara_seayah
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudaraseayah = (1 * suku_bagian_saudara)
          bagianharta_saudara_sayah = finalbagiansaudaraseayah * saudara_seayah
          teks_hasil += f"Harta Saudara Seayah : {round(bagianharta_saudara_sayah, 2)}<br/>"
          if (saudara_seayah > 1):
            j = 1
            while j <= saudara_seayah:
              teks_hasil += f"Harta Untuk Saudara Seayah {j} = {round(finalbagiansaudaraseayah, 2)}<br/>"
              j += 1
      elif (saudara_seayah == 0 and saudari_seayah > 0):
        if (bagiansaudariseayah != "termahjub"):
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek - finalbagiancucupr - \
            finalbagiananakpr - bagianharta_saudari_knd - \
            bagianharta_saudari_sibu - bagianharta_saudara_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudari_seayah = (1 * saudari_seayah)
          asalmasalah_saudara = asalmasalah_saudari_seayah
          suku_bagian_saudari = sisa_harta / asalmasalah_saudara
          finalbagiansaudarisayah = (1 * suku_bagian_saudari)
          bagianharta_saudari_sayah = finalbagiansaudarisayah * saudari_seayah
          teks_hasil += f"Harta Saudari Seayah : {round(bagianharta_saudari_sayah, 2)}<br/>"
          if (saudari_seayah > 1):
            j = 1
            while j <= saudari_seayah:
              teks_hasil += f"Harta Untuk Saudari Seayah {j} = {round(finalbagiansaudarisayah, 2)}<br/>"
              j += 1
      elif (saudara_seayah > 0 and saudari_seayah > 0):
        if (bagiansaudaraseayah != "termahjub" and bagiansaudariseayah != "termahjub"):
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek - \
            finalbagiancucupr - finalbagiananakpr - bagianharta_saudari_knd - \
            bagianharta_saudari_sibu - bagianharta_saudara_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudari_seayah = (1 * saudari_seayah)
          asalmasalah_saudara_seayah = (2 * saudara_seayah)
          asalmasalah_saudara = asalmasalah_saudara_seayah + asalmasalah_saudari_seayah
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudarisayah = (1 * suku_bagian_saudara)
          finalbagiansaudaraseayah = (2 * suku_bagian_saudara)
          bagianharta_saudari_sayah = finalbagiansaudarisayah * saudari_seayah
          bagianharta_saudara_sayah = finalbagiansaudaraseayah * saudara_seayah
          teks_hasil += f"Harta Saudari Seayah : {round(bagianharta_saudari_sayah, 2)}<br/>"
          if (saudari_seayah > 1):
            i = 1
            while i <= saudari_seayah:
              teks_hasil += f"Harta Untuk Saudari Seayah {i} = {round(finalbagiansaudarisayah, 2)}<br/>"
              i += 1
          teks_hasil += f"Harta Saudara Seayah : {round(bagianharta_saudara_sayah, 2)}<br/>"
          if (saudara_seayah > 1):
            j = 1
            while j <= saudara_seayah:
              teks_hasil += f"Harta Untuk Saudara Seayah {j} = {round(finalbagiansaudaraseayah, 2)}<br/>"
              j += 1
        elif (bagiansaudaraseayah != "termahjub" and bagiansaudariseayah == "termahjub"):
          
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek - \
            bagianharta_cucu_pr - finalbagiananakpr - bagianharta_saudari_knd - \
            bagianharta_saudari_sibu - bagianharta_saudara_sibu
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara_seayah = (1 * saudara_seayah)
          asalmasalah_saudara = asalmasalah_saudara_seayah
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          finalbagiansaudaraseayah = (1 * suku_bagian_saudara)
          bagianharta_saudara_sayah = finalbagiansaudaraseayah * saudara_seayah
          teks_hasil += f"Harta Saudara Seayah : {round(bagianharta_saudara_sayah, 2)}<br/>"
          if (saudara_seayah > 1):
            j = 1
            while j <= saudara_seayah:
              teks_hasil += f"Harta Untuk Saudara Seayah {j} = {round(finalbagiansaudaraseayah, 2)}<br/>"
              j += 1
        else:
          bagianharta_saudari_sayah = 0
          bagianharta_saudara_sayah = 0
          teks_hasil += f"Harta Saudari Seayah : {round(bagianharta_saudari_sayah, 2)}<br/>"
          teks_hasil += f"Harta Saudara Seayah : {round(bagianharta_saudara_sayah, 2)}<br/>"
    elif (jumlahasalmasalah < asalmasalah):
      tampil = ""
      teks_hasil += f"Jumlah Siham : {int(totalasalmasalah)}<br>"
      # antisipasi Zero division error
      # hitung harta suami/istri
      if (suami == True):
        # old
        # suku_bagian = harta / jumlahasalmasalah
        # if (asalmasalah_suami == 0):
        #     finalbagiansuami = 0
        #     ambil_bagian_harta = finalbagiansuami
        # else:
        #     if(ayah == False and ibu == False and kakek == False and nenek == 0):
        #         suku_bagian = harta / totalasalmasalah
        #         finalbagiansuami = asalmasalah_suami * suku_bagian
        #         ambil_bagian_harta = finalbagiansuami
        #     else:
        #         finalbagiansuami = asalmasalah_suami * suku_bagian
        #         ambil_bagian_harta = finalbagiansuami

        # new
        suku_bagian = harta / asalmasalah
        if (asalmasalah_suami == 0):
          finalbagiansuami = 0
          ambil_bagian_harta = finalbagiansuami
        else:
          finalbagiansuami = asalmasalah_suami * suku_bagian
          ambil_bagian_harta = finalbagiansuami
      else:
        suku_bagian = harta / asalmasalah
        if (asalmasalah_istri == 0):
          finalbagianistri = 0
          ambil_bagian_harta = finalbagianistri
        else:
          finalbagianistri = asalmasalah_istri * suku_bagian
          ambil_bagian_harta = finalbagianistri
      # hitung harta ibu
      if (asalmasalah_ibu == 0):
        finalbagianibu = 0
      else:
        sisa_harta = harta - ambil_bagian_harta
        if (bagiansisaibu == "*sisa"):
          if (ayah == True):
            asalmasalah_sisa = asalmasalah_ibu + asalmasalah_ayah
            suku_bagian = sisa_harta / asalmasalah_sisa
            finalbagianibu = asalmasalah_ibu * suku_bagian
          else:
            finalbagianibu = asalmasalah_ibu * suku_bagian
        else:
          if (ayah == False and kakek == False and anak_pr == 1 and ibu == True and cucu_lk == 0):
            if (cucu_pr > 0):
              asalmasalah_sisa = asalmasalah_ibu + asalmasalah_anakpr + asalmasalah_cucupr
            else:
              asalmasalah_sisa = asalmasalah_ibu + asalmasalah_anakpr
            tampil = "ubah"
            sisa_harta = harta - ambil_bagian_harta
            finalbagianibu = (sisa_harta * asalmasalah_ibu) / \
              int(asalmasalah_sisa)
          elif (ayah == False and kakek == False and anak_pr == 0 and ibu == True and cucu_lk == 0):
            if (cucu_pr > 0):
              tampil = "ubah"
              asalmasalah_sisa = asalmasalah_ibu + asalmasalah_cucupr
              sisa_harta = harta - ambil_bagian_harta
              finalbagianibu = (
                sisa_harta * asalmasalah_ibu) / int(asalmasalah_sisa)
            else:
              finalbagianibu = suku_bagian * asalmasalah_ibu
          elif (ayah == False and kakek == False and anak_pr > 1 and ibu == True and cucu_lk == 0):
            tampil = "ubah"
            asalmasalah_sisa = asalmasalah_ibu + asalmasalah_anakpr
            sisa_harta = harta - ambil_bagian_harta
            finalbagianibu = (sisa_harta * asalmasalah_ibu) / \
              int(asalmasalah_sisa)
          else:
            finalbagianibu = suku_bagian * asalmasalah_ibu
      # perhitungan bagian nenek
      # if(asalmasalah_nenek != 0):
      #     if(ayah == False and kakek =="0" and anak_lk == 0 and anak_pr == 0 and cucu_lk == 0 and cucu_pr == 0 and saudara_knd == 0 and saudari_knd == 0 and saudara_seayah == 0 and saudari_seayah == 0 and saudara_seibu == 0 and saudari_seibu == 0):
      #         sisa_harta_nenek = harta - ambil_bagian_harta
      #         finalbagiannenek = asalmasalah_nenek * sisa_harta_nenek
      #     else:
      #         finalbagiannenek = (asalmasalah_nenek * harta) / asalmasalah
      # else:
      #     finalbagiannenek = 0
      if (asalmasalah_nenek == 0):
        finalbagiannenek = 0
      else:
        sisa_harta = harta - ambil_bagian_harta
        if (ayah == False and kakek == False and anak_pr == 1 and nenek > 0 and cucu_lk == 0):
          if (cucu_pr > 0):
            asalmasalah_sisa = asalmasalah_nenek + asalmasalah_anakpr + asalmasalah_cucupr
          else:
            asalmasalah_sisa = asalmasalah_nenek + asalmasalah_anakpr
          tampil = "ubah"
          sisa_harta = harta - ambil_bagian_harta
          finalbagiannenek = (
            sisa_harta * asalmasalah_nenek) / int(asalmasalah_sisa)
        elif (ayah == False and kakek == False and anak_pr == 0 and nenek > 0 and cucu_lk == 0):
          if (cucu_pr > 0):
            tampil = "ubah"
            sisa_harta = harta - ambil_bagian_harta
            asalmasalah_sisa = asalmasalah_nenek + asalmasalah_cucupr
            finalbagiannenek = (
              sisa_harta * asalmasalah_nenek) / int(asalmasalah_sisa)
          else:
            if(masuk == "saudari-sibu"):
              # saudara
              if (saudara_seibu == 1):
                asalmasalah_saudara_seibu = 1
              elif (saudara_seibu > 1):
                asalmasalah_saudara_seibu = 2
              else:
                asalmasalah_saudara_seibu = 0
              # saudari
              if (saudari_seibu == 1):
                asalmasalah_saudari_seibu = 1
              elif (saudari_seibu > 1):
                asalmasalah_saudari_seibu = 2
              else:
                asalmasalah_saudari_seibu = 0
              asalmasalah_saudara = asalmasalah_nenek + asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
              suku_bagian = sisa_harta / asalmasalah_saudara
              finalbagiannenek =  asalmasalah_nenek * suku_bagian
            else:
              finalbagiannenek = suku_bagian * asalmasalah_nenek
        elif (ayah == False and kakek == False and anak_pr > 1 and nenek > 0 and cucu_lk == 0):
          tampil = "ubah"
          asalmasalah_sisa = asalmasalah_nenek + asalmasalah_anakpr
          sisa_harta = harta - ambil_bagian_harta
          finalbagiannenek = (
            sisa_harta * asalmasalah_nenek) / int(asalmasalah_sisa)
        else:
          finalbagiannenek = suku_bagian * asalmasalah_nenek
      
      # hitung harta anak perempuan
      finalbagiananakpr = asalmasalah_anakpr * suku_bagian
      # hitung harta kakek
      # if (asalmasalah_kakek == 0):
      #     finalbagiankakek = 0
      # else:
      #     if (bagiankakek == "sisa" and bagiansisakakek == ""):
      #         finalbagiankakek = suku_bagian * asalmasalah_kakek
      #         sisa_harta = harta - ambil_bagian_harta - \
      #             finalbagianibu - finalbagiananakpr - finalbagiannenek - finalbagiankakek
      #     elif (bagianayah == 0.16 and bagiansisa == "+sisa"):
      #         asalmasalah_sisa = sisa
      #         finalbagiankakek = suku_bagian * asalmasalah_kakek
      #     else:
      #         finalbagikakek = suku_bagian * asalmasalah_kakek

      # hitung harta ayah
      if (asalmasalah_ayah == 0):
        finalbagianayah = 0
      else:
        if (bagianayah == "sisa" and bagiansisa == ""):
          finalbagianayah = suku_bagian * asalmasalah_ayah
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - \
            finalbagiananakpr - finalbagianayah - finalbagiannenek
        elif (bagianayah == 0.16 and bagiansisa == "+sisa"):
          asalmasalah_sisa = sisa
          finalbagianayah = suku_bagian * asalmasalah_ayah
        else:
          finalbagianayah = suku_bagian * asalmasalah_ayah
      # batas hitung harta ayah
      # hitung harta kakek
      if (asalmasalah_kakek == 0):
        finalbagiankakek = 0
      else:
        if (bagiankakek == "sisa" and bagiansisakakek == ""):
          finalbagiankakek = suku_bagian * asalmasalah_kakek
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - \
            finalbagiananakpr - finalbagiankakek - finalbagiannenek
          # suku_bagian = sisa_harta / asalmasalah_sisa
        elif (bagiankakek == 0.16 and bagiansisakakek == "+sisa"):
          asalmasalah_sisa = sisa
          finalbagiankakek = suku_bagian * asalmasalah_kakek
        else:
          finalbagiankakek = suku_bagian * asalmasalah_kakek
      # batas hitung harta kakek
      
      # jika ada saudari sibu
      if (masuk == "saudari-sibu"):
        tampil = "ubah"
      if (current_waris['jk_pewaris'] == 'P'):
        if (ayah == False and ibu == True):
          sisa_harta = harta - finalbagianibu - ambil_bagian_harta
        else:
          sisa_harta = harta - finalbagianayah - finalbagianibu - \
            finalbagiananakpr - ambil_bagian_harta - finalbagiankakek - finalbagiannenek
      else:
        if (ayah == False and ibu == True):
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu
        else:
          sisa_harta = harta - finalbagianayah - finalbagianibu - \
            finalbagiananakpr - ambil_bagian_harta - finalbagiankakek - finalbagiannenek
      if (current_waris['jk_pewaris'] == 'P'):
        if (tampil == "ubah"):
          if (anak_pr > 0 and nenek > 0):
            asalmasalah_ubah = asalmasalah_nenek + asalmasalah_anakpr + asalmasalah_cucupr
            teks_hasil += f"Asal Masalah Sisa {sisa}<br/>"
            teks_hasil += f"Siham Anak Perempuan : {asalmasalah_anakpr}<br/>"
            if (cucu_pr > 0):
              teks_hasil += f"Siham Cucu Perempuan : {asalmasalah_cucupr}<br/>"
            teks_hasil += f"Siham Nenek : {asalmasalah_nenek}<br/>"
            teks_hasil += f"Asal Masalah Awal : 6<br/>"
            teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br/>"
            
          elif (anak_pr > 0 and ibu == True):
            asalmasalah_ubah = asalmasalah_ibu + asalmasalah_anakpr + asalmasalah_cucupr
            teks_hasil += f"Asal Masalah Sisa {sisa}<br/>"
            teks_hasil += f"Siham Anak Perempuan : {asalmasalah_anakpr}<br/>"
            if (cucu_pr > 0):
              teks_hasil += f"Siham Cucu Perempuan : {asalmasalah_cucupr}<br/>"
            teks_hasil += f"Siham Ibu : {asalmasalah_ibu}<br/>"
            teks_hasil += f"Asal Masalah Awal : 6<br/>"
            teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br/>"
            
          else:
            if (cucu_pr > 0 and ibu == True):
              asalmasalah_ubah = asalmasalah_ibu + asalmasalah_cucupr
              teks_hasil += f"Asal Masalah Sisa {sisa}<br/>"
              teks_hasil += f"Siham Cucu Perempuan : {asalmasalah_cucupr}<br/>"
              teks_hasil += f"Siham Ibu : {asalmasalah_ibu}<br/>"
              teks_hasil += f"Asal Masalah Awal : 6<br/>"
              teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br/>"
              
            elif (cucu_pr > 0 and nenek > 0):
              asalmasalah_ubah = asalmasalah_nenek + asalmasalah_cucupr
              teks_hasil += f"Asal Masalah Sisa {sisa}<br/>"
              teks_hasil += f"Siham Cucu Perempuan : {asalmasalah_cucupr}<br/>"
              teks_hasil += f"Siham Nenek : {asalmasalah_nenek}<br/>"
              teks_hasil += f"Asal Masalah Awal : 6<br/>"
              teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br/>"
              
            else:
              if (saudari_seibu > 0 or saudara_seibu > 0 and masuk == "saudari-sibu"):
                # saudara
                if (saudara_seibu == 1):
                  asalmasalah_saudara_seibu = 1
                elif (saudara_seibu > 1):
                  if(ibu == False and nenek == 0):
                    asalmasalah_saudara_seibu = 1
                  else:
                    asalmasalah_saudara_seibu = 2
                else:
                  asalmasalah_saudara_seibu = 0
                # saudari
                if (saudari_seibu == 1):
                  asalmasalah_saudari_seibu = 1
                elif (saudari_seibu > 1):
                  if(ibu == False and nenek == 0):
                    asalmasalah_saudari_seibu = 1
                  else:
                    asalmasalah_saudari_seibu = 2
                else:
                  asalmasalah_saudari_seibu = 0
                asalmasalah_ubah = asalmasalah_ibu + asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                teks_hasil += f"Asal Masalah Sisa {sisa}<br/>"
                if(nenek > 0):
                  teks_hasil += f"Siham Nenek: {asalmasalah_nenek}<br/>"
                elif(ibu == True):
                  teks_hasil += f"Siham Ibu: {asalmasalah_ibu}<br/>"
                if (saudari_seibu != 0):
                  teks_hasil += f"Siham Saudari Sibu : {asalmasalah_saudari_seibu}<br/>"
                if (saudara_seibu != 0):
                  teks_hasil += f"Siham Saudara Sibu : {asalmasalah_saudara_seibu}<br/>"
                if(ibu == False and nenek == 0):
                  if(saudari_seibu > 1 and saudara_seibu == 0):
                    teks_hasil += f"Asal Masalah Awal : 3<br/>"
                  elif(saudara_seibu > 1 and saudari_seibu == 0):
                    teks_hasil += f"Asal Masalah Awal : 3<br/>"
                  elif(saudara_seibu > 1 and saudari_seibu > 1):
                    teks_hasil += f"Asal Masalah Awal : 6<br/>"
                  else:
                    teks_hasil += "Asal Masalah Awal : 6<br/>"   
                else:
                  teks_hasil += f"Asal Masalah Awal : 6<br/>"
                teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
                
              else:
                teks_hasil += f"Asal Masalah Awal : {int(asalmasalah)}<br>"
                teks_hasil += f"Asal Masalah Menjadi : {int(jumlahasalmasalah)}<br>"
        else:
          teks_hasil += f"Asal Masalah Sisa : {int(asalmasalah - jumlahasalmasalah)}<br>"
      else:
        if (tampil == "ubah"):
          if (anak_pr > 0 and nenek > 0):
            asalmasalah_ubah = asalmasalah_nenek + asalmasalah_anakpr + asalmasalah_cucupr
            teks_hasil += f"Asal Masalah Sisa {sisa}<br>"
            teks_hasil += f"Siham Anak Perempuan : {asalmasalah_anakpr}<br>"
            if (cucu_pr > 0):
              teks_hasil += f"Siham Cucu Perempuan : {asalmasalah_cucupr}<br>"
            teks_hasil += f"Siham Nenek : {asalmasalah_nenek}<br>"
            teks_hasil += f"Asal Masalah Awal : 6<br>"
            teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
            
          elif (anak_pr > 0 and ibu == True):
            asalmasalah_ubah = asalmasalah_ibu + asalmasalah_anakpr + asalmasalah_cucupr
            teks_hasil += f"Asal Masalah Sisa {sisa}<br>"
            teks_hasil += f"Siham Anak Perempuan : {asalmasalah_anakpr}<br>"
            if (cucu_pr > 0):
              teks_hasil += f"Siham Cucu Perempuan : {asalmasalah_cucupr}<br>"
            teks_hasil += f"Siham Ibu : {asalmasalah_ibu}<br>"
            teks_hasil += f"Asal Masalah Awal : 6<br>"
            teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
            
          else:
            if (cucu_pr > 0 and ibu == True):
              asalmasalah_ubah = asalmasalah_ibu + asalmasalah_cucupr
              teks_hasil += f"Asal Masalah Sisa {sisa}<br>"
              teks_hasil += f"Siham Cucu Perempuan : {asalmasalah_cucupr}<br>"
              teks_hasil += f"Siham Ibu : {asalmasalah_ibu}<br>"
              teks_hasil += f"Asal Masalah Awal : 6<br>"
              teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              
            elif (cucu_pr > 0 and nenek > 0):
              asalmasalah_ubah = asalmasalah_nenek + asalmasalah_cucupr
              teks_hasil += f"Asal Masalah Sisa {sisa}<br>"
              teks_hasil += f"Siham Cucu Perempuan : {asalmasalah_cucupr}<br>"
              teks_hasil += f"Siham Nenek : {asalmasalah_nenek}<br>"
              teks_hasil += f"Asal Masalah Awal : 6<br>"
              teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
              
            else:
              if (saudari_seibu > 0 or saudara_seibu > 0 and masuk == "saudari-sibu"):
                # saudara
                if (saudara_seibu == 1):
                  asalmasalah_saudara_seibu = 1
                elif (saudara_seibu > 1):
                  if(ibu == False and nenek == 0):
                    asalmasalah_saudara_seibu = 1
                  else:
                    asalmasalah_saudara_seibu = 2
                else:
                  asalmasalah_saudara_seibu = 0
                # saudari
                if (saudari_seibu == 1):
                  asalmasalah_saudari_seibu = 1
                elif (saudari_seibu > 1):
                  if(ibu == False and nenek == 0):
                    asalmasalah_saudari_seibu = 1
                  else:
                    asalmasalah_saudari_seibu = 2
                else:
                  asalmasalah_saudari_seibu = 0
                asalmasalah_ubah = asalmasalah_ibu + asalmasalah_nenek + asalmasalah_saudari_seibu + asalmasalah_saudara_seibu
                teks_hasil += f"Asal Masalah Sisa {sisa}<br>"
                if(nenek > 0):
                  teks_hasil += f"Siham Nenek: {asalmasalah_nenek}<br>"
                elif(ibu == True):
                  teks_hasil += f"Siham Ibu: {asalmasalah_ibu}<br>"
                if (saudari_seibu != 0):
                  teks_hasil += f"Siham Saudari Sibu : {asalmasalah_saudari_seibu}<br>"
                if (saudara_seibu != 0):
                  teks_hasil += f"Siham Saudara Sibu : {asalmasalah_saudara_seibu}<br>"
                if(ibu == False and nenek == 0):
                  if(saudari_seibu > 1 and saudara_seibu == 0):
                    teks_hasil += f"Asal Masalah Awal : 3<br>"
                  elif(saudara_seibu > 1 and saudari_seibu == 0):
                    teks_hasil += f"Asal Masalah Awal : 3<br>"
                  elif(saudara_seibu > 1 and saudari_seibu > 1):
                    teks_hasil += f"Asal Masalah Awal : 6<br>"
                  else:
                    teks_hasil += "Asal Masalah Awal : 6<br>"   
                else:
                  teks_hasil += f"Asal Masalah Awal : 6<br>"
                teks_hasil += f"Asal Masalah Menjadi : {int(asalmasalah_ubah)}<br>"
                
              else:
                teks_hasil += f"Asal Masalah Awal : {int(asalmasalah)}<br>"
                teks_hasil += f"Asal Masalah Menjadi : {int(jumlahasalmasalah)}<br>"
        else:
          teks_hasil += f"Asal Masalah Sisa : {int(sisa)}<br>"
      # bagian cucu laki dan cucu perempuan
      finalbagiancucupr = 0
      finalbagiancuculk = 0
      sisa_cucu = 0
      cucu = ""
      if (cucu_pr > 0 and cucu_lk == 0):
        cucu = "kondisi1"
        finalbagiancuculk = 0
        if (bagiancucupr != "termahjub"):
          if (cucu_pr > 0 and anak_pr > 0):
            if (ayah == False and kakek == False):
              if (ibu == True):
                asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr + asalmasalah_ibu
              else:
                if (nenek > 0):
                  asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr + asalmasalah_nenek
                else:
                  asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr
              sisa_harta_cucu_pr = harta - ambil_bagian_harta
              suku_bagian_cucu = sisa_harta_cucu_pr / asalmasalah_sisa
            else:
              suku_bagian_cucu = harta / asalmasalah
            finalbagiancucupr = asalmasalah_cucupr * suku_bagian_cucu
            # sisa_harta_cucu_pr = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu - finalbagiannenek - finalbagiankakek
          elif (cucu_pr > 0 and anak_pr == 0):
            if (ayah == False and kakek == False):
              if (ibu == True):
                asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr + asalmasalah_ibu
              else:
                if (nenek > 0):
                  asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr + asalmasalah_nenek
                else:
                  asalmasalah_sisa = asalmasalah_anakpr + asalmasalah_cucupr
              sisa_harta_cucu_pr = harta - ambil_bagian_harta
              suku_bagian_cucu = sisa_harta_cucu_pr / asalmasalah_sisa
            else:
              suku_bagian_cucu = harta / asalmasalah
            finalbagiancucupr = asalmasalah_cucupr * suku_bagian_cucu
            # sisa_harta_cucu_pr = harta - ambil_bagian_harta - finalbagianayah - finalbagianibu - finalbagiannenek - finalbagiankakek

          else:
            finalbagiancucupr = asalmasalah_cucupr * suku_bagian
        else:
          finalbagiancucupr = 0
      elif (cucu_pr == 0 and cucu_lk > 0):
        if (bagiancuculk != "termahjub"):
          cucu = "kondisi2"
          sisa_harta_cucu = harta - ambil_bagian_harta - finalbagiananakpr - \
            finalbagianayah - finalbagiankakek - finalbagianibu - finalbagiannenek
          sisa_harta_cucu_lk = (1 * sisa_harta_cucu)
          finalbagiancuculk = sisa_harta_cucu_lk * cucu_lk
        else:
          finalbagiancuculk = 0
        sisa_cucu = finalbagiancuculk

      elif (cucu_pr > 0 and cucu_lk > 0):
        cucu = "kondisi3"
        asalmasalah_sisa_cucu = asalmasalah_cucupr + asalmasalah_cuculk
        sisa_harta_cucu = harta - ambil_bagian_harta - finalbagiananakpr - \
          finalbagianayah - finalbagiankakek - finalbagianibu - finalbagiannenek
        suku_bagian_cucu = sisa_harta_cucu / asalmasalah_sisa_cucu
        sisa_harta_cucu_pr = (1 * suku_bagian_cucu)
        sisa_harta_cucu_lk = (2 * suku_bagian_cucu)
        if (bagiancucupr != "termahjub"):
          finalbagiancucupr = sisa_harta_cucu_pr * cucu_pr
        else:
          finalbagiancucupr = 0
        if (bagiancuculk != "termahjub"):
          finalbagiancuculk = sisa_harta_cucu_lk * cucu_lk
        else:
          finalbagiancuculk = 0
        sisa_cucu = finalbagiancucupr + finalbagiancuculk
      # tampil bagian suami
      if (suami == True):
        teks_hasil += f"Bagian Harta Suami : {round(finalbagiansuami, 2)}<br/>"
      else:
        # tampil bagian istri jika lebih 1 harta per istri
        if (istri > 1):
          bagi_harta_istri = finalbagianistri / istri
          teks_hasil += f"Bagian Harta Istri : {round(finalbagianistri, 2)}<br/>"
          j = 1
          while j <= istri:
            teks_hasil += f"Harta Untuk Istri Ke- {j} = {bagi_harta_istri}<br>"
            j += 1
        else:
          if (istri != 0):
            teks_hasil += f"Bagian Harta Istri : {round(finalbagianistri, 2)}<br/>"
      if (bagianayah == 0.16 and bagiansisa == "+sisa"):
        sisa_harta_ayah = harta - ambil_bagian_harta - finalbagianayah - \
          finalbagiananakpr - finalbagianibu - finalbagiannenek - finalbagiancucupr
        teks_hasil += f"Bagian Harta Ayah 1/6 + sisa: {round(finalbagianayah, 2)} + {round(sisa_harta_ayah, 2)}<br/>"
        teks_hasil += f"Harta untuk ayah =  {round(finalbagianayah + sisa_harta_ayah , 2)}<br/>"
      else:
        sisa_harta_ayah = 0
        if (ayah == True):
          teks_hasil += f"Bagian Harta Ayah : {round(finalbagianayah)}<br/>"
      if (ibu == True):
        teks_hasil += f"Bagian Harta Ibu : {round(finalbagianibu, 2)}<br/>"
      if (nenek > 1):
        bagi_harta_nenek = finalbagiannenek / nenek
        teks_hasil += f"Bagian Harta Nenek : {round(finalbagiannenek, 2)}<br/>"
        j = 1
        while j <= nenek:
          teks_hasil += f"Harta Untuk Nenek Ke- {j} = round(bagi_harta_nenek, 2)<br/>"
          j += 1
      else:
        if (nenek != 0):
          teks_hasil += f"Bagian Harta Nenek : {round(finalbagiannenek, 2)}<br/>"
      if (bagiankakek == 0.16 and bagiansisakakek == "+sisa"):
        sisa_harta_kakek = harta - ambil_bagian_harta - finalbagiankakek - \
          finalbagiananakpr - finalbagianibu - finalbagiannenek - finalbagiancucupr
        teks_hasil += f"Bagian Harta Kakek 1/6 + sisa: {round(finalbagiankakek, 2)} + {round(sisa_harta_kakek, 2)}<br/>"
        teks_hasil += f"Harta untuk kakek =  {round(finalbagiankakek + sisa_harta_kakek, 2)}<br/>"
      else:
        sisa_harta_kakek = 0
        if (kakek == True):
          teks_hasil += f"Bagian Harta Kakek : {round(finalbagiankakek, 2)}<br/>"
      if (anak_pr > 1):
        sisa_harta = harta - ambil_bagian_harta
        if (ayah == False and ibu == False):
          if (kakek == True and nenek > 0):
            # sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - finalbagiannenek - sisa_harta_kakek
            # if(cucu_lk > 0):
            #     sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - finalbagiannenek - sisa_harta_kakek - sisa_cucu
            # else:
            #     sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - finalbagiannenek - sisa_harta_kakek - finalbagiancucupr
            # suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            # finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
            finalbagiananakpr = finalbagiananakpr
          elif (kakek == False and nenek > 0):
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - finalbagiannenek - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagiannenek - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
          elif (kakek == True and nenek == 0):
            if (bagiankakek == 0.16 and bagiansisakakek == "+sisa"):
              if (cucu_lk > 0):
                sisa_harta = harta - ambil_bagian_harta - \
                  finalbagiankakek - sisa_harta_kakek - sisa_cucu
              else:
                sisa_harta = harta - ambil_bagian_harta - \
                  finalbagiankakek - sisa_harta_kakek - finalbagiancucupr
              suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
              finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
            else:
              if (cucu_lk > 0):
                sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - sisa_cucu
              else:
                sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - finalbagiancucupr
              suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
              finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
          else:
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
            # suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            # finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
        elif (ayah == False and ibu == True):
          if (kakek == True):
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
          else:
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - finalbagianibu - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
        elif (ayah == True and ibu == False):
          if (nenek > 0):
            # sisa_harta = harta - ambil_bagian_harta - finalbagiannenek
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - finalbagiannenek - \
                sisa_harta_ayah - finalbagianayah - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagiannenek - \
                sisa_harta_ayah - finalbagianayah - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
          else:
            if (bagianayah == 0.16 and bagiansisa == "+sisa"):
              sisa_harta = harta - ambil_bagian_harta - \
                finalbagianayah - sisa_harta_ayah - finalbagiancucupr
              suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
              finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
            else:
              if (cucu_lk > 0):
                sisa_harta = harta - ambil_bagian_harta - finalbagianayah - sisa_cucu
              else:
                sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagiancucupr
              suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
              finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
        teks_hasil += f"Bagian Harta Anak Perempuan : {round(finalbagiananakpr, 2)}<br/>"
        sisa_harta_anak_pr = finalbagiananakpr / anak_pr
        # pembagian harta per anak perempuan
        i = 1
        while i <= anak_pr:
          teks_hasil += f"Harta Untuk Anak Perempuan {i} = {round(sisa_harta_anak_pr, 2)}<br/>"
          i += 1
      elif (anak_pr == 1):
        if (ayah == False and ibu == False):
          if (kakek == True and nenek > 0):
            # if(cucu_lk > 0):
            #     sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - finalbagiannenek - sisa_harta_kakek - sisa_cucu
            # else:
            #     sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - finalbagiannenek - sisa_harta_kakek - finalbagiancucupr
            # suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            # finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
            finalbagiananakpr = finalbagiananakpr
          elif (kakek == False and nenek > 0):
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - finalbagiannenek - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagiannenek - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
          elif (kakek == True and nenek == 0):
            if (bagiankakek == 0.16 and bagiansisakakek == "+sisa"):
              if (cucu_lk > 0):
                sisa_harta = harta - ambil_bagian_harta - \
                  finalbagiankakek - sisa_harta_kakek - sisa_cucu
              else:
                sisa_harta = harta - ambil_bagian_harta - \
                  finalbagiankakek - sisa_harta_kakek - finalbagiancucupr
              suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
              finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
            else:
              if (cucu_lk > 0):
                sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - sisa_cucu
              else:
                sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - finalbagiancucupr
              suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
              finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
          else:
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
        elif (ayah == False and ibu == True):
          if (kakek == True):
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - \
                finalbagianibu - sisa_harta_kakek - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagiankakek - \
                finalbagianibu - sisa_harta_kakek - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
          else:
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - finalbagianibu - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
        elif (ayah == True and ibu == False):
          if (nenek > 0):
            # sisa_harta = harta - ambil_bagian_harta - finalbagiannenek
            if (cucu_lk > 0):
              sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
                finalbagiannenek - sisa_harta_ayah - sisa_cucu
            else:
              sisa_harta = harta - ambil_bagian_harta - finalbagianayah - \
                finalbagiannenek - sisa_harta_ayah - finalbagiancucupr
            suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
            finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
          else:
            if (bagianayah == 0.16 and bagiansisa == "+sisa"):
              if (cucu_lk > 0):
                sisa_harta = harta - ambil_bagian_harta - \
                  finalbagianayah - sisa_harta_ayah - sisa_cucu
              else:
                sisa_harta = harta - ambil_bagian_harta - \
                  finalbagianayah - sisa_harta_ayah - finalbagiancucupr
              suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
              finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
            else:
              if (cucu_lk > 0):
                sisa_harta = harta - ambil_bagian_harta - finalbagianayah - sisa_cucu
              else:
                sisa_harta = harta - ambil_bagian_harta - finalbagianayah - finalbagiancucupr
              suku_bagian_sisa = sisa_harta / asalmasalah_anakpr
              finalbagiananakpr = suku_bagian_sisa * asalmasalah_anakpr
        teks_hasil += f"Bagian Harta Anak Perempuan : {round(finalbagiananakpr, 2)}<br/>"
      # bagian harta cucu pr
      if (cucu == "kondisi1"):
        if (bagiancucupr != "termahjub"):
          teks_hasil += f"Bagian Harta Cucu Perempuan : {round(finalbagiancucupr, 2)}<br/>"
          if (finalbagiancucupr == 0):
            sisa_harta_cucu_pr = 0
          else:
            sisa_harta_cucu_pr = finalbagiancucupr / cucu_pr
          # pembagian harta per cucu perempuan
          if (cucu_pr > 1):
            i = 1
            while i <= cucu_pr:
              teks_hasil += f"Harta Untuk Cucu Perempuan {i} = {round(sisa_harta_cucu_pr, 2)}<br/>"
              i += 1
      elif (cucu == "kondisi2"):
        # pembagian harta per cucu laki-laki
        if (bagiancuculk != "termahjub"):
          teks_hasil += f"Harta Cucu Laki-Laki : {round(finalbagiancuculk, 2)}<br/>"
          if (cucu_lk > 1):
            j = 1
            while j <= cucu_lk:
              teks_hasil += f"Harta Untuk Cucu Laki - Laki {j} = {round(sisa_harta_cucu_lk, 2)}<br/>"
              j += 1
      elif (cucu == "kondisi3"):
        # pembagian harta per cucu perempuan
        if (bagiancucupr != "termahjub"):
          teks_hasil += f"Harta Cucu Perempuan : {round(finalbagiancucupr, 2)}<br/>"
          if (cucu_pr > 1):
            i = 1
            while i <= cucu_pr:
              teks_hasil += f"Harta Untuk Cucu Perempuan {i} = {round(sisa_harta_cucu_pr, 2)}<br/>"
              i += 1
        # pembagian harta per cucu laki-laki
        if (bagiancuculk != "termahjub"):
          teks_hasil += f"Harta Cucu Laki-Laki : {round(finalbagiancuculk, 2)}<br/>"
          if (cucu_lk > 1):
            j = 1
            while j <= cucu_lk:
              teks_hasil += f"Harta Untuk Cucu Laki - Laki {j} = {round(sisa_harta_cucu_lk, 2)}<br/>"
              j += 1
      # saudara sibu dan saudari sibu
      if (saudara_seibu > 0 and saudari_seibu == 0):
        if (bagiansaudaraseibu != "termahjub"):
          if (masuk == "saudari-sibu"):
            if (saudara_seibu == 1):
              asalmasalah_saudara_seibu = 1
            else:
              asalmasalah_saudara_seibu = 2
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara = asalmasalah_saudara_seibu
          suku_bagian_saudara = sisa_harta / asalmasalah_saudara
          bagianharta_saudara_sibu = (asalmasalah_saudara_seibu * suku_bagian_saudara)
          finalbagiansaudarasibu = bagianharta_saudara_sibu / saudara_seibu
          teks_hasil += f"Harta Saudara Seibu : {round(bagianharta_saudara_sibu, 2)}<br/>"
          if (saudara_seibu > 1):
            j = 1
            while j <= saudara_seibu:
              teks_hasil += f"Harta Untuk Saudara Seibu {j} =  {round(finalbagiansaudarasibu, 2)}<br/>"
              j += 1
      elif (saudara_seibu == 0 and saudari_seibu > 0):
        if (bagiansaudariseibu != "termahjub"):
          if (masuk == "saudari-sibu"):
            if (saudari_seibu == 1):
              asalmasalah_saudari_seibu = 1
            else:
              asalmasalah_saudari_seibu = 2
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek
          if (sisa_harta <= 0):
            sisa_harta = 0
          asalmasalah_saudara = asalmasalah_saudari_seibu
          suku_bagian_saudari = sisa_harta / asalmasalah_saudara
          bagianharta_saudari_sibu = (asalmasalah_saudari_seibu * suku_bagian_saudari)
          finalbagiansaudarisibu = bagianharta_saudari_sibu / saudari_seibu
          teks_hasil += f"Harta Saudari Sibu : {round(bagianharta_saudari_sibu, 2)}<br/>"
          if (saudari_seibu > 1):
            j = 1
            while j <= saudari_seibu:
              teks_hasil += f"Harta Untuk Saudari Sibu {j} = {round(finalbagiansaudarisibu, 2)}<br/>"
              j += 1
      elif (saudara_seibu > 0 and saudari_seibu > 0):
        if (bagiansaudaraseibu != "termahjub" and bagiansaudariseibu != "termahjub"):
          # hitung_jumlah_saudara = saudara_seibu + saudari_seibu
          # if (hitung_jumlah_saudara > 2):
          #     if(masuk == "saudari1"):
          #         harta_sibu = harta / totalasalmasalah
          #     else:
          #         harta_sibu = harta / jumlahasalmasalah
          #     hitung_saudara = asalmasalah_saudara_seibu * harta_sibu
          #     hitung_saudari = asalmasalah_saudari_seibu * harta_sibu
          #     proses_hitung = hitung_saudara + hitung_saudari
          #     suku_bagian_saudara = proses_hitung / hitung_jumlah_saudara
          #     bagianharta_saudari_sibu = saudari_seibu * suku_bagian_saudara
          #     bagianharta_saudara_sibu = saudara_seibu * suku_bagian_saudara
          # else:
          if (masuk == "saudari-sibu"):
            # saudara
            if (saudara_seibu > 1):
              asalmasalah_saudara_seibu = 2
            else:
              asalmasalah_saudara_seibu = 1
            # saudari
            if (saudari_seibu > 1):
              asalmasalah_saudari_seibu = 2
            else:
              asalmasalah_saudari_seibu = 1
          sisa_harta = harta - ambil_bagian_harta - finalbagianibu - finalbagiannenek
          if (sisa_harta <= 0):
            sisa_harta = 0
          hitung_jumlah_saudara = saudara_seibu + saudari_seibu
          if (hitung_jumlah_saudara > 2):
            asalmasalah_saudara = asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
            harta_sibu = sisa_harta / asalmasalah_saudara
            hitung_saudara = asalmasalah_saudara_seibu * harta_sibu
            hitung_saudari = asalmasalah_saudari_seibu * harta_sibu
            proses_hitung = hitung_saudara + hitung_saudari
            suku_bagian_saudara = proses_hitung / hitung_jumlah_saudara
            bagianharta_saudari_sibu = saudari_seibu * suku_bagian_saudara
            bagianharta_saudara_sibu = saudara_seibu * suku_bagian_saudara
          else:
            asalmasalah_saudara = asalmasalah_saudara_seibu + asalmasalah_saudari_seibu
            suku_bagian_saudara = sisa_harta / asalmasalah_saudara
            bagianharta_saudari_sibu = asalmasalah_saudari_seibu * suku_bagian_saudara
            bagianharta_saudara_sibu = asalmasalah_saudara_seibu * suku_bagian_saudara
          finalbagiansaudarisibu = (bagianharta_saudari_sibu / saudari_seibu)
          finalbagiansaudarasibu = (bagianharta_saudara_sibu / saudara_seibu)
          
          teks_hasil += f"Harta Saudari Seibu : {round(bagianharta_saudari_sibu, 2)}<br/>"
          if (saudari_seibu > 1):
            i = 1
            while i <= saudari_seibu:
              teks_hasil += f"Harta Untuk Saudari Seibu {i} = {round(finalbagiansaudarisibu, 2)}<br/>"
              i += 1
          teks_hasil += f"Harta Saudara Seibu : {round(bagianharta_saudara_sibu, 2)}<br/>"
          if (saudara_seibu > 1):
            j = 1
            while j <= saudara_seibu:
              teks_hasil += f"Harta Untuk Saudara Seibu {j} = {round(finalbagiansaudarasibu, 2)}<br/>"
              j += 1

    response += [teks_hasil]

    return response
  else:
    response.append("Terjadi Kesalahan")

  return response