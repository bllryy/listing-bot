import os

def get_bot_names():
    """
    Returns a list of directory names from the parent directory,
    excluding blacklisted directories.

    Returns:
        list: A list of directory names.
    """
    blacklist = {'UTILITY', 'FILES', '.git', 'parent_api'}
    
    parent_dir = os.path.join(os.getcwd(), '..')
    
    try:
        directories = [d for d in os.listdir(parent_dir) 
                      if os.path.isdir(os.path.join(parent_dir, d))
                      and d not in blacklist]
        return directories
    except Exception as e:
        print(f"Error accessing directory: {e}")
        return []