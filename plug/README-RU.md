# Плагины AyuGram iOS

`.iosplug` включает встроенные iOS-функции; Python/Android-код не запускается.
Для пакетов `ayu-iosplug-2`, Pill Labels и Mini Avatar нужна IPA с этим обновлением движка.
Первые пять встроенных карточек v1 совместимы с прежней IPA, содержащей соответствующий плагин.
Импорт: Плагины → + → файл .iosplug → подтвердить установку. Проверка на iPhone ещё не выполнена.

Ни один пакет не обещает полный паритет с Android. Ограничения перечислены ниже.

## acd.plugin
Файл: `acd.iosplug`. База: native iosplug v1.
- Нужна обложка в previewRepresentations аудио; извлечение произвольной встроенной обложки из файла не перенесено.
- Сохранение требует разрешения Фото.

## bubble_pop.plugin
Не перенесён: Игра рисует Android overlay с разрешением поверх других приложений. В iOS портируемый вариант возможен внутри клиента; поведение поверх чужих приложений не воспроизводится обычной IPA.
- Нужна точка входа: In-app overlay renderer + gestures + lifecycle cleanup

## camera_flip.plugin
Файл: `camera_flip.iosplug`. База: iosplug engine 2.
- Native adapter for the round-video camera only. It uses the existing camera switch path, including torch, screen brightness and transition checks.
- One finger: vertical swipe over 60 points or double tap within 350 ms; 800 ms cooldown. Pinch and controls are excluded.
- Configure gesture and haptic feedback on this plugin page. Android reflection is replaced with a native bridge; source Python and Java are not executed.

## chat_colors.plugin
Файл: `chat_colors.iosplug`. База: iosplug engine 2.
- Native per-account chat-list colors. Configure colors, brightness and reset in this plugin page; choose a chat from the list or profile menu.
- Selected rows retain native selection. Message-search rows, loading placeholders, sponsored entries, community cards and archive group references are excluded. Up to 1024 colored chats per account.
- Personal colors and preferences stay in account settings; exported manifests contain plugin functionality. Python, Java reflection and Android drawing calls are not executed.

## custom_fab.plugin
Не перенесён: Меняет/прячет Android floating action button и назначает долгое нажатие. Нужен эквивалент в навигации iOS.
- Нужна точка входа: Compose button customization + long-press action routing

## del_my_msgs.plugin
Файл: `del_my_msgs.iosplug`. База: native iosplug v1.
- До 10 000 результатов поиска; учитываются тема и ограничения удаления Telegram.
- Счётчик означает обработанные ID; успешность каждого удаления отдельно не подтверждается.

## delete_gifts.plugin
Не перенесён: Заменяет сериализацию Telegram gift request и меню подарка. Нужны проверка TL-метода/слоя API, операция удаления и подтверждение в iOS UI.
- Нужна точка входа: Gift API compatibility + confirmed gift action + UI hook

## direct_drop_send_fork.plugin
Не перенесён: Нужны drag/drop источники, обработка файлов/текста, редактор медиа и маршрутизация в отправку. В текущем API есть только подготовка текста.
- Нужна точка входа: UIDrag/UIDrop integration + media/file send bridge

## edit_mode.plugin
Не перенесён: Исследует Android View tree и сохраняет правила скрытия/перемещения. Нужны отдельные стабильные iOS точки кастомизации; Android view IDs на iOS отсутствуют.
- Нужна точка входа: Stable native UI element registry + editor + persistent layout rules

## fast_crop.plugin
Не перенесён: Основная реализация упакована в Android DEX и загружается InMemoryDexClassLoader. Нужны нативный кроп, жесты и копирование результата.
- Нужна точка входа: Media gallery crop/zoom hooks + image clipboard

## formatted_copy.plugin
Файл: `formatted_copy.iosplug`. База: iosplug engine 2.
- Requires engine API 9. Use Copy with details in the message/album menu. For multiple selection, long-press Share or use its accessibility action. Standard Copy is unchanged.
- Up to 100 ordinary cloud messages and 1 MB. Native copy protection is respected. Copies plain text and media markers, not media files or rich clipboard fragments.

## game_arcade.plugin
Файл: `game_arcade.iosplug`. База: iosplug engine 2.
- Games open in the existing full-screen web view. They require the game site to be reachable. The Android WebView implementation is replaced by the native iOS bridge.
- Uses the existing plugin settings and .2048, .flappy and .dino chat commands.

## group_mentions.plugin
Файл: `group_mentions.iosplug`. База: iosplug engine 2.
- Requires native engine API 8. Up to five groups of seven usernames; configure on the plugin page.
- Plain text and unformatted captions only. Broadcasts, secret chats, formatted text and scheduled messages are excluded. A 60-second cooldown applies per account/chat.

