class PreprocessResult:
    path: str
    orig_filename: str
    delete: bool
    sample_count: int
    sample_rate: int
    length_ms: int

    new_index: int | None = None

    def __init__(self, path: str, orig_filename: str, delete: bool, sample_count: int, sample_rate: int, length_ms: int):
        self.path = path
        self.orig_filename = orig_filename
        self.delete = delete
        self.sample_count = sample_count
        self.sample_rate = sample_rate
        self.length_ms = length_ms
