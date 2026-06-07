<template>
    <el-dialog v-model="dialogVisible" :width="500" :show-close="false" class="dialog-body notes-report">
        <!-- dialog header -->
        <template #header="{ close, titleId, titleClass }">
            <q-toolbar>
                <q-toolbar-title style="font-size: 1rem;">
                    <q-icon name="fa-solid fa-address-card" class="p-ml-2 p-mr-2"></q-icon>
                    Profile
                </q-toolbar-title>
                <q-space />
                <q-separator vertical inset class="p-ml-3 p-mr-1" />
                <q-btn flat round dense color="primary" icon="close" @click="close" />
            </q-toolbar>
        </template>

        <!-- dialog body -->
        <div class="p-px-3 p-pb-2 p-mt-0">
          <div class="subtitle text-subtitle1 p-pb-0">User</div>
          <div class="p-mb-3">{{ userStore.getUser().name }}</div>

            <div class="p-d-flex p-justify-between p-items-center p-pb-2">
                <span class="subtitle text-subtitle1">Change Password</span>
                <q-btn @click="showPassword = !showPassword" style="opacity: 0.6;" :tooltip="showPassword ? 'Hide Password' : 'Show Password'"
                        :icon="showPassword ? 'visibility_off' : 'visibility'" position="left"
                        Xcolor="primary" size="sm" dense flat Xclass="p-mr-0">
                        <tooltip anchor="center left" self="center right">{{ showPassword ? 'Hide Passwords' : 'Show Passwords' }}</tooltip>
                </q-btn>
            </div>
                <div class="p-pb-3">
                    <q-input v-model="password" label="New Password" color="primary" clearable
                        dense :type="showPassword ? 'text' : 'password'" filled>
                    </q-input>
                </div>
                <div>
                    <q-input v-model="confirmPassword" label="Confirm Password" color="primary" clearable   
                    dense :type="showPassword ? 'text' : 'password'" filled>
                    </q-input>
                </div>
                <!-- Message area -->
                <div v-if="password && confirmPassword && password !== confirmPassword" class="p-pt-3 Xp-pb-2 p-pl-2 p-pr-2 p-bg-red-1">
                    <q-icon name="cancel" color="red" size="1.2rem" />
                    <span class="p-ml-2 text-red-5">Passwords do not match</span>
                </div>
                <div v-if="password && confirmPassword && password == confirmPassword" class="p-pt-3 Xp-pb-2 p-pl-2 p-pr-2 p-bg-green-1">
                    <q-icon name="check" color="green" size="1.2rem" />
                    <span class="p-ml-2 text-green-5">Passwords match</span>
                </div>
                <q-separator spaced class="p-mt-4 p-mb-2"/>
                <div class="p-d-flex p-justify-end p-items-center">
                    <q-btn label="Cancel" @click="closeDialog" no-caps  color="negative" size="md" class="p-mr-2"/>
                    <q-btn label="Change Password" @click="changePassword()" 
                    no-caps color="positive" size="md" :disabled="!password || !confirmPassword || password !== confirmPassword"/>
                </div>
        </div>
    </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useUserStore } from 'src/stores/user-store';
import useNotify from 'src/composables/useNotify.js';
import Tooltip from 'src/components/Tooltip.vue';

const userStore = useUserStore();
const { notify } = useNotify();

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const showPassword = ref(false);
const showConfirmPassword = ref(false);

// Emits
const emit = defineEmits(['update:modelValue'])

// Computed property to handle v-model
const dialogVisible = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  }
})

const password = ref('');
const confirmPassword = ref('');

// Watch for dialog visibility changes
watch(dialogVisible, (newValue) => {
  if (newValue) {
    console.log('ProfileDlg dialog opened - resetting form');
    resetForm();
  }
})

function resetForm() {
  showPassword.value = false;
  showConfirmPassword.value = false;
  password.value = '';
  confirmPassword.value = '';
}

function closeDialog() {
  dialogVisible.value = false;
  password.value = '';
  confirmPassword.value = '';
}

async function changePassword() {
  if (password.value !== confirmPassword.value) {
    console.log('Passwords do not match');
    return;
  }
  const success = await userStore.changePassword(password.value);
  closeDialog();
  if (success) {
    notify('Password changed successfully', 'positive');
  } else {
    notify('Password change failed', 'negative');
  }
}
</script>