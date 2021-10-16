import sys

def display_progress_bar(
    file_count: int,
    total_count: int,
    char: str = "█",
    scale: float = 0.55
) -> None:
    max_width = int(100 * scale)
    filled = int(round(max_width * file_count / float(total_count)))
    remaining = max_width - filled
    progress_bar = char * filled + " " * remaining
    percent = round(100.0 * file_count / float(total_count), 1)
    text = f"  |{progress_bar}| {percent}% ({file_count}/{total_count})\r"
    sys.stdout.write(text)
