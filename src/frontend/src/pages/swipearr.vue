<template>
  <v-dialog v-model="showSettings" max-height="700" max-width="600">
    <v-card>
      <div class="ma-4">
        <v-row>
          <v-card-title>
            Settings
          </v-card-title>
          <v-spacer/>
          <v-btn icon="mdi-close" @click="showSettings = false"/>
        </v-row>
        <v-card-text>
          <div v-for="(section, sectionKey) in userSettings" :key="sectionKey">
            <v-divider class="mb-4 mt-2"/>
            <v-row>
              <h3>{{ sectionKey }}</h3>
            </v-row>
            <v-row v-for="(setting, settingKey) in section" :key="settingKey" class="mb-n8 ml-0">
              <v-switch v-if="setting.type === 'switch'" v-model="userSettings[sectionKey][settingKey].value" :label="settingKey" color="secondary"
                        inset/>
              <v-select v-else-if="setting.type === 'select'" v-model="userSettings[sectionKey][settingKey].value"
                        :items="setting.props.items" :label="settingKey"/>
              <v-number-input v-else-if="setting.type === 'number'" v-model="userSettings[sectionKey][settingKey].value"
                              :label="settingKey" :max="setting.props.max"
                              :min="setting.props.min" type="number"/>
              <p v-else>Invalid setting type</p>
            </v-row>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-btn color="primary" variant="elevated" @click="clearSeenStorage">Clear seen storage</v-btn>
        </v-card-actions>
      </div>
    </v-card>
  </v-dialog>
  <v-dialog v-if="currentItem" v-model="editItemDialog" max-height="700" max-width="600">
    <v-card>
      <div class="ma-4">
        <v-row>
          <v-card-title>
            Edit: <span style="overflow-x: hidden; text-overflow: ellipsis; white-space: nowrap;">{{
              currentItem.title
            }}</span>
          </v-card-title>
          <v-spacer/>
          <v-btn icon="mdi-close" @click="editItemDialog = false"/>
        </v-row>
        <div class="mt-4">
          <v-select v-model="currentItem.qualityProfileId" :items="arrInfo[currentArr].qualityProfiles"
                    item-title="name" item-value="id"/>
          <v-autocomplete v-model="currentItem.tags" :items="arrInfo[currentArr].tags" chips closable-chips item-title="label"
                          item-value="id" label="Tags" multiple/>
          <v-switch v-model="currentItem.monitored" color="secondary" inset label="Monitored"/>
        </div>
        <v-card-actions class="mr-n2 mt-n6 mb-n2 float-right">
          <v-btn color="primary" variant="elevated" @click="submitEdit">Save changes</v-btn>
        </v-card-actions>
      </div>
    </v-card>
  </v-dialog>

  <v-tabs v-model="currentArr" class="mb-4">
    <v-tab value="radarr">Radarr</v-tab>
    <v-tab value="sonarr">Sonarr</v-tab>
    <v-spacer/>
    <v-btn icon="mdi-cog" @click="showSettings = true"/>
    <v-btn class="ml-4" icon="mdi-refresh" @click="getItems"/>
  </v-tabs>
  <div class="card-container">
    <div ref="tinderCardItem" class="tinder-card" v-bind:style="{ transform: returnTransformString }">
      <swipe-radarr v-if="currentArr === 'radarr'" :current-item="currentItem" :show-more-info="showMoreInfo"
                    :user-settings="userSettings"/>
      <swipe-sonarr v-if="currentArr === 'sonarr'" :current-item="currentItem" :show-more-info="showMoreInfo"
                    :user-settings="userSettings"/>
      <v-icon
        :style="{
          position: 'absolute',
          top: 'calc(50% - 10vw)',
          left: 'calc(50% - 10vw)',
          fontSize: '20vw',
          backgroundColor: 'rgba(0,0,0, 0.4)',
          borderRadius: '22vw',
          opacity: iconCard.opacity,
          color: iconCard.color
        }">
        {{ iconCard.type }}
      </v-icon>
    </div>
    <swipe-radarr v-if="currentArr === 'radarr'" :current-item="nextItem" :show-more-info="showMoreInfo"
                  :user-settings="userSettings" class="swipe-card next-card"/>
    <swipe-sonarr v-if="currentArr === 'sonarr'" :current-item="nextItem" :show-more-info="showMoreInfo"
                  :user-settings="userSettings" class="swipe-card next-card"/>
  </div>
  <v-card>
    <v-row class="align-center mx-1" style="height: 200%;">
      <v-col cols="auto">
        <v-btn icon style="font-size: 2em" variant="plain" @click="setPreviousItem">
          <v-icon>mdi-arrow-left</v-icon>
          <v-tooltip activator="parent" location="top">
            Previous item
          </v-tooltip>
        </v-btn>
      </v-col>
      <v-col>
        <v-btn block color="#e30000" style="height: 5em" variant="text" @click="permDelete(currentItem.id)">
          <v-icon style="font-size: 3em">mdi-delete-forever-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            Permanently delete
          </v-tooltip>
        </v-btn>
      </v-col>
      <v-col>
        <v-btn block color="#0091ff" style="height: 5em" variant="text" @click="editItem">
          <v-icon style="font-size: 3em">mdi-pencil</v-icon>
          <v-tooltip activator="parent" location="top">
            Edit item
          </v-tooltip>
        </v-btn>
      </v-col>
      <v-col cols="auto">
        <v-btn style="font-size: 2em" variant="plain" @click="setNextItem">
          <v-icon>mdi-arrow-right</v-icon>
          <v-tooltip activator="parent" location="top">
            Next item
          </v-tooltip>
        </v-btn>
      </v-col>
    </v-row>
  </v-card>
  <v-card class="mt-4">
    <v-row class="pa-4" style="display: flex; align-items: center;">
      <v-col cols="12" lg="3" md="3" sm="6" style="display: flex; align-items: center;" xl="3" xxl="3">
        <div class="downloaded-monitored"
             style="width: 1em; height: 1em; border-radius: 0.25em; margin-right: 0.5em;"></div>
        Downloaded (Monitored)
      </v-col>
      <v-col cols="12" lg="3" md="3" sm="6" style="display: flex; align-items: center;" xl="3" xxl="3">
        <div class="downloaded-unmonitored"
             style="width: 1em; height: 1em; border-radius: 0.25em; margin-right: 0.5em;"></div>
        Downloaded (Unmonitored)
      </v-col>
      <v-col cols="12" lg="3" md="3" sm="6" style="display: flex; align-items: center;" xl="3" xxl="3">
        <div class="missing-monitored"
             style="width: 1em; height: 1em; border-radius: 0.25em; margin-right: 0.5em;"></div>
        Missing (Monitored)
      </v-col>
      <v-col cols="12" lg="3" md="3" sm="6" style="display: flex; align-items: center;" xl="3" xxl="3">
        <div class="missing-unmonitored"
             style="width: 1em; height: 1em; border-radius: 0.25em; margin-right: 0.5em;"></div>
        Missing (Unmonitored)
      </v-col>
    </v-row>
  </v-card>
  <v-card class="mt-4">
    <v-card-text>
      Swipe interactions:
      <ul class="ml-4">
        <li><strong>Swipe left</strong>:
          <v-icon style="color:#fff">mdi-arrow-right</v-icon>
          Set next item
        </li>
        <li><strong>Swipe right</strong>:
          <v-icon style="color:#e30000">mdi-delete-forever-outline</v-icon>
          Permanently delete
        </li>
        <li><strong>Swipe up</strong>:
          <v-icon style="color:#0091ff">mdi-pencil</v-icon>
          Edit item
        </li>
        <li><strong>Tap</strong>: Show toggle more info on small screens</li>
        <li>Swipe down: Not being used</li>
      </ul>
    </v-card-text>
  </v-card>
