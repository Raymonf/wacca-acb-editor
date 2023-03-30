class MissingDependencyError(RuntimeError):
    """Raised when one or more dependencies are missing"""


class AudioPreprocessorError(RuntimeError):
    """Raised when the audio preprocessor encounters an error"""
