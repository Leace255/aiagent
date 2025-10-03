import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import available_functions, call_function


def main():
    if len(sys.argv) < 2:
        print("no prompt")
        sys.exit(1)

    prompt = sys.argv[1]
    system_prompt = system_prompt = """
    You are a helpful AI coding agent.

    When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

    - List files and directories
    - Read file contents
    - Execute Python files with optional arguments
    - Write or overwrite files

    All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
    """
    if prompt[0] == "-":
        print("provide prompt as first argument")
        sys.exit(1)

    _ = load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    messages = [
        types.Content(role="user", parts=[types.Part(text=prompt)]),
    ]

    verbose = False
    iterations = 0

    if len(sys.argv) >= 3:
        if sys.argv[2] == "--verbose":
            verbose = True

    while iterations <= 5:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[available_functions], system_instruction=system_prompt
            ),
        )

        if response.function_calls:
            function_call_result = call_function(
                response.function_calls[0], verbose=verbose
            )

            result = function_call_result.parts[0].function_response.response

            if not result:
                raise Exception("Error")

            function_result_message = types.Content(
                role="user", parts=[types.Part(text=str(result))]
            )

            messages.append(function_result_message)

            print(f"-> {result}")
            iterations += 1
            continue

        print(response.text)
        break

    if not verbose:
        return

    print(f"User prompt: {prompt}")
    print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}")


if __name__ == "__main__":
    main()
