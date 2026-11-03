// ==AyuPlugin==
// @id describe-photo
// @name Описать фото
// @author VoidGram
// @version 1.0.0
// @description Пункт «Описать фото» в меню сообщения с фото: что на снимке и какой на нём текст. Распознаётся на устройстве, фото никуда не отправляется.
// @permissions menu, ui, messages.read
// ==/AyuPlugin==

(function () {
    'use strict';
    ayu.ui.menu.add({ id: 'describe-photo', title: 'Описать фото', icon: 'text.viewfinder', media: 'photo' });
    ayu.on('menuAction', function (p) {
        if (!p || p.itemId !== 'describe-photo') return;
        ayu.media.describePhoto(p.peerId, p.messageId).then(function (text) {
            ayu.ui.alert({ title: 'Описание', message: text || 'Ничего не распознано.', buttons: [{ id: 'ok', title: 'OK' }] });
        }).catch(function (e) { ayu.toast('Не удалось: ' + e.message); });
    });
})();
