import subprocess
import re


def find_python_versions_windows():
    """Find all Python executables and check their version and CMake compatibility."""
    # Find all python executables
    try:
        output = subprocess.check_output("where python", shell=True, text=True)
    except subprocess.CalledProcessError:
        return []

    # Split the output by lines and filter out empty lines
    paths = [line.strip() for line in output.strip().split('\n') if line]

    # Use a regex pattern to match the version number when calling python --version
    versions = []
    version_pattern = re.compile(r'Python (\d+\.\d+\.\d+)')

    # Extract the versions and check development files
    for path in paths:
        command = f'"{path}" --version'
        try:
            version_output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            match = version_pattern.search(version_output)
            if match:
                version = match.group(1)
                is_ready = check_python_dev(path)
                versions.append((path, version, "Ready for CMake" if is_ready else "Not ready for CMake"))
        except subprocess.CalledProcessError as ex:
            print(f"Can't run command '{command}': {str(ex)}")
        except Exception as ex:
            print(f"Can't run command '{command}': {str(ex)}")
    
    return versions

if __name__ == "__main__":
    python_versions = find_python_versions_windows()
    if not python_versions:
        print("No Python installations found.")
    else:
        for path, version, status in python_versions:
            print(f"Python at {path} (version {version}) is {status}.")
