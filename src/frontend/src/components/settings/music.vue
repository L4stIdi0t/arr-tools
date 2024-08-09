<script setup>
import {onMounted, ref} from "vue";
import {useSettingsStore} from "@/stores/settings";
const settingsStore = useSettingsStore();

const spotifyPlaylistTypes = ['audio', 'video', 'both'];

const mediaServerPlaylists = ref([])
const spotifyPlaylists = ref([])

async function getPlaylistsMediaserver() {
  fetch("/api/mediaserver/playlists")
    .then(response => response.json())
    .then(data => {
      mediaServerPlaylists.value = data
    })
}

async function getplaylistsSpotify() {
  fetch("/api/spotify/playlists")
    .then(response => response.json())
    .then(data => {
      spotifyPlaylists.value = data
    })
}

const newSpotifyPlaylist = ref(null)
const newSpotifyPlaylistType = ref('audio')
async function addSpotifyPlaylist() {
  if (!newSpotifyPlaylist.value) return;
  if (!spotifyPlaylistTypes.includes(newSpotifyPlaylistType.value)) return;

  fetch("/api/spotify/playlist?playlist_url_id=" + encodeURIComponent(newSpotifyPlaylist.value) + "&playlist_type=" + encodeURIComponent(newSpotifyPlaylistType.value), {
    method: "PUT",
    headers: {
      'accept': 'application/json'
    }
  })
  .then(response => response.json())
  .then(data => {
    spotifyPlaylists.value = data
  })

  await getplaylistsSpotify()
}

async function removeSpotifyPlaylist(id) {
  fetch("/api/spotify/playlist?playlist_url_id=" + id, {
    method: 'DELETE'
  })
    .then(response => response.json())
    .then(data => {
      console.log('Successful response:', data);
    })
  await getplaylistsSpotify()
}

onMounted(async () => {
  await getPlaylistsMediaserver()
  await getplaylistsSpotify()
})
</script>

<template>
  <v-card class="mb-4">
    <v-card-title>Music video downloading settings</v-card-title>
    <v-card-text>
      <v-switch label="Enabled" hint="If enabled, music videos will be downloaded from Youtube" v-model="settingsStore.musicvideoSettings.enabled" persistent-hint/>
      <v-switch label="Use IMVDB" hint="If enabled, IMVDB will be used to search for music videos" v-model="settingsStore.musicvideoSettings.use_imvdb" persistent-hint/>
      <v-switch label="Use Shazam search" hint="If enabled, Shazam will be used to search for music videos" v-model="settingsStore.musicvideoSettings.use_shazam_search" persistent-hint/>
<!--      <v-switch label="Use Youtube search" hint="If enabled, Youtube will be used to search for music videos" v-model="settingsStore.musicvideoSettings.use_youtube_search" persistent-hint/>-->
      <v-switch label="Check song with recognition" hint="If enabled, the song will be checked for recognition" v-model="settingsStore.musicvideoSettings.check_song_with_recognition" persistent-hint/>
      <v-switch label="Check song for movement" hint="If enabled, the song will be checked for movement" v-model="settingsStore.musicvideoSettings.check_song_for_movement" persistent-hint/>
    </v-card-text>
    <v-card-actions>
      <v-btn color="primary" variant="elevated" @click="settingsStore.postMusicvideoSettings">Save</v-btn>
    </v-card-actions>
  </v-card>

  <v-card class="mb-4">
    <v-card-title>Spotify</v-card-title>
    <v-card-text>
      <v-row class="mx-2">
        <v-col cols="12" md="8">
          <v-text-field label="Enter playlist id or url" v-model="newSpotifyPlaylist" @keydown.enter="addSpotifyPlaylist"/>
        </v-col>
        <v-col cols="12" md="4">
          <v-select label="Playlist type" v-model="newSpotifyPlaylistType" :items="spotifyPlaylistTypes"/>
        </v-col>
        <v-col cols="12" class="mt-n12">
          <v-btn color="primary" variant="elevated" @click="addSpotifyPlaylist" class="mt-3">Add</v-btn>
        </v-col>
      </v-row>

      <v-list style="max-height: 13em">
        <v-list-item v-for="playlist in spotifyPlaylists" :key="playlist.id">
          <v-row>
            <v-col cols="auto">
              <v-list-item-title>{{ playlist.name }}</v-list-item-title>
              <v-list-item-subtitle>Type: {{ playlist.type }}</v-list-item-subtitle>
            </v-col>
            <v-spacer/>
            <v-col cols="auto">
              <v-list-item-subtitle class="mt-4">{{ playlist.id }}</v-list-item-subtitle>
            </v-col>
            <v-col cols="auto">
              <v-btn color="error" variant="elevated" @click="removeSpotifyPlaylist(playlist.id)" icon="mdi-trash-can-outline"></v-btn>
            </v-col>
            <v-divider/>
          </v-row>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>

  <v-card class="mb-4">
    <v-card-title>Mediaserver</v-card-title>
    <v-card-text>
      <v-autocomplete label="Playlists to convert to music video" multiple closable-chips chips v-model="settingsStore.musicvideoSettings.convert_playlists" :items="mediaServerPlaylists" item-title="title" item-value="id" />
    </v-card-text>
    <v-card-actions>
      <v-btn color="primary" variant="elevated" @click="settingsStore.postMusicvideoSettings">Save</v-btn>
    </v-card-actions>
  </v-card>

</template>

<style scoped>

</style>
