<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const authStore = useAuthStore()
const uiStore = useUiStore()

const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const isSubmitting = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true

  try {
    await authStore.login({
      email: email.value,
      password: password.value,
      remember_me: rememberMe.value,
    })
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Invalid credentials. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface-50 dark:bg-surface-950 p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-600 mb-4">
          <span class="text-white text-2xl font-bold">AI</span>
        </div>
        <h1 class="text-2xl font-bold text-surface-900 dark:text-white">AI Work Studio</h1>
        <p class="text-surface-500 mt-1">Sign in to your account</p>
      </div>

      <!-- Form -->
      <div class="card p-8">
        <form @submit.prevent="handleSubmit" class="space-y-5">
          <!-- Error alert -->
          <div v-if="error" class="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
          </div>

          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">
              Email address
            </label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="admin@aiworkstudio.com"
              class="input"
            />
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1.5">
              Password
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              placeholder="••••••••"
              class="input"
            />
          </div>

          <!-- Remember me & Forgot password -->
          <div class="flex items-center justify-between">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="rememberMe"
                type="checkbox"
                class="w-4 h-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="text-sm text-surface-600 dark:text-surface-400">Remember me</span>
            </label>
            <a href="#" class="text-sm text-primary-600 hover:text-primary-700">Forgot password?</a>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="isSubmitting"
            class="btn-primary w-full py-2.5"
          >
            <span v-if="isSubmitting">Signing in...</span>
            <span v-else>Sign in</span>
          </button>
        </form>
      </div>

      <!-- Footer -->
      <p class="text-center text-xs text-surface-500 mt-6">
        AI Work Studio v1.0.0 · Enterprise Edition
      </p>
    </div>
  </div>
</template>
