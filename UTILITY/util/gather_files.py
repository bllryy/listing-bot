# util/gather_files.py
import os
from shutil import copy2, copytree
import subprocess

def gather_files():
    """
    Gathers all Python files in the ../FILES directory and returns them in a list.
    Includes directories in the list.

    Returns:
        list: A list of strings, where each string is a path to a Python file or directory.
              Returns an empty list if the FILES directory does not exist or if no Python files are found.
    """
    files_list = []
    files_dir = os.path.join(os.getcwd(), '..', 'FILES')

    if not os.path.exists(files_dir):
        print(f"Error: Directory not found: {files_dir}")
        return files_list

    for root, directories, files in os.walk(files_dir):
        for name in files:
            if name.endswith(".py"):
                files_list.append(os.path.join(root, name))
        for name in directories:
             files_list.append(os.path.join(root,name)) #Fixed missing space.
    return files_list