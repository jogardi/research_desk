<template>
  <div>
    <q-layout v-if="userStore.isLoggedIn()" view="hHh Lpr lFf" class="page-flex-container">
    <q-header id="header" bordered Xelevated :style="{ display: store.showNavbar ? 'block' : 'none' }">
      <q-toolbar class="header-bg">
        <!-- Toolbar Logo and Title -->
        <q-toolbar-title>
          <div @click="reloadSite()" class="flex items-center Xq-py-md cursor-pointer" style="width: 338px;">
            <!-- <img
              src="/research-desk.png"
              style="width: 50px; height: 50px; margin-right: 0px; Xmargin-top: 10px; border-radius: 50%;"
            /> -->
            <span class="header-logo q-ml-sm Xtext-white">The Research Desk</span>
            <!-- <span class="q-ml-sm Xtext-white">AI Adventuresque</span> -->
            
          </div>
        </q-toolbar-title>
        <q-space />
        <!-- Toolbar Navigation Tabs -->
        <q-tabs v-model="store.layoutSelectedTab"  active-color="active-tab" :active-bg-color="store.layoutSelectedTab == 'guide' ? 'transparent' : 'active-tab'" Xno-caps
            indicator-color="transparent"
            Xindicator-color="store.layoutSelectedTab == 'builder'? transparent' : 'white'" 
            style="position: absolute; left: 400px;">
            <q-route-tab to="/" :replace="true" name="category-selector" label="Category Selector"  />
            <q-route-tab to="/context-builder" :replace="true" name="context-builder" label="Context Builder" :disable="noCategoriesSelected">
              <tooltip v-if="noCategoriesSelected">Please select categories</tooltip>
            </q-route-tab>
            <q-route-tab to="/explorer" :replace="true" name="explorer" label="Explorer" :disable="noCategoriesSelected || noExplorer">
              <tooltip v-if="noCategoriesSelected || noContextDocs">{{noCategoriesSelected? 'Please select categories' : ''}} {{!noCategoriesSelected && noContextDocs? 'Search and/or move items to context' : ''}}</tooltip>
            </q-route-tab>
            <q-route-tab to="/chat" :replace="true" name="chat" label="Chat" :disable="noCategoriesSelected">
              <tooltip v-if="noCategoriesSelected">Please select categories</tooltip>
            </q-route-tab>
            <q-route-tab to="/guide" :replace="true" name="guide" style="display: none"/>
            <!-- <q-route-tab to="/builder" :replace="true" name="builder" labels style="display: none" /> -->
            <!-- <q-route-tab to="/excerpts" :replace="true" name="excerpts" label="Excerpts" /> -->
        </q-tabs>
        <q-space />

        <!-- Toolbar Buttons -->
        <div>
          <!-- <span v-if="store.loading" class="text-info p-mr-0 spinner-message p-pb-2 p-pt-1 p-px-2 p-mr-3" style="border-radius: 5px;">
            <q-spinner-audio thickness="10" size="sm"/> <span>{{ store.loading }}</span>
          </span> -->
          <tooltip-btn tooltip="Save Thought Flow" @click="saveSession()" color="info" class="save-session-btn" icon="save" 
            dense flat style="font-size: .8rem;">
          </tooltip-btn>
          <tooltip-btn tooltip="Knowlegebase Tree" @click="openDocTree()" color="info" class="save-session-btn" icon="account_tree" 
            dense flat style="font-size: .8rem;">
          </tooltip-btn>
          <tooltip-btn tooltip="Report" v-if="sessionStore.session && sessionStore.session.contextDocs && sessionStore.session.contextDocs.length > 0" @click="showReport = !showReport" icon="description" color="info" class="save-session-btn" 
            dense flat style="font-size: .8rem;">
          </tooltip-btn>
          <tooltip-btn :tooltip="showNotes? 'Close Notes' : 'Open Notes'" @click="showNotes = !showNotes" icon="notes" color="info" class="save-session-btn" 
            dense flat style="font-size: .8rem;">
          </tooltip-btn>
          <tooltip-btn tooltip="User Guide" icon="help" to="/guide" @click="store.layoutSelectedTab = 'guide'" color="info" class="save-session-btn" 
            dense flat style="font-size: .8rem;">
          </tooltip-btn>
          <!-- <tooltip-btn Xtooltip="showNotes? 'Close Notes' : 'Open Notes'" @click="showNotes = !showNotes" class="save-session-btn" icon="comments"
            dense flat style="font-size: .8rem;">
          </tooltip-btn> -->
          
          <!-- Logged in User Dropdown Button -->
          <span v-if="userStore.isLoggedIn()">
            <q-btn class="user-info" icon="person" icon-right="expand_more" dense Xlabel="`${userStore.data? userStore.data.name : ''}`" 
              flat no-caps>
              <q-menu anchor="bottom right" self="top right" class="menu-bg">
                <q-list dense padding>
                  <menu-item icon="fa-solid fa-address-card" @click="showProfileDlg = true" color="primary">
                    Profile
                  </menu-item>
                  <menu-item icon="logout" @click="logout" color="primary">
                    Logout
                  </menu-item>
                </q-list> 
              </q-menu>
            </q-btn>
          </span>

          <!-- Dark/Light Mode Toggle Button -->
          <q-btn @click="toggleTheme()"
            :color="$q.dark.isActive ? 'orange-1' : 'black'" :icon="$q.dark.isActive ? 'wb_sunny' : 'nights_stay'"
             flat dense style="opacity: .8">
          </q-btn>
          <span v-if="!store.initialized"><q-spinner-audio thickness="10" size="sm"/>Initializing ...</span>

        </div>
      </q-toolbar>
    </q-header>

    <!-- 
      SIDE BAR 
    -->
    <q-drawer v-if="!store.pdfViewerData.show && store.initialized && store.layoutSelectedTab != 'guide'" id="left-drawer" Xdark bordered  class="q-pa-md"
      v-model="leftDrawerOpen"
      show-if-above
      :width="`${store.layoutSelectedTab == 'chat' || store.layoutSelectedTab == 'explorer' ? '400' : '325'}`"
      >
      <div v-if="store.layoutSelectedTab != 'chat' && store.layoutSelectedTab != 'explorer'">
        <div class="row justify-between items-center p-pl-1">
          <!-- <span class="text-subtitle1 text-weight-medium q-mr-xs" style="opacity: .7">Knowledgebase:</span>  -->
          <q-select v-if="knowledgebases.length > 1" v-model="selectedKnowledgebase" 
            :options="knowledgebases" label="Knowledgebase" 
            option-value="kb_name"
            option-label="kb_display_name"
            label-color="info" color="primary" dense 
              filled class="col col-grow Xtext-h6 Xtext-subtitle1 grow-1" style="font-size: 1rem" 
              @update:model-value="onChangeKnowledgebase()" />
          <div v-else class="" Xstyle="opacity: .7"> 
            <div class="text-info text-subtitle1" style="font-size: .8rem;">Knowledgebase</div>
            <div>{{ selectedKnowledgebase? selectedKnowledgebase.kb_display_name : '' }}</div>
          </div>
        </div>
        <q-separator spaced Xclass="q-ml-md"/>

        <div class="flex justify-between items-end p-pl-1 p-mt-3 p-mb-1">
          <div class="title text-subtitle1 text-weight-medium Xtext-h6" style="opacity: .7">Thought Flows</div>
          <tooltip-btn tooltip="Start a new thought flow" icon="add" @click="showAddSessionDialog()" flat size="sm" color="primary"></tooltip-btn>
        </div>
        <q-separator spaced Xclass="q-ml-md"/>
       
        <!-- Sessions <link rel="manifest" href="manifest.json"> -->
        <div class="p-pl-1">
          <q-list class="session-items"  Xdark v-if="sessionStore.session">
            <q-item class="name" v-for="session in sessionStore.sessionList" :key="session.id"
              @click="loadSession(session.id)" clickable
              :active="sessionStore.session.id == session.id">
              <q-item-section>
                <q-item-label>{{ session.name }}</q-item-label>
                <q-item-label caption class="description">{{ session.description }}</q-item-label>
              </q-item-section>
              <q-item-section v-if="sessionStore.session.id == session.id" side>
                <q-btn flat dense round icon="more_horiz" color="primary" class="q-mr-sm">
                  <q-menu anchor="bottom right" self="top right" class="menu-bg">
                    <q-list dense padding>
                      <menu-item icon="save" @click="saveSession()" color="positive">
                        Save
                      </menu-item>
                      <menu-item icon="alt_route" @click="showForkSessionDialog(session.name)" color="positive">
                        Fork
                      </menu-item>
                      <menu-item icon="share" color="positive">
                        Share
                      </menu-item>
                      <menu-item icon="edit" @click="showEditSessionDialog()" color="secondary">
                        Edit
                      </menu-item>
                      <menu-item icon="delete" @click="removeSession(session.id)" color="negative" >
                        Remove
                      </menu-item>                      
                    </q-list>
                  </q-menu>
                </q-btn>
              </q-item-section>
            </q-item>
          </q-list>
        </div>
      </div>
      <el-container v-if="store.layoutSelectedTab == 'chat' || store.layoutSelectedTab == 'explorer'" style="height: 100%; opacity: .7" class="chunk-text p-px-0">
        <el-header style="height: auto;" class="p-px-0">
          <div class="title text-subtitle1 text-weight-medium Xtext-info Xtext-h6" Xstyle="opacity: .7">Knowledgebase</div>
          <div class="text-subtitle1 text-weight-medium" style="font-size: 1.2rem;">{{ selectedKnowledgebase? selectedKnowledgebase.kb_display_name : '' }}</div>
          <div class="title text-subtitle1 text-weight-medium Xtext-h6 p-mt-3" Xstyle="opacity: .7">Thought Flow</div>
          <div class="text-subtitle1 text-weight-medium" style="font-size: 1.2rem;">{{ sessionStore.session.name }}</div>

          <div class="title text-subtitle1 text-weight-medium Xtext-h6 p-mt-3">Context - Source Excerpts</div>
        </el-header>
        <el-main class="p-pt-0 p-px-0">
        <div v-for="doc in sessionStore.session.contextDocs" :key="doc.documentID">
            <!-- <div class="text-bold">{{doc.documentCategory}}{{doc.documentName}}</div> -->
            <div class="text-subtitle1"><span class="p-mb-2" style="font-size: 1.0rem;">Document:</span> {{doc.documentCategory}}/{{doc.documentName}}</div>
            <div class="text-subtitle1 text-weight-medium" style="font-size: 1.2rem;">{{ doc.title }}</div>
            <div v-for="excerpt in doc.excerpts" :key="excerpt[0]" class="p-mt-2 p-ml-3 p-pb-3">
                <div v-html="excerpt[2].text" style="font-size: 1rem;"></div>
                <q-separator class="p-mt-3" />
            </div>
        </div>
        </el-main>
      </el-container>
    </q-drawer>
    
    <!-- 
      MAIN CONTENT
    -->
    <q-page-container>
      <!-- <div class="subtitle text-subtitle1">Selected Categories</div> -->
       <!-- Selected categories -->
      <selected-categories v-if="sessionStore.session && sessionStore.session.categories && sessionStore.session.categories.length > 0 && store.layoutSelectedTab != 'guide'" style="margin-top: 3px; margin-bottom: 5px;" />
      <q-separator inset style="padding-top: 0px; opacity: .5"/>

      <router-view />
    </q-page-container>
  </q-layout>

  <!-- Notes Editor -->
  <q-dialog v-model="showNotes" Xpersistent Xfull-width full-height position="bottom">
    <q-card style="width: 1100px; max-width: 90vw; height: 80vh; max-height: 90vh;">
      <notes-editor />
    </q-card>
  </q-dialog>

  <!-- Report -->
  <q-dialog v-model="showReport" :persistent="false">
    <q-card style="width: 1000px; max-width: 90vw; height: 80vh; max-height: 90vh;">
      <report />
    </q-card>
  </q-dialog>

  <!-- Doc Tree -->
  <q-dialog v-model="showDocTree" :persistent="false">
    <q-card style="width: 1000px; max-width: 90vw; height: 80vh; max-height: 90vh;">
      <doc-tree style="max-width: none !important;" />
    </q-card>
  </q-dialog>

  <!-- Edit Session -->
  <q-dialog v-model="showEditSession" Xpersistent>
    <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Edit Thought Flow</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="activeSessionItem.name" label="Thought Flow Name" filled clearable class="q-mb-md"/>
          <q-input v-model="activeSessionItem.description" label="Thought Flow Description" type="textarea" autogrow filled clearable />
        </q-card-section>
        <q-separator inset/>
        <q-card-actions align="right" class="text-primary">
          <q-btn @click="cancelEditSession()" Xflat label="Cancel" color="negative" v-close-popup />
          <q-btn @click="saveSession()" :disabled="!sessionItem.name || sessionItem.name == ''" Xflat label="Save" color="positive" v-close-popup />
        </q-card-actions>
      </q-card>
  </q-dialog>

  <!-- Add Session -->
  <q-dialog v-model="showAddSession" Xpersistent>
    <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Add Thought Flow</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="sessionItem.name" label="Thought Flow Name" filled clearable class="q-mb-md"/>
          <q-input v-model="sessionItem.description" label="Thought Flow Description" type="textarea" autogrow filled clearable />
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-icon name="warning" color="warning" size="sm" /> Make sure you save your current thought flow before adding a new one!
        </q-card-section>
        <q-separator inset/>
        <q-card-actions align="right" class="text-primary">
          <q-btn Xflat label="Cancel" color="negative" v-close-popup />
          <q-btn @click="addSession()" :disabled="!sessionItem.name || sessionItem.name == ''" Xflat label="Add" color="positive" v-close-popup />
        </q-card-actions>
      </q-card>
  </q-dialog>

  <!-- Fork Session -->
  <q-dialog v-model="showForkSession" Xpersistent>
    <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Fork Thought Flow: <span style="font-size: 1rem; font-weight: 400;">{{ sessionStore.session.name }}</span></div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="sessionItem.name" label="Thought Flow Name" filled clearable class="q-mb-md"/>
          <q-input v-model="sessionItem.description" label="Thought Flow Description" type="textarea" autogrow filled clearable />
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-icon name="warning" color="warning" size="sm" /> Make sure you save your current thought flow before forking!
        </q-card-section>
        <q-separator inset/>
        <q-card-actions align="right" class="text-primary">
          <q-btn Xflat label="Cancel" color="negative" v-close-popup />
          <q-btn @click="forkSession()" :disabled="!sessionItem.name || sessionItem.name == ''" Xflat label="Fork" color="positive" v-close-popup />
        </q-card-actions>
      </q-card>
  </q-dialog>

  <!-- Profile Dialog -->
    <profile-dlg v-model="showProfileDlg" />  
  </div>
