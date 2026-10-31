//! SDK for AyuGram plugins written in Rust.
//!
//! Build with `cargo build --release --target wasm32-unknown-unknown` (`crate-type = ["cdylib"]`)
//! and install the `.wasm` file in AyuGram. The app runs it in a WebAssembly interpreter; the
//! plugin talks to the app only through JSON messages, so it has no file, network or account access.
//!
//! ```ignore
//! use ayugram_plugin::{hooks, log, manifest};
//!
//! manifest!(br#"{"id":"shout","name":"Shout","author":"me","version":"1.0","description":"UPPERCASE"}"#);
//!
//! #[no_mangle]
//! pub extern "C" fn ayu_init() {
//!     hooks::before(hooks::OUTGOING_TEXT, |text, _ctx| Some(text.to_uppercase()));
//!     log("loaded");
//! }
//! ```

use std::cell::RefCell;

pub mod json;

/// Embeds the plugin header (JSON with id, name, author, version, description and optionally
/// `"inject": true`) as the `ayu.manifest` custom section, read by the app before running code.
#[macro_export]
macro_rules! manifest {
    ($json:expr) => {
        #[link_section = "ayu.manifest"]
        #[used]
        static AYU_MANIFEST: [u8; $json.len()] = *$json;
    };
}

#[link(wasm_import_module = "ayu")]
extern "C" {
    #[link_name = "host"]
    fn ayu_host(pointer: *const u8, length: usize) -> u64;
}

// MARK: Memory shared with the app

#[no_mangle]
pub extern "C" fn ayu_alloc(length: usize) -> *mut u8 {
    let mut buffer = Vec::<u8>::with_capacity(length.max(1));
    let pointer = buffer.as_mut_ptr();
    std::mem::forget(buffer);
    pointer
}

#[no_mangle]
pub unsafe extern "C" fn ayu_free(pointer: *mut u8, length: usize) {
    if !pointer.is_null() {
        drop(Vec::from_raw_parts(pointer, 0, length.max(1)));
    }
}

unsafe fn take_string(pointer: *mut u8, length: usize) -> String {
    let bytes = Vec::from_raw_parts(pointer, length, length.max(1));
    String::from_utf8(bytes).unwrap_or_default()
}

fn give_string(text: String) -> u64 {
    let mut bytes = text.into_bytes();
    bytes.shrink_to_fit();
    let length = bytes.len();
    let pointer = ayu_alloc(length);
    unsafe { std::ptr::copy_nonoverlapping(bytes.as_ptr(), pointer, length) };
    ((pointer as u64) << 32) | length as u64
}

/// Sends a JSON request to the app and returns its JSON answer.
pub fn request(message: &str) -> Option<String> {
    let packed = unsafe { ayu_host(message.as_ptr(), message.len()) };
    if packed == 0 {
        return None;
    }
    let pointer = (packed >> 32) as usize as *mut u8;
    let length = (packed & 0xffff_ffff) as usize;
    Some(unsafe { take_string(pointer, length) })
}

// MARK: API

