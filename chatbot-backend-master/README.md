# Chatbot backend
Chatbot backend for waris

Cara install awal

1. Buka terminal/CMD/PowerShell di folder chatbot-backend (disini)
2. jalankan command berikut
```
pip install -r requirements.txt
```

Inisiasi database :
```
python init_db.py
```

Run Server :
```
flask run
```

## Developer/debug mode
jika ingin menggunakan development mode/debug mode jalankan command berikut sebelum run server :

Windows
```
set FLASK_DEBUG=TRUE
```

Linux
```
export FLASK_DEBUG=TRUE
```
