import re

import py_cui
from py_cui.keys import get_ascii_from_char


class SimplishMenu:
    # Match any keys in square brackets:
    HOTKEY_REGEX = r'\[(.*?)\]'

    def __init__(self, title, items, row=0, column=0, root=None):
        items = list(items)
        row_span = len(items)
        column_span = max(len(item) for item in items)

        if root is None:
            root = py_cui.PyCUI(row_span+1, column_span+1, auto_focus_buttons=True, exit_key=None)

        self.menu = root.add_scroll_menu(title, row, column, row_span + 1, column_span)
        self.menu.add_key_command(py_cui.keys.KEY_ENTER, lambda: self.choose_item(self.menu.get()))

        # Hotkeys
        self.menu.add_text_color_rule(self.HOTKEY_REGEX, py_cui.RED_ON_BLACK, 'contains', match_type='regex')
        for item in items:
            self.add_item(item)
        self.root = root
        self.root.move_focus(self.menu)

    def choose_item(self, item):
        if self.menu.get() != item:
            # If item was chosen via hotkey, select it
            self.menu.set_selected_item(item)

        self.root.stop()

    @classmethod
    def get_hotkeys(cls, item):
        return ''.join(re.findall(cls.HOTKEY_REGEX, item)).lower()

    def add_item(self, item):
        hotkeys = self.get_hotkeys(item)
        for hotkey in hotkeys:
            self.menu.add_key_command(get_ascii_from_char(hotkey), lambda: self.choose_item(item))
        self.menu.add_item(item)

    def get(self):
        return self.menu.get()

    def show(self):
        self.root.move_focus(self.menu)
        self.root.start()


def choose_option(title, items):
    menu = SimplishMenu(title, items)
    menu.root.start()
    return menu.get()


if __name__ == '__main__':
    option = choose_option('Main Menu', ['Option [1]', 'Option [2]'])
    print("Chose: ", option)
