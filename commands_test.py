import shutil
import unittest
import os
import config
import commands


class TestCommands(unittest.TestCase):

	def setUp(self):
		# Set up paths and files for testing
		self.test_file_path = commands.sanitize_path("testfile.txt")

		if not os.path.exists(commands.sanitize_path('.')):
			os.mkdir(commands.sanitize_path('.'))
		with open(self.test_file_path, 'w') as f:
			f.write("This is a test file.")

	def tearDown(self):
		# Clean up after tests
		if os.path.exists(self.test_file_path):
			os.remove(self.test_file_path)

	def test_sanitize_path(self):
		path = commands.sanitize_path("test", "path")
		expected_path = os.path.join(config.STORAGE_DIR, "test", "path")
		self.assertEqual(path, expected_path)

	def test_list_conversations(self):
		# This is a basic test and assumes you have at least one conversation saved
		conversations = commands.list_convsersations()
		self.assertIsInstance(conversations, list)
		self.assertTrue(len(conversations) > 0)

	def test_save_conversation(self):
		commands.save_conversation("test_conversation")
		saved_path = os.path.join('.', 'data', 'conversations', "test_conversation.txt")
		self.assertTrue(os.path.exists(saved_path))

	def test_execute_fs_command(self):
		# Testing the fs.cat command
		content = commands.execute_fs_command("fs.cat", {"path": "testfile.txt"}).value
		self.assertEqual(content, "This is a test file.")

		# You should extend this test method to test other commands, or split them into multiple test methods.


class TestCommandsFs(unittest.TestCase):

	def setUp(self):
		# Setting up a testing directory inside the storage directory
		self.test_dir = config.STORAGE_DIR
		os.makedirs(self.test_dir, exist_ok=True)
		self.original_dir = os.getcwd()
		os.chdir(self.test_dir)

	def tearDown(self):
		# Clean up after tests by moving back to the original directory and removing the test directory
		os.chdir(self.original_dir)
		if os.path.exists(self.test_dir):
			shutil.rmtree(self.test_dir)

	def test_fs_cat(self):
		# Create a test file and read its content using fs.cat
		with open('test.txt', 'w') as f:
			f.write('test content')

		content = commands.execute_fs_command('fs.cat', {'path': os.path.join(self.test_dir, 'test.txt')}).value
		self.assertEqual(content, 'test content')

	def test_fs_cp(self):
		# Create a test file and copy it to a new location using fs.cp
		with open(os.path.join(self.test_dir, 'test.txt'), 'w') as f:
			f.write('test content')

		commands.execute_fs_command('fs.cp',
		                            {'src': os.path.join(self.test_dir, 'test.txt'),
		                             'destination': os.path.join(self.test_dir, 'copy_test.txt')})
		self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'copy_test.txt')))

	def test_fs_mv(self):
		# Create a test file and move it to a new location using fs.mv
		with open(os.path.join(self.test_dir, 'test.txt'), 'w') as f:
			f.write('test content')

		commands.execute_fs_command('fs.mv', {'src': os.path.join(self.test_dir, 'test.txt'),
		                                      'dest': os.path.join(self.test_dir, 'moved_test.txt')})
		self.assertFalse(os.path.exists(os.path.join(self.test_dir, 'test.txt')))
		self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'moved_test.txt')))

	def test_fs_rm(self):
		# Create a test file and delete it using fs.rm
		with open(os.path.join(self.test_dir, 'test.txt'), 'w') as f:
			f.write('test content')

		commands.execute_fs_command('fs.rm', {'path': os.path.join(self.test_dir, 'test.txt'), 'recursive': False})
		self.assertFalse(os.path.exists(os.path.join(self.test_dir, 'test.txt')))

	def test_fs_touch(self):
		# Create a new file using fs.touch
		commands.execute_fs_command('fs.touch', {'path': os.path.join(self.test_dir, 'new_file.txt')})
		self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'new_file.txt')))

	def test_fs_mkdir(self):
		# Create a new directory using fs.mkdir
		commands.execute_fs_command('fs.mkdir', {'path': 'new_directory'})
		self.assertTrue(os.path.exists('new_directory'))

	def test_fs_rmdir(self):
		# Create a directory and delete it using fs.rmdir
		os.mkdir('test_dir')
		commands.execute_fs_command('fs.rmdir', {'path': 'test_dir'})
		self.assertFalse(os.path.exists('test_dir'))

	def test_fs_ls(self):
		# Create a file and directory and list contents using fs.ls
		with open(os.path.join(self.test_dir, 'test.txt'), 'w') as f:
			f.write('test content')
		os.mkdir('test_dir')

		resp = commands.execute_fs_command('fs.ls', {'path': self.test_dir, 'recursive': False})
		self.assertIn('test.txt', resp.value)
		self.assertIn('test_dir', resp.value)

	def test_fs_save(self):
		# Save data to a file using fs.save
		data = 'save this content'
		commands.execute_fs_command('fs.save', {'path': os.path.join(self.test_dir, 'save_test.txt'), 'data': data})
		with open(os.path.join(self.test_dir, 'save_test.txt'), 'r') as f:
			saved_data = f.read()
		self.assertEqual(saved_data, data)


if __name__ == "__main__":
	unittest.main()
