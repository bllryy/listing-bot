import os

def map_python_files():
    # Create or clear map.txt
    with open('map.txt', 'w', encoding='utf-8') as map_file:
        # Walk through all directories
        for root, dirs, files in os.walk('.'):
            # Filter for Python files
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    # Normalize path (remove ./ and use forward slashes)
                    normalized_path = os.path.normpath(file_path).replace('\\', '/').lstrip('./')
                    
                    try:
                        # Read content of the Python file
                        with open(file_path, 'r', encoding='utf-8') as py_file:
                            content = py_file.read()
                            
                        # Write to map.txt with file path as header
                        map_file.write(f"\n{'='*50}\n")
                        map_file.write(f"File: {normalized_path}\n")
                        map_file.write(f"{'='*50}\n\n")
                        map_file.write(content)
                        map_file.write('\n\n')
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

if __name__ == "__main__":
    map_python_files()