# util/update_files.py
import os
import subprocess

def update_files():
    """
    Changes directory to the FILES folder and runs git pull.

    Returns:
        bool: True if the git pull was successful, False otherwise.
    """
    current_dir = os.getcwd()  # Store original directory
    files_dir = os.path.join(current_dir, '..', 'FILES')

    try:
        os.chdir(files_dir)
        result = subprocess.run(['git', 'pull'], capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:  # Print stderr even on success, as it might contain useful info
            print(result.stderr)
        print("Successfully pulled latest changes in FILES directory.")  # More explicit success
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during git pull: {e}")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("Error: 'git' command not found. Make sure Git is installed and in your PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    finally:
        os.chdir(current_dir)  # ALWAYS change back, even on error