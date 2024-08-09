<script setup>
import {computed, ref} from "vue";
import {useDisplay} from "vuetify";
import Connections from "@/components/settings/connections.vue";
import Dynaarr from "@/components/settings/dynaarr.vue";
import Music from "@/components/settings/music.vue";

const drawer = ref('connections');
const {mdAndDown} = useDisplay();
const isDrawerOpen = computed(() => {
  if (!mdAndDown.value) {
    return true;
  } else {
    return openDrawer.value;
  }
})
const openDrawer = ref(true);

const toggleDrawer = () => {
  openDrawer.value = !openDrawer.value;
};
</script>

<template>
  <v-navigation-drawer v-model="isDrawerOpen" width="200">
    <v-list-item @click="toggleDrawer" class="text-right my-4" v-if="mdAndDown"><v-icon>mdi-arrow-collapse-left</v-icon></v-list-item>
    <v-divider/>

    <v-list-item link @click="drawer = 'Connections'" title="Connections"/>
    <v-divider/>
    <v-list-item link @click="drawer = 'DynaArr'" title="DynaArr"/>
    <v-divider/>
    <v-list-item link @click="drawer = 'Music'" title="Music"/>
  </v-navigation-drawer>
  <v-window v-model="drawer">
    <h1 class="mb-4">
      <v-btn icon="mdi-menu" @click="toggleDrawer" v-if="mdAndDown" />
      {{drawer}}
    </h1>
    <v-window-item value="Connections">
      <connections/>
    </v-window-item>
    <v-window-item value="DynaArr">
      <dynaarr/>
    </v-window-item>
    <v-window-item value="Music">
      <music/>
    </v-window-item>
  </v-window>
</template>

<style scoped>

</style>
