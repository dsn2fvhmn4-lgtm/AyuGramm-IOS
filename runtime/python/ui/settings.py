"""exteraGram `ui.settings` on the AyuGram iOS runtime.

Each item serializes to a schema the native plugin page renders. Callbacks
(`on_change`, `on_click`) stay in Python and run when the host reports a
change or tap.
"""


class _Item:
    kind = "item"
    fields = ()

    def __init__(self, **kwargs):
        for name in self.fields:
            setattr(self, name, kwargs.pop(name, None))
        self.on_change = kwargs.pop("on_change", None)
        self.on_click = kwargs.pop("on_click", None)
        self.on_long_click = kwargs.pop("on_long_click", None)
        self.create_sub_fragment = kwargs.pop("create_sub_fragment", None)
        self.unsupported = sorted(k for k in kwargs if k not in ("icon", "link_alias", "accent", "red"))
        self.extra = kwargs

    def schema(self):
        result = {"type": self.kind}
        for name in self.fields:
            value = getattr(self, name)
            if value is not None:
                result[name] = value
        if self.on_click is not None or self.create_sub_fragment is not None:
            result["clickable"] = True
        for flag in ("accent", "red"):
            if self.extra.get(flag):
                result[flag] = True
        return result


class Header(_Item):
    kind = "header"
    fields = ("text",)

    def __init__(self, text=None, **kwargs):
        super().__init__(text=text, **kwargs)


class Divider(_Item):
    kind = "divider"
    fields = ("text",)

    def __init__(self, text=None, **kwargs):
        super().__init__(text=text, **kwargs)


class Switch(_Item):
    kind = "switch"
    fields = ("key", "text", "default", "subtext")

    def __init__(self, key=None, text=None, default=False, **kwargs):
        super().__init__(key=key, text=text, default=bool(default), **kwargs)


class Selector(_Item):
    kind = "selector"
    fields = ("key", "text", "default", "items")

    def __init__(self, key=None, text=None, default=0, items=None, **kwargs):
        super().__init__(key=key, text=text, default=int(default), items=[str(i) for i in (items or [])], **kwargs)


class Input(_Item):
    kind = "input"
    fields = ("key", "text", "default", "subtext")

    def __init__(self, key=None, text=None, default="", **kwargs):
        super().__init__(key=key, text=text, default=str(default or ""), **kwargs)


class EditText(_Item):
    kind = "edittext"
    fields = ("key", "hint", "default", "multiline", "max_length")

    def __init__(self, key=None, hint=None, default="", multiline=False, max_length=None, **kwargs):
        kwargs.pop("mask", None)
        super().__init__(key=key, hint=hint, default=str(default or ""), multiline=bool(multiline), max_length=max_length, **kwargs)


class Text(_Item):
    kind = "text"
    fields = ("text", "subtext", "default")

    def __init__(self, text=None, default=None, **kwargs):
        super().__init__(text=text, default=default, **kwargs)


class Custom(_Item):
    kind = "custom"
    fields = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.unsupported = ["view"]
