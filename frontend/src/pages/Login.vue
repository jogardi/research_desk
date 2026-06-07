<template>
    <q-page class="flex flex-center">
      <div class="q-pa-lg" style=" min-width: 600px; max-width: 600px;">
        <!-- <div class="text-center q-mb-lg">Choose your preferred login method</div> -->
        <div class="q-pa-lg" style=" min-width: 600px; max-width: 600px;"
          :style="$q.dark.isActive ? 'border: 1px solid #555' : 'border: 1px solid #ccc'">
        <div class="text-h5 q-mb-lg">Login</div>
  
        <q-form @submit.prevent="onSubmit" class="q-gutter-md" style="width: 100%"> 
          <q-input filled v-model="form.login" type="email" label="Email *" required />
          <q-input filled v-model="form.password" type="password" label="Password *" required />
          <div class="flex justify-end q-gutter-md">
            <!-- <q-btn outline color="primary" Xflat label="Forgot password" type="a" href="#" /> -->
            <q-btn :loading="loading" label="Login" type="submit" color="primary" Xclass="full-width" />
          </div>
  
          <q-banner v-if="invalidCredentials" rounded class="text-white bg-red-10">
            Invalid email or password. Please try again.
          </q-banner>
  
          <!-- <div class="row justify-end q-mt-md">
            <q-btn flat label="Forgot password" type="a" href="#" />
          </div> -->
        </q-form>
        <!-- TODO: Add social login -->
        <!-- <div class="Xtext-center q-my-md">Or sign in with</div>
        <div class="row Xjustify-center q-gutter-sm">
          <q-btn outline color="info" no-caps @click="loginWithProvider('google')"><i class="fa-brands fa-google q-mr-sm"></i> Google</q-btn>
          <q-btn outline color="info" no-caps @click="loginWithProvider('facebook')"><i class="fa-brands fa-facebook q-mr-sm"></i> Facebook</q-btn>
          <q-btn outline color="info" no-caps @click="loginWithProvider('twitter')"><i class="fa-brands fa-twitter q-mr-sm"></i> Twitter</q-btn>
        </div> -->
      </div>
    </div>
    </q-page>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  import { useStore } from 'src/stores/main-store';
  import { useUserStore } from 'src/stores/user-store';

  const store = useStore()
  const userStore = useUserStore();
  
  const router = useRouter();
  const loading = ref(false);
  const form = ref({
    login: '',
    password: ''
  });
  const invalidCredentials = ref(false);
  
  async function onSubmit() {
    loading.value = true;
    invalidCredentials.value = false;
    const loginSuccess = await userStore.login(form.value);
  
    loading.value = false;
    if (!loginSuccess) {
      invalidCredentials.value = true;
    } 
    else {
      console.log('*** Login successful');
      await store.initialize();
      // router.replace('/');
      window.location.href = '/'; // replace current page with home page
    }
  }
  
  function loginWithProvider(provider) {
    console.log(`Login with ${provider}`);
    // Add logic to handle login with social provider
  }
  </script>
  
  <style>
  /* Add any additional styles specific to your project */
  </style>