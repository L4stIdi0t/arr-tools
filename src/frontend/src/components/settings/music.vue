<script setup>
import {onMounted, ref} from "vue";
import {useSettingsStore} from "@/stores/settings";
const settingsStore = useSettingsStore();

const spotifyPlaylistTypes = ['audio', 'video', 'both'];
// https://gist.githubusercontent.com/jrnk/8eb57b065ea0b098d571/raw/936a6f652ebddbe19b1d100a60eedea3652ccca6/ISO-639-1-language.json
const subtitleLanguages = [
  {code: "all", name: "All languages"},
  { code: "aa", name: "Afar" },
  { code: "ab", name: "Abkhazian" },
  { code: "ae", name: "Avestan" },
  { code: "af", name: "Afrikaans" },
  { code: "ak", name: "Akan" },
  { code: "am", name: "Amharic" },
  { code: "an", name: "Aragonese" },
  { code: "ar", name: "Arabic" },
  { code: "as", name: "Assamese" },
  { code: "av", name: "Avaric" },
  { code: "ay", name: "Aymara" },
  { code: "az", name: "Azerbaijani" },
  { code: "ba", name: "Bashkir" },
  { code: "be", name: "Belarusian" },
  { code: "bg", name: "Bulgarian" },
  { code: "bh", name: "Bihari languages" },
  { code: "bi", name: "Bislama" },
  { code: "bm", name: "Bambara" },
  { code: "bn", name: "Bengali" },
  { code: "bo", name: "Tibetan" },
  { code: "br", name: "Breton" },
  { code: "bs", name: "Bosnian" },
  { code: "ca", name: "Catalan; Valencian" },
  { code: "ce", name: "Chechen" },
  { code: "ch", name: "Chamorro" },
  { code: "co", name: "Corsican" },
  { code: "cr", name: "Cree" },
  { code: "cs", name: "Czech" },
  {
    code: "cu",
    name: "Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic"
  },
  { code: "cv", name: "Chuvash" },
  { code: "cy", name: "Welsh" },
  { code: "da", name: "Danish" },
  { code: "de", name: "German" },
  { code: "dv", name: "Divehi; Dhivehi; Maldivian" },
  { code: "dz", name: "Dzongkha" },
  { code: "ee", name: "Ewe" },
  { code: "el", name: "Greek, Modern (1453-)" },
  { code: "en", name: "English" },
  { code: "eo", name: "Esperanto" },
  { code: "es", name: "Spanish; Castilian" },
  { code: "et", name: "Estonian" },
  { code: "eu", name: "Basque" },
  { code: "fa", name: "Persian" },
  { code: "ff", name: "Fulah" },
  { code: "fi", name: "Finnish" },
  { code: "fj", name: "Fijian" },
  { code: "fo", name: "Faroese" },
  { code: "fr", name: "French" },
  { code: "fy", name: "Western Frisian" },
  { code: "ga", name: "Irish" },
  { code: "gd", name: "Gaelic; Scottish Gaelic" },
  { code: "gl", name: "Galician" },
  { code: "gn", name: "Guarani" },
  { code: "gu", name: "Gujarati" },
  { code: "gv", name: "Manx" },
  { code: "ha", name: "Hausa" },
  { code: "he", name: "Hebrew" },
  { code: "hi", name: "Hindi" },
  { code: "ho", name: "Hiri Motu" },
  { code: "hr", name: "Croatian" },
  { code: "ht", name: "Haitian; Haitian Creole" },
  { code: "hu", name: "Hungarian" },
  { code: "hy", name: "Armenian" },
  { code: "hz", name: "Herero" },
  {
    code: "ia",
    name: "Interlingua (International Auxiliary Language Association)"
  },
  { code: "id", name: "Indonesian" },
  { code: "ie", name: "Interlingue; Occidental" },
  { code: "ig", name: "Igbo" },
  { code: "ii", name: "Sichuan Yi; Nuosu" },
  { code: "ik", name: "Inupiaq" },
  { code: "io", name: "Ido" },
  { code: "is", name: "Icelandic" },
  { code: "it", name: "Italian" },
  { code: "iu", name: "Inuktitut" },
  { code: "ja", name: "Japanese" },
  { code: "jv", name: "Javanese" },
  { code: "ka", name: "Georgian" },
  { code: "kg", name: "Kongo" },
  { code: "ki", name: "Kikuyu; Gikuyu" },
  { code: "kj", name: "Kuanyama; Kwanyama" },
  { code: "kk", name: "Kazakh" },
  { code: "kl", name: "Kalaallisut; Greenlandic" },
  { code: "km", name: "Central Khmer" },
  { code: "kn", name: "Kannada" },
  { code: "ko", name: "Korean" },
  { code: "kr", name: "Kanuri" },
  { code: "ks", name: "Kashmiri" },
  { code: "ku", name: "Kurdish" },
  { code: "kv", name: "Komi" },
  { code: "kw", name: "Cornish" },
  { code: "ky", name: "Kirghiz; Kyrgyz" },
  { code: "la", name: "Latin" },
  { code: "lb", name: "Luxembourgish; Letzeburgesch" },
  { code: "lg", name: "Ganda" },
  { code: "li", name: "Limburgan; Limburger; Limburgish" },
  { code: "ln", name: "Lingala" },
  { code: "lo", name: "Lao" },
  { code: "lt", name: "Lithuanian" },
  { code: "lu", name: "Luba-Katanga" },
  { code: "lv", name: "Latvian" },
  { code: "mg", name: "Malagasy" },
  { code: "mh", name: "Marshallese" },
  { code: "mi", name: "Maori" },
  { code: "mk", name: "Macedonian" },
  { code: "ml", name: "Malayalam" },
  { code: "mn", name: "Mongolian" },
  { code: "mr", name: "Marathi" },
  { code: "ms", name: "Malay" },
  { code: "mt", name: "Maltese" },
  { code: "my", name: "Burmese" },
  { code: "na", name: "Nauru" },
  {
    code: "nb",
    name: "Bokmål, Norwegian; Norwegian Bokmål"
  },
  { code: "nd", name: "Ndebele, North; North Ndebele" },
  { code: "ne", name: "Nepali" },
  { code: "ng", name: "Ndonga" },
  { code: "nl", name: "Dutch; Flemish" },
  { code: "nn", name: "Norwegian Nynorsk; Nynorsk, Norwegian" },
  { code: "no", name: "Norwegian" },
  { code: "nr", name: "Ndebele, South; South Ndebele" },
  { code: "nv", name: "Navajo; Navaho" },
  { code: "ny", name: "Chichewa; Chewa; Nyanja" },
  { code: "oc", name: "Occitan (post 1500)" },
  { code: "oj", name: "Ojibwa" },
  { code: "om", name: "Oromo" },
  { code: "or", name: "Oriya" },
  { code: "os", name: "Ossetian; Ossetic" },
  { code: "pa", name: "Panjabi; Punjabi" },
  { code: "pi", name: "Pali" },
  { code: "pl", name: "Polish" },
  { code: "ps", name: "Pushto; Pashto" },
  { code: "pt", name: "Portuguese" },
  { code: "qu", name: "Quechua" },
  { code: "rm", name: "Romansh" },
  { code: "rn", name: "Rundi" },
  { code: "ro", name: "Romanian; Moldavian; Moldovan" },
  { code: "ru", name: "Russian" },
  { code: "rw", name: "Kinyarwanda" },
  { code: "sa", name: "Sanskrit" },
  { code: "sc", name: "Sardinian" },
  { code: "sd", name: "Sindhi" },
  { code: "se", name: "Northern Sami" },
  { code: "sg", name: "Sango" },
  { code: "si", name: "Sinhala; Sinhalese" },
  { code: "sk", name: "Slovak" },
  { code: "sl", name: "Slovenian" },
  { code: "sm", name: "Samoan" },
  { code: "sn", name: "Shona" },
  { code: "so", name: "Somali" },
  { code: "sq", name: "Albanian" },
  { code: "sr", name: "Serbian" },
  { code: "ss", name: "Swati" },
  { code: "st", name: "Sotho, Southern" },
  { code: "su", name: "Sundanese" },
  { code: "sv", name: "Swedish" },
  { code: "sw", name: "Swahili" },
  { code: "ta", name: "Tamil" },
  { code: "te", name: "Telugu" },
  { code: "tg", name: "Tajik" },
  { code: "th", name: "Thai" },
  { code: "ti", name: "Tigrinya" },
  { code: "tk", name: "Turkmen" },
  { code: "tl", name: "Tagalog" },
  { code: "tn", name: "Tswana" },
  { code: "to", name: "Tonga (Tonga Islands)" },
  { code: "tr", name: "Turkish" },
  { code: "ts", name: "Tsonga" },
  { code: "tt", name: "Tatar" },
  { code: "tw", name: "Twi" },
  { code: "ty", name: "Tahitian" },
  { code: "ug", name: "Uighur; Uyghur" },
  { code: "uk", name: "Ukrainian" },
  { code: "ur", name: "Urdu" },
  { code: "uz", name: "Uzbek" },
  { code: "ve", name: "Venda" },
  { code: "vi", name: "Vietnamese" },
  { code: "vo", name: "Volapük" },
  { code: "wa", name: "Walloon" },
  { code: "wo", name: "Wolof" },
  { code: "xh", name: "Xhosa" },
  { code: "yi", name: "Yiddish" },
  { code: "yo", name: "Yoruba" },
  { code: "za", name: "Zhuang; Chuang" },
  { code: "zh", name: "Chinese" },
  { code: "zu", name: "Zulu" }
];


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
      <v-switch label="Download subtitles" hint="If enabled, subtitles will be downloaded" v-model="settingsStore.musicvideoSettings.download_subtitles" persistent-hint/>
      <v-select label="Subtitle languages" v-model="settingsStore.musicvideoSettings.subtitle_languages" :items="subtitleLanguages" item-value="code" item-title="name" multiple chips closable-chips/>
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
