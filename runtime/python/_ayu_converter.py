"""Whole-file AST conversion to bounded native text programs, without exec/eval."""
import ast
import hashlib

CONVERTER_ID = 'exteraGram/ast-send-hook-v2'


def require(value, message):
    if not value:
        raise ValueError(message)


def name(node, value):
    return isinstance(node, ast.Name) and node.id == value


def attribute(node, owner, field):
    return isinstance(node, ast.Attribute) and name(node.value, owner) and node.attr == field


def literal(node):
    require(isinstance(node, ast.Constant) and type(node.value) is str, 'Expected a literal string')
    require(len(node.value.encode()) <= 128, 'Text operand exceeds 128 bytes')
    return node.value


def text_reference(node, alias):
    return attribute(node, 'params', 'message') if alias is None else name(node, alias)


def expression(node, alias):
    if text_reference(node, alias):
        return []
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        if isinstance(node.left, ast.Constant):
            value = literal(node.left)
            return expression(node.right, alias) + ([dict(op='prepend', value=value)] if value else [])
        value = literal(node.right)
        return expression(node.left, alias) + ([dict(op='append', value=value)] if value else [])
    require(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and not node.keywords,
            'Unsupported text expression')
    result = expression(node.func.value, alias)
    method = node.func.attr
    if method in ('lower', 'upper', 'strip'):
        require(not node.args, method + ' accepts no arguments in this converter')
        return result + [dict(op=method)]
    if method in ('removeprefix', 'removesuffix'):
        require(len(node.args) == 1, 'Expected one prefix/suffix')
        value = literal(node.args[0])
        return result + ([dict(op='removePrefix' if method == 'removeprefix' else 'removeSuffix', value=value)] if value else [])
    require(method == 'replace' and len(node.args) in (2, 3), 'Unsupported string method: ' + method)
    find, value = literal(node.args[0]), literal(node.args[1])
    require(bool(find), 'Empty replacement patterns are not supported')
    instruction = dict(op='replace', find=find, value=value)
    if len(node.args) == 3:
        count = node.args[2]
        require(isinstance(count, ast.Constant) and type(count.value) is int and 0 <= count.value <= 4096,
                'Replacement count must be 0...4096')
        instruction['count'] = count.value
    return result + [instruction]


def condition(node, alias):
    negated = False
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        negated = True
        node = node.operand
    if isinstance(node, ast.Call):
        require(isinstance(node.func, ast.Attribute) and text_reference(node.func.value, alias)
                and len(node.args) == 1 and not node.keywords and node.func.attr in ('startswith', 'endswith'),
                'Unsupported branch condition')
        kind = 'prefix' if node.func.attr == 'startswith' else 'suffix'
        value = literal(node.args[0])
    else:
        require(isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1,
                'Unsupported branch condition')
        op = node.ops[0]
        if isinstance(op, (ast.In, ast.NotIn)):
            require(text_reference(node.comparators[0], alias), 'Expected a text membership test')
            kind, value = 'contains', literal(node.left)
            negated ^= isinstance(op, ast.NotIn)
        else:
            require(isinstance(op, (ast.Eq, ast.NotEq)) and text_reference(node.left, alias), 'Unsupported comparison')
            kind, value = 'equals', literal(node.comparators[0])
            negated ^= isinstance(op, ast.NotEq)
    return dict(kind=kind, value=value, negated=negated)


def statements(nodes, alias, depth=0):
    require(depth <= 4, 'Branch nesting exceeds four levels')
    program = []
    for node in nodes:
        if isinstance(node, ast.If):
            body = statements(node.body, alias, depth + 1)
            require(bool(body), 'Empty branches are not supported')
            item = dict(op='branch', condition=condition(node.test, alias), body=body)
            if node.orelse:
                item['otherwise'] = statements(node.orelse, alias, depth + 1)
            program.append(item)
        else:
            require(isinstance(node, ast.Assign) and len(node.targets) == 1 and text_reference(node.targets[0], alias),
                    'Only assignments to the outgoing text and supported if/else branches are converted')
            program.extend(expression(node.value, alias))
    return program


