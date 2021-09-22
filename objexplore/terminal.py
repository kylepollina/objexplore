from blessed import Terminal as BlessedTerminal


class Terminal(BlessedTerminal):
    def __init__(self, stack, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stack = stack

    @property
    def explorer_panel_width(self):
        return self.width // 4

    @property
    def explorer_panel_height(self):
        if self.stack.visible:
            return (self.height - 10) // 2
        else:
            return self.height - 6