## hide_attach_buttons.plugin
Файл: `hide_attach_buttons.iosplug`. База: native iosplug v1.
- Галерея и текущий активный раздел остаются доступными.

## lyu_mic_switch.plugin
Не перенесён: Перехватывает Android AudioRecord и обрабатывает PCM. Нужны интеграция iOS аудиосессии, выбор доступного микрофона и обработка записи. Бесшовность переключения требует проверки на устройстве.
- Нужна точка входа: Audio input selection + recording PCM/DSP hooks

## mini_avatar.plugin
Файл: `mini_avatar.iosplug`. База: iosplug batch engine 2.
- Размер применяется при следующем открытии чата.
- Горизонтальное смещение пузырьков, отдельные Android-геометрии и произвольные размеры не перенесены.
- Требуется обновлённая IPA из этой партии.

## msg_stats.plugin
Не перенесён: Нужны наблюдение за отправками, локальные счётчики, импорт истории и экран графиков. Текстовый хук счётчики не хранит.
- Нужна точка входа: Outgoing event observer + stats storage + charts/history loader

## ok_playlists.plugin
Не перенесён: Меняет MediaController: позицию воспроизведения и состав плейлиста по теме форума. Таких хуков в текущем API нет.
- Нужна точка входа: Player seek/progress + topic-scoped playlist hooks

## petpet.plugin
Файл: `petpet.iosplug`. База: iosplug engine 2.
- Requires native engine API 8. Open from the chat Plugins menu or .petpet / .петпет. Select an image in Files or use the current chat avatar. Maximum input 8 MB / 64 MP.
- This is a partial native adapter: URL/@username arguments, reply media, TGS/video stickers and original profile/message menus are not implemented. Send explicitly after previewing.

## pill_labels.plugin
Файл: `pill_labels.iosplug`. База: iosplug batch engine 2.
- Только стандартные подписи полей профиля; Android-журнал отладки не перенесён.
- Требуется обновлённая IPA из этой партии.

## player_resume.plugin
Не перенесён: Плеерная реализация находится в Android DEX. Нужны сохранение/восстановление воспроизведения и компактная кнопка плеера.
- Нужна точка входа: Player state + native mini-player UI

## plugins_menu.plugin
Не перенесён: Плагин называется Title Actions: назначает действия на заголовок exteraGram. Готовая вкладка Plugins не реализует переназначаемые действия заголовка.
- Нужна точка входа: Chat-list title gesture hook + action dispatcher/settings

## reactions_total.plugin
Файл: `reactions_total.iosplug`. База: iosplug engine 2.
- Requires native engine API 8. Uses the native timestamp line instead of modifying author metadata. Saved Messages tags and non-cloud messages are excluded.
- Changes appear on the next cell update or after reopening the chat. Android debug bulletins are not used.

## search_plus.plugin
Файл: `search_plus.iosplug`. База: iosplug engine 2.
- Up to six phrases separated by | and 40 results per phrase. Current chat/topic only; no automatic pagination.
- Advanced filters require the API 9 base app. Supports author @username or a known user ID, local calendar dates and a media-type picker. Earlier base apps retain basic multi-term search.
- An unknown author or missing access hash reports an error instead of dropping the filter. Phone lookup, arbitrary ID lookup and global search injection are not implemented.

## service_cleaner.plugin
Файл: `service_cleaner.iosplug`. База: native iosplug v1.
- Используются только сообщения, уже загруженные на устройство; полный серверный обход не реализован.

## smart_auto_archiver.plugin
Файл: `smart_auto_archiver.iosplug`. База: native iosplug v1.
- Проверяются до 1000 чатов; автоматический запуск не чаще раза в сутки при работающем приложении.
- Закреплённые, непрочитанные, чаты с упоминаниями и Избранное исключены.
- Непрерывный фоновый таймер Android не перенесён.

## smart_bookmark.plugin
Не перенесён: Нужны локальное хранилище заметок/задач/тегов, меню сообщений/чатов, поиск и резервное копирование. Текущие manifest actions таких сущностей не имеют.
- Нужна точка входа: Bookmark/note database + menus + task/search/backup UI

## story_scheduler.plugin
Не перенесён: Нужны захват черновика истории, очередь медиа, восстановление после перезапуска, повторы и Story upload API. Фоновый таймер iOS не гарантирует публикацию в заданную секунду.
- Нужна точка входа: Story draft/upload bridge + durable queue + scheduling policy

## unlim_accounts.plugin
Файл: `unlim_accounts.iosplug`. База: iosplug engine 2.
- Changes the local add-account limit in the current account while enabled. Telegram server limits and authentication requirements still apply.
- The embedded Android DEX/native payload is not loaded; the existing native iOS account-limit bridge is used.
