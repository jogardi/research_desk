import { ref, onMounted } from 'vue';
import { useQuasar } from 'quasar';

export const useTheme = () => {
  const $q = useQuasar();
  const theme = ref('light');

  const setTheme = async (newTheme) => {
    theme.value = newTheme;
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', newTheme);

      // Switch CSS theme files
      const themeLink = document.getElementById('theme-link');
      if (themeLink) {
        themeLink.remove();
      }

      const link = document.createElement('link');
      link.id = 'theme-link';
      link.rel = 'stylesheet';
      link.href = newTheme === 'dark' ? '/assets/css/dark-theme.css' : '/assets/css/light-theme.css';
      document.head.appendChild(link);

      // Set the dark mode state using $q.dark.set()
      $q.dark.set(newTheme === 'dark');
    }
  };

  const switchTheme = () => {
    if (theme.value === 'light') {
      setTheme('dark');
    } else {
      setTheme('light');
    }
  };

  onMounted(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme) {
        setTheme(savedTheme);
      } else {
        setTheme('light');
      }
    }
  });

  return {
    theme,
    switchTheme,
  };
}