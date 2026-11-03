'use strict';

// Update this block when a new IPA is published. All other download links use latest.
window.AYU_SITE = Object.freeze({
  release: {
    label: '27.0.2 · 149 МБ',
    ipa: 'https://github.com/dsn2fvhmn4-lgtm/AyuGramm-IOS/releases/download/build-88-branch/AyuGramm-IOS-27.0.2.ipa',
    checkedOn: '2026-11-01',
  },
  // A step accepts one screenshot or an array with labels for the image picker.
  // Online images keep their source link; the guide falls back to a diagram offline.
  screenshots: {
    iloader: {
      windows: {
        src: 'assets/steps/01-iloader-windows.webp',
        width: 584, height: 81, layout: 'strip',
        alt: 'Завершённая загрузка iloader-windows-x64.exe в браузере',
        caption: 'Установщик скачан. Открой iloader-windows-x64.exe и заверши установку.',
      },
      macos: null,
      linux: null,
    },
    ipa: {
      src: 'assets/steps/02-download-ipa.webp',
      width: 629, height: 472,
      alt: 'Главная страница VoidGram с кнопкой «Скачать IPA»',
      caption: 'Нажми «Скачать IPA» на этой странице и дождись завершения загрузки.',
    },
    connection: {
      src: 'https://cdsassets.apple.com/live/7WUAS350/images/ios/ios-16-iphone-14-pro-trust-this-computer-prompt.png',
      layout: 'phone',
      alt: 'Запрос Trust This Computer? на iPhone с кнопками Trust и Don’t Trust',
      caption: 'Нажми Trust («Доверять») на iPhone. На снимке — iOS 16 с английским интерфейсом.',
      source: { label: 'Apple Support', url: 'https://support.apple.com/109054' },
    },
    account: {
      src: 'assets/steps/04-apple-account.webp',
      width: 945, height: 1028,
      alt: 'iLoader 2.4.1 после входа: блок Logged in as, почта скрыта, iPhone выбран',
      caption: 'После входа появится Logged in as. Почта на снимке скрыта.',
    },
    install: {
      src: 'assets/steps/05-select-ipa.webp',
      width: 742, height: 41, layout: 'strip',
      alt: 'Файл AyuGramm-IOS-27.0.2(1).ipa в папке загрузок',
      caption: 'После Import IPA выбери скачанный файл с расширением .ipa.',
    },
    launch: [
      {
        label: '1. Настройки',
        src: 'https://docs.expo.dev/static/images/ios-dev-mode/ios-16-developer-mode-1.webp',
        alt: 'Экраны настроек iOS: Privacy & Security и пункт Developer Mode',
        caption: 'Конфиденциальность и безопасность → Режим разработчика. Пример на iOS 16; оформление новых версий может отличаться.',
        source: { label: 'Expo Docs', url: 'https://docs.expo.dev/guides/ios-developer-mode/' },
      },
      {
        label: '2. Перезапуск',
        src: 'https://docs.expo.dev/static/images/ios-dev-mode/ios-16-developer-mode-2.webp',
        alt: 'Переключатель Developer Mode и запрос перезапуска iPhone',
        caption: 'Включи Developer Mode и нажми Restart («Перезагрузить»).',
        source: { label: 'Expo Docs', url: 'https://docs.expo.dev/guides/ios-developer-mode/' },
      },
      {
        label: '3. Подтверждение',
        src: 'https://docs.expo.dev/static/images/ios-dev-mode/ios-16-developer-mode-3.webp',
        alt: 'Запрос Turn On Developer Mode? и экран ввода код-пароля iPhone',
        caption: 'После перезапуска разблокируй iPhone, нажми Turn On («Включить») и введи код-пароль устройства.',
        source: { label: 'Expo Docs', url: 'https://docs.expo.dev/guides/ios-developer-mode/' },
      },
    ],
  },
});
