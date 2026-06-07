import { useQuasar, QSpinnerAudio } from 'quasar';

export default function useNotify() {
  const $q = useQuasar();

  function notify(message, options = {}) {
    const defaultOptions = {
        message: message,
        color: $q.dark.isActive? 'grey-9' : 'grey-4',
        icon: 'info',
        iconColor: 'info',
        textColor: 'info',
        color: 'grey-9',
        timeout: 2500,
        position: 'bottom-right',
        };
    Object.assign(defaultOptions, options); // merge options
    const dismiss = $q.notify(defaultOptions);
    return dismiss;
  }

  function notifyProgress(message, timeout = 0) {
    const options = {
      spinner: QSpinnerAudio,
      message: message,
      position: 'top-right',
      timeout: timeout,
      iconColor: 'info',
      textColor: 'info',
      color: 'grey-10'
    };
    
    return $q.notify(options);
  }

  return { notify, notifyProgress };
}