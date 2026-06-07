
const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/CategorySelector.vue') },
      { path: 'context-builder', component: () => import('pages/ContextBuilder.vue') },
      { path: 'chat', component: () => import('pages/Chat.vue') },
      { path: 'explorer', component: () => import('pages/Explorer.vue') },
      { path: 'builder', component: () => import('pages/Builder.vue') },
      { path: 'guide', component: () => import('pages/UserGuide.vue') },
    ]
  },
  {
    path: '/login',
    component: () => import('layouts/LoginLayout.vue'), // Use the new layout for the login page
    children: [
      { path: '', component: () => import('pages/Login.vue') } // Adjust the path if necessary
    ]
  },

  // { path: '/login', component: () => import('pages/login.vue') },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
