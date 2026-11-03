// ==AyuPlugin==
// @id year-in-review
// @name Итоги года
// @author VoidGram
// @version 1.0.0
// @description Пункт «Итоги года» в меню сообщения: сколько вы переписывались в этом чате с 1 января, самые активные месяцы и дни.
// @permissions menu, messages.read
// ==/AyuPlugin==

(function () {
    'use strict';
    ayu.ui.menu.add({ id: 'year-in-review', title: 'Итоги года', icon: 'calendar.badge.clock' });
    ayu.on('menuAction', function (p) {
        if (!p || p.itemId !== 'year-in-review') return;
        ayu.tools.yearInReview(p.peerId).catch(function (e) { ayu.toast('Не удалось: ' + e.message); });
    });
})();
