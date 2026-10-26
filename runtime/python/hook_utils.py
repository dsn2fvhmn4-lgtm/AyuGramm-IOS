"""exteraGram `hook_utils` on the AyuGram iOS runtime.

There are no Java objects on iOS, so reflection reads and writes only work on
the Python fields of stub objects. Reads of anything else return None, as the
Android helpers do on failure.
"""
import _ayu_java

find_class = _ayu_java.find_class


def get_private_field(obj, field_name):
    _ayu_java.note("reflection", "get_private_field:" + str(field_name))
    try:
        value = getattr(obj, field_name)
    except Exception:
        return None
    return None if isinstance(value, _ayu_java.JavaMember) else value


def set_private_field(obj, field_name, new_value):
    _ayu_java.note("reflection", "set_private_field:" + str(field_name))
    try:
        setattr(obj, field_name, new_value)
        return True
    except Exception:
        return False


def get_static_private_field(clazz, field_name):
    _ayu_java.note("reflection", "get_static_private_field:" + str(field_name))
    value = _ayu_java.STATIC_IMPLEMENTATIONS.get(getattr(clazz, "name", ""), {}).get(field_name)
    return None if callable(value) else value


def set_static_private_field(clazz, field_name, new_value):
    _ayu_java.note("reflection", "set_static_private_field:" + str(field_name))
    return False
