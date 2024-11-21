// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: true },
  modules: [
    '@nuxt/fonts',
    '@nuxt/ui',
    '@pinia/nuxt',
    'pinia-plugin-persistedstate',
  ],
  colorMode: {
    preference: 'light'
  }, runtimeConfig: {
    public: {
      baseURL: '',
    },
  }, ssr: false,
})