'use strict';

(() => {
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  const supported = typeof Element.prototype.animate === 'function';
  const running = new Set();
  const ease = 'cubic-bezier(.22, .7, .3, 1)';
  const enabled = () => supported && !preference.matches;

  function animate(element, frames, options = {}) {
    if (!element || !enabled()) return null;
    const animation = element.animate(frames, { duration: 200, easing: ease, ...options });
    running.add(animation);
    animation.finished.then(() => running.delete(animation), () => running.delete(animation));
    return animation;
  }

  // Settings changes take effect during an animation as well as on the next click.
  preference.addEventListener('change', () => {
    if (preference.matches) [...running].forEach(animation => animation.cancel());
  });
  window.addEventListener('beforeprint', () => [...running].forEach(animation => animation.cancel()));

  const card = document.querySelector('.guide-content');
  let oldHeight = 0;
  let cardAnimation = null;
  let panelAnimation = null;
  let stepRevision = 0;

  document.addEventListener('voidgram:beforestepchange', () => {
    oldHeight = card.getBoundingClientRect().height;
    stepRevision++;
    cardAnimation?.cancel();
    panelAnimation?.cancel();
    card.classList.remove('is-changing');
  });
  document.addEventListener('voidgram:stepchange', event => {
    const revision = stepRevision;
    const panel = document.querySelector(`[data-panel="${event.detail.to}"]`);
    const height = card.getBoundingClientRect().height;
    panelAnimation = animate(panel, [
      { opacity: 0, transform: `translateX(${event.detail.to > event.detail.from ? 10 : -10}px)` },
      { opacity: 1, transform: 'translateX(0)' },
    ], { duration: 190 });
    if (oldHeight && Math.abs(height - oldHeight) > 1) {
      cardAnimation = animate(card, [{ height: `${oldHeight}px` }, { height: `${height}px` }], { duration: 220 });
      if (cardAnimation) {
        card.classList.add('is-changing');
        const settle = () => {
          if (revision === stepRevision) card.classList.remove('is-changing');
        };
        cardAnimation.finished.then(settle, settle);
      }
    }
    placeThumb(false);
  });
  // A late screenshot or viewport resize must never leave content clipped.
  function releaseCardHeight() {
    cardAnimation?.cancel();
    card.classList.remove('is-changing');
  }
  card.addEventListener('load', releaseCardHeight, true);
  window.addEventListener('resize', releaseCardHeight);

  const picker = document.querySelector('.os-picker');
  const thumb = document.createElement('span');
  thumb.className = 'os-thumb';
  thumb.setAttribute('aria-hidden', 'true');
  picker.prepend(thumb);
  function placeThumb(move) {
    const button = picker.querySelector('[aria-pressed="true"]');
    if (!button || !button.offsetWidth) return;
    picker.classList.toggle('is-sliding', move && enabled());
    thumb.style.width = `${button.offsetWidth}px`;
    thumb.style.transform = `translateX(${button.offsetLeft}px)`;
    picker.classList.add('has-thumb');
  }
  document.addEventListener('voidgram:oschange', () => placeThumb(true));
  if (typeof ResizeObserver === 'function') new ResizeObserver(() => placeThumb(false)).observe(picker);
  else window.addEventListener('resize', () => placeThumb(false));
  placeThumb(false);

  const progress = document.getElementById('progress-bar');
  const track = document.createElement('div');
  const fill = document.createElement('span');
  track.className = 'progress-track';
  fill.className = 'progress-fill';
  track.setAttribute('aria-hidden', 'true');
  track.append(fill);
  progress.after(track);
  progress.classList.add('motion-native-progress');
  fill.style.transform = `scaleX(${progress.value / progress.max})`;
  let previousValue = progress.value;
  document.addEventListener('voidgram:progresschange', () => {
    fill.style.transform = `scaleX(${progress.value / progress.max})`;
    if (progress.value > previousValue) {
      animate(document.querySelector('.complete-checkbox'), [
        { transform: 'scale(.85)' }, { transform: 'scale(1)' },
      ], { duration: 160 });
    }
    previousValue = progress.value;
  });

  // Native details stays open while height animates; only the latest click may
  // commit the final state. Rapid reversals start at the currently drawn height.
  document.querySelectorAll('.faq-list details').forEach(details => {
    const summary = details.querySelector('summary');
    let active = null;
    let expanded = details.open;
    let revision = 0;
    summary.addEventListener('click', event => {
      if (!enabled()) return;
      event.preventDefault();
      const next = !(active ? expanded : details.open);
      const height = details.getBoundingClientRect().height;
      const thisRevision = ++revision;
      active?.cancel();
      expanded = next;
      details.open = true;
      details.classList.add('is-animating');
      summary.setAttribute('aria-expanded', String(next));
      details.dataset.expanded = String(next);
      const borders = getComputedStyle(details);
      const target = next ? details.offsetHeight : summary.offsetHeight
        + parseFloat(borders.borderTopWidth || 0) + parseFloat(borders.borderBottomWidth || 0);
      active = animate(details, [{ height: `${height}px` }, { height: `${target}px` }], { duration: next ? 230 : 180 });
      const settle = () => {
        if (revision !== thisRevision) return;
        details.open = expanded;
        details.classList.remove('is-animating');
        delete details.dataset.expanded;
        summary.removeAttribute('aria-expanded');
        active = null;
      };
      if (active) active.finished.then(settle, settle);
      else settle();
    });
  });

})();