</template>

<script setup>
import {computed, onMounted, reactive, ref, watch} from "vue";
import {VNumberInput} from 'vuetify/labs/VNumberInput'
import interact from 'interactjs';
import SwipeRadarr from "@/components/swipearr/swipeRadarr.vue";
import SwipeSonarr from "@/components/swipearr/swipeSonarr.vue";

// region Database
import Dexie from 'dexie';

const db = new Dexie('SeenItemsDB');
db.version(1).stores({
  radarrSeenItems: 'id',
  sonarrSeenItems: 'id'
});
// endregion


// region UI variables
const showSettings = ref(false)
const editItemDialog = ref(false)
const showMoreInfo = ref(false)
const interactionsDisabled = ref(false)

const userSettings = reactive({
  visual: {
    played: {type: 'switch', value: true},
    favorited: {type: 'switch', value: true},
    youtube: {type: 'switch', value: true},
    size: {type: 'switch', value: true},
    runtime: {type: 'switch', value: true},
    year: {type: 'switch', value: true},
    qualityProfile: {type: 'switch', value: true},
    added: {type: 'switch', value: true},
    genres: {type: 'switch', value: true},
    tags: {type: 'switch', value: true},
    overview: {type: 'switch', value: true},
    links: {type: 'switch', value: true},
  },
  links: {
    imdb: {type: 'switch', value: true},
    tvdb: {type: 'switch', value: true},
    tmdb: {type: 'switch', value: true},
    website: {type: 'switch', value: true},
    tvMaze: {type: 'switch', value: true},
    tvRaze: {type: 'switch', value: true}
  },
  sorting: {
    seen: {type: 'switch', value: false},
    sync: {type: 'switch', value: true},
  }
})
const currentArr = ref('radarr')
const currentItem = ref(null)
const nextItem = ref(null)
const iconCard = reactive({opacity: 0, type: null, color: "#fff"})
const currentCardPosition = reactive({x: 0, y: 0, rotation: 0})
const returnTransformString = computed(() => {
  return `translate3D(${currentCardPosition.x}px, ${currentCardPosition.y}px, 0) rotate(${currentCardPosition.rotation}deg)`;
})
// endregion

