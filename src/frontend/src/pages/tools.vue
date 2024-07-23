<template>
  <v-dialog v-model="showOutput" max-width="770">
    <v-card>
      <v-card-title>
        Output:
      </v-card-title>
      <v-card-text>
        <div v-if="String(output).length === 0">
          No Changes
        </div>
        <div v-else>
          {{ output }}
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn color="primary" variant="elevated" @click="showOutput = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
  <v-row>
    <v-col v-for="tool in tools" cols="12" lg="6" md="6" xl="4" xxl="3">
      <v-card>
        <v-card-title>
          {{ tool.title }}
        </v-card-title>
        <v-card-text>
          {{ tool.description }}
        </v-card-text>
        <v-tabs v-model="tool.buttonPage" class="ml-4">
          <v-tab v-for="page in Object.keys(tool.buttons)" :value="page">{{ page }}</v-tab>
        </v-tabs>
        <v-window v-model="tool.buttonPage" class="pa-4">
          <v-window-item v-for="page in Object.keys(tool.buttons)" :value="page">
            <v-btn v-for="button in tool.buttons[page]" :color="button.color" :text="button.text"
                   class="mr-4" @click="apiCall(button.apiCall, button.apiType)"/>
          </v-window-item>
        </v-window>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import {reactive, ref} from "vue";

const tools = reactive([
  {
    title: 'Delete unmonitored',
    description: 'It deletes ALL unmonitored files, it can NOT be canceled',
    buttonPage: null,
    buttons:
      {
        sonarr: [
          {
            color: 'primary',
            text: 'dry',
            apiCall: '/api/sonarr/delete-unmonitored',
            apiType: 'GET'
          },
          {
            color: 'warning',
            text: 'delete',
            apiCall: '/api/sonarr/delete-unmonitored',
            apiType: 'DELETE'
          }
        ],
        radarr: [
          {
            color: 'primary',
            text: 'dry',
            apiCall: '/api/radarr/delete-unmonitored',
            apiType: 'GET'
          },
          {
            color: 'warning',
            text: 'delete',
            apiCall: '/api/radarr/delete-unmonitored',
            apiType: 'DELETE'
          }
        ]
      }
  }
])

const showOutput = ref(false)
const output = ref(null)

const apiCall = async function (apiUrl, apiType) {
  try {
    const response = await fetch(apiUrl, {
      method: apiType,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    if (data) {
      showOutput.value = true
      output.value = data
    }
    return data;
  } catch (error) {
    console.error('Error:', error);
    showOutput.value = true
    output.value = error
    throw error;
  }
};
</script>