</template>

<script setup>
  import { ref, onMounted, onBeforeMount, defineAsyncComponent } from 'vue'
  import { useQuasar } from 'quasar'
  import { useStore } from 'src/stores/main-store';
  import { useUserStore } from 'src/stores/user-store';
  import { useSessionStore } from 'src/stores/session-store';
  import { useSearchStore } from 'src/stores/search-store';
  import { useCategoryStore } from 'src/stores/category-store';
  import TooltipBtn from 'src/components/TooltipBtn.vue'
  import Tooltip from 'src/components/Tooltip.vue'
  import MenuItem from 'src/components/MenuItem.vue'
  import { useRouter } from 'vue-router';
  import { inject, computed } from 'vue'
  import useNotify from 'src/composables/useNotify';
  import { useTheme } from 'src/composables/useTheme';
  import SelectedCategories from 'src/components/SelectedCategories.vue'

  import { getActivePinia } from 'pinia';

    const { theme, switchTheme } = useTheme();

  const notesEditor = defineAsyncComponent(() => import('src/components/NotesEditor.vue'))
  const report = defineAsyncComponent(() => import('src/components/Report.vue'))
  const docTree = defineAsyncComponent(() => import('src/components/DocTree.vue'))
  const profileDlg = defineAsyncComponent(() => import('src/components/ProfileDlg.vue'))

  const store = useStore()
  const userStore = useUserStore()
  const sessionStore = useSessionStore()
  const searchStore = useSearchStore()
  const categoryStore = useCategoryStore();

  const { notify } = useNotify()

  const router = useRouter();
  
  const leftDrawerOpen = ref(false)

  const $q = useQuasar()
  // const bus = inject('bus') // EventBus
  

  // $q.dark.toggle() // toggle dark mode
  // $q.dark.set(true) // set dark mode

  const knowledgebases = ref([]);

  const selectedKnowledgebase = ref(null)

  const showNotes = ref(false)
  const showReport = ref(false)
  const showDocTree = ref(false)
  const loadingDocTreeData = ref(false)
  const showEditSession = ref(false)
  const showAddSession = ref(false)
  const showForkSession = ref(false)
  const showProfileDlg = ref(false)
  const sessionItem = ref({ name: '', description: '' })
  const activeSessionItem = computed(() => sessionStore.sessionList.find(session => session.id == sessionStore.session.id))
  
  onBeforeMount(async () => {
  console.log("*** MainLayout.vue - onBeforeMount ***")
});

