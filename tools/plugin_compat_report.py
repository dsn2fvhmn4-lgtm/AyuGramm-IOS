"""Compatibility report: how an exteraGram .plugin would run on the AyuGram iOS Python runtime.

Static by default: the plugin source is parsed, never executed. The support
tables come from the runtime itself (runtime/hook_map.json and the Python
implementations in runtime/python/_ayu_java.py), so the report can only claim
what the runtime implements.

`--dry-run` additionally loads each plugin in the runtime with the mock native
bridge and calls on_plugin_load. That EXECUTES plugin code on this machine;
use it only for plugins you trust.

    python tools/plugin_compat_report.py plugins/*.plugin --markdown report.md --json report.json
    python tools/plugin_compat_report.py --inventory docs/ANDROID_PLUGIN_INVENTORY.json
"""
import argparse
import ast
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime" / "python"
sys.path.insert(0, str(RUNTIME))

import _ayu_java  # noqa: E402  (installs the Java import finder in this process only)

HOOK_MAP = json.loads((ROOT / "runtime" / "hook_map.json").read_text(encoding="utf-8"))
METHODS = {(m["class"], m["method"]): m for m in HOOK_MAP["methods"]}
WIRED = {"wired", "partial"}

# SDK names the shim implements: "ok", "partial" (with the reason) or "no".
SDK = {
    "base_plugin": {name: ("ok", None) for name in ("BasePlugin", "HookResult", "HookStrategy", "AppEvent", "MenuItemData", "MenuItemType", "MethodHook", "MethodReplacement", "XposedHook")},
    "client_utils": {
        "send_text": ("ok", None), "send_message": ("partial", "plain text only"), "run_on_queue": ("ok", None),
        "get_queue_by_name": ("ok", None), "get_user_config": ("partial", "client user id only"),
        "send_photo": ("no", "media sending not bridged"), "send_document": ("no", "media sending not bridged"),
        "send_video": ("no", "media sending not bridged"), "send_audio": ("no", "media sending not bridged"),
        "edit_message": ("no", "editing not bridged"), "send_request": ("no", "raw TL requests not bridged"),
        "RequestCallback": ("no", "raw TL requests not bridged"), "NotificationCenterDelegate": ("no", "NotificationCenter not bridged"),
        **{name: ("partial", "returns an opaque stub; Java methods on it are unsupported") for name in (
            "get_last_fragment", "get_account_instance", "get_messages_controller", "get_contacts_controller",
            "get_media_data_controller", "get_connections_manager", "get_location_controller",
            "get_notifications_controller", "get_messages_storage", "get_send_messages_helper", "get_file_loader",
            "get_secret_chat_helper", "get_download_controller", "get_notifications_settings",
            "get_notification_center", "get_media_controller")},
        **{q: ("ok", None) for q in ("STAGE_QUEUE", "GLOBAL_QUEUE", "CACHE_CLEAR_QUEUE", "SEARCH_QUEUE", "PHONE_BOOK_QUEUE", "THEME_QUEUE", "EXTERNAL_NETWORK_QUEUE", "PLUGINS_QUEUE")},
    },
    "android_utils": {"run_on_ui_thread": ("ok", None), "copy_to_clipboard": ("ok", None), "log": ("ok", None), "R": ("ok", None),
                      "OnClickListener": ("no", "Android views"), "OnLongClickListener": ("no", "Android views")},
    "hook_utils": {"find_class": ("ok", None), "get_private_field": ("no", "no Java objects on iOS"), "set_private_field": ("no", "no Java objects on iOS"),
                   "get_static_private_field": ("no", "no Java objects on iOS"), "set_static_private_field": ("no", "no Java objects on iOS")},
    "file_utils": {name: ("ok", None) for name in ("get_plugins_dir", "get_cache_dir", "get_files_dir", "get_images_dir", "get_videos_dir", "get_audios_dir",
                                                    "get_documents_dir", "ensure_dir_exists", "list_dir", "write_file", "read_file", "write_file_bytes",
                                                    "read_file_bytes", "delete_file")},
    "ui.bulletin": {"BulletinHelper": ("ok", None)},
    "ui.alert": {"AlertDialogBuilder": ("ok", None)},
    "ui.settings": {**{name: ("partial", "native settings page pending; values and callbacks work") for name in ("Header", "Divider", "Switch", "Selector", "Input", "EditText", "Text")},
                    "Custom": ("no", "custom Android views")},
    "extera_utils.text_formatting": {"parse_text": ("partial", "entities are parsed by the host at send time"), "TLEntityType": ("ok", None), "RawEntity": ("ok", None)},
}
SDK["file_utils"]["FilesController"] = ("no", "file-type handlers not bridged")
SDK_METHODS = {
    "add_on_send_message_hook": ("ok", None), "remove_on_send_message_hook": ("ok", None),
    "add_menu_item": ("ok", None), "remove_menu_item": ("ok", None),
    "get_setting": ("ok", None), "set_setting": ("ok", None), "export_settings": ("ok", None), "import_settings": ("ok", None),
    "hook_method": ("ok", None), "hook_all_methods": ("ok", None), "hook_all_constructors": ("ok", None), "unhook_method": ("ok", None),
    "add_hook": ("no", "TL request/update hooks not bridged"), "remove_hook": ("ok", None), "log": ("ok", None),
}
MENU_TYPES = {"MESSAGE_CONTEXT_MENU": "ok", "CHAT_ACTION_MENU": "ok",
              "DRAWER_MENU": "partial", "MAIN_MENU": "partial", "PROFILE_ACTION_MENU": "partial"}
