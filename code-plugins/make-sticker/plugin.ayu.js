// ==AyuPlugin==
// @id make-sticker
// @name Сделать стикер
// @author VoidGram
// @version 1.0.0
// @description Пункт «Сделать стикер» в меню сообщения с фото: вырезает объект с фото и отправляет его стикером в открытый чат. Нужна iOS 17.
// @permissions menu, messages
// ==/AyuPlugin==

(function () {
    'use strict';
    ayu.ui.menu.add({ id: 'make-sticker', title: 'Сделать стикер', icon: 'scissors', media: 'photo' });
    ayu.on('menuAction', function (p) {
        if (!p || p.itemId !== 'make-sticker') return;
        ayu.media.cutOutSticker(p.peerId, p.messageId).catch(function (e) { ayu.toast('Стикер не получился: ' + e.message); });
    });
})();
