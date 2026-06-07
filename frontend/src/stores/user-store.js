import { defineStore } from 'pinia';
import { ref } from 'vue';
import * as API from 'src/api/api.js';

export const useUserStore = defineStore('user', () => {
    // STATE:
    // const data = ref(null);

    // ACTIONS:
    // Function to handle user login
    async function login(form) {
        const result = await API.login(form);
        return result != null; // Returns true if login is successful
    }

    // Function to handle user logout
    async function logout() {
        await API.logout();
    }

    // Function to fetch current user details
    async function getUserFromServer() {
        return await API.getUserFromServer();
    }

    // GETTERS:
    // Computed property to check if user is logged in
    function isLoggedIn() {
        return localStorage.getItem('_id_');
    };

    // get the user from localStorage
    function getUser() {
        let userData = null;
        const user = localStorage.getItem('user')
        if (user) {
            try {
                userData = JSON.parse(user);
            } 
            catch (error) {
                console.error('Error parsing user from localStorage:', error);
                // Clear corrupted data
                localStorage.removeItem('user');
            }
        } 
        return userData;
    }

    function setKnowledgebase(kb_name) {
        const user = getUser();
        user.kb_name = kb_name;
        localStorage.setItem('user', JSON.stringify(user));
    }

    async function changePassword(newPassword) {
        return await API.changePassword(newPassword);
    }

    // RETURN STATE, ACTIONS, AND GETTERS:
    return {
        login,
        logout,
        getUser,
        setKnowledgebase,
        isLoggedIn,
        changePassword
    };
});
