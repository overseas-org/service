
class Stage:
    def __init__(self, name):
        self.name = name
        self.steps = []
        self.varriables = []
        self.credentials = []
        self.groovy = ""

    def to_groovy(self):
        groovy_str = ""
        if self.steps:
            groovy_str = f"\n\t\tstage('{self.name}') {{"
            groovy_str += "\n\t\t\tsteps {"
            for step in self.steps:
                if isinstance(step, str):
                    groovy_str += f"\n\t\t\t\t{step}"
                else:
                    groovy_str += step.to_groovy()
            groovy_str += "\n\t\t\t}"
            groovy_str += "\n\t\t}"
        return groovy_str
