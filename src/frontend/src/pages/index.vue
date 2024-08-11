<template>
  <v-card>
    <v-card-title>Welcome to Dyna-Arr</v-card-title>
    <v-card-text>
      <p>Well it expanded more then it was supposed to at the beginning, please pick what to do</p>
    </v-card-text>
  </v-card>
  <v-row>
    <v-col cols="12" lg="6" md="6" xl="6" xxl="6">
      <v-card class="mt-4">
        <v-card-title>DynaArr</v-card-title>
        <v-card-text>
          This will allow you to automate dynamically changed quality of your media files and which content to monitor
        </v-card-text>
        <v-card-actions>
          <v-btn color="primary" variant="flat" @click="navigateToRoute('/dynaarr')">Configure</v-btn>
        </v-card-actions>
      </v-card>
    </v-col>
    <v-col cols="12" lg="6" md="6" xl="6" xxl="6">
      <v-card class="mt-4">
        <v-card-title>SwipeArr</v-card-title>
        <v-card-text>
          A Tinder like interface to swipe through your media files and decide what to keep and what to delete
          <p>
            To use you need to enter Arr server details and optionally media server details in DynaArr
          </p>
        </v-card-text>
        <v-card-actions>
          <v-btn color="primary" variant="flat" @click="navigateToRoute('/settings')">Use</v-btn>
        </v-card-actions>
      </v-card>
    </v-col>
  </v-row>


  <v-card class="mt-4">
    <v-card-title>Why -Arr</v-card-title>
    <v-card-text>
      Well it is a third party tool to control the *arr suite but it is not associated with it. They will also most
      likely not give support if you are using this
    </v-card-text>
  </v-card>
  <v-card class="mt-4">
    <v-card-title>Tools</v-card-title>
    <v-card-text>
      Additional tools which might be useful in certain use cases
    </v-card-text>
    <v-card-actions>
      <v-btn color="primary" variant="flat" @click="navigateToRoute('/tools')">Go to</v-btn>
    </v-card-actions>
  </v-card>
  <v-card v-if="changelog" class="mt-4">
    <v-card-title>Changelog</v-card-title>
    <div>
      <v-list class="mt-n2 mb-2" style="max-height: 20vh">
        <v-list-item v-for="changes in changelog" :key="changes.version">
          <v-sheet class="mx-1 mb-2" elevation="1">
            <div class="pa-2">
              <h3>Version {{ changes.version }}</h3>
              <div v-if="changes.added.length !== 0">
                <h4>Added:</h4>
                <ul class="ml-4">
                  <li v-for="addition in changes.added">
                    {{ addition }}
                  </li>
                </ul>
              </div>
              <div v-if="changes.removed.length !== 0">
                <h4>Removed:</h4>
                <ul class="ml-4">
                  <li v-for="addition in changes.removed">
                    {{ addition }}
                  </li>
                </ul>
              </div>
              <div v-if="changes.changed.length !== 0">
                <h4>Changed:</h4>
                <ul class="ml-4">
                  <li v-for="addition in changes.changed">
                    {{ addition }}
                  </li>
                </ul>
              </div>
            </div>
          </v-sheet>
        </v-list-item>
      </v-list>
    </div>
  </v-card>
</template>

<script setup>
import {useRouter} from "vue-router";
import {onMounted, ref} from "vue";

const router = useRouter();
const changelog = ref(null);

function navigateToRoute(route) {
  router.push({name: route});
}

async function getChangelog() {
  try {
    const url = `/api/system/changelog`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorMessage = `An error occurred: ${response.status}`;
      throw new Error(errorMessage);
    }

    changelog.value = await response.json();
  } catch (error) {
    console.error('Error fetching changelog', error);
  }
}

onMounted(async () => {
  await getChangelog()
})
</script>
