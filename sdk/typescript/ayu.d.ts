// Type declarations for AyuGram for iOS JavaScript and TypeScript plugins (27.5).
// Plugins run in JavaScriptCore with `ayu` as a global. Each API marked with a permission needs
// `// @permissions name` in the plugin header; network access also needs `// @connect host`.

declare namespace Ayu {
  type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

  interface HookContext {
    peerId?: string;
    messageId?: string;
    [key: string]: Json | undefined;
  }

  /** Return a string to replace the value, or undefined/null to keep it. */
  type TextHook = (value: string, ctx: HookContext) => string | null | undefined | void;

  interface Hooks {
    before(point: string, fn: TextHook): void;
    after(point: string, fn: TextHook): void;
    replace(point: string, fn: TextHook): void;
    readonly points: {
      readonly outgoingText: "message.outgoing.text";
      readonly lyricsText: "lyrics.text";
      /** Rewrite a URL before it opens (permission `links`). */
      readonly linkOpen: "link.open";
      /** Decorate how a message's text is shown; stored data never changes. */
      readonly messageRender: "message.render";
      /** Change or drop (return "") a local notification's text (permission `notifications`). */
      readonly notificationBeforeShow: "notification.beforeShow";
    };
  }

  interface AlertButton { id: string; title: string; style?: "default" | "destructive" }

  interface ScreenRow {
    id: string;
    type: "text" | "button" | "toggle" | "link" | "value";
    title: string;
    subtitle?: string;
    value?: boolean | string;
    url?: string;
  }

  interface ScreenSection { title?: string; footer?: string; rows: ScreenRow[] }

  interface Ui {
    alert(options: { title: string; message?: string; buttons?: AlertButton[] }, fn?: (choice: string | null) => void): void;
    sheet(options: { title: string; message?: string; items: { id: string; title: string }[] }, fn?: (choice: string | null) => void): void;
    menu: { add(item: { id: string; title: string; icon?: string }): void; remove(id: string): void };
    profile: {
      addBlock(options: { id: string; peerId?: string; title?: string; text: string }): void;
      removeBlock(id: string): void;
      addButton(options: { id: string; peerId?: string; title: string }): void;
      removeButton(id: string): void;
    };
    overlay: {
      create(options: { id: string; effect: "snow" | "leaves" | "rain" | "stars" | "confetti"; amount?: number; speed?: number; color?: string; fps?: number }): void;
      update(id: string, options: { effect?: string; amount?: number; speed?: number; color?: string; fps?: number }): void;
      addText(options: { id: string; text: string; anchor?: "topLeft" | "topRight" | "bottomLeft" | "bottomRight" | "center"; color?: string; size?: number }): void;
      /** A live clock over the app (format like "HH:mm:ss"). */
      addClock(options: { id: string; format?: string; anchor?: string; color?: string; size?: number }): void;
      /** A live FPS counter; remove it with overlay.remove(id). */
      showFPS(options: { id: string; anchor?: string; color?: string; size?: number }): void;
      remove(id: string): void;
    };
    /** A bottom-bar tab showing a plugin screen (permission `screens`; two plugin tabs at most). */
    tabs: { add(options: { id: string; title: string; icon?: string; screen: Json }): void; remove(id: string): void };
    /** A panel sliding in from the left with a plugin screen (permission `screens`). */
    sidebar: { show(screen: Json): void };
    /** A search screen: queries go to onQuery, answer with setResults(id, rows). Taps send `searchResult` { id, rowId }. */
    searchBar: {
      show(options: { id?: string; title?: string; placeholder?: string }, onQuery?: (query: string) => void): void;
      setResults(id: string, rows: { id: string; title: string; subtitle?: string }[]): void;
    };
    /** An emoji in the corner of a chat's avatar in the chat list (permission `badges`). */
    avatar: { decorate(peerId: string, emoji: string): void; clear(peerId: string): void };
    /** A colour or two-colour gradient over the chat wallpaper, under the messages (permission `overlay`). */
    chatBackground: { set(options: { colors: string[]; alpha?: number }): void; reset(): void };
    /** A button over the whole app; the callback runs on tap (permission `overlay`). */
    floatingButton: { add(options: { id: string; icon?: string; title?: string; anchor?: "bottomRight" | "bottomLeft" | "topRight" | "topLeft"; color?: string }, onTap?: () => void): boolean; remove(id: string): void };
    progress: { show(options: { id: string; title?: string; value: number; anchor?: string }): void; hide(id: string): void };
    animation: { play(name?: "confetti" | "snow" | "stars" | "leaves" | "rain", seconds?: number): void };
    font: {
      /** `weight` and `style` apply to regular text in the whole app. */
      set(options: { element?: "messages" | "lists"; size?: number; weight?: "light" | "regular" | "medium" | "semibold" | "bold"; style?: "normal" | "rounded" | "monospaced" | "italic" }): void;
      reset(element: "messages" | "lists"): void;
    };
    badge: { add(options: { peerId: string; badge: { text: string } }): void; remove(options: { peerId: string }): void };
    gifts: { catalog: { list(fn?: (gifts: Gift[]) => void): Promise<Gift[]> } };
  }