onMounted(async () => {
  const user = await userStore.getUser();
  knowledgebases.value = user.kb_list;
  selectedKnowledgebase.value = knowledgebases.value.find(kb => kb.kb_name == user.kb_name);
})

function toggleTheme() {
  let newTheme = null
  if ($q.dark.isActive) {
    newTheme = 'light-theme'
  } 
  else {
    newTheme = 'dark-theme'
  }
  switchTheme(newTheme)
}

function reloadSite() {
  window.location.replace('/');
  // router.replace('/'); // go to category selector
}

const noCategoriesSelected = computed(() => {
  return sessionStore.session && sessionStore.session.categories && sessionStore.session.categories.length == 0
})

const noContextDocs = computed(() => {
  return sessionStore.session && sessionStore.session.contextDocs && sessionStore.session.contextDocs.length == 0
})

const noSemanticDocs = computed(() => {
  return searchStore.semanticDocs && searchStore.semanticDocs.length == 0
})

const noTextDocs = computed(() => {
  return searchStore.textDocs && searchStore.textDocs.length == 0
})

const noExplorer = computed(() => {
  return noContextDocs.value && noSemanticDocs.value && noTextDocs.value
})

async function onChangeKnowledgebase() {
  await sessionStore.loadSessionListForKbName(selectedKnowledgebase.value.kb_name);
  await categoryStore.initData(sessionStore.session.categories);
  userStore.setKnowledgebase(selectedKnowledgebase.value.kb_name);
  const pinia = getActivePinia();
  pinia.state.value.main = {}; // Clear the store state

  // clear search results
  searchStore.semanticDocs = [] // clear semantic chunks
  searchStore.textDocs = [] // clear text chunks
  searchStore.semanticSearchQuery = '' // clear semantic search query
  searchStore.textSearchQuery = '' // clear text search query

  setTimeout(() => {
    router.replace('/'); // switch to category selector
  }, 100);   
}

