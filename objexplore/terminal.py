from blessed import Terminal as BlessedTerminal


class Terminal(BlessedTerminal):
    def __init__(self, stack, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stack = stack
        self.explorer_size_extra = 0

    def increase_explorer_size(self):
        # if self.explorer_panel_width + self.explorer_size_extra < self.width:
        if self.width - self.explorer_panel_width > 20:
            self.explorer_size_extra += 1

    def decrease_explorer_size(self):
        if self.explorer_panel_width + self.explorer_size_extra > 10:
            self.explorer_size_extra -= 1

    @property
    def explorer_panel_width(self):
        ...

    @property
    def explorer_panel_height(self):
        if self.stack.visible:
            return (self.height - 10) // 2
        else:
            return self.height - 6
