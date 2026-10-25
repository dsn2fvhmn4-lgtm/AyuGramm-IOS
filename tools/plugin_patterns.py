"""Static whole-file Android plugin patterns. Never imports or executes plugin code."""
import ast
import hashlib

TEMPLATE_ID = 'exteraGram/literal-send-hook-v1'
LIMITATIONS = [
    'Automatic literal replacements apply to plain cloud text only. Entity-bearing/formatted text (including links), media captions, secret chats and forwards are unchanged.',
    'Replacement must be nonempty and must not expand UTF-8 or UTF-16 length. Enabled plugins run in installation order.',
    'This file matched the complete literal-send-hook template. Python, Java, Xposed, external dependencies and additional statements are not executed.',
]


def require(value, message='No complete iOS template for this source'):
    if not value:
        raise ValueError(message)


def is_name(node, name):
    return isinstance(node, ast.Name) and node.id == name


def attribute(node, owner, name):
    return isinstance(node, ast.Attribute) and is_name(node.value, owner) and node.attr == name


def literal(node):
    require(isinstance(node, ast.Constant) and isinstance(node.value, str), 'Only literal strings are supported')
    return node.value


def return_value(node, modify=True):
    require(isinstance(node, ast.Return) and isinstance(node.value, ast.Call))
    call = node.value
    require(is_name(call.func, 'HookResult') and not call.args)
    if not modify:
        require(not call.keywords)
        return
    require([item.arg for item in call.keywords] == ['strategy', 'params'])
    require(attribute(call.keywords[0].value, 'HookStrategy', 'MODIFY') and is_name(call.keywords[1].value, 'params'))


def compile_source(data):
    require(0 < len(data) <= 65536, 'Template source limit is 64 KB')
    text = data.decode('utf-8')
    require('\0' not in text and '\t' not in text and len(text.splitlines()) <= 512)
    require(all(len(line.encode('utf-8')) <= 4096 for line in text.splitlines()), 'Line exceeds template limit')
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        raise ValueError(f'Unsupported source syntax at line {error.lineno}') from None
    body = list(tree.body)
    require(body and isinstance(body[0], ast.ImportFrom))
    imports = body.pop(0)
    require(imports.module == 'base_plugin' and imports.level == 0 and len(imports.names) == 3)
    require(all(item.asname is None for item in imports.names))
    require({item.name for item in imports.names} == {'BasePlugin', 'HookResult', 'HookStrategy'})
    has_typing = False
    if body and isinstance(body[0], ast.ImportFrom):
        item = body.pop(0)
        require(item.module == 'typing' and item.level == 0 and len(item.names) == 1 and item.names[0].name == 'Any' and item.names[0].asname is None)
        has_typing = True
    metadata = {}
    keys = {'__id__', '__name__', '__author__', '__version__', '__description__', '__icon__', '__min_version__', '__app_version__', '__sdk_version__'}
    while body and isinstance(body[0], ast.Assign):
        item = body.pop(0)
        require(len(item.targets) == 1 and isinstance(item.targets[0], ast.Name))
        key = item.targets[0].id
        require(key in keys and key not in metadata)
        metadata[key] = literal(item.value)
    require(len(body) == 1 and isinstance(body[0], ast.ClassDef))
    plugin = body[0]
    require(plugin.name not in {'BasePlugin', 'HookResult', 'HookStrategy', 'Any'}, 'Plugin class must not shadow SDK names')
    require(not getattr(plugin, 'type_params', []))
    require(len(plugin.bases) == 1 and is_name(plugin.bases[0], 'BasePlugin') and not plugin.decorator_list and not plugin.keywords)
    require(len(plugin.body) == 2 and all(isinstance(item, ast.FunctionDef) for item in plugin.body))
    load, send = plugin.body
    for method, name, args in [(load, 'on_plugin_load', ['self']), (send, 'on_send_message_hook', ['self', 'account', 'params'])]:
        require(method.name == name and not method.decorator_list and not getattr(method, 'type_params', []))
        require([item.arg for item in method.args.args] == args)
        plain = method.returns is None and all(item.annotation is None for item in method.args.args)
        typed_load = name == 'on_plugin_load' and isinstance(method.returns, ast.Constant) and method.returns.value is None and method.args.args[0].annotation is None
        typed_send = name == 'on_send_message_hook' and is_name(method.returns, 'HookResult') and method.args.args[0].annotation is None and is_name(method.args.args[1].annotation, 'int') and is_name(method.args.args[2].annotation, 'Any')
        require(plain or typed_load or (typed_send and has_typing))
        require(not method.args.posonlyargs and not method.args.kwonlyargs and not method.args.vararg and not method.args.kwarg and not method.args.defaults)
    require(len(load.body) == 1 and isinstance(load.body[0], ast.Expr) and isinstance(load.body[0].value, ast.Call))
    call = load.body[0].value
    require(attribute(call.func, 'self', 'add_on_send_message_hook') and not call.args and not call.keywords)
    actions_body = send.body
    prefix = None
    if actions_body and isinstance(actions_body[0], ast.If):
        require(len(actions_body) == 2)
        condition = actions_body[0]
        call = condition.test
        require(not condition.orelse and isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute))
        require(attribute(call.func.value, 'params', 'message') and call.func.attr == 'startswith' and len(call.args) == 1 and not call.keywords)
        prefix = literal(call.args[0])
        return_value(actions_body[1], modify=False)
        actions_body = condition.body
        require(len(actions_body) == 2, 'Conditional templates support one replacement')
    require(2 <= len(actions_body) <= 9)
    return_value(actions_body[-1])
    actions = []
    for item in actions_body[:-1]:
        require(isinstance(item, ast.Assign) and len(item.targets) == 1 and attribute(item.targets[0], 'params', 'message'))
        call = item.value
        require(isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute))
        require(attribute(call.func.value, 'params', 'message') and call.func.attr == 'replace' and len(call.args) == 2 and not call.keywords)
        find, replacement = map(literal, call.args)
        utf16 = lambda value: len(value.encode('utf-16-le')) // 2
        require(0 < len(find.encode()) <= 128 and replacement and len(replacement.encode()) <= len(find.encode()) and utf16(replacement) <= utf16(find), 'Automatic replacements must be nonempty and nonexpanding')
        require(prefix is None or len(prefix.encode()) <= 128)
        action = dict(id=f'send_{len(actions)}', title='Outgoing text replacement', kind='outgoingReplace', find=find, replacement=replacement)
        if prefix is not None:
            action['prefix'] = prefix
        actions.append(action)
    require('__id__' in metadata and '__name__' in metadata)
    require(0 < len(metadata['__id__']) <= 64 and all(char in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for char in metadata['__id__']))
    for key, limit in [('__name__', 64), ('__author__', 128), ('__version__', 32), ('__description__', 2048)]:
        require(len(metadata.get(key, '')) <= limit)
    require(bool(metadata['__name__']) and bool(metadata.get('__author__', 'Unknown')) and bool(metadata.get('__version__', '1.0')))
    return dict(format='ayugram-ios-plugin', apiVersion=1, id=metadata['__id__'], name=metadata['__name__'], author=metadata.get('__author__', 'Unknown'), version=metadata.get('__version__', '1.0'), summary=metadata.get('__description__', 'Converted outgoing-text hook'), actions=actions, convertedFrom=TEMPLATE_ID, sourceSHA256=hashlib.sha256(data).hexdigest(), limitations=LIMITATIONS)
