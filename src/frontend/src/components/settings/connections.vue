<script setup>
import { useSettingsStore } from '@/stores/settings';
import {onMounted} from "vue";
const settingsStore = useSettingsStore();

const serverTypes = [
  {name: 'Emby', id: 'emby'},
  {name: 'Jellyfin', id: 'jellyfin'}
]

onMounted(async () => {
  await settingsStore.getMediaserverSettings();
  await settingsStore.getRadarrSettings();
  await settingsStore.getSonarrSettings();
  await settingsStore.getSpotifySettings();
});
</script>

<template>
  <v-card class="mb-4">
    <v-card-title>MediaServer</v-card-title>
    <v-card-text>
      <v-select v-model="settingsStore.mediaserverSettings.media_server_type" :items="serverTypes" item-title="name" item-value="id"
                label="Server type"/>
      <v-text-field v-model="settingsStore.mediaserverSettings.media_server_base_url" label="Server adress"
                    placeholder="http://media_server:8096/"/>
      <v-text-field v-model="settingsStore.mediaserverSettings.media_server_api_key" label="API key" placeholder="XXXXXXXXXXXXXX"/>
    </v-card-text>
    <v-card-actions>
      <v-btn @click="settingsStore.postMediaserverSettings()" color="primary" variant="elevated">Save</v-btn>
    </v-card-actions>
  </v-card>
  <v-card class="mb-4">
    <v-card-title>Radarr</v-card-title>
    <v-card-text>
      <v-text-field v-model="settingsStore.radarrSettings.base_url" label="Server address" placeholder="http://radarr:7878/"/>
      <v-text-field v-model="settingsStore.radarrSettings.api_key" label="API key" placeholder="XXXXXXXXXXXXXX"/>
    </v-card-text>
    <v-card-actions>
      <v-btn @click="settingsStore.postRadarrSettings; console.log('radarr')" color="primary" variant="elevated">Save</v-btn>
    </v-card-actions>
  </v-card>
  <v-card class="mb-4">
    <v-card-title>Sonarr</v-card-title>
    <v-card-text>
      <v-text-field v-model="settingsStore.sonarrSettings.base_url" label="Server address" placeholder="http://sonarr:8989/"/>
      <v-text-field v-model="settingsStore.sonarrSettings.api_key" label="API key" placeholder="XXXXXXXXXXXXXX"/>
    </v-card-text>
    <v-card-actions>
      <v-btn @click="settingsStore.postSonarrSettings()" color="primary" variant="elevated">Save</v-btn>
    </v-card-actions>
  </v-card>
  <v-card class="mb-4">
    <v-card-title>Spotify</v-card-title>
    <v-card-text>
      <v-text-field v-model="settingsStore.spotifySettings.client_id" label="Client ID" placeholder="XXXXXXXXXXXXXX"/>
      <v-text-field v-model="settingsStore.spotifySettings.client_secret" label="Client secret" placeholder="XXXXXXXXXXXXXX"/>
    </v-card-text>
    <v-card-actions>
      <v-btn @click="settingsStore.postSpotifySettings()" color="primary" variant="elevated">Save</v-btn>
    </v-card-actions>
  </v-card>

</template>

<style scoped>

</style>
