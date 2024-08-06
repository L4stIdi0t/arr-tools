// stores/mediaStore.js
import { defineStore } from 'pinia';
import {reactive, ref} from 'vue';

export const useMediaStore = defineStore('mediaStore', () => {
  const radarrItems = ref(null);
  const sonarrItems = ref(null);
  const radarrInfo = ref({
      quality_profiles: [],
      tags: []
    });

  const sonarrInfo = ref({
      quality_profiles: [],
      tags: []
    });
  const mediaInfo = ref(
    {
      users: [],
    }
  );

  const fetched = reactive({
    radarrItems: false,
    sonarrItems: false,
    radarrInfo: false,
    sonarrInfo: false,
    mediaInfo: false
  });

  async function fetchRadarrItems(force = false) {
    if (!fetched.radarrItems || force) {
      const response = await fetch('/api/radarr/items');
      radarrItems.value = await response.json();
      fetched.radarrItems = true;
    }
  }

  async function fetchSonarrItems(force = false) {
    if (!fetched.sonarrItems || force) {
      const response = await fetch('/api/sonarr/items');
      sonarrItems.value = await response.json();
      fetched.sonarrItems = true;
    }
  }

  async function fetchRadarrInfo(force = false) {
    if (!fetched.radarrInfo || force) {
      const response = await fetch('/api/radarr/info');
      radarrInfo.value = await response.json();
      fetched.radarrInfo = true;
    }
  }

  async function fetchSonarrInfo(force = false) {
    if (!fetched.sonarrInfo || force) {
      const response = await fetch('/api/sonarr/info');
      sonarrInfo.value = await response.json();
      fetched.sonarrInfo = true;
    }
  }

  async function fetchMediaInfo() {
    if (!fetched.mediaInfo) {
      const response = await fetch('/api/mediaserver/media-info');
      mediaInfo.value = await response.json();
      fetched.mediaInfo = true;
      updateItemsWithMediaInfo();
    }
  }

  function updateItemsWithMediaInfo() {
    if (mediaInfo.value) {
      const { movies, series } = mediaInfo.value;

      if (radarrItems.value) {
        radarrItems.value.forEach(item => {
          item.favorited = !!movies.favorited.includes(item.id);
          item.played = !!movies.played.includes(item.id);
        });
      }

      if (sonarrItems.value) {
        sonarrItems.value.forEach(item => {
          item.favorited = !!series.favorited.includes(item.id);
          item.played = !!series.played.includes(item.id);
        });
      }
    }
  }

  async function fetchAllData() {
    await Promise.all([
      fetchRadarrItems(),
      fetchSonarrItems(),
      fetchRadarrInfo(),
      fetchSonarrInfo(),
      fetchMediaInfo()
    ]);
  }

  return {
    radarrItems,
    sonarrItems,
    radarrInfo,
    sonarrInfo,
    mediaInfo,
    fetchRadarrItems,
    fetchSonarrItems,
    fetchRadarrInfo,
    fetchSonarrInfo,
    fetchMediaInfo,
    fetchAllData,
  };
});
