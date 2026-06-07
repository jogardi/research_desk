import { nextTick } from 'vue'
import renderMathInElement from 'katex/contrib/auto-render/auto-render';
import 'katex/dist/katex.min.css';

const defaultOptions = {
  delimiters: [
    { left: '$$', right: '$$', display: true },
    { left: '\\[', right: '\\]', display: true },
    { left: '$', right: '$', display: false },
    { left: '\\(', right: '\\)', display: false }
  ],
  throwOnError: false,
  strict: 'ignore'
};

function renderElement(el, options) {
  try {
    renderMathInElement(el, { ...defaultOptions, ...(options || {}) });
  } catch (err) {
    // no-op
  }
}

export default ({ app }) => {
  app.directive('katex', {
    async mounted(el, binding) {
      await nextTick();
      renderElement(el, binding?.value);
      el.__katexLastContent = el.innerHTML;
    },
    async updated(el, binding) {
      await nextTick();
      const content = el.innerHTML;
      if (el.__katexLastContent !== content || binding.oldValue !== binding.value) {
        renderElement(el, binding?.value);
        el.__katexLastContent = el.innerHTML;
      }
    }
  });
};