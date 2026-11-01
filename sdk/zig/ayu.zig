//! AyuGram plugin SDK for Zig.
//!
//! Build:  zig build-exe plugin.zig -target wasm32-freestanding -fno-entry -rdynamic -O ReleaseSmall
//! Then:   ayu pack plugin.wasm manifest.json plugin.wasm   (adds the `ayu.manifest` section)
//!
//! The ABI is the same as the Rust SDK's: the app calls `ayu_init`, `ayu_dispatch`, `ayu_alloc`
//! and `ayu_free`; the plugin calls the single import `ayu.host` with a JSON request and gets a
//! JSON answer back as `(pointer << 32) | length`. No allocation happens in the hot path beyond
//! the one buffer per message, and every buffer goes back to the same page allocator.
//!
//! ```zig
//! const ayu = @import("ayu.zig");
//! fn shout(text: []const u8, ctx: ayu.Context) ?[]const u8 {
//!     _ = ctx;
//!     return ayu.upper(text);
//! }
//! export fn ayu_init() void {
//!     ayu.hooks.before(ayu.hooks.outgoing_text, shout);
//!     ayu.log("loaded");
//! }
//! ```

const std = @import("std");

const allocator = std.heap.wasm_allocator;

extern "ayu" fn host(pointer: [*]const u8, length: usize) u64;

// MARK: Memory shared with the app

export fn ayu_alloc(length: usize) ?[*]u8 {
    const buffer = allocator.alloc(u8, @max(length, 1)) catch return null;
    return buffer.ptr;
}

export fn ayu_free(pointer: ?[*]u8, length: usize) void {
    if (pointer) |p| allocator.free(p[0..@max(length, 1)]);
}

fn give(text: []const u8) u64 {
    const pointer = ayu_alloc(text.len) orelse return 0;
    @memcpy(pointer[0..text.len], text);
    return (@as(u64, @intFromPtr(pointer)) << 32) | @as(u64, text.len);
}

/// Sends a JSON request to the app; the caller frees the answer with `release`.
pub fn request(message: []const u8) ?[]u8 {
    const packed_value = host(message.ptr, message.len);
    if (packed_value == 0) return null;
    const pointer: [*]u8 = @ptrFromInt(@as(usize, @intCast(packed_value >> 32)));
    const length: usize = @intCast(packed_value & 0xffff_ffff);
    return pointer[0..length];
}

pub fn release(answer: ?[]u8) void {
    if (answer) |a| ayu_free(a.ptr, a.len);
}

// MARK: JSON helpers (enough for the host protocol)

/// Writes `text` as a JSON string literal into `out`.
pub fn quote(out: *std.ArrayList(u8), text: []const u8) !void {
    try out.append('"');
    for (text) |c| {
        switch (c) {
            '"' => try out.appendSlice("\\\""),
            '\\' => try out.appendSlice("\\\\"),
            '\n' => try out.appendSlice("\\n"),
            '\r' => try out.appendSlice("\\r"),
            '\t' => try out.appendSlice("\\t"),
            0...8, 11, 12, 14...31 => try out.writer().print("\\u{x:0>4}", .{c}),
            else => try out.append(c),
        }
    }
    try out.append('"');
}

/// The string value of `"key":"…"` in a flat JSON object (escapes resolved), owned by the caller.
pub fn stringField(json: []const u8, key: []const u8) ?[]u8 {
    var needle_buffer: [80]u8 = undefined;
    const needle = std.fmt.bufPrint(&needle_buffer, "\"{s}\":", .{key}) catch return null;
    const start = std.mem.indexOf(u8, json, needle) orelse return null;
    var index = start + needle.len;
    while (index < json.len and json[index] == ' ') index += 1;
    if (index >= json.len or json[index] != '"') return null;
    index += 1;
    var out = std.ArrayList(u8).init(allocator);
    while (index < json.len) : (index += 1) {
        const c = json[index];
        if (c == '"') return out.toOwnedSlice() catch null;
        if (c == '\\' and index + 1 < json.len) {
            index += 1;
            const escaped: u8 = switch (json[index]) {
                'n' => '\n',
                't' => '\t',
                'r' => '\r',
                else => json[index],
            };
            out.append(escaped) catch return null;
        } else {
            out.append(c) catch return null;
        }
    }
    out.deinit();
    return null;
}

fn send(comptime format: []const u8, args: anytype) void {
    const message = std.fmt.allocPrint(allocator, format, args) catch return;
    defer allocator.free(message);
    release(request(message));
}

fn quoted(text: []const u8) []u8 {
    var out = std.ArrayList(u8).init(allocator);
    quote(&out, text) catch {};
    return out.toOwnedSlice() catch &[_]u8{};
}

// MARK: API

pub fn log(text: []const u8) void {
    const q = quoted(text);
    defer allocator.free(q);
    send("{{\"op\":\"log\",\"level\":\"info\",\"text\":{s}}}", .{q});
}

