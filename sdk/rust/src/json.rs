//! The little JSON the plugin protocol needs, without dependencies.

/// `text` as a JSON string literal.
pub fn quote(text: &str) -> String {
    let mut out = String::with_capacity(text.len() + 2);
    out.push('"');
    for ch in text.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

/// Position just after `"key":` (whitespace skipped), searching the whole message.
fn value_start(json: &str, key: &str) -> Option<usize> {
    let needle = format!("\"{}\"", key);
    let mut from = 0;
    while let Some(found) = json[from..].find(&needle) {
        let mut index = from + found + needle.len();
        let bytes = json.as_bytes();
        while index < bytes.len() && (bytes[index] as char).is_whitespace() {
            index += 1;
        }
        if index < bytes.len() && bytes[index] == b':' {
            index += 1;
            while index < bytes.len() && (bytes[index] as char).is_whitespace() {
                index += 1;
            }
            return Some(index);
        }
        from = from + found + 1;
    }
    None
}

/// The string value of the first `"key"` in the message, unescaped.
pub fn string_field(json: &str, key: &str) -> Option<String> {
    let start = value_start(json, key)?;
    let rest = &json[start..];
    let mut chars = rest.chars();
    if chars.next()? != '"' {
        return None;
    }
    let mut out = String::new();
    while let Some(ch) = chars.next() {
        match ch {
            '"' => return Some(out),
            '\\' => match chars.next()? {
                'n' => out.push('\n'),
                'r' => out.push('\r'),
                't' => out.push('\t'),
                'b' => out.push('\u{8}'),
                'f' => out.push('\u{c}'),
                'u' => {
                    let hex: String = (0..4).filter_map(|_| chars.next()).collect();
                    let mut code = u32::from_str_radix(&hex, 16).ok()?;
                    // Surrogate pairs (emoji) arrive as two escapes.
                    if (0xd800..0xdc00).contains(&code) {
                        let mut lookahead = chars.clone();
                        if lookahead.next() == Some('\\') && lookahead.next() == Some('u') {
                            let low: String = (0..4).filter_map(|_| lookahead.next()).collect();
                            if let Ok(low) = u32::from_str_radix(&low, 16) {
                                code = 0x10000 + ((code - 0xd800) << 10) + (low - 0xdc00);
                                chars = lookahead;
                            }
                        }
                    }
                    out.push(char::from_u32(code).unwrap_or('\u{fffd}'));
                }
                other => out.push(other),
            },
            other => out.push(other),
        }
    }
    None
}

/// The numeric value of the first `"key"` in the message.
pub fn number_field(json: &str, key: &str) -> Option<f64> {
    let start = value_start(json, key)?;
    let end = json[start..]
        .find(|c: char| !(c.is_ascii_digit() || c == '.' || c == '-' || c == 'e' || c == 'E' || c == '+'))
        .map(|offset| start + offset)
        .unwrap_or(json.len());
    json[start..end].parse().ok()
}
