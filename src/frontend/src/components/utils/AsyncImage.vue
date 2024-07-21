<template>
  <div class="image-container">
    <div v-if="!loaded" class="animated-background"/>
    <img
      :alt="alt"
      :class="loaded ? 'image' : 'hide-image'"
      :draggable="draggable"
      :src="src"
      @load="loaded = true"
    />
  </div>
</template>

<script setup>
import {ref} from "vue";

const props = defineProps({
  src: {type: String, required: true},
  alt: {type: String, default: ""},
  draggable: {type: Boolean, default: true}
});

const loaded = ref(false);
</script>

<style scoped>
.image-container {
  width: 100%;
  height: 100%;
  display: block;
}

.hide-image {
  visibility: hidden;
  position: absolute;
  top: 0;
  left: 0;
}

.image {
  display: block;
  object-fit: cover;
  width: 100%;
  height: 100%;
}

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
  width: 100%;
  height: 100%;
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
</style>
