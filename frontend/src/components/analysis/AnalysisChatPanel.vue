<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import api from '@/services/api'

const props = defineProps<{
  jobId: string
  artworkName: string
}>()

interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<ChatMsg[]>([])
const inputText = ref('')
const isLoading = ref(false)
const chatContainer = ref<HTMLElement | null>(null)

// Initial greeting
messages.value.push({
  role: 'assistant',
  content: `I'm your production analyst for **${props.artworkName}**. Ask me anything about this analysis — why a metric has a certain value, what it means for printing, or how to fix issues. I can only discuss this specific artwork's analysis results.`,
})

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    const response = await api.post('/analysis/chat', {
      job_id: props.jobId,
      message: text,
      history: messages.value.slice(-10),
    })

    const reply = response.data.data?.reply || 'Sorry, I could not process that.'
    messages.value.push({ role: 'assistant', content: reply })
  } catch (err: any) {
    const detail = err.response?.data?.detail || 'Failed to get response'
    messages.value.push({ role: 'assistant', content: `⚠️ Error: ${detail}` })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// Reset chat when job changes
watch(() => props.jobId, () => {
  messages.value = [{
    role: 'assistant',
    content: `I'm your production analyst for **${props.artworkName}**. Ask me anything about this analysis.`,
  }]
})
</script>

<template>
  <div class="card flex flex-col h-[450px]">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 border-b border-surface-200 dark:border-surface-800">
      <div class="flex items-center gap-2">
        <span class="text-lg">💬</span>
        <div>
          <h3 class="text-sm font-semibold text-surface-900 dark:text-white">Analysis Chat</h3>
          <p class="text-[10px] text-surface-500">Ask about this analysis · No image generation · Restricted to report data</p>
        </div>
      </div>
      <span class="badge-info text-[10px]">GPT-5.5</span>
    </div>

    <!-- Messages -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-3">
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <div
          :class="[
            'max-w-[80%] rounded-xl px-4 py-2.5 text-sm',
            msg.role === 'user'
              ? 'bg-primary-600 text-white rounded-br-sm'
              : 'bg-surface-100 dark:bg-surface-800 text-surface-800 dark:text-surface-200 rounded-bl-sm'
          ]"
        >
          <p class="whitespace-pre-wrap leading-relaxed">{{ msg.content }}</p>
        </div>
      </div>

      <!-- Typing indicator -->
      <div v-if="isLoading" class="flex justify-start">
        <div class="bg-surface-100 dark:bg-surface-800 rounded-xl px-4 py-2.5 rounded-bl-sm">
          <span class="flex gap-1">
            <span class="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
          </span>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="p-3 border-t border-surface-200 dark:border-surface-800">
      <div class="flex items-center gap-2">
        <input
          v-model="inputText"
          @keydown="handleKeydown"
          type="text"
          placeholder="Ask about the analysis... (e.g. 'Why is blackout 34.8%?')"
          class="input flex-1"
          :disabled="isLoading"
        />
        <button
          @click="sendMessage"
          :disabled="!inputText.trim() || isLoading"
          class="btn-primary px-4"
        >
          Send
        </button>
      </div>
      <p class="text-[10px] text-surface-400 mt-1.5">Restricted to this artwork's analysis only. No image generation.</p>
    </div>
  </div>
</template>