  interface Gift { giftId: string; title: string; stars: number; fileId: string; limited: boolean; soldOut: boolean; remains?: number; total?: number }

  interface FetchResponse { status: number; headers: Record<string, string>; text: string; json<T = Json>(): T }

  interface Message { id: string; peerId: string; text: string; outgoing: boolean; date: number; authorId?: string }

  interface Ayu {
    readonly pluginId: string;
    log(...values: unknown[]): void;
    warn(...values: unknown[]): void;
    error(...values: unknown[]): void;
    toast(text: string): void;
    /** chatOpen, chatClose, profileOpen, profileClose, screenChange, appForeground, appBackground,
     *  accountChange, settingsChange, menuAction, profileButton, uiResult, messageDeleted, messageEdited,
     *  messageSent, intent, composerButton, screenAction, busMessage, trackChange (inject). */
    on(event: string, fn: (payload: any) => void): void;
    hooks: Hooks;
    settings: {
      declare(items: { key: string; type: "toggle" | "text" | "slider" | "color" | "select" | "preview"; title: string; subtitle?: string; default?: Json; min?: number; max?: number; step?: number; options?: (string | { value: string; title: string })[] }[]): void;
      get(key: string): Json;
    };
    storage: { get(key: string): string | null; set(key: string, value: string | null): void };
    /** Keychain-backed values, separate from storage (permission `secrets`). */
    secrets: { get(key: string): string | null; set(key: string, value: string | null): void };
    ui: Ui;
    registry: { developers: { isVerified(peerId: string): boolean; info(peerId: string): { verified: boolean; kind?: string; text?: string } } };
    /** write, hasText and clear need `clipboard`; read needs `clipboard.read` (iOS shows its paste notice). */
    clipboard: { write(text: string): void; read(): Promise<string | null>; hasText(): Promise<boolean>; clear(): boolean };
    /** Permission `device`. battery, isCharging, screen and darkMode come from a snapshot refreshed after every read. */
    device: {
      info(): { battery: number; charging: boolean; orientation: "portrait" | "landscape"; reduceMotion: boolean; lowPowerMode: boolean; locale: string };
      battery(): number | null; isCharging(): boolean; screen(): { width: number; height: number; scale: number } | null; darkMode(): boolean;
      model(): string; systemVersion(): string; timezone(): { id: string; offsetMinutes: number }; isLowPower(): boolean;
      freeDisk(): number | null; memory(): number; uptime(): number; thermalState(): "nominal" | "fair" | "serious" | "critical";
    };
    haptics: {
      play(style?: "light" | "medium" | "heavy" | "soft" | "rigid" | "success" | "warning" | "error" | "selection"): void;
      /** Up to 16 taps, `interval` ms apart (30-1000, default 120). */
      pattern(styles: HapticStyle[] | HapticStyle, interval?: number): boolean;
    };
    /** HTTPS to the hosts in `@connect` only (permission `network`). */
    net: { fetch(url: string, init?: { method?: string; headers?: Record<string, string>; body?: string }): Promise<FetchResponse> };
    /** Permission `messages` (send/edit/react) and `messages.read` (get). */
    messages: {
      send(options: { peerId: string; text: string; replyTo?: string }): Promise<boolean>;
      edit(options: { peerId: string; messageId: string; text: string }): Promise<boolean>;
      react(options: { peerId: string; messageId: string; emoji: string }): Promise<boolean>;
      get(options: { peerId: string; limit?: number }): Promise<Message[]>;
      /** Local bookmarks (this device): list needs `messages.read`, add/remove need `messages`. */
      bookmarks: {
        list(): { peerId: string; messageId: number; text: string; chat: string; tag: string; savedAt: number }[];
        add(options: { peerId: string; messageId: number; text?: string; chat?: string; tag?: string }): void;
        remove(peerId: string, messageId: number): void;
      };
    };
    /** Local note and nickname of a person (this device; get: `messages.read`, set: `messages`). */
    profile: {
      notes: { get(peerId: string): string | null; set(peerId: string, value: string | null): void };
      nickname: { get(peerId: string): string | null; set(peerId: string, value: string | null): void };
    };
    /** On-device image processing; base64 in and out. fromMessage needs `messages.read`, sendImage `messages`. */
    media: {
      process(data: string, ops: ({ op: "filter"; name: "mono" | "noir" | "chrome" | "fade" | "instant" | "sepia" | "invert" | "blur" | "sharpen" | "vignette" | "pixellate"; amount?: number } | { op: "resize"; maxSide: number } | { op: "cropSquare" } | { op: "rotate"; degrees: number } | { op: "brightness" | "contrast" | "saturation"; amount: number })[], options?: { format?: "jpeg" | "png"; quality?: number }): Promise<string>;
      fromMessage(peerId: string, messageId: number): Promise<{ data: string; width: number; height: number }>;
      sendImage(peerId: string, data: string, caption?: string): Promise<boolean>;
    };
    /**
     * TL hooks, official plugins only. `block` drops presence/read-mark calls before they are sent
     * (pre_request); `onRequest` (post_request) and `onUpdate` (on_update) report method and update
     * constructor names, never their contents.
     */
    tl: {
      block(method: string): boolean;
      unblock(method: string): boolean;
      onRequest(fn: (method: string, error: number | null) => void): boolean;
      onUpdate(fn: (constructor: string) => void): boolean;
    };
    /** The music player. Spectrum, visualizer and canvas need the `overlay` permission. */
    player: {
      state(): { title?: string; artist?: string; duration?: number; position?: number; playing?: boolean };
      control(action: "play" | "pause" | "next" | "previous" | string): boolean;
      play(): boolean; pause(): boolean; next(): boolean; previous(): boolean;
      /** The real spectrum of what is playing: bands from 40 Hz to 16 kHz (log scale), each 0…1. */
      spectrum: {
        get(bands?: number): { bands: number[]; level: number; active: boolean };
        subscribe(fn: (bands: number[], level: number) => void, options?: { bands?: number; fps?: number }): boolean;
        unsubscribe(): void;
      };
      /** A native visualizer drawn by the app at the display rate (reacts to bass without JS per frame). */
      visualizer: {
        set(options: { style: "bars" | "mirror" | "wave" | "circle" | "dots"; color?: string; bands?: number; opacity?: number; gain?: number }): void;
        clear(): void;
      };
      /** Shapes drawn inside the player window; x/y/w/h are 0…1 of the content area. */
      canvas: {
        draw(shapes: ({ type: "rect"; x: number; y: number; w: number; h: number; radius?: number; color?: string; alpha?: number } | { type: "circle"; x: number; y: number; w: number; h: number; color?: string; alpha?: number } | { type: "line"; x: number; y: number; x2: number; y2: number; width?: number; color?: string; alpha?: number } | { type: "text"; x: number; y: number; text: string; size?: number; color?: string; alpha?: number })[]): void;
        clear(): void;
      };
    };
    /** Device gestures: "shake" and "screenshot". */
    gestures: { on(type: "shake" | "screenshot", fn: (payload: { type: string }) => void): void };
    /** The open chat (permission `ui`). */
    chat: {
      scrollTo(messageId: number): void;
      /** Buttons in the chat bar above the keyboard; the callback gets the open chat's peerId. */
      toolbar: { add(button: { id: string; title: string; icon?: string }, onTap?: (peerId: string) => void): boolean; remove(id: string): void; filter(options: { words?: string[]; authors?: string[] }): void };
      /** Hide messages by words or authors in every chat (permission `messages.read`). */
      filter: { set(options: { words?: string[]; authors?: string[] }): void };
    };
    /** Dot commands typed in the composer: `.calc 2+2`. Return the text to send, or null to cancel. */
    commands: { register(name: string, description: string, fn: (args: string, ctx: HookContext) => string | null | undefined): void };
    /** Messages between plugins. */
    bus: { emit(topic: string, data?: Json): void; on(topic: string, fn: (data: Json, from: string) => void): void };
    i18n: { readonly language: string; t(strings: Record<string, string>): string };
    /** The OpenAI-compatible service set in AyuGram → Tools (permission `ai`). */
    ai: { complete(prompt: string, options?: { system?: string; maxTokens?: number }): Promise<string> };
    /** A full page drawn by AyuGram; taps arrive as the `screenAction` event { screenId, rowId, value }. */
    screens: { show(screen: { id: string; title: string; sections: ScreenSection[] }): void };
    /** Buttons above the keyboard; taps arrive as `composerButton` { id, text } (permission `composer`). */
    /** Buttons above the keyboard; a tap sends the `composerButton` event { id, text, selection, selectionStart, selectionEnd }. */
    composer: { addButton(button: { id: string; title: string; icon?: string }): void; removeButton(id: string): void; setText(text: string): void; replaceSelection(text: string): void };
    /** Local scheduling: runs while the app is open. */
    scheduler: { daily(time: string, fn: () => void): number; at(date: Date | number, fn: () => void): number; cancel(id: number): void };
    files: { export(name: string, text: string): void };
    permissions: { has(name: string): boolean; request(names: string[], fn?: (granted: boolean) => void): void };

