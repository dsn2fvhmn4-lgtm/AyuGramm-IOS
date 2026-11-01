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
    /** A button over the whole app; the callback runs on tap (permission `overlay`). */
    floatingButton: { add(options: { id: string; icon?: string; title?: string; anchor?: "bottomRight" | "bottomLeft" | "topRight" | "topLeft"; color?: string }, onTap?: () => void): boolean; remove(id: string): void };
    progress: { show(options: { id: string; title?: string; value: number; anchor?: string }): void; hide(id: string): void };
    animation: { play(name?: "confetti" | "snow" | "stars" | "leaves" | "rain", seconds?: number): void };
    font: {
      /** `weight` applies to regular text in the whole app. */
      set(options: { element?: "messages" | "lists"; size?: number; weight?: "light" | "regular" | "medium" | "semibold" | "bold" }): void;
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
    clipboard: { write(text: string): void };
    device: { info(): { battery: number; charging: boolean; orientation: "portrait" | "landscape"; reduceMotion: boolean; lowPowerMode: boolean; locale: string } };
    haptics: { play(style?: "light" | "medium" | "heavy" | "soft" | "rigid" | "success" | "warning" | "error" | "selection"): void };
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
    /** The open chat (permission `ui`). */
    chat: { scrollTo(messageId: number): void };
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
  }
}

declare const ayu: Ayu.Ayu;
declare function setTimeout(fn: () => void, ms?: number): number;
declare function setInterval(fn: () => void, ms?: number): number;
declare function clearTimeout(id: number): void;
declare function clearInterval(id: number): void;
