<template>
  <div>
    <v-container fluid>
      <div class="text-center pa-8">
        <v-icon icon="mdi-help-circle" size="96" color="grey-lighten-1" />
        <h1 class="text-h2 mt-6 mb-2">
          404
        </h1>
        <h2 class="text-h5 mb-4">
          Page Not Found
        </h2>
        <p class="text-body-1 text-medium-emphasis mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <v-btn
          color="primary"
          size="large"
          @click="$router.push('/')"
        >
          Go Home
        </v-btn>
      </div>
    </v-container>
  </div>
</template>