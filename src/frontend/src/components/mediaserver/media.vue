<script setup>
import {onMounted, ref, watch} from 'vue'
import isEqual from 'lodash/isEqual'

const serverTypes = [
  {name: 'Emby', id: 'emby'},
  {name: 'Jellyfin', id: 'jellyfin'}
]

const newSettings = ref({
  media_server_type: 'emby',
  media_server_base_url: "http://media_server:8096/",
  media_server_api_key: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

  create_leaving_soon_collections: false
})
const retrievedSettings = ref()

async function getMediaServerSettings() {
  fetch("/api/mediaserver/settings")
    .then(response => response.json())
    .then(data => {
      console.log(data)
      newSettings.value = {...data}
      retrievedSettings.value = data
    })
}

async function postMediaSettings() {
  try {
    const response = await fetch('/api/mediaserver/settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(newSettings.value)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Error: ${response.status} - ${errorData.detail}`);
    }

    const data = await response.json();
    console.log('Successful response:', data);
  } catch (error) {
    console.error('Error:', error);
  }
  await getMediaServerSettings()
}

const settingsAreEqual = ref(true)

watch([newSettings, retrievedSettings], () => {
  settingsAreEqual.value = isEqual(newSettings.value, retrievedSettings.value)
}, {deep: true})

onMounted(async () => {
  await getMediaServerSettings()
})
</script>

<template>
  <div style="position: fixed; right: 1.5em; bottom: 1.5em; z-index: 1">
    <v-btn :disabled="settingsAreEqual" color="primary" variant="elevated" @click="postMediaSettings">Save</v-btn>
  </div>
  <v-card>
    <v-card-title>Connection</v-card-title>
    <v-col>
      <v-select v-model="newSettings.media_server_type" :items="serverTypes" item-title="name" item-value="id"
                label="Server type"/>
      <v-text-field v-model="newSettings.media_server_base_url" label="Server adress"
                    placeholder="http://media_server:8096/"/>
      <v-text-field v-model="newSettings.media_server_api_key" label="API key" placeholder="XXXXXXXXXXXXXX"/>
    </v-col>
  </v-card>
  <!--  <v-card class="mt-4">-->
  <!--    <v-card-title>General</v-card-title>-->
  <!--    <v-col>-->
  <!--      <v-switch v-model="newSettings.create_leaving_soon_collections" label="Create leaving soon collections"-->
  <!--                hint="Creates collections for items which are soon to be deleted/removed" inset color="secondary"/>-->
  <!--    </v-col>-->
  <!--  </v-card>-->
</template>

<style scoped>

</style>
