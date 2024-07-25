<template>
  <div style="position: fixed; right: 1.5em; bottom: 1.5em; z-index: 1">
    <v-btn :disabled="!settingsAreEqual" class="mr-4" color="secondary" variant="elevated" @click="getDryRun">Dry run
    </v-btn>
    <v-btn :disabled="settingsAreEqual" color="primary" variant="elevated" @click="postRadarrSettings">Save</v-btn>
  </div>

  <v-dialog v-model="showFilteredItems" max-width="770">
    <v-card>
      <v-card-title>
        {{ filteredItems.length }} items
      </v-card-title>
      <v-row class="ma-4" no-gutters>
        <v-col v-for="currentItem in filteredItems" cols="auto">
          <v-col cols="12">
            <async-image :alt="`${currentItem.title} poster`" :src="currentItem.images[0].remoteUrl"
                         style="width: 10em; height: 15em"/>
          </v-col>
          <v-col style="max-width: 10em; text-overflow: ellipsis; overflow: hidden; white-space: nowrap">
            {{ currentItem.title }}
          </v-col>
        </v-col>
      </v-row>
      <v-card-actions>
        <v-btn color="primary" variant="elevated" @click="showFilteredItems=false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="showDryRun" max-width="770">
    <v-card>
      <div v-if="Object.keys(dryRunInfo).length > 0">
        <v-sheet class="ma-2 mb-0" elevation="2">
          <v-card-title>
            Quality Changes:
          </v-card-title>
          <v-list v-if="dryRunInfo.quality_changes" max-height="30vh">
            <v-row v-for="item in dryRunInfo.quality_changes" class="ma-0 pa-0">
              <v-col cols="auto">
                {{ getQuality(item.item.qualityProfileId) }}
                <strong>-></strong>
                {{ getQuality(item.new_quality_profile) }}
              </v-col>
              <v-col>
                {{ item.item.title }}
              </v-col>
              <v-divider/>
            </v-row>
          </v-list>
          <v-card-text v-else>
            No items
          </v-card-text>
        </v-sheet>

        <v-sheet class="ma-2 mb-0" elevation="2">
          <v-card-title>
            Monitor Changes:
          </v-card-title>
          <v-list v-if="dryRunInfo.monitorable_items" max-height="30vh">
            <v-row v-for="item in dryRunInfo.monitorable_items" class="ma-0 pa-0">
              <v-col>
                {{ item.title }}
              </v-col>
              <v-divider/>
            </v-row>
          </v-list>
          <v-card-text v-else>
            No items
          </v-card-text>
        </v-sheet>
        <v-sheet class="ma-2 mb-0" elevation="2">
          <v-card-title>
            Deletes:
          </v-card-title>
          <v-list v-if="dryRunInfo.deletable_items" max-height="30vh">
            <v-row v-for="item in dryRunInfo.deletable_items" class="ma-0 pa-0">
              <v-col>
                {{ item.title }}
              </v-col>
              <v-divider/>
            </v-row>
          </v-list>
          <v-card-text v-else>
            No items
          </v-card-text>
        </v-sheet>
      </div>

      <v-card-actions>
        <v-btn color="primary" variant="elevated" @click="showDryRun=false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-card>
    <v-card-title>Connection</v-card-title>
    <v-col>
      <v-text-field v-model="newSettings.base_url" label="Server address" placeholder="http://127.0.0.1:7878/"/>
      <v-text-field v-model="newSettings.api_key" label="API key" placeholder="XXXXXXXXXXXXXX"/>
      <v-switch v-model="newSettings.enabled" color="secondary" inset
                label="If Radarr should be used for auto management"/>
      <v-alert v-if="!newSettings.enabled" density="compact" type="warning">
        Before enabling please first do a dry run of your settings because it can delete files...
      </v-alert>
    </v-col>
  </v-card>
  <v-card class="mt-4">
    <v-card-title>General</v-card-title>
    <v-col>
      <v-switch v-model="newSettings.use_watched" color="secondary" inset
                label="Use watched items in changes or ignore all watched"/>
      <v-switch v-model="newSettings.use_favorite" color="secondary" inset
                label="Use favorited items in changes or ignore all favorites"/>
      <v-switch v-model="newSettings.use_on_resume" color="secondary"
                inset label="Use items on resume in changes or ignore all items on resume"/>
      <v-divider/>
    </v-col>
    <v-row class="mb-1" style="cursor: pointer" @click="qualityNotCollapsed = !qualityNotCollapsed">
      <h4 class="ml-7">Quality profiles</h4>
      <v-spacer/>
      <v-icon class="mr-8">{{ qualityNotCollapsed ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
    </v-row>
    <v-expand-transition>
      <v-col v-if="qualityNotCollapsed">
        <v-select v-model="newSettings.ultra_quality_profile" :items="qualityProfiles" hint="Like a 4K profile"
                  item-title="name" item-value="id" label="Ultra quality profile"/>
        <v-select v-model="newSettings.high_quality_profile" :items="qualityProfiles" hint="Like a 1080p profile"
                  item-title="name" item-value="id" label="High quality profile"/>
        <v-select v-model="newSettings.normal_quality_profile" :items="qualityProfiles"
                  hint="Like a average profile" item-title="name" item-value="id" label="Normal quality profile"/>
        <v-select v-model="newSettings.low_quality_profile" :items="qualityProfiles" hint="Like a microsized profile"
                  item-title="name" item-value="id" label="Low quality profile"/>
        <v-select v-model="newSettings.watched_quality_profile" :items="qualityOptions" item-title="name"
                  item-value="id" label="Watched quality profile"/>
        <v-select v-model="newSettings.favorited_quality_profile" :items="qualityOptions"
                  item-title="name" item-value="id" label="Favorite quality profile"/>
        <v-select v-model="newSettings.on_resume_quality_profile" :items="qualityOptions"
                  item-title="name" item-value="id" label="On resume quality profile"/>
        <v-select v-model="newSettings.very_popular_quality_profile" :items="qualityOptions"
                  item-title="name" item-value="id" label="Very popular quality profile"/>
        <v-select v-model="newSettings.popular_quality_profile" :items="qualityOptions" item-title="name"
                  item-value="id" label="Popular quality profile"/>
        <v-select v-model="newSettings.less_popular_quality_profile" :items="qualityOptions"
                  item-title="name" item-value="id" label="Less popular quality profile"/>
        <v-select v-model="newSettings.unpopular_quality_profile" :items="qualityOptions"
                  item-title="name" item-value="id" label="Unpopular quality profile"/>
        <v-switch v-model="newSettings.search_for_quality_upgrades" color="secondary" inset
                  label="Upgrade on quality profile change"/>
        <v-switch v-model="newSettings.monitor_quality_changes" color="secondary" inset
                  label="Monitor on quality profile changed items"/>

        <v-autocomplete v-model="newSettings.exclude_users_from_quality_upgrades" :items="mediaServerUsers" chips
                        closable-chips
                        item-title="Name" item-value="Id" label="Excluded users from quality upgrades"
                        multiple/>
        <v-autocomplete v-model="newSettings.exclude_tags_from_quality_upgrades" :items="tags" chips closable-chips
                        item-title="label" item-value="id" label="Excluded tags from quality upgrades" multiple/>
        <v-divider/>
      </v-col>
    </v-expand-transition>
    <v-row class="mb-1" style="cursor: pointer" @click="decayNotCollapsed = !decayNotCollapsed">
      <h4 class="ml-7 mt-2">Decay</h4>
      <v-spacer/>
      <v-icon class="mr-8">{{ decayNotCollapsed ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
    </v-row>
    <v-expand-transition>
      <v-col v-if="decayNotCollapsed">
        <v-number-input v-model="newSettings.watched_decay_days" label="Watched decay days"/>
        <v-number-input v-model="newSettings.favorite_decay_days" label="Favorited decay days"/>
        <v-number-input v-model="newSettings.on_resume_decay_days" label="On resume decay days"/>
        <v-number-input v-model="newSettings.very_popular_decay_days" label="Very popular decay days"/>
        <v-number-input v-model="newSettings.popular_decay_days" label="Popular decay days"/>
        <v-number-input v-model="newSettings.less_popular_decay_days" label="Less popular decay days"/>
        <v-number-input v-model="newSettings.unpopular_decay_days" label="Unpopular decay days"/>
        <v-select v-model="newSettings.decay_start_timer" :items="decayStartTimer" item-title="name"
                  item-value="id" label="Decay start timer"/>
        <!--        <v-select v-model="newSettings.decay_method" label="Decay method" :items="decayMethod" item-title="name" item-value="id"/>-->
        <v-divider/>
      </v-col>
    </v-expand-transition>
    <v-row class="mb-1" style="cursor: pointer" @click="monitoredNotCollapsed = !monitoredNotCollapsed">
      <h4 class="ml-7 mt-2">Monitored</h4>
      <v-spacer/>
      <v-icon class="mr-8">{{ monitoredNotCollapsed ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
    </v-row>
    <v-expand-transition>
      <v-col v-if="monitoredNotCollapsed">
        <v-switch v-model="newSettings.mark_favorited_as_monitored" color="secondary" inset
                  label="Mark favorited items as monitored"/>
        <v-switch v-model="newSettings.mark_on_resume_as_monitored" color="secondary" inset
                  label="Mark on resume items as monitored"/>
        <v-switch v-model="newSettings.mark_very_popular_as_monitored" color="secondary"
                  inset label="Mark very popular items as monitored"/>
        <v-switch v-model="newSettings.mark_popular_as_monitored" color="secondary" inset
                  label="Mark popular items as monitored"/>
        <v-switch v-model="newSettings.mark_less_popular_as_monitored" color="secondary"
                  inset label="Mark less popular items as monitored"/>
        <v-switch v-model="newSettings.mark_unpopular_as_monitored"
                  :disabled="newSettings.mark_unpopular_as_unmonitored"
                  color="secondary" inset label="Mark unpopular items as monitored"/>
        <v-switch v-model="newSettings.mark_unpopular_as_unmonitored"
                  :disabled="newSettings.mark_unpopular_as_monitored"
                  color="secondary" inset label="Mark unpopular items as unmonitored"/>
        <v-autocomplete v-model="newSettings.exclude_tags_from_monitoring" :items="tags" chips closable-chips
                        item-title="label" item-value="id" label="Excluded tags from monitoring" multiple/>
        <v-autocomplete v-model="newSettings.exclude_users_from_monitoring" :items="mediaServerUsers" chips
                        closable-chips
                        item-title="Name" item-value="Id" label="Excluded users from monitoring"
                        multiple/>
        <v-divider/>
      </v-col>
    </v-expand-transition>
    <v-row class="mb-1">
      <h4 class="ml-7 mt-2">Deletion</h4>
    </v-row>
    <v-expand-transition>
      <v-col>
        <v-alert v-if="newSettings.enabled" density="compact" type="warning">
          This instance is enabled and enabling deletion will permanently delete items
        </v-alert>
        <v-switch v-model="newSettings.delete_unmonitored_files" color="secondary" inset
                  label="Delete unmonitored files"/>
        <v-autocomplete v-model="newSettings.exclude_tags_from_deletion" :items="tags" chips closable-chips
                        item-title="label" item-value="id" label="Excluded tags from deletion" multiple/>
        <v-divider/>
      </v-col>
    </v-expand-transition>
  </v-card>
  <v-card class="mt-6">
    <v-row class="ma-4 mb-0">
      <v-select v-model="popularityFilter" :items="popularityFilters" density="compact" label='Filter type'/>
      <v-btn :disabled="!popularityFilter" class="ml-4 mt-1" color="primary" variant="elevated" @click="addFilter">Add
        popularity filter
      </v-btn>
    </v-row>
  </v-card>
  <div>
    <div v-for="section in Object.keys(newSettings.popular_filters)" :key="section">
      <v-card v-if="newSettings.popular_filters[section].length != 0" class="mt-4">
        <v-card-title>{{ section }}</v-card-title>
        <v-sheet v-for="filter, idx in newSettings.popular_filters[section]" class="ma-4 mt-2" elevation="4">
          <v-row class="mx-2">
            <v-col cols="auto" style="min-width: 12em">
              <v-select :items="filterFields" :model-value="Object.keys(filter)[0]" item-title="name" item-value="id"
                        @update:model-value="handleFilterTypeChange($event, idx, section)"/>
            </v-col>
            <v-col>
              <v-text-field :model-value="filter[Object.keys(filter)[0]]" hint="E.g. Comedy&&Adventure"
                            label="Filter string"
                            @update:model-value="handleFilterStringChange($event, idx, section)"/>
            </v-col>
            <v-col cols="auto">
              <v-btn class="mt-2" color="error" icon variant="text" @click="deleteFilter(idx, section)">
                <v-icon style="font-size: 2em">mdi-delete-circle-outline</v-icon>
              </v-btn>
            </v-col>
          </v-row>
        </v-sheet>
        <v-card-actions>
          <v-btn color="secondary" variant="elevated" @click="showFilterPreview(section)">Show preview</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import {onMounted, ref, watch} from 'vue'
import {VNumberInput} from 'vuetify/labs/VNumberInput'
import isEqual from 'lodash/isEqual'
import {filter_items} from "@/utils/filterParser";
import AsyncImage from "@/components/utils/AsyncImage.vue";

const popularityFilters = ['Unpopular', 'Less Popular', 'Popular', 'Very Popular']
const popularityFilter = ref(null)

const decayStartTimer = [
  {name: "Added", id: 0},
  {name: "Shortest", id: 1},
  {name: "Watched else Added", id: 2},
  {name: "Watched else Shortest", id: 3},
]
const decayMethod = [
  {name: "Delete & Downgrade", id: 2},
  {name: "Downgrade", id: 3}
]
const qualityOptions = [
  {name: "Ultra", id: 3},
  {name: "High", id: 2},
  {name: "Normal", id: 1},
  {name: "Low", id: 0}
]

const getQuality = function (id) {
  const item = qualityProfiles.value.find(entry => entry.id === id);
  return item ? item.name : null;
};

function formatName(id) {
  return id.replace(/\./g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1 $2')
    .replace(/^./, str => str.toUpperCase());
}

const fields = [
  "title",
  "sortTitle",
  "year",
  "runtime",
  "genres",
  "tags",
  "ratings.imdb.votes",
  "ratings.imdb.value",
  "ratings.tmdb.votes",
  "ratings.tmdb.value",
  "ratings.metacritic.value",
  "ratings.rottenTomatoes.value",
  "popularity"
];

const filterFields = fields.map(field => ({
  name: formatName(field),
  id: field
}));

const newSettings = ref({
  base_url: "http://radarr:7878/",
  api_key: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  enabled: false,

  ultra_quality_profile: null,
  high_quality_profile: null,
  normal_quality_profile: null,
  low_quality_profile: null,
  watched_quality_profile: 2,
  favorited_quality_profile: 3,
  on_resume_quality_profile: 2,
  very_popular_quality_profile: 2,
  popular_quality_profile: 1,
  less_popular_quality_profile: 0,
  unpopular_quality_profile: 0,
  search_for_quality_upgrades: true,
  monitor_quality_changes: true,
  exclude_tags_from_quality_upgrades: [],
  exclude_users_from_quality_upgrades: [],

  use_watched: true,
  use_favorite: true,
  use_on_resume: false,

  watched_decay_days: 30,
  favorite_decay_days: 180,
  on_resume_decay_days: 14,
  very_popular_decay_days: 30,
  popular_decay_days: 60,
  less_popular_decay_days: 90,
  unpopular_decay_days: 120,
  decay_method: 3,
  decay_start_timer: "added",

  mark_favorited_as_monitored: true,
  mark_on_resume_as_monitored: false,
  mark_very_popular_as_monitored: true,
  mark_popular_as_monitored: true,
  mark_less_popular_as_monitored: true,
  mark_unpopular_as_monitored: false,
  mark_unpopular_as_unmonitored: true,
  exclude_tags_from_monitoring: [],
  exclude_users_from_monitoring: [],

  delete_unmonitored_files: false,
  exclude_tags_from_deletion: [],

  popular_filters: {
    very_popular: [],
    popular: [],
    less_popular: [],
    unpopular: []
  },
  monitor_filters: [],
  unmonitor_filters: []
})
const retrievedSettings = ref()
let arrItems = []
const filteredItems = ref(null)
const showFilteredItems = ref(false)
const dryRunInfo = ref(null)
const showDryRun = ref(false)

const qualityNotCollapsed = ref(true)
const monitoredNotCollapsed = ref(true)
const decayNotCollapsed = ref(true)

const tags = ref([])
const qualityProfiles = ref([])
const mediaServerUsers = ref([])

async function showFilterPreview(section) {
  filteredItems.value = filter_items(arrItems, newSettings.value.popular_filters[section])
  showFilteredItems.value = true
}

async function getDryRun() {
  fetch("/api/radarr/dry")
    .then(response => response.json())
    .then(data => {
      dryRunInfo.value = data
      showDryRun.value = true
    })
}

async function handleFilterTypeChange(value, idx, section) {
  const filterObject = newSettings.value.popular_filters[section][idx];
  const oldKey = Object.keys(filterObject)[0];
  filterObject[value] = filterObject[oldKey];
  delete filterObject[oldKey];
}

async function handleFilterStringChange(value, idx, section) {
  const filterObject = newSettings.value.popular_filters[section][idx];
  const key = Object.keys(filterObject)[0];
  filterObject[key] = value;
}

async function addFilter() {
  if (!popularityFilter.value) return;

  newSettings.value.popular_filters[popularityFilter.value.toLowerCase().replace(/\s+/g, '_')].push({"title": ""})
}

async function deleteFilter(idx, section) {
  newSettings.value.popular_filters[section].splice(idx, 1)
}

async function getServerData() {
  fetch("/api/radarr/info")
    .then(response => response.json())
    .then(data => {
      qualityProfiles.value = data.quality_profiles
      tags.value = data.tags
    })

  fetch("/api/mediaserver/info")
    .then(response => response.json())
    .then(data => {
      mediaServerUsers.value = data.users
    })

}

async function getRadarrSettings() {
  fetch("/api/radarr/settings")
    .then(response => response.json())
    .then(data => {
      newSettings.value = {...data}
      retrievedSettings.value = data
    })
}

async function postRadarrSettings() {
  try {
    const response = await fetch('/api/radarr/settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(newSettings.value)
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
  await getRadarrSettings()
}


async function getArrItems() {
  fetch("/api/radarr/items")
    .then(response => response.json())
    .then(data => {
      arrItems = data
    })
}

const settingsAreEqual = ref(true)

watch([newSettings, retrievedSettings], () => {
  settingsAreEqual.value = isEqual(newSettings.value, retrievedSettings.value)
}, {deep: true})

onMounted(async () => {
  await getRadarrSettings()
  await getServerData()
  await getArrItems()
})
</script>

<style scoped>

</style>
