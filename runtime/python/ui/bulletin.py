"""exteraGram `ui.bulletin` on the AyuGram iOS runtime: native toasts."""
import _ayu_bridge
import _ayu_java


def _show(kind, text, subtitle=None, button=None):
    _ayu_bridge.call("bulletin.show", plugin=_ayu_java.current_plugin(), kind=kind, text=str(text), subtitle=subtitle, button=button)


class BulletinHelper:
    DURATION_SHORT = 1500
    DURATION_LONG = 2750
    DURATION_PROLONG = 5000

    @staticmethod
    def show_info(message, fragment=None):
        _show("info", message)

    @staticmethod
    def show_error(message, fragment=None):
        _show("error", message)

    @staticmethod
    def show_success(message, fragment=None):
        _show("success", message)

    @staticmethod
    def show_simple(text, icon_res_id=0, fragment=None):
        _show("info", text)

    @staticmethod
    def show_two_line(title, subtitle, icon_res_id=0, fragment=None):
        _show("info", title, subtitle=str(subtitle))

    @staticmethod
    def show_with_button(text, icon_res_id, button_text, on_click, fragment=None, duration=DURATION_PROLONG):
        # Bulletin buttons need a native callback round trip; shown without it for now.
        _ayu_java.note("unsupportedSdk", "BulletinHelper.show_with_button:callback")
        _show("info", text)

    @staticmethod
    def show_undo(text, on_undo, on_action=None, subtitle=None, fragment=None):
        _ayu_java.note("unsupportedSdk", "BulletinHelper.show_undo:callback")
        _show("info", text, subtitle=subtitle)
        if on_action is not None:
            on_action()

    @staticmethod
    def show_copied_to_clipboard(message=None, fragment=None):
        _show("copied", message or "")

    @staticmethod
    def show_link_copied(is_private_link_info=False, fragment=None):
        _show("copied", "")

    @staticmethod
    def show_file_saved_to_gallery(is_video=False, amount=1, fragment=None):
        _show("success", "")

    @staticmethod
    def show_file_saved_to_downloads(file_type_enum_name="UNKNOWN", amount=1, fragment=None):
        _show("success", "")
