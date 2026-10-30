// ==AyuPlugin==
// @id smart-quotes
// @name Smart quotes
// @author AyuGramm-IOS
// @version 1.0
// @description Replaces the outgoing-text handler: straight quotes become «ёлочки» or “curly” quotes, "--" becomes an em dash. Turns off the fast-share button as a feature-toggle example.
// ==/AyuPlugin==

const style = ayu.storage.get('style') || 'auto';

function curly(text, ctx) {
    const russian = style === 'ru' || (style === 'auto' && /[а-яё]/i.test(text));
    let open = true;
    return text
        .replace(/--/g, '—')
        .replace(/"/g, () => {
            const mark = russian ? (open ? '«' : '»') : (open ? '“' : '”');
            open = !open;
            return mark;
        });
}

// `replace` disables the native outgoing-text handler (JSON .plugin outgoing rules) while
// this plugin is on; use `before`/`after` to run alongside it instead.
ayu.hooks.replace(ayu.hooks.points.outgoingText, curly);

ayu.features.disable('fastShare');

ayu.on('chatOpen', ({ peerId }) => ayu.log('chat opened', peerId));
ayu.on('unload', () => ayu.log('smart quotes off'));
ayu.log('smart quotes ready, style =', style);
