import { defineStore } from 'pinia';
import {reactive, ref} from 'vue';
import {useMediaStore} from "@/stores/mediainfo";
const mediaInfoStore = useMediaStore();

export const useSettingsStore = defineStore('settings', () => {
  const fetchedSettings = reactive({
    mediaserver: null,
    radarr: null,
    sonarr: null,
    spotify: null,
    musicvideo: null
  });

  const mediaserverSettings = ref({
  "media_server_type": "emby",
  "media_server_base_url": "http://media_server:8096/",
  "media_server_api_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "create_leaving_soon_collections": false
});

  async function getMediaserverSettings() {
    if (fetchedSettings.mediaserver) {
      return;
    }

    try {
      const response = await fetch('/api/mediaserver/settings');

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${response.status} - ${errorData.detail}`);
      }

      mediaserverSettings.value = await response.json();
      fetchedSettings.mediaserver = true;
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function postMediaserverSettings() {
    if (!fetchedSettings.mediaserver) {
      console.error('Settings not fetched yet');
      return;
    }
    try {
      const response = await fetch('/api/mediaserver/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(mediaserverSettings.value)
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

    await getMediaserverSettings();
    // Ensure mediaInfoStore is properly imported and instantiated before this call
    await mediaInfoStore.fetchMediaInfo(true);
  }

  const radarrSettings = ref({
    "base_url": "http://radarr:7878/",
    "api_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "enabled": false,
    "ultra_quality_profile": 0,
    "high_quality_profile": 0,
    "normal_quality_profile": 0,
    "low_quality_profile": 0,
    "watched_quality_profile": 2,
    "favorited_quality_profile": 3,
    "on_resume_quality_profile": 2,
    "very_popular_quality_profile": 2,
    "popular_quality_profile": 1,
    "less_popular_quality_profile": 0,
    "unpopular_quality_profile": 0,
    "search_for_quality_upgrades": true,
    "monitor_quality_changes": true,
    "exclude_tags_from_quality_upgrades": [],
    "exclude_users_from_quality_upgrades": [],
    "use_watched": true,
    "use_favorite": true,
    "use_on_resume": false,
    "watched_decay_days": 30,
    "favorite_decay_days": 180,
    "on_resume_decay_days": 14,
    "very_popular_decay_days": 30,
    "popular_decay_days": 60,
    "less_popular_decay_days": 90,
    "unpopular_decay_days": 120,
    "decay_method": 3,
    "decay_start_timer": 3,
    "mark_favorited_as_monitored": true,
    "mark_on_resume_as_monitored": false,
    "mark_very_popular_as_monitored": true,
    "mark_popular_as_monitored": true,
    "mark_less_popular_as_monitored": true,
    "mark_unpopular_as_monitored": false,
    "mark_unpopular_as_unmonitored": true,
    "exclude_tags_from_monitoring": [],
    "exclude_users_from_monitoring": [],
    "delete_unmonitored_files": false,
    "exclude_tags_from_deletion": [],
    "popular_filters": {
      "very_popular": [],
      "popular": [],
      "less_popular": [],
      "unpopular": []
    }
  });

  async function getRadarrSettings() {
    if (fetchedSettings.radarr) {
      return;
    }

    try {
      const response = await fetch('/api/radarr/settings');

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${response.status} - ${errorData.detail}`);
      }

      radarrSettings.value = await response.json();
      fetchedSettings.radarr = true;
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function postRadarrSettings() {
    if (!fetchedSettings.radarr) {
      console.error('Settings not fetched yet');
      return;
    }

    try {
      const response = await fetch('/api/radarr/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(radarrSettings.value)
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

    await getRadarrSettings();
    // Ensure mediaInfoStore is properly imported and instantiated before this call
    await mediaInfoStore.fetchRadarrInfo(true);
  }

  const sonarrSettings = ref({
    "base_url": "http://sonarr:8989/",
    "api_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "enabled": false,
    "use_watched": true,
    "use_favorite": true,
    "ultra_quality_profile": 0,
    "high_quality_profile": 0,
    "normal_quality_profile": 0,
    "low_quality_profile": 0,
    "watched_quality_profile": 2,
    "favorited_quality_profile": 3,
    "very_popular_quality_profile": 2,
    "popular_quality_profile": 1,
    "less_popular_quality_profile": 0,
    "unpopular_quality_profile": 0,
    "search_for_quality_upgrades": true,
    "monitor_quality_changes": true,
    "exclude_tags_from_quality_upgrades": [],
    "exclude_users_from_quality_upgrades": [],
    "watched_decay_days": 30,
    "favorite_decay_days": 180,
    "very_popular_decay_days": 30,
    "popular_decay_days": 60,
    "less_popular_decay_days": 90,
    "unpopular_decay_days": 120,
    "decay_method": 3,
    "decay_start_timer": 3,
    "mark_favorited_as_monitored": true,
    "mark_very_popular_as_monitored": true,
    "mark_popular_as_monitored": true,
    "mark_less_popular_as_monitored": true,
    "mark_unpopular_as_monitored": false,
    "mark_unpopular_as_unmonitored": true,
    "exclude_tags_from_monitoring": [],
    "exclude_users_from_monitoring": [],
    "monitoring_amount": 0,
    "base_monitoring_amount": 1,
    "delete_unmonitored_files": false,
    "exclude_tags_from_deletion": [],
    "popular_filters": {
      "very_popular": [],
      "popular": [],
      "less_popular": [],
      "unpopular": []
    }
  });

  async function getSonarrSettings() {
    if (fetchedSettings.sonarr) {
      return;
    }

    try {
      const response = await fetch('/api/sonarr/settings');

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${response.status} - ${errorData.detail}`);
      }

      sonarrSettings.value = await response.json();
      fetchedSettings.sonarr = true;
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function postSonarrSettings() {
    if (!fetchedSettings.sonarr) {
      console.error('Settings not fetched yet');
      return;
    }

    try {
      const response = await fetch('/api/sonarr/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(sonarrSettings.value)
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

    await getSonarrSettings();
    // Ensure mediaInfoStore is properly imported and instantiated before this call
    await mediaInfoStore.fetchSonarrInfo(true);
  }

  const spotifySettings = ref({
    "client_id": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "client_secret": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "playlists": []
  });

  async function getSpotifySettings(force = false) {
    if (fetchedSettings.spotify && !force) {
      return;
    }

    try {
      const response = await fetch('/api/spotify/settings');

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${response.status} - ${errorData.detail}`);
      }

      spotifySettings.value = await response.json();
      fetchedSettings.spotify = true;
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function postSpotifySettings() {
    if (!fetchedSettings.spotify) {
      console.error('Settings not fetched yet');
      return;
    }
    try {
      const response = await fetch('/api/spotify/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(spotifySettings.value)
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
  }

  const musicvideoSettings = ref({
    "enabled": true,
    "use_imvdb": true,
    "use_shazam_search": true,
    "use_youtube_search": false,
    "good_keywords": [
      "official",
      "official video",
      "music video",
      "vevo",
      "uncensured",
      "uncensored"
    ],
    "bad_keywords": [
      "acoustic",
      "lyrics",
      "remix"
    ],
    "exclude_words": [
      "tutorial",
      "cover",
      "lesson",
      "karaoke",
      "lessons",
      "live",
      "audio"
    ],
    "check_song_with_recognition": true,
    "check_song_for_movement": true,
    "convert_playlists": [],
    "download_subtitles": true,
    "subtitle_languages": ["en"]
  });

  async function getMusicvideoSettings() {
    if (fetchedSettings.musicvideo) {
      return;
    }

    try {
      const response = await fetch('/api/music-video/settings');

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error: ${response.status} - ${errorData.detail}`);
      }

      musicvideoSettings.value = await response.json();
      fetchedSettings.musicvideo = true;
    } catch (error) {
      console.error('Error:', error);
    }
  }

  async function postMusicvideoSettings() {
    if (!fetchedSettings.musicvideo) {
      console.error('Settings not fetched yet');
      return;
    }
    try {
      const response = await fetch('/api/music-video/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(musicvideoSettings.value)
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
  }

  return {
    mediaserverSettings,
    getMediaserverSettings,
    postMediaserverSettings,
    radarrSettings,
    getRadarrSettings,
    postRadarrSettings,
    sonarrSettings,
    getSonarrSettings,
    postSonarrSettings,
    spotifySettings,
    getSpotifySettings,
    postSpotifySettings,
    musicvideoSettings,
    getMusicvideoSettings,
    postMusicvideoSettings
  };
});