function loadSession (sessionId) {
  if (sessionStore.session.id == sessionId) {
    return;
  }
  $q.dialog({
        title: 'Do you want to leave this Thought Flow?',
        message: 'You may have unsaved changes!',
        cancel: true,
        // persistent: true,
        ok: {
          color: 'positive'
        },
        cancel: {
          color: 'negative'
        }
      }).onOk(async () => {
        const isError = await sessionStore.loadSession(sessionId) // load requested session
        if (isError) {
          return;
        }
        searchStore.semanticDocs = [] // clear semantic chunks
        searchStore.textDocs = [] // clear text chunks
        searchStore.semanticSearchQuery = '' // clear semantic search query
        searchStore.textSearchQuery = '' // clear text search query

        // bus.emit('session-loaded');
        // router.replace('/context-builder');
        setTimeout(() => {
          router.replace('/'); // switch to category selector
        }, 100);        
      })
} 

function showAddSessionDialog() {
  // clear session item
  sessionItem.value.name = ''; 
  sessionItem.value.description = ''; 
  // show add session dialog
  showAddSession.value = true
}

function showForkSessionDialog() {
  // clear session item
  sessionItem.value.name = ''; 
  sessionItem.value.description = ''; 
  // show fork session dialog
  showForkSession.value = true
}

