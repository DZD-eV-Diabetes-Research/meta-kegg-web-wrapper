<template>
  <NuxtLayout>
    <Layout>
      <NuxtPage />
    </Layout>
  </NuxtLayout>
</template>

<script setup lang="ts">
useHead({
  title: 'MetaKegg',
  meta: [
    { name: 'description', content: 'Dife-DZD Webapp to do MetaKegg stuff' }
  ],
})
</script>

<style>
/* div {
  font-family: Poppins, sans-serif;
} */
</style>