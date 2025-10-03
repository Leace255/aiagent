import os
import subprocess
from functions.config import *
from google.genai import types


def get_files_info(working_directory, directory="."):
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target = os.path.join(working_directory, directory)
        target_abs = os.path.abspath(target)

        if not target_abs.startswith(working_dir_abs):
            return f'Error: Cannot list "{directory} as it is outside the permitted working directory"'

        if not os.path.isdir(directory):
            return f'Error: "{directory}" is not a directory'
        contents = os.listdir(target_abs)
        results = []
        for content in contents:
            path = os.path.join(target_abs, content)
            results.append(
                f"- {content}: file_size={os.path.getsize(path)} bytes, is_dir={os.path.isdir(path)}"
            )
        return "\n".join(results)

    except Exception as e:
        print(f"Error: {e}")


def get_file_content(working_directory, file_path):
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target = os.path.join(working_directory, file_path)
        target_abs = os.path.abspath(target)

        if not target_abs.startswith(working_dir_abs):
            return f'Error: Cannot read "{file_path} as it is outside the permitted working directory"'

        if not os.path.isfile(target_abs):
            return f'Error: "File not found or is not a regular file: "{file_path}"'

        with open(target_abs, "r") as f:
            content = f.read(MAX_CHARS)
            if len(content) >= 10000:
                content += f' [...File "{file_path}" truncated at 10000 characters]'
            print(content)
    except Exception as e:
        print(f"Error: {e}")


def write_file(working_directory, file_path, content):
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target = os.path.join(working_directory, file_path)
        target_abs = os.path.abspath(target)

        if not target_abs.startswith(working_dir_abs):
            return f'Error: Cannot write to "{file_path} as it is outside the permitted working directory"'

        parent_directory = os.path.dirname(target_abs)
        if not os.path.exists(parent_directory):
            os.makedirs(parent_directory)

        with open(target_abs, "w") as f:
            f.write(content)
            return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    except Exception as e:
        print(f"Error: {e}")


def run_python_file(working_directory, file_path, args=[]):
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target = os.path.join(working_directory, file_path)
        target_abs = os.path.abspath(target)

        if not target_abs.startswith(working_dir_abs):
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        if not os.path.exists(target_abs):
            return f'Error: File "{file_path}" not found'
        if file_path[-3:] != ".py":
            return f'Error: "{file_path}" is not a Python file.'

        completed_process = subprocess.run(
            ["python", target_abs] + args, timeout=30, capture_output=True
        )

        if len(completed_process.stdout) == 0 and len(completed_process.stderr) == 0:
            return "no output produced."

        message = (
            f"STDOUT: {completed_process.stdout}\nSTDERR: {completed_process.stderr}\n"
        )

        if completed_process.returncode != 0:
            message += f"process exited with code {completed_process.returncode}"

        return message
    except Exception as e:
        print(f"Error: executing Python file: {e}")


def call_function(function_call_part, verbose=False):
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")

    function_name = function_call_part.name
    args = function_call_part.args.copy()
    args["working_directory"] = "./calculator"
    functions = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "run_python_file": run_python_file,
        "write_file": write_file,
    }

    if function_name not in functions:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    response = functions[function_name](**args)

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": response},
            )
        ],
    )


schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Gets file content, truncated to 10000 chars, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file path to read the file from, relative to the working directory.",
            ),
        },
    ),
)


schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Runs specified python file, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file_path to run the file from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
            "args": types.Schema(
                type=types.Type.STRING,
                description="List of arguments to pass to the function, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes to specified file the specified content, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file path to write the file to, relative to the working directory.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content to write to the file, relative to the working directory.",
            ),
        },
    ),
)

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ]
)
