"""exteraGram `ui.alert` on the AyuGram iOS runtime.

The dialog is described to the host as data and shown as a native alert or
action sheet. Button and item listeners are kept as Python callbacks the host
invokes when the user taps.
"""
import _ayu_bridge
import _ayu_java


class AlertDialogBuilder:
    ALERT_TYPE_MESSAGE = 0
    ALERT_TYPE_LOADING = 2
    ALERT_TYPE_SPINNER = 3
    BUTTON_POSITIVE = -1
    BUTTON_NEGATIVE = -2
    BUTTON_NEUTRAL = -3

    def __init__(self, context=None, progress_style=ALERT_TYPE_MESSAGE, resources_provider=None):
        self.owner = _ayu_java.current_plugin()
        self.style = progress_style
        self.title = None
        self.message = None
        self.items = None
        self.items_listener = None
        self.buttons = {}
        self.red = set()
        self.cancelable = True
        self.on_dismiss = None
        self.on_cancel = None
        self.dialog_id = None
        self.progress = 0
        self._shown = False

    def set_title(self, title):
        self.title = str(title)
        return self

    def set_message(self, message):
        self.message = str(message)
        return self

    def set_message_text_view_clickable(self, clickable):
        return self

    def set_view(self, view, height=-2):
        _ayu_java.note("unsupportedSdk", "AlertDialogBuilder.set_view")
        return self

    def set_items(self, items, listener=None, icons=None):
        self.items = [str(i) for i in items]
        self.items_listener = listener
        return self

    def set_positive_button(self, text, listener=None):
        self.buttons[self.BUTTON_POSITIVE] = (str(text), listener)
        return self

    def set_negative_button(self, text, listener=None):
        self.buttons[self.BUTTON_NEGATIVE] = (str(text), listener)
        return self

    def set_neutral_button(self, text, listener=None):
        self.buttons[self.BUTTON_NEUTRAL] = (str(text), listener)
        return self

    def make_button_red(self, button_type):
        self.red.add(button_type)
        return self

    def get_button(self, button_type):
        return None

    def set_on_back_button_listener(self, listener):
        return self

    def set_on_dismiss_listener(self, listener):
        self.on_dismiss = listener
        return self

    def set_on_cancel_listener(self, listener):
        self.on_cancel = listener
        return self

    def set_cancelable(self, cancelable):
        self.cancelable = bool(cancelable)
        return self

    def set_canceled_on_touch_outside(self, cancel):
        return self

    def set_top_image(self, *args, **kwargs):
        return self

    set_top_drawable = set_top_animation = set_dim_enabled = set_dialog_button_color_key = set_blurred_background = set_top_image

    def create(self):
        return self

    def _callback(self, fn, kind):
        if fn is None:
            return None

        def invoke(value=None):
            if kind == "dismiss":
                fn(self)
            else:
                fn(self, value)
        return _ayu_bridge.register_callback(self.owner, invoke)

    def show(self):
        if self._shown:
            return self
        self._shown = True
        buttons = []
        for which in (self.BUTTON_NEGATIVE, self.BUTTON_NEUTRAL, self.BUTTON_POSITIVE):
            if which in self.buttons:
                text, listener = self.buttons[which]
                buttons.append({"which": which, "text": text, "destructive": which in self.red,
                                "callback": self._callback(listener, "button")})
        self.dialog_id = _ayu_bridge.call(
            "alert.show", plugin=self.owner, title=self.title, message=self.message,
            items=self.items, itemsCallback=self._callback(self.items_listener, "item"),
            buttons=buttons, cancelable=self.cancelable,
            spinner=self.style in (self.ALERT_TYPE_LOADING, self.ALERT_TYPE_SPINNER),
            dismissCallback=self._callback(self.on_dismiss, "dismiss"))
        return self

    def set_progress(self, progress):
        self.progress = int(progress)

    def dismiss(self):
        if self.dialog_id is not None:
            _ayu_bridge.call("alert.dismiss", id=self.dialog_id)
            self.dialog_id = None

    def get_dialog(self):
        return self if self.dialog_id is not None else None