// region Data variables
const items = reactive({radarr: null, sonarr: null})
const notSeenItems = reactive({radarr: null, sonarr: null})
const arrInfo = reactive({radarr: {qualityProfiles: null, tags: null}, sonarr: {qualityProfiles: null, tags: null}})
const seenItems = reactive({radarr: null, sonarr: null})
// endregion

// region Helper functions
const getTag = function (id) {
  const item = arrInfo[currentArr.value].tags.find(entry => entry.id === id);
  return item ? item.label : id;
};
const getQuality = function (id) {
  const item = arrInfo[currentArr.value].qualityProfiles.find(entry => entry.id === id);
  return item ? item.name : id;
}
// endregion

// region SET ITEMS
function setItems() {
  currentItem.value = notSeenItems[currentArr.value][currentItemIndex[currentArr.value]]
  if (currentItemIndex[currentArr.value] === -1) currentItemIndex[currentArr.value] = notSeenItems[currentArr.value].length - 1

  let nextItemIndex = currentItemIndex[currentArr.value] + 1
  if (nextItemIndex > notSeenItems[currentArr.value].length - 1) nextItemIndex = 0;
  else if (nextItemIndex < 0) nextItemIndex = notSeenItems[currentArr.value].length - 1;
  nextItem.value = notSeenItems[currentArr.value][nextItemIndex]

  currentItem.value.qualityProfileIdText = getQuality(currentItem.value.qualityProfileId) || currentItem.value.qualityProfileId
  currentItem.value.tagsText = currentItem.value.tags.map(tag => getTag(tag) || tag);
  nextItem.value.qualityProfileIdText = getQuality(nextItem.value.qualityProfileId)
  nextItem.value.tagsText = nextItem.value.tags.map(tag => getTag(tag));
}

const currentItemIndex = reactive({radarr: 0, sonarr: 0})

function setPreviousItem() {
  currentItemIndex[currentArr.value] -= 1
  if (currentItemIndex[currentArr.value] === -1) currentItemIndex[currentArr.value] = notSeenItems[currentArr.value].length - 1
  setItems()
}

function setNextItem() {
  addItemToSeenStorage(currentItem.value, currentArr.value);
  currentItemIndex[currentArr.value] += 1
  if (currentItemIndex[currentArr.value] === notSeenItems[currentArr.value].length) currentItemIndex[currentArr.value] = 0
  setItems()
}

// endregion

