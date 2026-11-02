// ==AyuPlugin==
// @id bookmarks
// @name Закладки
// @author AyuGram-IOS
// @version 1.0.0
// @description Пункт «В закладки» в меню сообщения. Закладки с тегами открываются в Настройки → AyuGram → Инструменты → Закладки.
// @permissions menu, ui, messages
// ==/AyuPlugin==

(function () {
    'use strict';
    ayu.settings.declare([
        { key: 'tag', type: 'text', title: 'Тег по умолчанию', subtitle: 'Например «прочитать позже»; можно оставить пустым', default: '' }
    ]);
    ayu.ui.menu.add({ id: 'bookmark', title: 'В закладки', icon: 'bookmark.fill' });
    ayu.on('menuAction', function (p) {
        if (!p || p.itemId !== 'bookmark') return;
        var tag = String(ayu.settings.get('tag') || '').replace(/^[#\s]+|\s+$/g, '').toLowerCase().slice(0, 32);
        ayu.messages.bookmarks.add({ peerId: p.peerId, messageId: Number(p.messageId), text: String(p.text || '').slice(0, 500), tag: tag });
        ayu.toast(tag ? 'В закладках · #' + tag : 'В закладках');
    });
})();