pub fn toast(text: []const u8) void {
    const q = quoted(text);
    defer allocator.free(q);
    send("{{\"op\":\"toast\",\"text\":{s}}}", .{q});
}

/// Any extended API with a JSON object of arguments: `call("ui.menu.add", "{\"id\":\"a\",\"title\":\"A\"}")`.
pub fn call(op: []const u8, args_json: []const u8) ?[]u8 {
    const trimmed = std.mem.trim(u8, args_json, " \n\t");
    const inner = if (trimmed.len >= 2) std.mem.trim(u8, trimmed[1 .. trimmed.len - 1], " ") else "";
    const q = quoted(op);
    defer allocator.free(q);
    const message = if (inner.len == 0)
        std.fmt.allocPrint(allocator, "{{\"op\":{s}}}", .{q}) catch return null
    else
        std.fmt.allocPrint(allocator, "{{\"op\":{s},{s}}}", .{ q, inner }) catch return null;
    defer allocator.free(message);
    return request(message);
}

/// ASCII upper case into a new buffer (handy for examples).
pub fn upper(text: []const u8) ?[]const u8 {
    const out = allocator.alloc(u8, text.len) catch return null;
    for (text, 0..) |c, i| out[i] = std.ascii.toUpper(c);
    return out;
}

// MARK: Hooks and events

pub const Context = struct {
    peer_id: []const u8,
    raw: []const u8,
};

pub const TextHandler = *const fn (text: []const u8, ctx: Context) ?[]const u8;
pub const EventHandler = *const fn (payload: []const u8) void;

var text_handlers: [32]TextHandler = undefined;
var text_handler_count: usize = 0;
var event_names: [32][]const u8 = undefined;
var event_handlers: [32]EventHandler = undefined;
var event_count: usize = 0;

pub const hooks = struct {
    pub const outgoing_text = "message.outgoing.text";
    pub const lyrics_text = "lyrics.text";
    pub const link_open = "link.open";
    pub const message_render = "message.render";

    fn register(point: []const u8, mode: []const u8, handler: TextHandler) void {
        if (text_handler_count >= text_handlers.len) return;
        text_handlers[text_handler_count] = handler;
        text_handler_count += 1;
        send("{{\"op\":\"hook\",\"point\":\"{s}\",\"mode\":\"{s}\",\"handler\":{d}}}", .{ point, mode, text_handler_count });
    }

    pub fn before(point: []const u8, handler: TextHandler) void {
        register(point, "before", handler);
    }
    pub fn after(point: []const u8, handler: TextHandler) void {
        register(point, "after", handler);
    }
    pub fn replace(point: []const u8, handler: TextHandler) void {
        register(point, "replace", handler);
    }
};

/// Subscribes to an app event (`chatOpen`, `messageDeleted`, `accountChange`, …).
pub fn on(event: []const u8, handler: EventHandler) void {
    if (event_count >= event_handlers.len) return;
    event_names[event_count] = event;
    event_handlers[event_count] = handler;
    event_count += 1;
    send("{{\"op\":\"on\",\"event\":\"{s}\"}}", .{event});
}

export fn ayu_dispatch(pointer: [*]u8, length: usize) u64 {
    const message = pointer[0..length];
    defer ayu_free(pointer, length);
    const op = stringField(message, "op") orelse return give("{}");
    defer allocator.free(op);
    if (std.mem.eql(u8, op, "hook")) {
        const marker = "\"handler\":";
        var id: usize = 0;
        if (std.mem.indexOf(u8, message, marker)) |at| {
            var i = at + marker.len;
            while (i < message.len and message[i] >= '0' and message[i] <= '9') : (i += 1) id = id * 10 + (message[i] - '0');
        }
        const owned_text = stringField(message, "text");
        defer if (owned_text) |t| allocator.free(t);
        const owned_peer = stringField(message, "peerId");
        defer if (owned_peer) |p| allocator.free(p);
        const text: []const u8 = owned_text orelse "";
        const peer: []const u8 = owned_peer orelse "";
        if (id == 0 or id > text_handler_count) return give("{\"text\":null}");
        const result = text_handlers[id - 1](text, .{ .peer_id = peer, .raw = message });
        if (result) |value| {
            var out = std.ArrayList(u8).init(allocator);
            defer out.deinit();
            out.appendSlice("{\"text\":") catch return 0;
            quote(&out, value) catch return 0;
            out.append('}') catch return 0;
            return give(out.items);
        }
        return give("{\"text\":null}");
    }
    if (std.mem.eql(u8, op, "event")) {
        const name = stringField(message, "event") orelse return give("{}");
        defer allocator.free(name);
        for (event_names[0..event_count], 0..) |event, i| {
            if (std.mem.eql(u8, event, name)) event_handlers[i](message);
        }
    }
    return give("{}");
}
