<template>
  <transition name="fade">
    <div v-if="show" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="handleCancel">
      <div class="bg-card border border-border rounded-lg shadow-lg w-full max-w-md p-6" @click.stop>
        <h3 class="text-lg font-semibold mb-2">{{ title }}</h3>
        <p class="text-muted-foreground mb-4">{{ message }}</p>
        <div class="flex justify-end space-x-3">
          <button class="btn btn-ghost" @click="handleCancel">
            {{ cancelText }}
          </button>
          <button :class="confirmButtonClass" @click="handleConfirm">
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '确认操作'
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: '确认'
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  type: {
    type: String,
    default: 'default', // 'default', 'danger', 'warning'
    validator: (value) => ['default', 'danger', 'warning'].includes(value)
  }
})

const emit = defineEmits(['confirm', 'cancel', 'update:show'])

const confirmButtonClass = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'btn btn-destructive'
    case 'warning':
      return 'btn bg-amber-500 hover:bg-amber-600 text-white'
    default:
      return 'btn btn-primary'
  }
})

function handleConfirm() {
  emit('confirm')
  emit('update:show', false)
}

function handleCancel() {
  emit('cancel')
  emit('update:show', false)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

