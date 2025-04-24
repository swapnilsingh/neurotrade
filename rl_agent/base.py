class BaseAgent:
    def __init__(self, name="BaseAgent"):
        self.name = name

    def vote(self, state):
        raise NotImplementedError("Subclasses must implement this method")
