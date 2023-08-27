import argparse
import datetime
import json
import os
import re

import openai

from commands import write_to_log, load_conversation, list_conversations, save_conversation, execute_fs_command
from config import SYSTEM_MESSAGE, COMMANDS_DICT, LOG_DIR, STORAGE_DIR, CONVERSATIONS_DIR

# set your OpenAI API key
# noinspection SpellCheckingInspection
openai.api_key = "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"

LOG_FILE = os.path.join(LOG_DIR, datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f") + ".txt")
conversation_name = 'conversation_' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f")
prompt = ''
response_count = 0
logged_response_count = 0
last_logged = {}
# noinspection PyPep8

# Ensure required directories exist
for d in CONVERSATIONS_DIR, STORAGE_DIR, LOG_DIR:
	if not os.path.exists(d):
		os.makedirs(d)


def interact_with_chatgpt():
	global prompt
	global response_count
	# Update the user's prompt in the conversation context
	messages = [
		{
			'role': 'system',
			'content': SYSTEM_MESSAGE
		},
		{
			'role': 'user',
			'content': prompt
		}
	]
	write_to_log(code_tag="before interact")
	# Send the conversation to ChatGPT and get the response
	response = openai.ChatCompletion.create(
		model="gpt-4-0613",
		messages=messages
	)
	response_count += 1

	# Extract the assistant's message from the response in JSON format
	assistant_raw_response = response['choices'][0]['message']['content'].strip()
	formatted_response = format_response(assistant_raw_response)

	# If the response isn't in the desired format, handle accordingly

	# Parse and execute commands in the assistant's response
	write_to_log(assistant_raw_response=assistant_raw_response, code_tag='before execute')
	executed_results = parse_and_execute_commands(formatted_response)

	if executed_results['error_message']:
		return_gpt = True
		command_results = [executed_results['error_message']]
	else:
		command_results = executed_results["results"]
		return_gpt = executed_results["return"]

	write_to_log(assistant_raw_response=assistant_raw_response, executed_results=executed_results,
				 return_gpt=return_gpt,
				 code_tag="after interact")
	# Return the results of the executed commands and the user message
	return {
		"command_results": command_results,
		"assistant_message": executed_results["user_message"],
		"return": return_gpt
	}


def parse_and_execute_commands(response):
	global prompt
	commands = response["commands"]
	user_message = response["user"]
	results = []
	result = ''
	index = 1  # Initialize index for error tracking
	was_error = False
	return_gpt = False
	err_message = ''
	for command_obj in commands:
		# try:
		err_message = f'Unable to parse command number {index}. Command: "{command_obj}".\n'

		if not isinstance(command_obj, dict):
			err_message += "JSON does not return a valid dictionary object for this section.\n"
			was_error = True
		else:
			if "commandName" not in command_obj:
				err_message += '"commandName" not found in dictionary.\n'
				was_error = True

			command = command_obj.get("commandName", "")
			parameters = command_obj.get("parameters", {})

			if not isinstance(parameters, dict):
				parameters = {str(parameters): ""}

			if command not in COMMANDS_DICT:
				err_message += f'Command not found: "{command}".\n'
				was_error = True
			else:
				required_params = COMMANDS_DICT[command]
				missing_params = [param for param in required_params if param not in parameters]

				if missing_params:
					err_message += f"Error: Missing parameters for {command}: {', '.join(missing_params)}.\n"
					was_error = True

			if not was_error:
				# Execute the parsed commands
				if command.startswith("fs."):
					return_gpt, result = execute_fs_command(command, parameters)

					if str(result).startswith('Error:'):
						err_message = result
						was_error = True

				elif command == "conv.ls":
					result = list_conversations()
					return_gpt = True
				elif command == "conv.load":
					filename = parameters["name"].strip()
					result = load_conversation(filename)
					return_gpt = True
				elif command == "conv.save":
					result = save_conversation(parameters["name"].strip())
				else:
					err_message += f'Invalid command: "{command}".\n'
					was_error = True
				results.append(result)
			else:
				# Print the error message or handle it accordingly
				print(err_message)
				# Append error message to results (if desired)
				results.append(err_message)

		# except Exception as e:
		#      was_error=True
		#      err_message='Error: python raised ' + str(type(e)) + str(e.args)

		if was_error:
			break

		index += 1

	return {"error_message": err_message if was_error else "", "results": results, "user_message": user_message,
			"return": return_gpt}


def format_response(assistant_response):
	# Try to find JSON structure within the response
	json_match = re.search(r'^[^\{]*?(\{.*?})[^}]*?$', assistant_response, re.DOTALL)

	if json_match:
		json_str = json_match.group(1).strip()
		try:
			data = json.loads(json_str)

			# Extract the user message separately
			#            gpt_return = str(data.get("return", False)).lower() == "true"

			return {
				"commands": data.get("commands", []),
				"user": data.get("user", ""),
				"return": str(data.get("return", False)).lower() == "true"

			}
		except json.JSONDecodeError:
			# If there's an issue with the JSON structure, return an error
			return {
				"commands": [],
				"user": "Error: Incorrect command structure in the response.",
				"return": True
			}
	else:
		# If no illustrative JSON structure was found, return the original response
		return {
			"commands": [],
			"user": assistant_response,
			"return": True
		}


def parse_filepath(*fps):
	retval = ""

	if fps:
		paths = fps
		paths = [path2[:-1] if (path2 and path2[-1] in ['/', '\\']) else path2 for path2 in paths]
		paths = [path2[1:] if path2 and path2[0] in ['/', '\\'] else path2 for path2 in paths]
		paths = [path2 for path2 in paths if path2]

		for fp in paths:
			retval = os.path.join(retval, fp)
		retval = os.path.realpath(retval)
	return retval


def main():
	"""
	"""
	parser = argparse.ArgumentParser(description="ChatGPT-4 Command Line Interface")
	parser.add_argument("initial_prompt", type=str, help="Initial prompt for the model", default="", nargs='*')
	args = parser.parse_args()
	initial_prompt = ' '.join(args.initial_prompt)
	global prompt
	return_gpt = False
	command_results = []
	while True:
		if initial_prompt != "":
			user_input = initial_prompt
			initial_prompt = ""
		elif return_gpt:
			user_input = '\n'.join(command_results)
		else:
			user_input = input("")

		user_input = user_input.strip()
		if user_input.lower() == "exit":
			print("Exiting...")
			break

		if return_gpt:
			prompt += f"API: {command_results}\n"
		else:
			prompt += f"User: {user_input}\n"

		response = interact_with_chatgpt()
		write_to_log(user_input=user_input, return_gpt=return_gpt, response=str(response), code_tag="interact response")
		return_gpt = response["return"]

		# Display the assistant's message
		print("ChatGPT:", response["assistant_message"])

		# If there are command results, display them
		command_results = response["command_results"]

		#        if command_results:
		#            print("Command Results:", ', '.join(command_results))

		prompt += f"ChatGPT: {response['assistant_message']}\n"
		write_to_log(user_input=user_input, return_gpt=return_gpt, response=str(response), code_tag="end main loop")
		save_conversation(conversation_name)


if __name__ == "__main__":
	main()
