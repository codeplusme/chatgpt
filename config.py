import os

from gpt import conversation_name

STORAGE_DIR = os.path.join(DATA_DIR, 'storage')
CONVERSATIONS_DIR = os.path.join(DATA_DIR, 'conversations')
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
DATA_DIR = os.path.realpath(os.path.join(os.getcwd(), 'data'))
LOG_DIR = os.path.join(DATA_DIR, 'logs')