STDLIB = set(getattr(sys, "stdlib_module_names", ()))
# Stdlib modules that do not work on iOS (no subprocesses, GUI or terminal).
IOS_UNAVAILABLE = {"subprocess", "multiprocessing", "tkinter", "curses", "readline", "venv", "ensurepip", "idlelib", "turtle"}
SHIM_MODULES = {"base_plugin", "client_utils", "android_utils", "hook_utils", "file_utils", "ui", "ui.bulletin", "ui.alert",
                "ui.settings", "extera_utils", "extera_utils.text_formatting", "java"}


def is_java(module):
    return module == "java" or module.startswith(_ayu_java.JAVA_PREFIXES) or any(p.startswith(module + ".") for p in _ayu_java.JAVA_PREFIXES)


def java_member_supported(class_name, member):
    return member in _ayu_java.STATIC_IMPLEMENTATIONS.get(class_name, {})


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()
        self.names = {}          # local name -> ("sdk", module, name) | ("java", class) | ("module", module)
        self.vars = {}           # variable -> ("class", name) | ("method", class, method)
        self.sdk = []            # (module, name, status, reason)
        self.self_calls = {}
        self.hooks = []          # (class, method) or ("<dynamic>", expr)
        self.java_calls = {}
        self.java_objects = {}
        self.menu_types = set()
        self.request_hooks = []
        self.overrides = set()
        self.unknown_modules = set()

    # imports
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
            local = alias.asname or alias.name.split(".")[0]
            self.names[local] = ("module", alias.name if alias.asname else alias.name.split(".")[0])

    def visit_ImportFrom(self, node):
        module = node.module or ""
        self.imports.add(module)
        for alias in node.names:
            local = alias.asname or alias.name
            if is_java(module) and module != "java":
                self.names[local] = ("java", module + "." + alias.name)
            elif module == "java":
                self.names[local] = ("javahelper", alias.name)
            else:
                self.names[local] = ("sdk", module, alias.name)
                if module in SDK:
                    status, reason = SDK[module].get(alias.name, ("no", "not provided by the iOS shim"))
                    self.sdk.append((module, alias.name, status, reason))

    # resolution helpers
    def class_of(self, node):
        if isinstance(node, ast.Name):
            bound = self.names.get(node.id) or ()
            if bound[:1] == ("java",):
                return bound[1]
            var = self.vars.get(node.id)
            if var and var[0] == "class":
                return var[1]
        if isinstance(node, ast.Call):
            func = node.func
            literal = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str) else None
            callee = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if literal and callee in ("find_class", "jclass", "findClass", "forName"):
                return literal
        if isinstance(node, ast.Attribute):
            owner = self.class_of(node.value)
            if owner and node.attr[:1].isupper() and not node.attr.isupper():
                return owner + "$" + node.attr
            if owner and node.attr in ("class_", "_class", "klass"):
                return owner
        return None

    def method_of(self, node):
        if isinstance(node, ast.Name) and self.vars.get(node.id, ("",))[0] == "method":
            return self.vars[node.id][1:]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("getDeclaredMethod", "getMethod", "getDeclaredConstructor", "getConstructor"):
            owner = self.class_of(node.func.value)
            if node.func.attr.endswith("Constructor"):
                return (owner, "<init>") if owner else None
            if owner and node.args and isinstance(node.args[0], ast.Constant):
                return owner, node.args[0].value
        return None

    def visit_Assign(self, node):
        method = self.method_of(node.value)
        cls = None if method else self.class_of(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if method:
                    self.vars[target.id] = ("method",) + tuple(method)
                elif cls:
                    self.vars[target.id] = ("class", cls)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if node.name in ("on_send_message_hook", "pre_request_hook", "post_request_hook", "on_update_hook", "on_updates_hook", "on_app_event", "create_settings"):
            self.overrides.add(node.name)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == "MenuItemType":
            self.menu_types.add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "self" and func.attr in SDK_METHODS:
            self.self_calls[func.attr] = self.self_calls.get(func.attr, 0) + 1
            if func.attr == "hook_method" and node.args:
                target = self.method_of(node.args[0])
                self.hooks.append(tuple(target) if target and target[0] else ("<dynamic>", ast.unparse(node.args[0])[:80]))
            elif func.attr in ("hook_all_methods", "hook_all_constructors") and node.args:
                owner = self.class_of(node.args[0])
                name = "<init>" if func.attr == "hook_all_constructors" else (node.args[1].value if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) else None)
                self.hooks.append((owner, name) if owner and name else ("<dynamic>", ast.unparse(node)[:80]))
            elif func.attr == "add_hook" and node.args:
                self.request_hooks.append(ast.unparse(node.args[0])[:80])
        elif isinstance(func, ast.Attribute):
            owner = self.class_of(func.value)
            if owner and func.attr not in ("getDeclaredMethod", "getMethod", "getDeclaredConstructor", "getConstructor", "getName", "getClass"):
                key = owner + "#" + func.attr
                if not java_member_supported(owner, func.attr):
                    self.java_calls[key] = self.java_calls.get(key, 0) + 1
        else:
            owner = self.class_of(func)
            if owner and owner not in _ayu_java.CONSTRUCTORS:
                self.java_objects[owner] = self.java_objects.get(owner, 0) + 1
        self.generic_visit(node)


