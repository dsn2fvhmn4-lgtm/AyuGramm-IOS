//! Emoji shortcuts, written in Rust: `:fire:` → 🔥, `:heart:` → ❤️ and others in messages you send.

use ayugram_plugin::{hooks, log, manifest, storage};

manifest!(br#"{"id":"emoji-shortcuts-rs","name":"Emoji shortcuts (Rust)","author":"murk-sus & dsn2fvhmn4-lgtm","version":"1.0","description":"Rust plugin: :fire:, :heart:, :ok:, :lol:, :100: and other shortcuts become emoji in messages you send.","tags":["text","emoji","rust"]}"#);

const SHORTCUTS: &[(&str, &str)] = &[
    (":fire:", "🔥"),
    (":heart:", "❤️"),
    (":ok:", "👌"),
    (":lol:", "😂"),
    (":cry:", "😢"),
    (":skull:", "💀"),
    (":clap:", "👏"),
    (":eyes:", "👀"),
    (":100:", "💯"),
    (":think:", "🤔"),
    (":pray:", "🙏"),
    (":rocket:", "🚀"),
    (":star:", "⭐"),
    (":thumbsup:", "👍"),
    (":thumbsdown:", "👎"),
];

#[no_mangle]
pub extern "C" fn ayu_init() {
    hooks::before(hooks::OUTGOING_TEXT, |text, _context| {
        if !text.contains(':') {
            return None;
        }
        let mut result = text.to_string();
        let mut count = 0;
        for (code, emoji) in SHORTCUTS {
            if result.contains(code) {
                count += result.matches(code).count();
                result = result.replace(code, emoji);
            }
        }
        if count == 0 {
            return None;
        }
        let total = storage::get("replaced").and_then(|v| v.parse::<u64>().ok()).unwrap_or(0) + count as u64;
        storage::set("replaced", Some(&total.to_string()));
        Some(result)
    });
    log("Emoji shortcuts ready");
}
