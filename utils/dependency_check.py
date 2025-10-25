import os
import subprocess
import json
import re
import platform
from typing import List, Tuple, Union


def find_cmake(vs_where_path: str, default_path: str = None) -> str | None:
    """
    Finds the CMake executable by searching in the system PATH, Visual Studio installations, 
    or the default installation directory.

    Args:
        vs_where_path (str): Path to the `vswhere.exe` utility for locating Visual Studio installations.

    Returns:
        str or None: The directory containing the `cmake.exe` executable if found, otherwise `None`.

    Notes:
        - The search order is:
          1. System PATH (using `where cmake`).
          2. Visual Studio installations via `vswhere.exe`.
          3. Default installation directory under `ProgramFiles`.
        - Prints messages indicating where CMake was found or if it could not be located.
    """
    # 1. Check if CMake is available through the PATH (using 'where cmake')
    try:
        result = subprocess.run(["where", "cmake"], capture_output=True, text=True, check=True)
        cmake_exe = result.stdout.strip()
        if os.path.isfile(cmake_exe):
            return os.path.dirname(cmake_exe)
    except subprocess.CalledProcessError:
        # CMake not found in PATH via "where cmake" command
        pass

    # 2. Check Visual Studio installations using vswhere    
    if os.path.exists(vs_where_path):
        vswhere_cmd = [
            vs_where_path,
            "-all",             # List all instances
            "-products", "*",    # Include all installed products
            "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",  # Require VC++ toolset
            "-property", "installationPath",  # Get the installation path
            "-format", "json"
        ]

        try:
            result = subprocess.run(vswhere_cmd, capture_output=True, text=True, check=True)
            instances = json.loads(result.stdout)

            for instance in instances:
                vs_path = instance["installationPath"]
                cmake_vs_path = os.path.join(vs_path, "Common7", "IDE", "CommonExtensions", "Microsoft", "CMake", "CMake")

                # Check if CMake exists in this path
                cmake_exe = os.path.join(cmake_vs_path, "bin", "cmake.exe")
                if os.path.isfile(cmake_exe):
                    print(f"CMake found in Visual Studio installation at: {cmake_exe}")
                    return os.path.dirname(cmake_exe)

        except subprocess.CalledProcessError as e:
            print(f"Error running vswhere: {e}")

    # 3. Check default installation path (if CMake was installed separately but not added to PATH)
    cmake_exe = os.path.join(os.environ.get('ProgramFiles', ''), 'CMake', 'bin', 'cmake.exe')
    if os.path.isfile(cmake_exe):
        print(f"CMake found in default installation path at: {cmake_exe}")
        return os.path.dirname(cmake_exe)

    print("CMake not found.")
    return default_path


def map_toolset_version(toolset_version: str) -> str:
    major, minor, _ = toolset_version.split('.')
    major, minor = int(major), int(minor)
    if major != 14:
        raise Exception("Unexpected toolset version")
    
    if minor >= 30:
        return "v143"
    elif minor >= 20:
        return "v142"
    elif minor >= 10:
        return "v141"
    else:
        raise Exception("Unexpected toolset version") 


def find_visual_studio_compilers(vs_where_path: str) -> List[str]:
    """
    Finds installed Visual Studio compilers and their available toolsets using `vswhere.exe`.

    This function runs the `vswhere.exe` utility to locate all installed Visual Studio instances
    that include the VC++ toolset, then retrieves the available toolset versions from each instance.

    Args:
        vs_where_path (str): The path to the `vswhere.exe` executable.

    Returns:
        list[tuple]: A list of toolset versions tuples (e.g., ('v142', '14.29.30133'), ('v143', '14.42.34433')) 
        found in the Visual Studio instances.

    Raises:
        FileNotFoundError: If the specified `vswhere.exe` is not found.
    """
    if not os.path.exists(vs_where_path):
        print(f"vswhere.exe not found at {vs_where_path}")
        return []

    # Run vswhere to list installed Visual Studio instances with toolset information
    vswhere_cmd = [
        vs_where_path,
        "-all",            # List all instances
        "-products", "*",   # Include all installed products
        "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",  # Require VC++ toolset
        "-property", "installationPath",  # Get the installation path
        "-format", "json"
    ]
    toolsets_found = []
    try:
        result = subprocess.run(vswhere_cmd, capture_output=True, text=True, check=True)
        instances = json.loads(result.stdout)

        for instance in instances:
            vs_path = instance["installationPath"]
            vc_tools_path = os.path.join(vs_path, "VC", "Tools", "MSVC")
            if os.path.exists(vc_tools_path):
                # List directories in MSVC folder to check available toolsets
                toolsets = os.listdir(vc_tools_path)
                for toolset in toolsets:
                    toolsets_found.append(toolset)

        if toolsets_found:
            toolsets_found = [(map_toolset_version(toolset), toolset) for toolset in toolsets_found]
            print(f"Found toolsets: {toolsets_found}")
        else:
            print("No toolsets found.")
        return toolsets_found

    except subprocess.CalledProcessError as e:
        print(f"Error running vswhere: {e}")
        return toolsets_found


