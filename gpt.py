# import the necessary libraries
import argparse
import datetime
import json
import os
import re
import shutil

import openai

COMMANDS_DICT = {
	# Conversation Commands
	"conv.ls": [],
	"conv.load": ["name"],
	"conv.save": ["name"],

	# File System (fs) Commands
	"fs.cat": ["path"],
	"fs.cp": ["src", "dest"],
	"fs.mv": ["src", "dest"],
	"fs.rm": ["path"],
	"fs.touch": ["path"],
	"fs.mkdir": ["path"],
	"fs.rmdir": ["path"],
	"fs.save": ["path"],
	"fs.ls": ["path"]
}

# set your OpenAI API key
# noinspection SpellCheckingInspection
openai.api_key = "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"
DATA_DIR = os.path.realpath(os.path.join(os.getcwd(), 'data'))
LOG_DIR = os.path.join(DATA_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f") + ".txt")
STORAGE_DIR = os.path.join(DATA_DIR, 'storage')
CONVERSATIONS_DIR = os.path.join(DATA_DIR, 'conversations')
conversation_name = 'conversation_' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f")
prompt = ''
response_count = 0
logged_response_count = 0
last_logged = {}
# noinspection PyPep8
SYSTEM_MESSAGE = '''Hello! You are an efficient assistant with the ability to interact with a custom python API. When sending a query or request, 
create a valid JSON object to be parsed by the API. Regardless of the question, make sure to follow this structure in your answer. EVERY SINGLE RESPONSE SHOULD BE READABLE BY json.loads(json_response)
The response create a valid JSON array of objects:
	
		"commands": [
			{
				"commandName": "SpecificCommand",
				"parameters": {
					"paramKey1": "value1",
					"paramKey2": "value2",
					// ... any additional parameters
				}
			},
			// ... any additional command structures as needed
		], 
		"user": "Message or response meant for the user"
	}
	```
	**Supported Commands:**
	- **Conversation Commands:**
	  - `conv.ls:{}`: Lists saved conversations.
	  - `conv.load:{"name":"Conversation_Name_to_load"}`: Loads a specific saved conversation.
	  - `conv.save:{"name":"Conversation_Name_to_save"}`: Saves the current conversation.
- **File System Commands:** Note: use windows path format with backslash

  - `fs.cat:{"path":"filename_to_display"}`: 
	- Description: Displays the contents of the specified file.
  
  - `fs.cp:{"src":"source_filepath_or_dir","destination":"dest_filepath_or_dir"}`: 
	- Description: Copies the source file or directory to the specified destination.
  
  - `fs.mv:{"src":"src_filepath_or_dir","dest":"dest_filepath_or_dir"}`: 
	- Description: Moves or renames the source file or directory to the specified dest.
  
  - `fs.rm:{"path":"filename_to_remove", "recursive":true_or_false}`: 
	- Description: Removes the specified file or directory. If "recursive" is set to true, it will recursively remove directories and their contents.
  
  - `fs.touch:{"path":"filename_to_create"}`: 
	- Description: Creates a new empty file with the given filename.
  
  - `fs.mkdir:{"path":"actual_directory_name"}`: 
	- Description: Creates a new directory in the storage space.
  
  - `fs.rmdir:{"path":"directory_name_to_remove"}`: 
	- Description: Removes the specified directory. Note: This will only remove empty directories.
  
  - `fs.ls:{"path":"optional_path_here", "recursive":true_or_false}`: 
	- Description: Lists contents in the storage directory or a specified path. If "recursive" is set to true, it lists all files and directories under the specified path recursively.
  
  - `fs.save:{"path":"actual_filename_to_save","data":"actual_data_to_save"}`: 
	- Description: Saves provided data to the specified filename.

	  example: {"commands": [{"command":"fs.save", "parameters":{"path":"folder_to_save_to\chat_gpt_saved_it_here.txt","data":"chatgpt saved this for me.txt"}],"user": "It has been saved!"}
	  Regardless of the question, make sure to follow this structure in your answer. EVERY SINGLE RESPONSE SHOULD BE READABLE BY json.loads(json_response)
	  locally, files are saved here: "''' + STORAGE_DIR + '". conversations are saved here: "' + CONVERSATIONS_DIR + '". only subdirectories of this the conversations and storage directories can be deleted. This conversation is named: ' + conversation_name

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
			return {"error_message": err_message if was_error else "", "results": results,
					"user_message": user_message, "return": return_gpt}

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


def load_conversation(filename):
	filepath = os.path.join('.', 'data', 'conversations', filename) + '.txt'
	if os.path.exists(filepath):
		with open(filepath, 'r') as file:
			return file.read().strip()
	else:
		return f"Error: {filename} not found."


def list_conversations():
	return [conversation.replace('.txt', '') for conversation in os.listdir(CONVERSATIONS_DIR)]


def save_conversation(filename):
	filepath = os.path.join('.', 'data', 'conversations', filename + '.txt')
	with open(filepath, 'w') as file:
		file.write(prompt)
	return f"Conversation saved as {filename}."


def execute_fs_command(command, parameters):
	recursive = parameters.get("recursive", "false")
	recursive = str(recursive).lower() == "true"
	path = parse_filepath(parameters.get("path", ''))
	src = parse_filepath(parameters.get("src", ''))
	dest = parse_filepath(parameters.get("dest", ''))
	if command == "fs.cat":
		path = os.path.join(STORAGE_DIR, path)
		with open(path, 'r') as file:
			return True, file.read()

	elif command == "fs.cp":
		src = os.path.join(STORAGE_DIR, src)
		dest = os.path.join(STORAGE_DIR, dest)
		if os.path.isdir(src):
			shutil.copytree(src, dest)
		else:
			shutil.copy2(src, dest)
		return False, f"Copied {parameters['src']} to {parameters['dest']}"

	elif command == "fs.mv":
		shutil.move(src, dest)
		return False, f"Moved/Renamed {parameters['src']} to {parameters['dest']}"

	elif command == "fs.rm":
		if parse_filepath('storage', '') == path:
			return True, 'Error: Cannot delete '
		if not path.endswith('*'):
			paths = [path]
		else:
			paths = os.listdir(os.path.dirname(path))
		for child in paths:
			if recursive and os.path.isdir(child):
				shutil.rmtree(child)
			else:
				os.remove(child)

		return False, f"Removed {parameters['path']}"

	elif command == "fs.touch":
		with open(path, 'a'):
			os.utime(path, None)
		return False, f"Created {parameters['path']}"

	elif command == "fs.mkdir":
		os.makedirs(path, exist_ok=True)
		return False, f"Created directory {parameters['path']}"

	elif command == "fs.rmdir":
		if parse_filepath('storage', '') == path:
			return 'Error: Cannot delete base directory.'
		os.rmdir(path)  # Note: This will only remove empty directories.
		return False, f"Removed directory {parameters['path']}"

	elif command == "fs.ls":

		path = parse_filepath('storage', parameters.get("path", ""))
		if recursive:
			all_files = []
			for dirpath, dirnames, filenames in os.walk(path):
				for fname in filenames:
					all_files.append(os.path.join(dirpath, fname).replace(STORAGE_DIR, ''))
			return True, all_files
		else:
			return True, os.listdir(path)

	elif command == "fs.save":

		with open(path, 'w') as file:
			file.write(parameters["data"])
		return False, f"Saved data to {parameters['path']}"

	else:
		return True, f"Error:Invalid command: {command}"


def main():
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


def write_to_log(code_tag, user_input='', response='', **kwargs):
	global prompt
	global logged_response_count
	global response_count
	global last_logged
	lines = {"code_tag": code_tag + '[' + str(response_count) + ']', "user_input": user_input,
			 "prompt": '"' + repr(prompt.strip()) + '"',
			 "response": response}
	if logged_response_count == response_count:
		ks = list(lines)
		for k in ks:
			if last_logged.get(k, '') == lines[k]:
				del lines[k]
			else:
				last_logged[k] = lines[k]
	else:
		last_logged = lines
	text = '\n'.join([key + ':' + str(var) for d in [lines, kwargs] for key, var in d.items() if var])
	text += '\n\n'
	if logged_response_count != response_count:
		text = '\n' + '-' * 25 + '#' + str(response_count) + '\n'
		last_logged = lines

	with open(LOG_FILE, 'a') as file:
		file.write(text)
	logged_response_count = response_count

if __name__ == "__main__":
	main()
