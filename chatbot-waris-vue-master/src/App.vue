<script setup>
import ChatDialog from './components/ChatDialog.vue';

</script>

<script>
export default {
  data() {
    return {
      user: null
    }
  },
  methods: {
    checkUser() {
      const user = localStorage.getItem('user')
      if (user) {
        this.axios.get('/guest/check', 
          {
            params: {
              guest_id: user
            }
          }).then(res => {
            if (localStorage.getItem('user') == null && res.data != null) {
              localStorage.setItem('user', res.data.guest_id)
              this.user = res.data.guest_id
            }
            console.log(res)
          })
      } else {
        this.createUser()
      }
    },
    createUser() {
      this.axios.post('/guest/create').then(res => {
        if (res.status == 200) {
          const data = res.data
          localStorage.setItem('user', data.guest_id)
          this.user = data.guest_id
        } else {
          console.log(res)
        }
      })
    }
  },
  computed: {
    getUserId() {
      const user = localStorage.getItem('user')
      return user != null ? parseInt(user) : null;
    }
  },
  mounted() {
    this.checkUser()
  }
}
</script>


<template>
  <div class="flex flex-col mb-1">
    <header class="w-full py-1 text-center justify-self-center bg-[#1ba36a]">
      <h2 class="font-bold text-white">Chatbot Waris</h2>
    </header>
    
    <main class="h-full">
      <ChatDialog :user_id="getUserId" />
    </main>
  </div>
</template>
