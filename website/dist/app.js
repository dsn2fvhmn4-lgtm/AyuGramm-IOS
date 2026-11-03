'use strict';

(() => {
  const config = window.AYU_SITE || { screenshots: {} };
  const panels = [...document.querySelectorAll('[data-panel]')];
  const stepLinks = [...document.querySelectorAll('[data-step]')];
  const osButtons = [...document.querySelectorAll('[data-os]')];
  const completed = new Set();
  const storageKey = 'ayugram-install-guide-v1';
  const previous = document.getElementById('previous-step');
  const next = document.getElementById('next-step');
  const complete = document.getElementById('complete-step');
  const live = document.getElementById('live-status');
  const dialog = document.getElementById('screenshot-dialog');
  const osOptions = {
    windows: { title: 'Windows', format: '.exe', url: 'https://github.com/nab138/iloader/releases/latest/download/iloader-windows-x64.exe' },
    macos: { title: 'macOS', format: '.dmg', url: 'https://github.com/nab138/iloader/releases/latest/download/iloader-darwin-universal.dmg' },
    linux: { title: 'Linux', format: '.deb / .rpm / AppImage', url: 'https://github.com/nab138/iloader/releases/latest' },
  };
  let os = 'windows';
  let current = 1;

  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    if (Object.prototype.hasOwnProperty.call(osOptions, saved.os)) os = saved.os;
    if (Array.isArray(saved.completed)) saved.completed.forEach(value => {
      if (Number.isInteger(value) && value >= 1 && value <= panels.length) completed.add(value);
    });
  } catch { /* The guide remains usable if local storage is unavailable. */ }

  function save() {
    try { localStorage.setItem(storageKey, JSON.stringify({ os, completed: [...completed] })); } catch { /* Optional persistence. */ }
  }

  function updateProgress() {
    stepLinks.forEach(link => link.classList.toggle('is-complete', completed.has(Number(link.dataset.step))));
    document.getElementById('progress-label').textContent = `Пройдено ${completed.size} из ${panels.length}`;
    document.getElementById('progress-bar').value = completed.size;
    document.getElementById('reset-progress').hidden = completed.size === 0;
    complete.setAttribute('aria-pressed', String(completed.has(current)));
    document.getElementById('completion-message').hidden = completed.size !== panels.length;
  }

  function selectStep(step, { focus = false, scroll = false } = {}) {
    if (!Number.isInteger(step) || step < 1 || step > panels.length) return;
    current = step;
    panels.forEach(panel => { panel.hidden = Number(panel.dataset.panel) !== current; });
    stepLinks.forEach(link => {
      const active = Number(link.dataset.step) === current;
      link.classList.toggle('is-active', active);
      if (active) link.setAttribute('aria-current', 'step'); else link.removeAttribute('aria-current');
    });
    previous.disabled = current === 1;
    next.querySelector('span').textContent = current === panels.length ? 'Готово' : 'Дальше';
    next.querySelector('use').setAttribute('href', current === panels.length ? '#check' : '#arrow');
    updateProgress();
    if (focus) {
      document.getElementById(`title-${current}`).focus({ preventScroll: true });
      try { history.replaceState(null, '', `#step-${current}`); } catch { /* file:// previews can restrict history. */ }
    }
    if (scroll) {
      const target = matchMedia('(max-width: 650px)').matches ? document.querySelector('.guide-sidebar') : document.querySelector('.guide-content');
      target.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
    }
  }

  const originalCaptions = new Map();
  function showScreenshot(figure) {
    const kind = figure.dataset.screenshot;
    const configured = kind === 'iloader' ? config.screenshots?.iloader?.[os] : config.screenshots?.[kind];
    const entries = (Array.isArray(configured) ? configured : [configured]).filter(entry => entry?.src);
    const schema = figure.querySelector('.schematic');
    const badge = figure.querySelector('.scheme-label');
    const caption = figure.querySelector('figcaption');
    if (!originalCaptions.has(figure)) originalCaptions.set(figure, caption.textContent);
    figure.querySelector('.screenshot-stage')?.remove();
    figure.querySelector('.screenshot-picker')?.remove();
    figure.querySelector('.zoom-screenshot')?.remove();
    schema.hidden = false;
    badge.hidden = false;
    caption.textContent = originalCaptions.get(figure);
    if (!entries.length) return;

    const picker = document.createElement('div');
    picker.className = 'screenshot-picker';
    picker.setAttribute('role', 'group');
    picker.setAttribute('aria-label', 'Экраны этого шага');
    if (entries.length > 1) figure.insertBefore(picker, schema);

    function setCaption(value, text) {
      caption.textContent = text;
      if (!value.source?.url) return;
      const source = document.createElement('a');
      source.href = value.source.url;
      source.textContent = value.source.label || 'Инструкция';
      source.target = '_blank';
      source.rel = 'noopener noreferrer';
      caption.append(' Источник: ', source, '.');
    }

    function render(value, index) {
      figure.querySelector('.screenshot-stage')?.remove();
      figure.querySelector('.zoom-screenshot')?.remove();
      schema.hidden = false;
      badge.hidden = false;
      setCaption(value, originalCaptions.get(figure));
      [...picker.children].forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));

      const stage = document.createElement('div');
      stage.className = 'screenshot-stage';
      stage.hidden = true;
      if (value.layout === 'strip') {
        stage.tabIndex = 0;
        stage.setAttribute('role', 'region');
        stage.setAttribute('aria-label', 'Скриншот с горизонтальной прокруткой');
      }
      const img = document.createElement('img');
      img.className = 'screenshot-image';
      img.dataset.layout = value.layout || 'standard';
      img.alt = value.alt || originalCaptions.get(figure);
      // Load while the fallback is visible, including inside a hidden step panel.
      img.loading = 'eager';
      img.decoding = 'async';
      img.referrerPolicy = 'no-referrer';
      if (value.width && value.height) { img.width = value.width; img.height = value.height; }
      stage.append(img);
      const zoom = document.createElement('button');
      zoom.type = 'button';
      zoom.className = 'zoom-screenshot';
      zoom.textContent = 'Увеличить скриншот ↗';
      zoom.hidden = true;
      const open = () => {
        if (!img.complete || !img.naturalWidth) return;
        if (typeof dialog.showModal !== 'function') { window.open(img.src, '_blank', 'noopener'); return; }
        const target = dialog.querySelector('img');
        target.referrerPolicy = 'no-referrer';
        target.src = img.src;
        target.alt = img.alt;
        target.dataset.layout = img.dataset.layout;
        dialog.querySelector('p').textContent = value.caption || img.alt;
        dialog.showModal();
        const viewport = dialog.querySelector('.dialog-image-stage');
        viewport.scrollLeft = 0;
        viewport.scrollTop = 0;
      };
      img.addEventListener('load', () => {
        if (!img.isConnected) return;
        schema.hidden = true;
        badge.hidden = true;
        stage.hidden = false;
        zoom.hidden = false;
        setCaption(value, value.caption || originalCaptions.get(figure));
      });
      img.addEventListener('error', () => {
        if (!img.isConnected) return;
        stage.remove();
        zoom.remove();
        schema.hidden = false;
        badge.hidden = false;
        setCaption(value, `Скриншот не загрузился. ${originalCaptions.get(figure)}`);
      });
      img.addEventListener('click', open);
      zoom.addEventListener('click', open);
      figure.insertBefore(stage, caption);
      figure.insertBefore(zoom, caption);
      img.src = value.src;
    }

    if (entries.length > 1) entries.forEach((entry, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = entry.label || `Экран ${index + 1}`;
      button.addEventListener('click', () => render(entry, index));
      picker.append(button);
    });
    render(entries[0], 0);
  }

  function selectOS(value) {
    if (!Object.prototype.hasOwnProperty.call(osOptions, value)) return;
    os = value;
    osButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.os === os)));
    document.querySelectorAll('[data-os-panel]').forEach(panel => { panel.hidden = panel.dataset.osPanel !== os; });
    const option = osOptions[os];
    const link = document.getElementById('iloader-download');
    link.href = option.url;
    link.querySelector('span').textContent = os === 'linux' ? 'Выбрать сборку Linux' : `Скачать для ${option.title}`;
    document.getElementById('illustration-platform').textContent = `${option.title} · ${option.format}`;
    showScreenshot(document.querySelector('[data-screenshot="iloader"]'));
    save();
  }

  function followStepHash({ scroll = false } = {}) {
    const match = location.hash.match(/^#step-([1-6])$/);
    if (match) selectStep(Number(match[1]), { scroll });
  }

  document.documentElement.classList.add('js-ready');
  document.querySelector('.step-controls').hidden = false;
  if (config.release?.ipa) document.querySelectorAll('[data-ipa-link]').forEach(link => { link.href = config.release.ipa; });
  if (config.release?.label) document.querySelectorAll('[data-release-label]').forEach(label => { label.textContent = config.release.label; });
  document.querySelectorAll('.step-visual:not([data-screenshot="iloader"])').forEach(showScreenshot);
  selectOS(os);
  selectStep(1);
  followStepHash();

  document.querySelectorAll('a[href^="#step-"]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    const step = Number(link.getAttribute('href').slice(6));
    selectStep(step, { focus: true, scroll: true });
  }));
  window.addEventListener('hashchange', () => followStepHash({ scroll: true }));
  osButtons.forEach(button => button.addEventListener('click', () => selectOS(button.dataset.os)));
  previous.addEventListener('click', () => selectStep(current - 1, { focus: true, scroll: true }));
  next.addEventListener('click', () => {
    if (current < panels.length) selectStep(current + 1, { focus: true, scroll: true });
    else {
      completed.add(current);
      save();
      updateProgress();
      live.textContent = completed.size === panels.length ? 'Все шаги отмечены. VoidGram готов к запуску.' : 'Последний шаг отмечен. Можно вернуться к остальным шагам.';
    }
  });
  complete.addEventListener('click', () => {
    if (completed.has(current)) completed.delete(current); else completed.add(current);
    save(); updateProgress();
    live.textContent = `Шаг ${current} ${completed.has(current) ? 'отмечен как пройденный' : 'снова не отмечен'}. Пройдено ${completed.size} из ${panels.length}.`;
  });
  document.getElementById('reset-progress').addEventListener('click', () => {
    completed.clear(); save(); updateProgress(); live.textContent = 'Отметки шагов сброшены.';
  });
  dialog.querySelector('button').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
})();
