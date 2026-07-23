<script setup lang="ts">
const props = defineProps<{
  src: string
  alt?: string
}>()

const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <div class="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-4" @click.self="emit('close')">
    <button @click="emit('close')" class="absolute top-4 right-4 text-white/70 hover:text-white text-3xl z-10">×</button>
    <img :src="src" :alt="alt || ''" class="max-w-[90vw] max-h-[90vh] object-contain rounded-lg shadow-2xl" />
  </div>
</template>