def metadata_of(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith("__") and node.targets[0].id.endswith("__"):
            try:
                value = ast.literal_eval(node.value)
            except ValueError:
                continue
            if isinstance(value, (str, list)):
                result[node.targets[0].id.strip("_")] = value
    return result


def grade(items):
    statuses = [i["status"] for i in items]
    if not statuses:
        return "unsupported"
    if all(s == "ok" for s in statuses):
        return "runs"
    if any(s in ("ok", "partial") for s in statuses):
        return "partial"
    return "unsupported"


def analyze_source(path):
    data = Path(path).read_bytes()
    report = {"file": Path(path).name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    blockers = []
    if b"__DEX_BEGIN__" in data or b"__NATIVE_BEGIN__" in data:
        blockers.append("Embeds an Android DEX/JNI payload, which cannot load on iOS.")
    try:
        tree = ast.parse(data.decode("utf-8-sig"), filename=report["file"])
    except (SyntaxError, UnicodeDecodeError) as error:
        report.update(verdict="unsupported", blockers=["Source does not parse: %s" % error], features=[], risks=[])
        return report
    meta = metadata_of(tree)
    analyzer = Analyzer()
    analyzer.visit(tree)
    features, risks = [], []

    if "add_on_send_message_hook" in analyzer.self_calls or "on_send_message_hook" in analyzer.overrides:
        features.append({"feature": "Send-message hook", "status": "ok", "notes": "Plain cloud text; media and secret chats bypass it."})
    for request in analyzer.request_hooks:
        features.append({"feature": "TL hook %s" % request, "status": "no", "notes": "Request/update hooks are not bridged yet."})
    for cls, method in analyzer.hooks:
        if cls == "<dynamic>":
            features.append({"feature": "Java hook (unresolved: %s)" % method, "status": "partial", "notes": "Target computed at runtime; works only if it resolves to a wired method."})
            continue
        entry = METHODS.get((cls, method))
        status = "no" if entry is None else ("ok" if entry["status"] == "wired" else "partial" if entry["status"] == "partial" else "no")
        notes = "Not in hook_map.json." if entry is None else "%s%s" % (entry["status"], (": " + entry["notes"]) if entry.get("notes") else "")
        features.append({"feature": "Java hook %s#%s" % (cls, method), "status": status, "notes": notes})
    if "add_menu_item" in analyzer.self_calls:
        types = sorted(analyzer.menu_types) or ["(unknown)"]
        for menu in types:
            status = MENU_TYPES.get(menu, "partial")
            features.append({"feature": "Menu item %s" % menu, "status": status,
                             "notes": "Shown under AyuGram · Plugins in the message menu." if status != "ok" else "Message menu → AyuGram · Plugins."})
    if "create_settings" in analyzer.overrides:
        features.append({"feature": "Settings page", "status": "partial", "notes": "Values, defaults and on_change work; native rendering of the page is pending."})
    if "on_app_event" in analyzer.overrides:
        features.append({"feature": "App lifecycle events", "status": "ok", "notes": "START/RESUME/PAUSE/STOP from UIApplication."})

    for module, name, status, reason in analyzer.sdk:
        if status != "ok":
            risks.append({"item": "%s.%s" % (module, name), "status": status, "notes": reason})
    for method, count in sorted(analyzer.self_calls.items()):
        status, reason = SDK_METHODS[method]
        if status != "ok" and method != "add_hook":
            risks.append({"item": "self.%s" % method, "status": status, "notes": reason})
    for call, count in sorted(analyzer.java_calls.items()):
        risks.append({"item": "Java call %s" % call, "status": "no", "notes": "Raises UnsupportedJavaCall; the callback that makes it stops (%d site%s)." % (count, "" if count == 1 else "s")})
    for cls, count in sorted(analyzer.java_objects.items()):
        risks.append({"item": "Java object %s" % cls, "status": "partial", "notes": "Created as an opaque stub; its methods are unsupported."})
    for module in sorted(analyzer.imports):
        root = module.split(".")[0]
        if not module or is_java(module) or module in SHIM_MODULES or root in SHIM_MODULES:
            continue
        if root in IOS_UNAVAILABLE:
            risks.append({"item": "import %s" % module, "status": "no", "notes": "Not available on iOS."})
        elif root not in STDLIB:
            risks.append({"item": "import %s" % module, "status": "no", "notes": "Third-party package; pip packages are not bundled."})
    if meta.get("requirements"):
        blockers.append("Declares __requirements__ %s; pip packages are not installed on iOS." % meta["requirements"])

    verdict = grade(features)
    if verdict == "runs" and any(r["status"] == "no" for r in risks):
        verdict = "partial"
    if blockers:
        verdict = "unsupported"
    supported = sum(1 for f in features if f["status"] == "ok") + 0.5 * sum(1 for f in features if f["status"] == "partial")
    report.update(metadata=meta, verdict=verdict, coverage=round(100 * supported / len(features)) if features else 0,
                  blockers=blockers, features=features, risks=risks)
    return report


def analyze_inventory(entry):
    """Coarse grading from the static inventory (no source available)."""
    features, risks, blockers = [], [], []
    calls = set(entry.get("sdkCalls", []))
    if "add_on_send_message_hook" in calls:
        features.append({"feature": "Send-message hook", "status": "ok", "notes": ""})
    if "add_menu_item" in calls:
        features.append({"feature": "Menu items", "status": "partial", "notes": "Menu types unknown from the inventory."})
    if calls & {"hook_method", "hook_all_methods"}:
        classes = [c for c in entry.get("javaClasses", []) if c.startswith("org.telegram.")]
        wired = sorted({m["class"] for m in HOOK_MAP["methods"] if m["status"] in WIRED} & set(classes))
        features.append({"feature": "Java method hooks", "status": "partial" if wired else "no",
                         "notes": "Hooked methods unknown from the inventory. Classes with wired methods: %s." % (", ".join(wired) or "none")})
    for module in entry.get("imports", []):
        if module in SDK or module in SHIM_MODULES or is_java(module):
            continue
        root = module.split(".")[0]
        if root in IOS_UNAVAILABLE or (root not in STDLIB):
            risks.append({"item": "import %s" % module, "status": "no", "notes": "Not available on iOS."})
    android_ui = [c for c in entry.get("javaClasses", []) if c.startswith(("android.", "org.telegram.ui."))]
    if android_ui:
        risks.append({"item": "Android UI classes", "status": "no", "notes": ", ".join(android_ui[:6]) + ("…" if len(android_ui) > 6 else "")})
    if entry.get("embeddedAndroidRuntimeMarkers"):
        blockers.append("Embeds an Android DEX/JNI payload, which cannot load on iOS.")
    verdict = "unsupported" if blockers else grade(features)
    if verdict == "runs" and risks:
        verdict = "partial"
    supported = sum(1 for f in features if f["status"] == "ok") + 0.5 * sum(1 for f in features if f["status"] == "partial")
    metadata = {k.strip("_"): v for k, v in entry.get("metadata", {}).items()}
    return {"file": entry.get("file"), "sha256": entry.get("sha256"), "bytes": entry.get("bytes"), "metadata": metadata,
            "verdict": verdict, "coverage": round(100 * supported / len(features)) if features else 0,
            "blockers": blockers, "features": features, "risks": risks, "source": "inventory (no source; coarse)"}


def native_adapter(sha256):
    """Reviewed native adapters are matched by hash on import and take precedence over the runtime."""
    sys.path.insert(0, str(ROOT / "tools"))
    from analyze_plugin import REVIEWED_STATUS
    from convert_plugin import SEARCH_PLUS_SHA256
    if sha256 == SEARCH_PLUS_SHA256:
        return "Reviewed native Search+ adapter"
    return REVIEWED_STATUS.get(sha256)


def dry_run(path):
    import _ayu_host
    import tempfile
    data_dir = tempfile.mkdtemp(prefix="ayu-dry-")
    _ayu_host.configure({"dataDir": data_dir})
    reply = json.loads(_ayu_host.call(json.dumps({"op": "load", "args": {"path": str(path)}})))
    if not reply["ok"]:
        return {"loaded": False, "error": reply["error"]}
    result = reply["result"]
    _ayu_host.unload({"id": result["id"]})
    return {"loaded": True, "sendHook": result["sendHook"], "menuItems": len(result["menuItems"]),
            "diagnostics": result["diagnostics"], "errors": result["errors"]}


def markdown(reports):
    icon = {"runs": "✅ runs", "partial": "🟡 partial", "unsupported": "⛔ unsupported"}
    mark = {"ok": "✅", "partial": "🟡", "no": "⛔"}
    lines = ["# exteraGram plugin compatibility (AyuGram iOS Python runtime)", "",
             "Generated by `tools/plugin_compat_report.py` from runtime/hook_map.json (version %s). Static analysis unless a dry run is listed." % HOOK_MAP.get("version"), "",
             "| Plugin | Version | Verdict | Coverage | Blockers / main gaps |", "|---|---|---|---|---|"]
    for r in reports:
        meta = r.get("metadata", {})
        gaps = r["blockers"] or [f["feature"] for f in r["features"] if f["status"] == "no"][:3] or [x["item"] for x in r["risks"] if x["status"] == "no"][:3]
        verdict = icon[r["verdict"]] + (" (native adapter)" if r.get("nativeAdapter") else "")
        lines.append("| %s (`%s`) | %s | %s | %d%% | %s |" % (meta.get("name", r["file"]), r["file"], meta.get("version", "?"), verdict,
                                                      r["coverage"], "; ".join(gaps).replace("|", "\\|") or "—"))
    for r in reports:
        meta = r.get("metadata", {})
        lines += ["", "## %s" % meta.get("name", r["file"]), "",
                  "`%s` · %s bytes · sha256 `%s`%s" % (r["file"], r.get("bytes"), r.get("sha256"), " · " + r["source"] if r.get("source") else ""), "",
                  "**Verdict: %s** (coverage %d%%)" % (icon[r["verdict"]], r["coverage"])]
        if r.get("nativeAdapter"):
            lines += ["", "Imported through its native adapter instead of the Python runtime: %s." % r["nativeAdapter"]]
        for blocker in r["blockers"]:
            lines.append("- ⛔ %s" % blocker)
        if r["features"]:
            lines += ["", "| Feature | Status | Notes |", "|---|---|---|"]
            lines += ["| %s | %s | %s |" % (f["feature"], mark[f["status"]], f["notes"].replace("|", "\\|")) for f in r["features"]]
        if r["risks"]:
            lines += ["", "Calls and imports:", ""]
            lines += ["- %s %s: %s" % (mark[x["status"]], x["item"], x["notes"]) for x in r["risks"]]
        if r.get("dryRun"):
            d = r["dryRun"]
            lines += ["", "Dry run: %s" % ("loaded" if d["loaded"] else "failed: " + d["error"])]
            if d.get("errors"):
                lines += ["- runtime error: %s" % e for e in d["errors"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sources", nargs="*", type=Path)
    parser.add_argument("--inventory", type=Path, action="append", default=[])
    parser.add_argument("--dry-run", action="store_true", help="Execute on_plugin_load with the mock bridge (runs plugin code!)")
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    reports = []
    for source in args.sources:
        report = analyze_source(source)
        if args.dry_run and not report["blockers"]:
            report["dryRun"] = dry_run(source)
        reports.append(report)
    for inventory in args.inventory:
        reports += [analyze_inventory(e) for e in json.loads(inventory.read_text(encoding="utf-8"))]
    for report in reports:
        report["nativeAdapter"] = native_adapter(report.get("sha256"))
    if args.json:
        args.json.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = markdown(reports)
    if args.markdown:
        args.markdown.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