pub fn log(text: &str) {
    request(&format!(r#"{{"op":"log","level":"info","text":{}}}"#, json::quote(text)));
}

pub fn warn(text: &str) {
    request(&format!(r#"{{"op":"log","level":"warning","text":{}}}"#, json::quote(text)));
}

pub fn toast(text: &str) {
    request(&format!(r#"{{"op":"toast","text":{}}}"#, json::quote(text)));
}

pub mod storage {
    use super::{json, request};

    pub fn get(key: &str) -> Option<String> {
        let answer = request(&format!(r#"{{"op":"storage.get","key":{}}}"#, json::quote(key)))?;
        json::string_field(&answer, "value")
    }

    pub fn set(key: &str, value: Option<&str>) {
        let value = value.map(json::quote).unwrap_or_else(|| "null".to_string());
        request(&format!(r#"{{"op":"storage.set","key":{},"value":{}}}"#, json::quote(key), value));
    }
}

pub mod features {
    use super::{json, request};

    pub fn disable(name: &str) {
        request(&format!(r#"{{"op":"feature","name":{},"disabled":true}}"#, json::quote(name)));
    }

    pub fn enable(name: &str) {
        request(&format!(r#"{{"op":"feature","name":{},"disabled":false}}"#, json::quote(name)));
    }
}

/// Needs `"inject": true` in the manifest and an official signature (or the developer option).
pub mod player {
    use super::{json, request};

    /// `play`, `pause`, `toggle`, `next`, `previous`.
    pub fn control(action: &str) -> bool {
        request(&format!(r#"{{"op":"player.control","action":{}}}"#, json::quote(action)))
            .map(|answer| answer.contains("\"ok\":true") || answer.contains("\"ok\": true"))
            .unwrap_or(false)
    }

    /// The raw JSON state: title, artist, position, duration, playing.
    pub fn state() -> Option<String> {
        request(r#"{"op":"player.state"}"#)
    }
}

/// Context handed to text hooks.
pub struct Context {
    pub peer_id: String,
    pub raw: String,
}

type TextHandler = Box<dyn Fn(&str, &Context) -> Option<String>>;

thread_local! {
    static HANDLERS: RefCell<Vec<TextHandler>> = RefCell::new(Vec::new());
    static EVENTS: RefCell<Vec<(String, Box<dyn Fn(&str)>)>> = RefCell::new(Vec::new());
}

pub mod hooks {
    use super::{json, request, Context, HANDLERS};

    pub const OUTGOING_TEXT: &str = "message.outgoing.text";
    pub const LYRICS_TEXT: &str = "lyrics.text";

    fn register(point: &str, mode: &str, handler: impl Fn(&str, &Context) -> Option<String> + 'static) {
        let id = HANDLERS.with(|handlers| {
            let mut handlers = handlers.borrow_mut();
            handlers.push(Box::new(handler));
            handlers.len()
        });
        request(&format!(r#"{{"op":"hook","point":{},"mode":{},"handler":{}}}"#, json::quote(point), json::quote(mode), id));
    }

    pub fn before(point: &str, handler: impl Fn(&str, &Context) -> Option<String> + 'static) {
        register(point, "before", handler);
    }

    pub fn after(point: &str, handler: impl Fn(&str, &Context) -> Option<String> + 'static) {
        register(point, "after", handler);
    }

    pub fn replace(point: &str, handler: impl Fn(&str, &Context) -> Option<String> + 'static) {
        register(point, "replace", handler);
    }
}

/// Subscribes to an app event (`chatOpen`, `appForeground`, `trackChange`, …); the payload is JSON.
pub fn on(event: &str, handler: impl Fn(&str) + 'static) {
    EVENTS.with(|events| events.borrow_mut().push((event.to_string(), Box::new(handler))));
    request(&format!(r#"{{"op":"on","event":{}}}"#, json::quote(event)));
}

#[no_mangle]
pub unsafe extern "C" fn ayu_dispatch(pointer: *mut u8, length: usize) -> u64 {
    let message = take_string(pointer, length);
    match json::string_field(&message, "op").as_deref() {
        Some("hook") => {
            let id = json::number_field(&message, "handler").unwrap_or(0.0) as usize;
            let text = json::string_field(&message, "text").unwrap_or_default();
            let context = Context {
                peer_id: json::string_field(&message, "peerId").unwrap_or_default(),
                raw: message.clone(),
            };
            let result = HANDLERS.with(|handlers| {
                let handlers = handlers.borrow();
                handlers.get(id.wrapping_sub(1)).and_then(|handler| handler(&text, &context))
            });
            give_string(match result {
                Some(text) => format!(r#"{{"text":{}}}"#, json::quote(&text)),
                None => r#"{"text":null}"#.to_string(),
            })
        }
        Some("event") => {
            let name = json::string_field(&message, "event").unwrap_or_default();
            EVENTS.with(|events| {
                for (event, handler) in events.borrow().iter() {
                    if *event == name {
                        handler(&message);
                    }
                }
            });
            give_string("{}".to_string())
        }
        _ => give_string("{}".to_string()),
    }
}