// region Tinder functions
async function permDelete(id, importListExclusion = true, deleteFiles = true) {
  try {
    interactionsDisabled.value = true;
    const url = `/api/${currentArr.value}/item?id=${id}&importListExclusion=${importListExclusion}&deleteFiles=${deleteFiles}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorMessage = `An error occurred: ${response.status}`;
      throw new Error(errorMessage);
    }

    notSeenItems[currentArr.value] = notSeenItems[currentArr.value].filter(item => item.id !== id);
    setPreviousItem()
    setNextItem()

    return await response.json();
  } catch (error) {
    console.error('Error deleting item:', error);
  } finally {
    interactionsDisabled.value = false;
  }
}

function editItem() {
  editItemDialog.value = true;
}

async function submitEdit() {
  // delete favorited and played keys
  const item = { ...currentItem.value };
  delete item.favorited;
  delete item.played;
  delete item.qualityProfileIdText;
  delete item.tagsText;

  fetch(`/api/${currentArr.value}/item`, {
    method: 'POST',
    headers: {
      'accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(item)
  })
    .then(response => response.json())
    .then(editItemDialog.value = false)
    .catch(error => console.error('Error:', error));
}

// endregion

async function getItems() {
  const fetchRadarrItems = fetch("/api/radarr/items").then(response => response.json());
  const fetchSonarrItems = fetch("/api/sonarr/items").then(response => response.json());
  const fetchRadarrInfo = fetch("/api/radarr/info").then(response => response.json());
  const fetchSonarrInfo = fetch("/api/sonarr/info").then(response => response.json());

  const [radarrItems, sonarrItems, radarrInfo, sonarrInfo] = await Promise.all([
    fetchRadarrItems,
    fetchSonarrItems,
    fetchRadarrInfo,
    fetchSonarrInfo
  ]);

  items.radarr = radarrItems;
  items.sonarr = sonarrItems;
  arrInfo.radarr.qualityProfiles = radarrInfo.quality_profiles;
  arrInfo.radarr.tags = radarrInfo.tags;
  arrInfo.sonarr.qualityProfiles = sonarrInfo.quality_profiles;
  arrInfo.sonarr.tags = sonarrInfo.tags;
}

function loadSettings() {
  const savedSettings = localStorage.getItem('userSettings');
  if (savedSettings) {
    Object.assign(userSettings, JSON.parse(savedSettings));
  }
  if (userSettings.sorting.sync.value) {
    fetch("/api/system/user-settings").then(response => response.json()).then(data => {
      if (data) {
        Object.assign(userSettings, data);
        localStorage.setItem('userSettings', JSON.stringify(userSettings));
      }
    });
  }
}

async function saveSettings() {
  localStorage.setItem('userSettings', JSON.stringify(userSettings));
  if (userSettings.sorting.sync.value) {
    fetch("/api/system/user-settings", {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        settings: JSON.stringify(userSettings)
      }).toString()
    });
  }
}

function clearSeenStorage() {
  db.radarrSeenItems.clear();
  db.sonarrSeenItems.clear();
  if (userSettings.sorting.sync.value) {
    fetch("/api/system/clear-seen-items", {
      method: 'DELETE',
    });
  }
  getSeenItems();
}

async function addItemToSeenStorage(item, arr) {
  // First, check if the item is already in the database
  const existingItem = await db.table(`${arr}SeenItems`).get(item.id);

  const dbAddition = {
    id: item.id
  }

  if (!existingItem) {
    if (arr === 'radarr') {
      await db.radarrSeenItems.put(dbAddition);
    } else if (arr === 'sonarr') {
      await db.sonarrSeenItems.put(dbAddition);
    }
  } else {
    console.warn('item already in db: ', item.title, ' id: ', item.id);
    console.log("Recommended to clear the seen storage (at the bottom of settings on this page)")
  }

  if (userSettings.sorting.sync.value) {
    fetch("/api/system/seen-item", {
      method: 'POST',
      body: new URLSearchParams({
        id: item.id,
        arr: arr
      }).toString(),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
    });
  }
}

async function cleanUpStorage() {
  const radarrIds = items.radarr.map(item => item.id);
  const sonarrIds = items.sonarr.map(item => item.id);
  const radarrItemsToRemove = await db.radarrSeenItems.where('id').noneOf(radarrIds).toArray();
  const sonarrItemsToRemove = await db.sonarrSeenItems.where('id').noneOf(sonarrIds).toArray();
  if (radarrItemsToRemove.length > 0) {
    await db.radarrSeenItems.bulkDelete(radarrItemsToRemove.map(item => item.id));
  }

  if (sonarrItemsToRemove.length > 0) {
    await db.sonarrSeenItems.bulkDelete(sonarrItemsToRemove.map(item => item.id));
  }
}

async function getSeenItems() {
  if (userSettings.sorting.seen.value) {
    notSeenItems.radarr = items.radarr
    notSeenItems.sonarr = items.sonarr

    currentItemIndex.radarr = 0;
    currentItemIndex.sonarr = 0;
    setItems();
    return
  }

  if (userSettings.sorting.sync.value) {
    await fetch("/api/system/seen-items").then(response => response.json()).then(data => {
      seenItems.radarr = data.radarr;
      seenItems.sonarr = data.sonarr;
    });
  } else {
    seenItems.radarr = (await db.radarrSeenItems.toArray()).map(item => item.id);
    seenItems.sonarr = (await db.sonarrSeenItems.toArray()).map(item => item.id);
  }
  notSeenItems.radarr = items.radarr.filter(item => !seenItems.radarr.includes(item.id));
  notSeenItems.sonarr = items.sonarr.filter(item => !seenItems.sonarr.includes(item.id));

  currentItemIndex.radarr = 0;
  currentItemIndex.sonarr = 0;
  setItems();
}

async function getAdditionalMediaServerInfo() {
  if (!items.radarr || !items.sonarr) return;
  fetch("/api/mediaserver/media-info").then(response => response.json()).then(data => {
    items.radarr.forEach(item => {
      item.favorited = !!data.movies.favorited.includes(item.id);
      item.played = !!data.movies.played.includes(item.id);
    });
    items.sonarr.forEach(item => {
      item.favorited = !!data.series.favorited.includes(item.id);
      item.played = !!data.series.played.includes(item.id);
    });
  });
}

function setupInteraction() {
  interact('.tinder-card')
    .on('tap', function () {
      showMoreInfo.value = !showMoreInfo.value
    })
    .draggable({
      inertia: false,
      modifiers: [
        interact.modifiers.restrictRect({
          endOnly: true
        })
      ],
      listeners: {
        move(event) {
          if (interactionsDisabled.value) return;

          const screenWidth = window.innerWidth;
          const screenHeight = window.innerHeight;

          currentCardPosition.x += event.dx;
          currentCardPosition.y += event.dy;
          const X = currentCardPosition.x;
          const Y = currentCardPosition.y;

          const maxRotation = 20;

          currentCardPosition.rotation = maxRotation * (X / (screenWidth / 2));
          if (currentCardPosition.rotation > maxRotation) {
            currentCardPosition.rotation = maxRotation;
          } else if (currentCardPosition.rotation < -maxRotation) {
            currentCardPosition.rotation = -maxRotation;
          }

          const posX = Math.abs(X);
          const posY = Math.abs(Y);
          const xBigger = posX > posY;
          if (xBigger) {
            iconCard.opacity = Math.max(posX / (screenWidth / 3), posX / 300);
          } else {
            iconCard.opacity = Math.max(posY / (screenHeight / 3), posY / 300);
          }

          if (X < 0 && xBigger) {
            iconCard.type = "mdi-arrow-right";
            iconCard.color = "#fff";
          } else if (X > 0 && xBigger) {
            iconCard.type = "mdi-delete-forever-outline";
            iconCard.color = "#e30000";
          } else if (Y > 0) {
            iconCard.type = "mdi-pencil";
            iconCard.color = "#0091ff";
          }
        },
        end() {
          if (interactionsDisabled.value) return;
          
          const screenWidth = window.innerWidth;
          const screenHeight = window.innerHeight;

          const X = currentCardPosition.x;
          const Y = currentCardPosition.y;

          const isSwipeLeft = X < -0.33 * screenWidth || X < -300;
          const isSwipeRight = X > 0.33 * screenWidth || X > 300;
          const isSwipeUp = Y < -0.33 * screenHeight || Y < -300;
          const isSwipeDown = Y > 0.33 * screenHeight || Y > 300;

          if (isSwipeLeft) {
            setNextItem();
          } else if (isSwipeRight) {
            permDelete(currentItem.value.id)
          } else if (isSwipeUp) {
            // Not being used
          } else if (isSwipeDown) {
            editItem();
          }

          // Reset the position
          currentCardPosition.x = 0;
          currentCardPosition.y = 0;
          currentCardPosition.rotation = 0;

          iconCard.opacity = 0;
          iconCard.type = null;
        }
      }
    });
}

watch(currentArr, () => setItems())
watch(userSettings, (previous, current) => {
  saveSettings();
  getAdditionalMediaServerInfo();
  getSeenItems();

  if (!previous.sorting.sync.value && current.sorting.sync.value) {
    loadSettings();
  }
})

onMounted(async () => {
  await getItems();
  loadSettings();
  await getSeenItems();
  setItems();
  setupInteraction();
  await getAdditionalMediaServerInfo();
  await cleanUpStorage();
});
</script>

<style scoped>
:deep(.missing-unmonitored) {
  background-color: #ffa500;
}

:deep(.downloaded-unmonitored) {
  background-color: #888;
}

:deep(.missing-monitored) {
  background-color: #f05050;
}

:deep(.downloaded-monitored) {
  background-color: #00853d;
}

.tinder-card {
  touch-action: none;
  position: relative;
  z-index: 2;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  -khtml-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;

}

.card-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.swipe-card {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.next-card {
  z-index: 1;
}
</style>
