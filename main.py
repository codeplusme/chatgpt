import argparse
import json
import os
import re
import openai
import commands
import config
from log import write_to_log

# set your OpenAI API key
# noinspection SpellCheckingInspection
openai.api_key = "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"
# Ensure required directories exist

for d in config.CONVERSATIONS_DIR, config.STORAGE_DIR, config.LOG_DIR:
	if not os.path.exists(d):
		os.makedirs(d)


def setup_messages(user_content):
	"""
	Set up the initial messages for OpenAI API interaction.

	:param user_content: The user's content for interaction.
	:type user_content: str
	:return: The initialized messages list.
	:rtype: list
	"""
	return [
		{
			'role': 'system',
			'content': config.SYSTEM_MESSAGE
		},
		{
			'role': 'user',
			'content': user_content
		}
	]


def interact_with_chatgpt() -> dict:
	"""
    Interact with ChatGPT and process its response.

    This function sends a prompt to ChatGPT and receives its response. It then processes the response,
    identifies and executes commands, and prepares the response for presentation to the user.

    :return: Dictionary containing results of the executed commands, the message from the assistant, and a flag for further interactions.
    :rtype: dict
    """

	messages = setup_messages(config.prompt)
	write_to_log(code_tag="before interact")
	response = openai.ChatCompletion.create(
		model="gpt-4-0613",
		messages=messages
	)
	config.response_count += 1
	assistant_raw_response = response['choices'][0]['message']['content'].strip()
	formatted_response: dict = format_response(assistant_raw_response)

	write_to_log(assistant_raw_response=assistant_raw_response, code_tag='before execute')
	execute_results: dict = commands.execute_commands(formatted_response)

	if execute_results['errors']:  # Updated from 'error_message' to 'errors'
		return_to_gpt = True
		command_results = execute_results['errors']
	else:
		command_results = execute_results["results"]
		return_to_gpt = execute_results["return_flag"]  # Updated to 'return_flag' based on the new structure

	write_to_log(assistant_raw_response=assistant_raw_response, executed_results=execute_results,
	             return_to_gpt=return_to_gpt,
	             code_tag="after interact")
	return {
		"command_results": command_results,
		"assistant_message": formatted_response['user'],
		"return_to_gpt": return_to_gpt
	}


def format_response(assistant_response: str) -> dict:
	"""
	Format the response from ChatGPT.

	Attempts to extract a JSON structure from the response. If successful, processes the JSON to
	extract commands, user messages, and a return flag. If unsuccessful, it handles the response accordingly.

	:param assistant_response: Raw response from ChatGPT.
	:type assistant_response: str
	:return: Dictionary containing extracted commands, user message, and a return flag.
	:rtype: dict
	"""
	# Try to find JSON structure within the response
	json_match = re.search(r'^[^\{]*?(\{.*?})[^}]*?$', assistant_response, re.DOTALL)

	if json_match:
		json_str = json_match.group(1).strip()
		try:
			data = json.loads(json_str)

			# Extract the user message separately
			#            return_to_gpt = str(data.get("return_to_gpt", False)).lower() == "true"

			return {
				"commands": data.get("commands", []),
				"user": data.get("user", ""),
				"return_to_gpt": str(data.get("return_to_gpt", False)).lower() == "true"

			}
		except json.JSONDecodeError:
			# If there's an issue with the JSON structure, return an error
			return {
				"commands": [],
				"user": "Error: Incorrect command structure in the response.",
				"return_to_gpt": True
			}
	else:
		# If no illustrative JSON structure was found, return the original response
		return {
			"commands": [],
			"user": assistant_response,
			"return_to_gpt": True
		}


def get_user_input(initial_prompt: str, command_results: list) -> str:
	"""Fetch the user input for interaction with ChatGPT."""
	if initial_prompt:
		user_input = initial_prompt.strip()
		initial_prompt = ""
	elif command_results:
		user_input = '\n'.join(command_results)
	else:
		user_input = input("").strip()

	return user_input


def display_response(gpt_response: dict):
	"""Display the response from ChatGPT."""
	print("ChatGPT:", gpt_response["assistant_message"])


def update_prompt(user_input: str, gpt_response: dict) -> str:
	"""Update the conversation prompt."""
	prompt = f"User: {user_input}\nChatGPT: {gpt_response['assistant_message']}\n"
	return prompt


def main():
	parser = argparse.ArgumentParser(description="ChatGPT-4 Command Line Interface")
	parser.add_argument("initial_prompt", type=str, help="Initial prompt for the model", default="", nargs='*')
	args = parser.parse_args()

	command_results = []
	return_to_gpt = False
	while True:
		user_input = get_user_input(args.initial_prompt, command_results)

		if user_input.lower() == "exit":
			print("Exiting...")
			break

		gpt_response = interact_with_chatgpt()
		display_response(gpt_response)

		command_results = gpt_response["command_results"]
		return_to_gpt = gpt_response["return_to_gpt"]

		config.prompt += update_prompt(user_input, gpt_response)
		commands.save_conversation()


if __name__ == "__main__":
	main()