def return_hook(node, modify):
    require(isinstance(node, ast.Return) and isinstance(node.value, ast.Call), 'Expected HookResult return')
    call = node.value
    require(name(call.func, 'HookResult') and not call.args, 'Expected HookResult return')
    if not modify:
        require(not call.keywords, 'Expected an unchanged HookResult')
    else:
        require({k.arg for k in call.keywords} == {'strategy', 'params'} and len(call.keywords) == 2,
                'Only HookStrategy.MODIFY is converted')
        arguments = {k.arg: k.value for k in call.keywords}
        require(attribute(arguments['strategy'], 'HookStrategy', 'MODIFY') and name(arguments['params'], 'params'),
                'Only HookStrategy.MODIFY with params is converted')


def without_docstring(nodes):
    return nodes[1:] if nodes and isinstance(nodes[0], ast.Expr) and isinstance(nodes[0].value, ast.Constant) and isinstance(nodes[0].value.value, str) else nodes


def compile_source(source):
    require(isinstance(source, str) and 0 < len(source.encode()) <= 65536 and '\0' not in source,
            'Plugin source limit is 64 KB')
    require(len(source.splitlines()) <= 1024, 'Plugin exceeds 1024 lines')
    tree = ast.parse(source[1:] if source.startswith("\ufeff") else source)
    require(sum(1 for _ in ast.walk(tree)) <= 4096, 'Plugin AST exceeds 4096 nodes')
    metadata = {}
    plugin = None
    sdk = set()
    keys = {'__id__', '__name__', '__author__', '__version__', '__description__', '__icon__', '__app_version__', '__sdk_version__', '__min_version__'}
    for node in without_docstring(tree.body):
        if isinstance(node, ast.ImportFrom):
            require(node.level == 0 and all(n.asname is None for n in node.names), 'Relative/aliased imports are not converted')
            imported = {n.name for n in node.names}
            if node.module == 'base_plugin':
                require(imported <= {'BasePlugin', 'HookResult', 'HookStrategy'}, 'Unsupported SDK import')
                sdk.update(imported)
            else:
                require(node.module == 'typing' and imported <= {'Any', 'Optional', 'Dict'}, 'Plugin dependency has no native mapping')
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            key = node.targets[0].id
            require(key in keys and key not in metadata, 'Unsupported or duplicate top-level assignment')
            require(isinstance(node.value, ast.Constant) and type(node.value.value) is str, 'Metadata must be literal strings')
            metadata[key] = node.value.value
        elif isinstance(node, ast.ClassDef):
            require(plugin is None, 'Only one plugin class is supported')
            plugin = node
        else:
            raise ValueError('Top-level executable code has no native mapping')
    require(sdk == {'BasePlugin', 'HookResult', 'HookStrategy'} and plugin is not None, 'Missing plugin SDK or class')
    require(not plugin.decorator_list and not plugin.keywords and not getattr(plugin, 'type_params', [])
            and len(plugin.bases) == 1 and name(plugin.bases[0], 'BasePlugin')
            and plugin.name not in sdk | {'str', 'isinstance', 'int'}, 'Unsupported plugin class')
    methods = {}
    for method in without_docstring(plugin.body):
        require(isinstance(method, ast.FunctionDef) and method.name not in methods and not method.decorator_list
                and not getattr(method, 'type_params', []), 'Unsupported class body')
        require(not method.args.defaults and not method.args.kw_defaults and not method.args.kwonlyargs
                and not method.args.posonlyargs and method.args.vararg is None and method.args.kwarg is None,
                'Unsupported method parameters')
        for annotation in [method.returns] + [argument.annotation for argument in method.args.args]:
            if annotation is not None:
                require(all(isinstance(part, (ast.Name, ast.Load, ast.Constant, ast.Subscript, ast.Tuple))
                            for part in ast.walk(annotation)), 'Executable annotations have no native mapping')
        methods[method.name] = method
    require(set(methods) == {'on_plugin_load', 'on_send_message_hook'}, 'Extra plugin methods need a native mapping')
    load, send = methods['on_plugin_load'], methods['on_send_message_hook']
    require([a.arg for a in load.args.args] == ['self'] and [a.arg for a in send.args.args] == ['self', 'account', 'params'],
            'Unexpected hook parameters')
    load_body = without_docstring(load.body)
    require(len(load_body) == 1 and isinstance(load_body[0], ast.Expr) and isinstance(load_body[0].value, ast.Call),
            'Unsupported plugin initialization')
    call = load_body[0].value
    require(attribute(call.func, 'self', 'add_on_send_message_hook') and not call.args and not call.keywords,
            'Unsupported plugin initialization')
    body = without_docstring(send.body)
    require(bool(body), 'Empty send hook')
    # Common Android guard: the native seam already accepts plain strings only.
    if isinstance(body[0], ast.If) and isinstance(body[0].test, ast.UnaryOp) and isinstance(body[0].test.op, ast.Not):
        guard = body[0]
        test = guard.test.operand
        if isinstance(test, ast.Call) and name(test.func, 'isinstance'):
            require(not guard.orelse and len(guard.body) == 1 and not test.keywords and len(test.args) == 2
                    and attribute(test.args[0], 'params', 'message') and name(test.args[1], 'str'), 'Unsupported type guard')
            return_hook(guard.body[0], False)
            body = body[1:]
    require(bool(body), 'Empty send hook')
    return_hook(body[-1], True)
    body = body[:-1]
    alias = None
    if body and isinstance(body[0], ast.Assign) and len(body[0].targets) == 1 and isinstance(body[0].targets[0], ast.Name):
        first = body.pop(0)
        alias = first.targets[0].id
        require(alias not in {'self', 'account', 'params', 'HookResult', 'HookStrategy', 'str', 'isinstance', 'int'}
                and attribute(first.value, 'params', 'message'), 'Unsupported local text binding')
        require(body and isinstance(body[-1], ast.Assign) and len(body[-1].targets) == 1
                and attribute(body[-1].targets[0], 'params', 'message') and name(body[-1].value, alias),
                'Local text must be committed to params.message before return')
        body = body[:-1]
    program = statements(body, alias)
    def size(items):
        return sum(1 + size(i.get('body', [])) + size(i.get('otherwise', [])) for i in items)
    require(bool(program) and size(program) <= 64, 'Native text program must contain 1...64 instructions')
    plugin_id, title = metadata.get('__id__', ''), metadata.get('__name__', '')
    require(0 < len(plugin_id) <= 64 and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in plugin_id), 'Invalid plugin ID')
    require(0 < len(title) <= 64, 'Invalid plugin name')
    for key, limit in [('__author__', 128), ('__version__', 32), ('__description__', 2048)]:
        require(len(metadata.get(key, '')) <= limit, 'Metadata exceeds native limit')
    require(bool(metadata.get('__author__', 'Unknown')) and bool(metadata.get('__version__', '1.0')), 'Empty author/version')
    return dict(format='ayugram-ios-plugin', apiVersion=6, id=plugin_id, name=title,
                author=metadata.get('__author__', 'Unknown'), version=metadata.get('__version__', '1.0'),
                summary=metadata.get('__description__', ''),
                actions=[dict(id='send_program', title='Converted outgoing text', kind='outgoingReplace', program=dict(instructions=program))],
                convertedFrom=CONVERTER_ID, sourceSHA256=hashlib.sha256(source.encode()).hexdigest(), limitations=[
                    'Converted to a native text program. Original plugin code is not executed.',
                    'Plain cloud text only; formatted text, media captions, forwards and secret chats are unchanged.',
                    'Output is limited to 8192 UTF-8 bytes and 4096 UTF-16 units. Empty/oversized results retain the original text.',
                    'Only the mapped operations are supported; Java views, external dependencies and other hooks are rejected.',
                ])
