import { settingsApi } from '@/api/settings'

export class MapLoadError extends Error {
  code: string
  constructor(message: string, code: string) {
    super(message)
    this.code = code
  }
}

let loadingPromise: Promise<string> | null = null

export const loadMapScript = async (): Promise<string> => {
  if (loadingPromise) return loadingPromise

  loadingPromise = (async () => {
    // 1. Get Settings
    let settings
    try {
        settings = await settingsApi.getSettings()
    } catch (e) {
        throw new MapLoadError('Failed to fetch settings', 'SETTINGS_ERROR')
    }

    const mapSettings = settings.map
    
    let apiKey = ''
    if (mapSettings && mapSettings.api_keys && mapSettings.api_keys.length > 0) {
      // Randomly select one key
      const keys = mapSettings.api_keys
      apiKey = keys[Math.floor(Math.random() * keys.length)]
    } else if (mapSettings && mapSettings.api_key) {
      apiKey = mapSettings.api_key
    }

    if (!apiKey) {
      throw new MapLoadError('Map API Key is missing', 'MAP_KEY_MISSING')
    }

    const { provider } = mapSettings

    // 2. Load Provider Script
    if (provider === 'tianditu') {
      await loadTianditu(apiKey)
      return apiKey
    } else {
        // Placeholder for other providers
        throw new MapLoadError(`Provider ${provider} is not supported yet`, 'UNSUPPORTED_PROVIDER')
    }
  })()

  return loadingPromise.catch(e => {
      loadingPromise = null // Reset on error so we can retry
      throw e
  })
}

const loadTianditu = (key: string) => {
  return new Promise<void>((resolve, reject) => {
    if ((window as any).T) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = `https://api.tianditu.gov.cn/api?v=4.0&tk=${key}`
    script.type = 'text/javascript'
    script.onload = () => resolve()
    script.onerror = () => reject(new MapLoadError('Failed to load map script', 'SCRIPT_LOAD_ERROR'))
    document.head.appendChild(script)
  })
}
