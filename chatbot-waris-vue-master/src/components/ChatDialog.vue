<script>
import Chat from './Chat.vue';
import moment from 'moment'

export default {
  setup() {

    const room = localStorage.getItem('room')

    return {
      room
    }
  },
  props: {
    user_id: Number
  },
  components: {
    Chat
  },
  data() {
    return {
      chats: [],
      message: null,
      isConnected: false
    }
  },
  methods: {
    scrollChat() {
      const el = this.$refs.scrollToMe;

      if (el) {
        // Use el.scrollIntoView() to instantly scroll to the element
        el.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    },
    scrolledChat(e) {
      // const elChats = this.$refs.chats;
      console.log(e.target.client);
    },
    async getUserRoom() {
      await this.axios.get('/chat-room/room/user/'+this.user_id).then(res => {
        if (res.status == 200) {
          const data = res.data
          console.log(res);
          if (data.room !== null) {
            console.log(data.room);
            localStorage.setItem("room", data.room.id)
            this.connectRoom(data.room.id)
          } else {
            this.createRoom(this.user_id)
            const room = parseInt(localStorage.getItem("room"))
            this.connectRoom(room)
          }
        } else {
          console.error(res)
        }
      })
    },
    async createRoom(user_id) {
      const data = {
        user_id: user_id
      }
      await this.axios.post('/chat-room/create', data).then(res => {
        if(res.status == 200) {
          const data = res.data
          localStorage.setItem("room", data.room.id)
          console.log('room created')
        } else {
          console.error(res)
        }
      });
    },
    connectRoom(room_id) {
      console.log('connecting to ' + room_id)
      this.$socket.emit('join', {
        user: this.user_id,
        room: room_id
      })
    },
    async getMessages(room_id){
      await this.axios.get('/messages/'+room_id).then(res => {
        if (res.status == 200) {
          const data = res.data
          console.log(data)
          if(data.data_msgs) {
            this.chats = data.data_msgs
          } else {
            console.log('No messages!!')
          }
        } else {
          console.log('Failed get messages!!')
        }
      })
    },
    sendMessage() {
      const data = {
        message: this.message
      }
      if (data.message !== null && data.message !== '') {
        this.axios.post('/messages/create/' + this.room, data).then(res => {
          if (res.status == 200) {
            const data = res.data
            if (data.data_msg) {
              this.chats.push(data.data_msg)
              this.$socket.emit('send_message', data.data_msg)
              this.message = null
              setTimeout(this.scrollChat(), 2000)
            } else {
              console.log('No messages!!')
            }
          } else {
            console.log('Failed get messages!!')
          }
        })
      }
    },
    async startChat(room_id) {
      var res = await this.axios.get('/start-chat/' + room_id)
      if (res.status == 200) {
        const data = res.data
        console.log(data)
        if (data.data) {
          this.chats.push(data.data)
        } else {
          console.log('No messages!!')
        }
      } else {
        console.log('Failed start chat!!')
      }
    }
  },
  computed: {
    chatsComputed() {
      return this.chats.map(function (item) {
        return {
          id: item.id,
          from: item.message_from == 'u' ? 'user' : 'bot',
          message: item.message_text,
          date_sent: moment.utc(item.created_at, "ddd, DD MMM YYYY HH:mm:ss").local().format('ddd, DD MMM YYYY HH:mm:ss'),
          read_at: item.read_at
        };
      });
    },
    isChatScrolled() {
      const scrollToMe = this.$refs.scrollToMe;
      const elChats = this.$refs.chats;
      return elChats.scrollTop;
    },
    isStartMessageReceive() {
      const last_chat = this.chats.at(-1);
      if (last_chat) {
        const now = moment();
        const last_chat_created = moment.utc(last_chat.created_at, "ddd, DD MMM YYYY HH:mm:ss");
        const diffHour = now.diff(last_chat_created, 'hour');
        if (last_chat.message_text === "Assalamu'alaikum Wr. Wb<br/>Selamat datang di sistem chatbot waris!! Silahkan ketik /hitung untuk memulai perhitungan waris!!" && diffHour < 2) {
          return true
        }
      }
      return false;
    }
  },
  sockets: {
    connect: function () {
      console.log('Socket Connected');
      this.isConnected = true;
    },
    disconnect: function () {
      console.log('Disconnected');
      this.isConnected = false
    },
    join: function (data) {
      console.log(data)
    },
    leave: function (data) {
      console.log(data)
    },
    start_reply_message: function (data) {
      console.log(data)
      this.chats.push(data);
    },
    reply_message: function (data) {
      for (const key in data) {
        if (Object.hasOwnProperty.call(data, key)) {
          const element = data[key];
          this.chats.push(element);
        }
      }
      setTimeout(this.scrollChat(), 2000);
    }
  },
  async mounted() {
    if (this.user_id) {
      await this.getUserRoom();
      await this.getMessages(this.room)
    }
    if (this.room && !this.isStartMessageReceive) {
      console.log('start Message')
      await this.startChat(this.room);
    }
    this.scrollChat();
  },
  updated() {
    // const scrollToMe = this.$refs.scrollToMe;
    // if (scrollToMe) {
    //   console.log(scrollToMe.scrollTop);
    // }
    // const chats = this.$refs.chats;
    // if(chats) {
    //   console.log(scrollToMe.scrollHeight);
    // }
    this.scrollChat();
  }

}
</script>

<template>
  <div class="chat-dialog">
    <div class="chat-items" ref="chats">
      <Chat v-for="chat in chatsComputed" :key="chat.id" :chat="chat" :sender="chat.from == 'user' ? true : false" />
      <div ref="scrollToMe"></div>
    </div>
    <div class="chat-button">
      <textarea type="textarea" @keydown.enter="sendMessage" v-model="message" class="m-0 border-0 p-0 w-full py-1 px-3 resize-none focus:ring-0 focus-visible:ring-0 overflow-x-hidden" rows="1" placeholder="Write some message!!"></textarea>
      <button type="button" class="bg-slate-200 right-0 py-1 px-3 hover:bg-indigo-200 active:bg-gray-500" :onclick="sendMessage">Send</button>
    </div>
  </div>
</template>