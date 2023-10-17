import { createApp } from 'vue'
import App from './App.vue'

import './assets/main.css'
import { createStore } from 'vuex'
import axios from 'axios'
import VueAxios from 'vue-axios'
import SocketIO from 'socket.io-client'
import VueSocketIO from 'vue-3-socket.io'
import moment from 'moment'
const envVar = import.meta.env;

moment.locale('id');
const socket_url = envVar.VITE_SOCKETIO_HOST || 'ws://127.0.0.1:5000'
const socket = SocketIO(`${socket_url}/chats`);
const store = createStore({})
axios.defaults.baseURL = envVar.VITE_BACKEND_URL || 'http://127.0.0.1:5000';
axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded';

createApp(App)
  .use(store)
  .use(VueAxios, axios)
  .use(new VueSocketIO({
    debug: true,
    connection: socket
  }))
  .mount('#app')