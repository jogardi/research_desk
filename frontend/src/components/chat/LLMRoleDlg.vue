<template>
    <el-dialog v-model="dialogVisible" :width="800" :show-close="false" :top="dialogTop + 'px'" class="dialog-body notes-report">
    <!-- dialog header -->
    <template #header="{ close, titleId, titleClass }">
      <q-toolbar>
        <q-toolbar-title style="font-size: 1rem;"><q-icon name="android" class="p-ml-2 p-mr-2"></q-icon>
          AI Model Roles
      </q-toolbar-title>
      

          <q-space />
          <!-- <tooltip-btn tooltip="Download as PDF" flat dense color="positive" icon="picture_as_pdf" size="md" /> -->
          <!-- <tooltip-btn tooltip="Share" icon="share" flat size="sm" color="positive" class="p-mr-1" Xstyle="font-size: .8rem;"></tooltip-btn> -->
          <q-separator vertical inset class="p-ml-3 p-mr-1" />
          <q-btn flat round dense color="primary" icon="close" @click="close" />
      </q-toolbar>
    </template>

    <!-- dialog body -->
    <div Xclass="p-px-3">
      <div class="p-d-flex p-justify-between p-align-items-center p-pb-2 p-pt-0 p-pl-3 p-pr-2">
        <span class="p-d-flex p-align-items-center" style="font-size: 0.8rem; opacity: .7;"><q-icon name="info" size="xs" Xcolor="info" /> <span class="p-ml-1">Click a radio button to select a role.</span></span>
        <span>  
          <q-btn v-if="sessionStore.session.selectedLlmRoleId" label="Clear Role" @click="sessionStore.session.selectedLlmRoleId = null" flat no-caps color="negative" dense size="md" icon="clear" />
        <q-btn label="Add Role" @click="showAddRoleDialog()" icon="add" flat no-caps color="primary" dense size="md" class="p-ml-3"></q-btn>
      </span>
      </div>
      <q-separator inset />
      <el-scrollbar id="text-search-help-dlg-body" always max-height="510px" class="p-pt-0 p-pb-3 p-px-5">
            <q-list  class="sys-prompts-bg" separator padding>
              <q-item v-for="llmRole in store.llmRoles" :key="llmRole.id" Xtag="label" class="q-pa-sm cursor-pointer">
                <q-item-section side top> 
                    <q-radio v-model="sessionStore.session.selectedLlmRoleId" :val="llmRole.id" Xclass="q-mb-sm" dense size="md" color="primary" />                   
                </q-item-section>
              <q-item-section>
                    {{ llmRole.role }}
                    </q-item-section>
                    <q-item-section side top>
                      <div class="p-d-flex p-align-items-center">
                        <q-btn @click="showEditRoleDialog(llmRole)" 
                      flat dense round icon="edit" color="primary" size="sm">
                    </q-btn>
                    <q-btn @click="removeLlmRole(llmRole.id)" 
                      flat dense round icon="delete" color="red-3" size="sm">
                    </q-btn>
                      </div>
              </q-item-section>
            </q-item>
          </q-list>
        </el-scrollbar>
        </div>
    </el-dialog>

<!-- Edit role -->
<q-dialog v-model="showEditRole" Xpersistent>
    <q-card style="min-width: 600px;">
        <q-card-section>
          <div class="text-positive">Edit AI ModelRole</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="role" type="textarea" Xlabel="AI Model Role" autogrow filled clearable Xclass="q-mb-md" style="font-size: .9rem;"/>
        </q-card-section>
        <q-separator inset/>
        <q-card-actions align="right" class="text-primary">
          <q-btn @click="cancelEditRole()" Xflat label="Cancel" color="negative" v-close-popup />
          <q-btn @click="saveLlmRole()" :disabled="!role || role == ''" Xflat label="Save" color="positive" v-close-popup />
        </q-card-actions>
      </q-card>
  </q-dialog>

  <!-- Add Role -->
  <q-dialog v-model="showAddRole" Xpersistent>
    <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-positive">Add AI ModelRole</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="role" Xlabel="AI Model Role" type="textarea" autogrow filled clearable class="q-mb-md" style="font-size: .9rem;"/>
        </q-card-section>
        <q-separator inset/>
        <q-card-actions align="right" class="text-primary">
          <q-btn Xflat label="Cancel" color="negative" v-close-popup />
          <q-btn @click="addLlmRole()" :disabled="!role || role == ''" Xflat label="Add" color="positive" v-close-popup />
        </q-card-actions>
      </q-card>
  </q-dialog>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import { computed } from 'vue'
import { useStore } from 'src/stores/main-store';
import { useSessionStore } from 'src/stores/session-store';
import useUtils from 'src/composables/useUtils';
import uuid4 from 'uuid4'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const store = useStore();
const sessionStore = useSessionStore();
const utils = useUtils();
const $q = useQuasar()

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

// Variables
const dialogTop = 150

const activeRoleItem = ref(null)
const role = ref(null)

const showAddRole = ref(false)
const showEditRole = ref(false)

// Watch for changes to sessionStore.session.selectedLlmRoleId
watch(
  () => sessionStore.session.selectedLlmRoleId,
  async () => {
    await utils.updateTotalTokens();
  }
)

// Functions
const removeLlmRole = async (llmRoleId) => {
  $q.dialog({
        title: 'Do you want to remove this AI Model Role?',
        message: 'Removing this AI Model Role will be permanent!',
        cancel: true,
        // persistent: true,
        ok: {
          color: 'positive'
        },
        cancel: {
          color: 'negative'
        }
      }).onOk(async () => {
        await store.removeLlmRole(llmRoleId)
      })

}

function showAddRoleDialog() {
  role.value = ''
  showAddRole.value = true
}

async function addLlmRole() {
  await store.addLlmRole(role.value)
  showAddRole.value = false
  role.value = ''
}

function showEditRoleDialog(llmRole) {
  activeRoleItem.value = llmRole
  role.value = llmRole.role;
  showEditRole.value = true
}

async function saveLlmRole() {
  activeRoleItem.value.role= role.value
  await store.saveLlmRole(activeRoleItem.value)
    showEditRole.value = false
    role.value = ''
  }
</script>

<style scoped>
    .help-subtitle {
        font-weight: 400 !important;
        padding-right: 5px;
        font-size: 1.1rem;
    }

    h6 {
        font-size: 1.1rem;
        margin-top: 20px;
        margin-bottom: 0px;
        font-weight: 400 !important;
    }

    #text-search-help-dlg-body div {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>