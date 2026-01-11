import { watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Ref } from 'vue'

export function useModalBack(visible: Ref<boolean>, onBack?: () => void) {
  const router = useRouter()
  const route = useRoute()

  // Track if we pushed a state for this modal
  let pushedState = false

  watch(visible, (newVal) => {
    if (newVal) {
      // Push a new state so back button closes modal
      // We add a hash or query param to indicate modal state if needed, 
      // but simpler is just pushing state object
      pushedState = true
      history.pushState({ modalOpen: true }, '')
    } else {
      // If closed programmatically (not by back button)
      // We might need to go back if we pushed state and it's still top
      if (pushedState) {
        pushedState = false
        // Check if we are still in the same state we pushed?
        // It's tricky to know if the user already pressed back.
        // But usually, if we pushed state, we should go back.
        // However, if the user pressed back, visible becomes false via the popstate listener below.
        // So we only need to go back if visible became false via other means (e.g. Save button)
        // AND we haven't already popped the state.
        
        // This is tricky. A safer way is:
        // When modal opens, we rely on the popstate event to close it.
        // But if we close it manually, we should essentially "undo" the pushState.
        // history.back() does that.
        history.back()
      }
    }
  })

  const handlePopState = (event: PopStateEvent) => {
    if (visible.value) {
      // User pressed back
      // We set pushedState to false because the state is already popped
      pushedState = false
      visible.value = false
      if (onBack) onBack()
    }
  }

  window.addEventListener('popstate', handlePopState)

  onBeforeUnmount(() => {
    window.removeEventListener('popstate', handlePopState)
    // If component unmounts while modal is open (e.g. navigation), we should cleanup
    if (visible.value && pushedState) {
      // We don't want to trigger back here usually as we are navigating away
    }
  })
}
