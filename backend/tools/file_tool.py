# File Tool placeholder (read_file / write_file)
def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str) -> bool:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True
