<script setup>
import sonarr from "@/components/settings/dynaarr/sonarr.vue";
import {ref} from "vue";
import Radarr from "@/components/settings/dynaarr/radarr.vue";

const arrType = ref('sonarr')
</script>

<template>
  <v-tabs v-model="arrType">
    <v-tab value="sonarr">Sonarr</v-tab>
    <v-tab value="radarr">Radarr</v-tab>
  </v-tabs>
  <v-window v-model="arrType">
    <v-window-item value="sonarr">
      <sonarr />
    </v-window-item>
    <v-window-item value="radarr">
      <radarr />
    </v-window-item>
  </v-window>
</template>

<style scoped>

</style>
