<script setup>
import {formatBytes, formatDate, formatTimeLength, relativeDate} from "@/utils/formatters";
import {useDisplay} from "vuetify";
import {computed} from "vue";

const {mdAndUp} = useDisplay()

const props = defineProps({
  currentItem: {required: true, type: [Object, null]},
  userSettings: {required: true, type: Object},
  showMoreInfo: {required: true, type: Boolean}
})

const getColorClass = computed(() => {
  if (!props.currentItem) return;
  const exists = props.currentItem.statistics.sizeOnDisk > 0 || false
  if (props.currentItem.monitored) {
    if (exists) return 'downloaded-monitored'
    return "missing-monitored"
  }
  if (exists) return 'downloaded-unmonitored'
  return "missing-unmonitored"
})

const getPosterImage = function (arrItem) {
  const poster = arrItem.images.find(image => image.coverType === "poster");
  return poster ? poster.remoteUrl : null;
}
</script>

<template>
  <v-card>
    <v-row no-gutters>
      <v-col v-if="mdAndUp || !showMoreInfo" cols="12" lg="6" md="6" xl="6" xxl="6">
        <div class="ma-4">
          <div v-if="!currentItem" class="animated-background" style="width: 100%; padding-top: 150%"/>
          <v-img v-else :alt="`${currentItem.title} poster`" :draggable="false" :src='getPosterImage(currentItem)'>
            <div v-if="currentItem.ended" style="width: 40%; padding-top: 40%; position: absolute; right: -20%; top: -20%; background-color: #f05050; transform: rotate(45deg);" />
            <div style="width: 100%; position: absolute; bottom: 1.25em;">
              <v-icon v-if="currentItem.played" style="font-size: 5em; color: #00853d">mdi-check-bold</v-icon>
              <v-icon v-if="currentItem.favorited" style="font-size: 5em; color: #ff0000">mdi-heart</v-icon>
            </div>
            <div :class="getColorClass" style="width: 100%; height: 1em; position: absolute; bottom: 0;"/>
          </v-img>
        </div>
      </v-col>
      <v-col v-if="currentItem && (mdAndUp || showMoreInfo)" :class="{'mt-4': true, 'mx-3': !mdAndUp}" cols="12" lg="6"
             md="6" xl="6" xxl="6">
        <div>
          <v-row>

          </v-row>
          <v-row class="mt-6">
            <v-card-title v-if="!mdAndUp" class="mt-n4">
              {{ currentItem.title }}
            </v-card-title>
            <v-col v-if="userSettings.visual.size.value" class="mt-n4" cols="12" lg="6" md="6" sm="12" xl="6" xs="12"
                   xxl="6">
              <p>Size: {{ formatBytes(currentItem.statistics.sizeOnDisk) }}</p>
            </v-col>
            <v-col v-if="userSettings.visual.runtime.value" class="mt-n4" cols="12" lg="6" md="6" sm="12" xl="6" xs="12"
                   xxl="6">
              <p>Runtime: {{ formatTimeLength(currentItem.runtime) }}</p>
            </v-col>
            <v-col v-if="userSettings.visual.year.value" class="mt-n4" cols="12" lg="6" md="6" sm="12" xl="6" xs="12"
                   xxl="6">
              <p>Year: {{ currentItem.year }}</p>
            </v-col>
            <v-col v-if="userSettings.visual.qualityProfile.value" class="mt-n4" cols="12" lg="6" md="6" sm="12" xl="6" xs="12"
                   xxl="6">
              <p>Quality: {{ currentItem.qualityProfileIdText }}</p>
            </v-col>
            <v-col v-if="userSettings.visual.added.value" class="mt-n4" cols="12" lg="6" md="6" sm="12" xl="6" xs="12"
                   xxl="6">
              <div>
                <p>Added: {{ relativeDate(currentItem.added) }}</p>
                <v-tooltip activator="parent" location="top">
                  {{ formatDate(currentItem.added) }}
                </v-tooltip>
              </div>
            </v-col>
          </v-row>

          <v-row v-if="userSettings.visual.links.value" class="show-links mb-4 mx-1" style="font-size: 0.8em">
            <a v-if="userSettings.links.imdb.value && currentItem.imdbId && currentItem.imdbId !== 0" :href="`https://www.imdb.com/title/${currentItem.imdbId}`" class="mr-2"
               target="_blank">IMDB</a>
            <a v-if="userSettings.links.tvdb.value && currentItem.tvdbId && currentItem.tvdbId !== 0" :href="`http://www.thetvdb.com/?tab=series&id=${currentItem.tvdbId}`" class="mr-2"
               target="_blank">TVDB</a>
            <a v-if="userSettings.links.tmdb.value && currentItem.tmdbId && currentItem.tmdbId !== 0" :href="`https://www.themoviedb.org/tv/${currentItem.tmdbId}`" class="mr-2"
               target="_blank">TMDB</a>
            <a v-if="userSettings.links.tvMaze.value && currentItem.tvMazeId && currentItem.tvMazeId !== 0" :href="`https://www.tvmaze.com/shows/${currentItem.tvMazeId}/_`" class="mr-2"
               target="_blank">TvMaze</a>
          </v-row>


          <v-chip-group v-if="userSettings.visual.genres.value" class="mt-n2">
            <v-chip v-for="genre in currentItem.genres" :key="genre">
              {{ genre }}
            </v-chip>
          </v-chip-group>

          <v-chip-group v-if="userSettings.visual.tags.value" class="mt-n2">
            <v-chip v-for="tag in currentItem.tagsText" :key="tag">
              {{ tag }}
            </v-chip>
          </v-chip-group>

          <v-card-text class="ml-n6 mr-4">
            <p v-if="userSettings.visual.overview.value" class="ml-3">{{ currentItem.overview }}</p>
          </v-card-text>
        </div>
      </v-col>
    </v-row>
  </v-card>
</template>

<style scoped>
@keyframes gradient {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.animated-background {
  background-size: 400% 400%;
  background-image: linear-gradient(
    to right,
    rgba(125, 125, 125, 0.8),
    rgba(125, 125, 125, 0.5),
    rgba(125, 125, 125, 0.8),
    rgba(125, 125, 125, 0.5)
  );
  animation: gradient 3s ease infinite;
}

.video-container {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 Aspect Ratio */
  overflow: hidden;
}

.video-container iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.show-links {
  text-decoration: underline;
  color: dodgerblue;
}
</style>
