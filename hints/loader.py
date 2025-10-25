import os
import glob
from pathlib import Path

def load_hints():
    """
    Scans the current directory for txt files and loads their content into a dictionary.
    
    Returns:
        dict: Dictionary where keys are filenames without .txt extension 
              and values are file contents as strings
    """
    hints_dict = {}
    
    # Get the directory where this loader.py file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all txt files in the current directory
    txt_files = glob.glob(os.path.join(current_dir, "*.txt"))
    
    for txt_file in txt_files:
        try:
            # Get filename without extension
            filename = os.path.splitext(os.path.basename(txt_file))[0]
            
            # Read file content
            with open(txt_file, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Add to dictionary
            hints_dict[filename] = content
            
            print(f"Loaded: {filename}")
            
        except Exception as e:
            print(f"Error loading {txt_file}: {e}")
    
    print(f"Total files loaded: {len(hints_dict)}")
    return hints_dict

# Global variable - this will be populated when the module is imported
HINTS = load_hints()