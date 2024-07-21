<template>
  <v-app>
    <v-app-bar :elevation="4" scroll-behavior="elevate">
      <v-col>
        <v-tabs v-model="currentPage" align-tabs="center">
          <v-tab :value="'home'" @click="navigateToRoute('/')">Home</v-tab>
          <v-tab :value="'dynaarr'" @click="navigateToRoute('/dynaarr')">DynaArr</v-tab>
          <v-tab :value="'swipearr'" @click="navigateToRoute('/swipearr')">SwipeArr</v-tab>
          <v-tab :value="'tools'" @click="navigateToRoute('/tools')">Tools</v-tab>
        </v-tabs>
      </v-col>
    </v-app-bar>

    <v-main style="height: calc(100% - 5em)">
      <v-container>
        <router-view/>
      </v-container>
    </v-main>
    <v-footer class="align-center text-center" style="height: 5em">
      <a class="ml-4" href="/docs">API</a>
      <a class="ml-4" href="https://github.com/mah-thingies/arr-tools/">Github</a>
    </v-footer>
  </v-app>
</template>

<script setup>
import {useTheme} from "vuetify";
import {onMounted, ref, watch} from "vue";
import {useRoute, useRouter} from 'vue-router';

const theme = useTheme();
const colorSchemeQuery = window.matchMedia("(prefers-color-scheme: dark)");

function setTheme() {
  theme.global.name.value = !colorSchemeQuery.matches ? "light" : "dark";
  const color = colorSchemeQuery.matches ? "#212121" : "#ffffff";
  document
    .querySelector('meta[name="theme-color"]')
    .setAttribute("content", color);
}

const router = useRouter();
const route = useRoute();
const currentPage = ref('');

function navigateToRoute(route) {
  router.push({path: route});
}

function updateCurrentPage() {
  const path = route.path.split('/')[1];
  currentPage.value = path ? path : 'home';
}

onMounted(() => {
  setTheme();
  colorSchemeQuery.addEventListener("change", setTheme);
  updateCurrentPage();
});

watch(route, updateCurrentPage);
</script>

<style>
a,
a:hover,
a:visited,
a:active {
  color: inherit;
  text-decoration: none;
}
</style>
