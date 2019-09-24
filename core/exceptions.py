class ConfigurationError(Exception):
    pass

class OverwriteError(Exception):
    pass

class PrerequisiteError(Exception):
    pass

class CommandLineError(Exception):
    pass

class FatalError(Exception):
    pass
