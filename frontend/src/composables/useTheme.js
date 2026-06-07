import { ref, onMounted } from 'vue';
import { useQuasar } from 'quasar';

export const useTheme = () => {
  const $q = useQuasar();
  const theme = ref('light-theme');
  const isProd = process.env.NODE_ENV === 'production';

  console.log('isProd', isProd);

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
      // link.href = `/src/css/${newTheme}.css`;
      link.href = isProd ? `/css/${newTheme}.css` : `/src/css/${newTheme}.css`;
      document.head.appendChild(link);

      // Set the dark mode state using $q.dark.set()
      $q.dark.set(newTheme.includes('dark'));
      // For element-plus:
      const htmlElement = document.documentElement
      htmlElement.classList.remove(newTheme.includes('dark') ? 'light' : 'dark')
      htmlElement.classList.add(newTheme)
    }
  };

  const switchTheme = (newTheme) => {
    setTheme(newTheme);
  };

  onMounted(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme) {
        setTheme(savedTheme);
      } else {
        // setTheme('light-theme');
        setTheme('dark-theme');
      }
    }
  });

  return {
    theme,
    switchTheme,
  };
};
