<script setup>
import {ref} from 'vue';
import Media from "@/components/mediaserver/media.vue";
import Sonarr from "@/components/mediaserver/sonarr.vue";
import Radarr from "@/components/mediaserver/radarr.vue";

const configType = ref()
</script>

<template>
  <v-tabs v-model="configType">
    <v-tab value="media">Media server</v-tab>
    <v-tab value="sonarr">Sonarr</v-tab>
    <v-tab value="radarr">Radarr</v-tab>
  </v-tabs>
  <v-window v-model="configType" class="mt-2">
    <v-window-item value="media">
      <media/>
    </v-window-item>
    <v-window-item value="sonarr">
      <sonarr/>
    </v-window-item>
    <v-window-item value="radarr">
      <radarr/>
    </v-window-item>
  </v-window>
</template>

<style scoped>
</style>
