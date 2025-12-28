# util/copy_files.py
import os
from shutil import copytree, rmtree

def _delete_python_files(directory):
    """
    Deletes ONLY Python files within the given directory and its subdirectories.
    """
    if not os.path.exists(directory):
        print(f"Directory does not exist: {directory}")
        return

    for root, _, files in os.walk(directory):
        for name in files:
            if name.endswith(".py"):
                filepath = os.path.join(root, name)
                try:
                    os.remove(filepath)
                    print(f"Deleted: {filepath}")
                except OSError as e:
                    print(f"Error deleting {filepath}: {e}")


def copy_gathered_files(destination_directory, token: str = None):
    """
    Copies all files and directories from the FILES directory to the destination.
    Selectively removes ONLY .py files in the destination *before* copying.
    """
    if os.path.basename(os.path.abspath(destination_directory)) == "UTILITY":
        print(f"Refusing to copy files to the UTILITY directory for safety reasons.")
        return False
        
    files_dir = os.path.join(os.getcwd(), '..', 'FILES')

    if token:
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory)
            with open(os.path.join(destination_directory, ".env"), "w") as f:
                f.write(f"TOKEN={token}")
            copytree(files_dir, destination_directory, dirs_exist_ok=True)
            print(f"Copied initial files to {destination_directory}")
            return

    _delete_python_files(destination_directory)
    copytree(files_dir, destination_directory, dirs_exist_ok=True)
    print(f"Copied files to: {destination_directory}")