function showEditSessionDialog() {
  // save active session item
  sessionItem.value.name = activeSessionItem.value.name;
  sessionItem.value.description = activeSessionItem.value.description; 
  // show edit session dialog
  showEditSession.value = true
}


function cancelEditSession() {
  // restore active session item
  activeSessionItem.value.name = sessionItem.value.name
  activeSessionItem.value.description = sessionItem.value.description
}

async function addSession() {
  await sessionStore.addSession({ name: sessionItem.value.name, description: sessionItem.value.description })
  // router.replace('/context-builder');
  setTimeout(() => {
    router.replace('/'); // switch to category selector
  }, 100);
}

async function forkSession() {
  await sessionStore.forkSession(sessionStore.session.id, { name: sessionItem.value.name, description: sessionItem.value.description })
  // router.replace('/context-builder');
  setTimeout(() => {
    router.replace('/'); // switch to category selector
  }, 100);
}


async function removeSession(sessionId) {
  $q.dialog({
        title: 'Do you want to remove this Thought Flow?',
        message: 'Removing this Thought Flow will delete all its data!',
        cancel: true,
        // persistent: true,
        ok: {
          color: 'positive'
        },
        cancel: {
          color: 'negative'
        }
      }).onOk(async () => {
        sessionStore.sessionList = sessionStore.sessionList.filter(session => session.id != sessionId)
        await sessionStore.removeSession(sessionId)
        // router.replace('/context-builder');
        setTimeout(() => {
          router.replace('/'); // switch to category selector
        }, 100);
      })
}

async function saveSession() {
  sessionStore.session.kb_name = selectedKnowledgebase.value.kb_name; // this line will be removed in the future
  const isError = await sessionStore.saveSession();
  if (isError) {
    return;
  }
  notify(`Thought Flow "${sessionStore.session.name}" saved!`, { icon: 'save' })
}

function toggleLeftDrawer () {
    leftDrawerOpen.value = !leftDrawerOpen.value
}

async function logout() {
  await userStore.logout();
  router.replace('/login');
}

async function openDocTree() {
  loadingDocTreeData.value = true;
  await store.loadDocTreeData();
  setTimeout(() => {
    loadingDocTreeData.value = false;
  }, 10000);
  showDocTree.value = !showDocTree.value;
}
</script>

<style scoped>
.page-flex-container {
  display: flex;
  flex-direction: column;
  height: 100vh; /* Make it fill the full viewport height */
  overflow: hidden; /* Prevent the page from scrolling */
}

/* Override Element Plus container width constraints */
:deep(.el-container),
:deep(.el-main),
:deep(.el-scrollbar) {
  max-width: none !important;
  width: 100% !important;
}

:deep(.el-tree) {  
  font-size: 1rem !important;
  opacity: .8 !important;
}
</style>