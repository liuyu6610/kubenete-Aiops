<template>
  <div class="ai-copilot">
    <!-- Floating Button -->
    <button 
      class="copilot-toggle" 
      :class="{ 'copilot-toggle--active': isOpen }"
      @click="isOpen = !isOpen"
    >
      <div class="glow-dot" style="margin-right: 8px;"></div>
      <span class="copilot-toggle__text">AI 助手</span>
    </button>

    <!-- Chat Panel -->
    <transition name="slide-up">
      <div v-if="isOpen" class="copilot-panel glass-card">
        <div class="panel-header">
          <span class="panel-title">🧠 KubeSentinel Copilot</span>
          <button class="close-btn" @click="isOpen = false">×</button>
        </div>
        
        <div class="chat-area" ref="chatArea">
          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            class="message"
            :class="msg.role === 'user' ? 'message--user' : 'message--ai'"
          >
            <div class="message__content">{{ msg.content }}</div>
          </div>
          <div v-if="isLoading" class="message message--ai">
            <div class="message__content typing-indicator">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        </div>

        <div class="input-area">
          <input 
            v-model="input" 
            @keyup.enter="sendMessage"
            type="text" 
            placeholder="询问集群状态或故障原因..." 
            class="chat-input"
          />
          <button @click="sendMessage" class="send-btn" :disabled="isLoading || !input.trim()">
            发送
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'

const isOpen = ref(false)
const input = ref('')
const isLoading = ref(false)
const chatArea = ref(null)
const { send, onMessage } = useWebSocket()

const messages = ref([
  { role: 'ai', content: '你好！我是 KubeSentinel AI (由 GLM-5 架构驱动)，可以自主提取监控、查阅日志、分析事件并生成排障与治愈方案。' }
])

const scrollToBottom = async () => {
  await nextTick()
  if (chatArea.value) {
    chatArea.value.scrollTop = chatArea.value.scrollHeight
  }
}

onMounted(() => {
  onMessage((data) => {
    if (data.type === 'CHAT_RESPONSE') {
      messages.value.push({ role: 'ai', content: data.payload })
      isLoading.value = false
      scrollToBottom()
    }
  })
})

const sendMessage = async () => {
  if (!input.value.trim() || isLoading.value) return
  
  const userText = input.value.trim()
  messages.value.push({ role: 'user', content: userText })
  input.value = ''
  isLoading.value = true
  scrollToBottom()

  // Real LLM Copilot interaction via WebSocket
  send({ type: 'CHAT_REQUEST', payload: userText })
}
</script>

<style scoped>
.ai-copilot {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 9999;
}

.copilot-toggle {
  display: flex;
  align-items: center;
  background: var(--bg-card);
  border: 1px solid var(--accent-primary);
  color: var(--text-primary);
  padding: 12px 24px;
  border-radius: 30px;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
  transition: all 0.3s ease;
  font-family: var(--font-sans);
  font-weight: 600;
}
.copilot-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.6);
}
.copilot-toggle--active {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
}

.copilot-panel {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 360px;
  height: 500px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(10, 14, 26, 0.5);
}
.panel-title {
  font-weight: 700;
  font-size: 14px;
  color: var(--text-primary);
}
.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 20px;
  cursor: pointer;
}
.close-btn:hover {
  color: var(--color-danger);
}

.chat-area {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  max-width: 85%;
  display: flex;
}
.message--user {
  align-self: flex-end;
}
.message--user .message__content {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: white;
  border-radius: 16px 16px 0 16px;
}
.message--ai {
  align-self: flex-start;
}
.message--ai .message__content {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 16px 16px 16px 0;
}

.message__content {
  padding: 10px 14px;
  font-size: 13px;
  line-height: 1.5;
}

.typing-indicator span {
  animation: blink 1.4s infinite;
  animation-fill-mode: both;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0% { opacity: 0.2; }
  20% { opacity: 1; }
  100% { opacity: 0.2; }
}

.input-area {
  padding: 12px;
  background: rgba(10, 14, 26, 0.5);
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 8px;
}
.chat-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: 20px;
  outline: none;
  font-size: 13px;
}
.chat-input:focus {
  border-color: var(--accent-primary);
}
.send-btn {
  background: var(--accent-primary);
  color: white;
  border: none;
  padding: 0 16px;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Animations */
.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
</style>
