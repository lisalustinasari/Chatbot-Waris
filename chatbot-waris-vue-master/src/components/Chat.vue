<template>
  <div :class="classChat">
    <div class="chat-card">
      <div class="chat-user">{{ this.chat.from }}</div>
      <p class="chat-message" v-html="this.chat.message"></p>
      <div class="chat-date">{{ this.chat.date_sent }}</div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    sender: Boolean,
    chat: {
      id: Number,
      from: String,
      message: String,
      date_sent: String
    }
  },
  data() {
    return {
      // chatData: this.chat
    }
  },
  computed: {
    classChat() {
      return this.sender ? 'chat-sender' : 'chat-receiver'
    }
  }
}
</script>