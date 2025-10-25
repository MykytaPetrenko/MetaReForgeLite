from ..globals import ADDON_DIRECTORY, DNACALIB_REMOVAL_FILE, DNA_CALIB_WIN_FILES, DNA_CALIB_LOCAL_DIRECTORY
import os
import time


def process_dnacalib_removal():
    target_file = os.path.join(ADDON_DIRECTORY, DNACALIB_REMOVAL_FILE)
    # Check if target file exists
    if os.path.exists(target_file):
        print(f"{target_file} exists. Proceeding to remove files.")
        time.sleep(3)
        # Remove each file in the provided list
        for file_name in DNA_CALIB_WIN_FILES + ["vtx_color.py"]:
            file_path = os.path.join(DNA_CALIB_LOCAL_DIRECTORY, file_name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Removed: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
            else:
                print(f"File not found: {file_path}")
        
        # Remove the target file itself
        try:
            os.remove(target_file)
            print(f"Removed: {target_file}")
        except Exception as e:
            print(f"Error removing {target_file}: {e}")
    else:
        print(f"{target_file} does not exist. No action taken.")