def check_python_dev(python_exe_path: str) -> bool:
    """
    Checks if the given Python installation includes development headers and libraries.

    Args:
        python_exe_path (str): The full path to the Python executable to check.

    Returns:
        bool: 
            - 'True' if the Python installation has development headers and libraries.
            - 'False' otherwise.
    """
    try:
        # First, try using sysconfig to get the include directory
        include_dir_cmd = f'"{python_exe_path}" -c "import sysconfig; print(sysconfig.get_path(\'include\'))"'
        include_dir = subprocess.check_output(include_dir_cmd, shell=True, text=True).strip()
        # Check if "Python.h" exists in the include directory
        python_h = os.path.join(os.path.dirname(python_exe_path), 'include', 'Python.h')
        if not os.path.isfile(python_h):
            # Development headers are not found
            return False

        # Extract the major and minor version for the current Python executable
        version_cmd = f'"{python_exe_path}" -c "import sys; print(f\'{{sys.version_info.major}}{{sys.version_info.minor}}\')"'
        version = subprocess.check_output(version_cmd, shell=True, text=True).strip()

        # Check in default locations
        python_lib = os.path.join(
            os.path.dirname(python_exe_path), 'libs', f'python{version}.lib'
        )
        if os.path.isfile(python_lib):
            # Development library found
            return True
        else:
            # Development library is not found
            return False
    except Exception as ex:
        print(f"Error checking development files for {python_exe_path}: {ex}")
        return False


def find_python_versions_windows() -> List[tuple]:
    """
    Finds all Python executables on a Windows system and retrieves their version numbers.

    This function uses the `where` command to locate Python executables on the system, 
    then runs each executable with the `--version` flag to extract the version number.
    It also checks if the Python installation is a development build.

    Returns:
        list[tuple]: A list of tuples where each tuple contains:
            - str: The path to the Python executable.
            - str: The Python version string (e.g., '3.9.7').
            - bool: Whether the Python installation is a development version.
    """
    try:
        output = subprocess.check_output("where python", shell=True, text=True)
    except subprocess.CalledProcessError:
        return []

    # Split the output by lines and filter out empty lines
    paths = [line.strip() for line in output.strip().split('\n') if line]
    # Use a regex pattern to match the version number when calling python --version
    versions = []
    version_pattern = re.compile(r'Python (\d+\.\d+\.\d+)')
    # Extract the versions
    for path in paths:
        command = f'"{path}" --version'
        try:
            version_output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            match = version_pattern.search(version_output)
            if match:
                version = match.group(1)
                versions.append((path, version, check_python_dev(path)))
        except subprocess.CalledProcessError as ex:
            print(f"Can't run command '{command}': {str(ex)}")
        except Exception as ex:
            print(f"Can't run command '{command}': {str(ex)}")
    return versions


def get_python_recommendation() -> str:
    """
    Generates a Python version recommendation based on the current Python interpreter's version.
    """
    python_version = platform.python_version()
    major_minor = ".".join(python_version.split(".")[:2])  # Extract major and minor version
    return f"Python {major_minor}.X is recommended (X - any number)"


def get_compiler_info() -> Tuple[str, int]:
    """
    Retrieves the compiler information used to build the current Python interpreter.

    This function determines the compiler used to build Python (e.g., MSC for Microsoft Visual C++) 
    and, if applicable, extracts the MSC version number. It returns a formatted string describing 
    the compiler and the MSC version as a separate value.

    Returns:
        tuple:
            - str: A formatted string describing the compiler (e.g., `VSC v.1929 is used.`) 
              or the raw compiler information if it's not an MSC compiler.
            - int or None: The MSC version as an integer (e.g., `1929`), or `None` if not applicable.

    Example:
        >>> get_compiler_info()
        ('VSC v.1929 is used.', 1929)

    Notes:
        - If the compiler is not MSC, the function returns the raw compiler information in the 
          first element of the tuple, and `None` in the second element.
    """
    compiler = platform.python_compiler()

    # Using regular expression to extract MSC version number
    msc_version_match = re.search(r"MSC v\.(\d+)", compiler)
    if msc_version_match:
        msc_version = int(msc_version_match.group(1))  # Extract the numeric part of MSC version
        compiler_output = f"VSC v.{msc_version} is used."
    else:
        compiler_output = f"Compiler information: {compiler}"
        msc_version = None  # In case it's not an MSC compiler
    
    return compiler_output, msc_version


def map_msc_to_toolset(msc_version: int) -> str:
    """
    Maps an MSC (Microsoft C++ Compiler) version to the corresponding Visual Studio toolset version.

    This function takes an MSC version number (e.g., 1929 for 'MSC v1929') and determines the 
    recommended Visual Studio toolset version (e.g., 'v142').

    Args:
        msc_version (int): The MSC version number to map.

    Returns:
        str: A string indicating the recommended toolset version (e.g., 'v142').

    Notes:
        - The mapping is based on common MSC to toolset correspondences:
          - MSC 1900: v140 (Visual Studio 2015)
          - MSC 1910: v141 (Visual Studio 2017)
          - MSC 1920: v142 (Visual Studio 2019)
          - MSC 1930: v143 (Visual Studio 2022)
    """

    msvc_map = {
        1900: 'v140',
        1910: 'v141',
        1920: 'v142',
        1930: 'v143'
    }
    for version, toolset in msvc_map.items():
        if msc_version >= version:
            current_toolset = toolset
    return current_toolset


def get_toolset_recommendation() -> str:
    """
    Provides a recommendation for the Visual Studio toolset based on the compiler used to build Python.

    Returns:
        str: A string containing the recommended toolset (e.g., `Recommended toolset is v142`)

    """
    _, msc_version = get_compiler_info()
    
    if msc_version:
        return f"Recommended toolset is {map_msc_to_toolset(msc_version)}"
    else:
        return "Recommended toolset is not defined!"


if __name__ == "__main__":
    vw_where = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    print(f"VS Compilers: {find_visual_studio_compilers(vw_where)}")
    python_versions = find_python_versions_windows()
    print(f"Python versions: {python_versions}")
    print(f"CMAKE: {find_cmake(vw_where)}")    
    
    # Displaying the complete output
    print(get_python_recommendation())
    print(get_toolset_recommendation())