    // 27.6
    /** Hex digests of UTF-8 text; randomBytes is base64. No permission. */
    crypto: { sha256(text: string): string; sha1(text: string): string; sha512(text: string): string; md5(text: string): string; hmac(key: string, text: string): string; randomBytes(count?: number): string; uuid(): string };
    encoding: { base64Encode(text: string): string; base64Decode(base64: string): string | null; hexEncode(text: string): string; hexDecode(hex: string): string | null };
    app: { version(): string | null; build(): string | null; name(): string; plugins(): { id: string; name: string; enabled: boolean }[] };
    /** On-device speech (permission `ui`). */
    speech: { speak(text: string, options?: { language?: string; rate?: number }): boolean; stop(): boolean; isSpeaking(): boolean; voices(): string[] };
    /** Local reminders, each plugin only its own (permission `notifications`). Returns the reminder id. */
    notify: { schedule(options: { id?: string; title: string; body?: string; seconds?: number }): string | null; cancel(id: string): boolean; cancelAll(): boolean };
    text: {
      capitalize(text: string): string; titleCase(text: string): string; reverse(text: string): string; truncate(text: string, length: number, ellipsis?: string): string;
      slugify(text: string): string; wordCount(text: string): number; charCount(text: string): number; stripEmoji(text: string): string;
      escapeHtml(text: string): string; unescapeHtml(text: string): string; translit(text: string): string;
      /** ghbdtn ⇄ привет */
      swapLayout(text: string): string; mock(text: string): string; between(text: string, start: string, end?: string): string | null;
      template(text: string, vars: Record<string, unknown>): string;
    };
    date: {
      format(date: Date | number | string, pattern?: string): string; relative(date: Date | number | string, language?: string): string;
      addDays(date: Date | number | string, days: number): Date; diffDays(from: Date | number | string, to?: Date | number | string): number;
      isToday(date: Date | number | string): boolean; startOfDay(date?: Date | number | string): Date;
      /** "1h 30m" → 5400000 ms; units ms s m h d w. */
      parseDuration(text: string): number | null; formatDuration(ms: number, language?: string): string;
    };
    color: { hexToRgb(hex: string): { r: number; g: number; b: number } | null; rgbToHex(r: number, g: number, b: number): string; lighten(hex: string, amount?: number): string | null; darken(hex: string, amount?: number): string | null; mix(a: string, b: string, amount?: number): string | null; contrastText(hex: string): "#000000" | "#FFFFFF"; random(): string };
    math: { clamp(value: number, min: number, max: number): number; lerp(a: number, b: number, t: number): number; random(min?: number, max?: number): number; randomInt(min: number, max: number): number; round(value: number, digits?: number): number; sum(list: number[]): number; average(list: number[]): number; median(list: number[]): number; percent(part: number, total: number): number };
    url: { parse(url: string): { protocol: string; host: string; port: number | null; path: string; query: Record<string, string>; hash: string } | null; build(base: string, params: Record<string, unknown>): string; param(url: string, name: string): string | null; isUrl(text: string): boolean; extract(text: string): string[]; domain(url: string): string | null };
    array: { chunk<T>(list: T[], size: number): T[][]; unique<T>(list: T[], key?: keyof T | ((item: T) => unknown)): T[]; shuffle<T>(list: T[]): T[]; sample<T>(list: T[]): T | null; groupBy<T>(list: T[], key: keyof T | ((item: T) => unknown)): Record<string, T[]>; sortBy<T>(list: T[], key: keyof T | ((item: T) => unknown), descending?: boolean): T[] };
    async: { sleep(ms: number): Promise<void>; debounce<F extends (...args: any[]) => void>(fn: F, ms: number): F; throttle<F extends (...args: any[]) => unknown>(fn: F, ms: number): F; retry<T>(fn: () => T | Promise<T>, times?: number, delay?: number): Promise<T>; timeout<T>(promise: Promise<T>, ms: number): Promise<T> };
    format: { bytes(value: number, digits?: number): string; number(value: number, digits?: number): string; plural(count: number, forms: [string, string, string] | [string, string]): string };
    extract: { mentions(text: string): string[]; hashtags(text: string): string[]; emails(text: string): string[] };
  }
  type HapticStyle = "light" | "medium" | "heavy" | "soft" | "rigid";
}

declare const ayu: Ayu.Ayu;
declare function setTimeout(fn: () => void, ms?: number): number;
declare function setInterval(fn: () => void, ms?: number): number;
declare function clearTimeout(id: number): void;
declare function clearInterval(id: number): void;
