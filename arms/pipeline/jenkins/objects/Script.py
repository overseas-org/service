

class Script:
    def __init__(self):
        self.commands = []

    def to_groovy(self):
        groovy_str = f"\n\t\t\t\tscript{{"
        for command in self.commands:
            groovy_str += f"\n\t\t\t\t\t{command}"
        groovy_str += "\n\t\t\t\t}"
        return groovy_str