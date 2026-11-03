// ==AyuPlugin==
// @id chat-statistics
// @name Статистика чата (вся история)
// @author VoidGram
// @version 1.0.0
// @description Пункт «Статистика чата» в меню сообщения: авторы, слова, часы и дни активности по всем сообщениям чата, сохранённым на устройстве.
// @permissions menu, messages.read
// ==/AyuPlugin==

(function () {
    'use strict';
    ayu.ui.menu.add({ id: 'chat-statistics', title: 'Статистика чата', icon: 'chart.bar.fill' });
    ayu.on('menuAction', function (p) {
        if (!p || p.itemId !== 'chat-statistics') return;
        ayu.tools.chatStats(p.peerId).catch(function (e) { ayu.toast('Не удалось: ' + e.message); });
    });
})();
