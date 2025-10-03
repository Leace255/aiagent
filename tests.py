from functions.get_files_info import get_files_info
from functions.get_files_info import get_file_content
from functions.get_files_info import write_file
from functions.get_files_info import run_python_file


print(run_python_file("calculator", "main.py"))
print(run_python_file("calculator", "main.py", ["3 + 5"]))
print(run_python_file("calculator", "tests.py"))
print(run_python_file("calculator", "../main.py"))
print(run_python_file("calculator", "nonexistent.py"))
