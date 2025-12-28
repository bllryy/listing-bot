import os

def count_lines():
    file_count = 0
    total_lines = 0
    for root, dirs, files in os.walk("."):
        for file in files:

            if ".git" in root or ".idea" in root or "venv" in root:
                continue

            if not file.endswith(".py"):
                continue

            try:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    file_count += 1
            except UnicodeDecodeError:
                pass

    return total_lines, file_count

if __name__ == "__main__":
    print(count_lines())