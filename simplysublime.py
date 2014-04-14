import sublime, sublime_plugin
from simplenote import Simplenote

from threading import Thread
from multiprocessing.pool import ThreadPool
from os import path, makedirs, remove, listdir
from datetime import datetime
import time

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

def sort_notes(a_note, b_note):
	if 'pinned' in a_note['systemtags']:
		return 1
	elif 'pinned' in b_note['systemtags']:
		return -1
	else:
		date_a = datetime.fromtimestamp(float(a_note['modifydate']))
		date_b = datetime.fromtimestamp(float(b_note['modifydate']))
		return cmp(date_a, date_b)

def show_message(message):
	if not message:
		message = ''
	for window in sublime.windows():
			for currentView in window.views():
				currentView.set_status('simply_sublime', message)

def remove_status():
	show_message(None)

def open_note(note):
	filepath = get_path_for_note(note)
	if not path.exists(filepath):
		f = open(filepath, 'w')
		try:
			content = note['content']
			f.write(content)
		except KeyError:
			pass
		f.close()
	sublime.active_window().open_file(filepath)

def get_path_for_note(note):
	return path.join(temp_path, note['key'])

def get_note_from_path(view_filepath):
	note = None
	if path.dirname(view_filepath) == temp_path:
		note_key = path.split(view_filepath)[1]
		note = [note for note in notes if note['key'] == note_key][0]
	
	return note

def close_view(view):
	view.set_scratch(True)
	view.window().focus_view(view)
	view.window().run_command("close_file")

class NoteCreator(Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
		Thread.__init__(self, group, target, name, args, kwargs, Verbose)

	def run(self):
		print('Simply Sublime: Creating note')
		self.note = simplenote_instance.add_note('')[0];

	def join(self):
		Thread.join(self)
		return self.note

class NoteDownloader(Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
		Thread.__init__(self, group, target, name, args, kwargs, Verbose)
		self.notes = []

	def download_note(self, note_id):
		print('Simply Sublime: Downloading %s' % note_id)
		note = simplenote_instance.get_note(note_id)[0]
		return note

	def run(self):
		self.note_list = [note for note in simplenote_instance.get_note_list()[0] if note['deleted'] == 0]

		import weakref
		self._children = weakref.WeakKeyDictionary()

		pool = ThreadPool(processes=2)
		results = []
		for current_note in self.note_list:
			async_result = pool.apply_async(self.download_note, (current_note['key'],))
			results.append(async_result)

		pool.close()
		pool.join()
		self.notes = [result.get() for result in results]

	def join(self):
		Thread.join(self)
		return self.notes

class NoteDeleter(Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, note=None):
		Thread.__init__(self, group, target, name, args, kwargs, Verbose)
		self.note = note

	def run(self):
		print('Simply Sublime: Deleting %s' % self.note['key'])
		simplenote_instance.trash_note(self.note['key'])

class NoteUpdater(Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, note=None):
		Thread.__init__(self, group, target, name, args, kwargs, Verbose)
		self.note = note

	def run(self):
		print('Simply Sublime: Updating %s' % self.note['key'])
		self.note['modifydate'] = time.time()
		self.note = simplenote_instance.update_note(self.note)[0]

	def join(self):
		Thread.join(self)
		return self.note

class HandleNoteViewCommand(sublime_plugin.EventListener):

	def check_updater(self):
		global notes

		if self.progress >= 3:
			self.progress = 0
		self.progress += 1

		if self.updater.is_alive():
			show_message('Simply Sublime: Uploading note%s' % ( '.' * self.progress) )
			sublime.set_timeout(self.check_updater, 1000)
		else:
			# We get all data back except the content of the note
			# we need to merge it ourselves
			modified_note_resume = self.updater.join()
			print(modified_note_resume)
			for index, note in enumerate(notes):
				if note['key'] == modified_note_resume['key']:
					modified_note_resume['content'] = note['content']
					notes[index] = modified_note_resume
					print(notes[index])
					break
			notes.sort(key=cmp_to_key(sort_notes), reverse=True)

			show_message('Simply Sublime: Done')
			sublime.set_timeout(remove_status, 2000)

	def on_post_save(self, view):
		self.progress = -1

		view_filepath = view.file_name()
		note = get_note_from_path(view_filepath)
		if note:
			note['content'] = view.substr(sublime.Region(0, view.size())).encode('utf-8')
			self.updater = NoteUpdater(note=note)
			self.updater.start()
			sublime.set_timeout(self.check_updater, 1000)

class ShowSimplySublimeNotesCommand(sublime_plugin.ApplicationCommand):

	def get_note_name(self, note):
		index = note['content'].find('\n');
		if index > -1:
			title = note['content'][:index]
		else:
			title = note['content']
		title = title.decode('utf-8')
		return title

	def handle_selected(self, selected_index):
		if not selected_index > -1:
			return

		selected_note = notes[selected_index]
		open_note(selected_note)

	def run(self):
		if not started:
			if not start():
				return

		i = 0
		keys = []
		for note in	notes:
			i += 1
			title = self.get_note_name(note)
			keys.append(title)
		sublime.active_window().show_quick_panel(keys, self.handle_selected)

class StartSimplySublimeCommand(sublime_plugin.ApplicationCommand):

	def check_download(self):
		if self.progress >= 3:
			self.progress = 0
		self.progress += 1
		if self.download_thread.is_alive():
			show_message('Simply Sublime: Downloading notes%s' % ( '.' * self.progress) )
			sublime.set_timeout(self.check_download, 1000)
		else:
			global notes
			notes = self.download_thread.join()
			notes.sort(key=cmp_to_key(sort_notes), reverse=True)
			show_message('Simply Sublime: Done')
			sublime.set_timeout(remove_status, 2000)

	def run(self):
		self.progress = -1

		show_message('Simply Sublime: Setting up')
		if not path.exists(temp_path):
			makedirs(temp_path)
		for f in listdir(temp_path):
			remove(path.join(temp_path, f))

		show_message('Simply Sublime: Downloading notes')
		self.download_thread = NoteDownloader()
		self.download_thread.start()
		self.check_download()

class CreateSimplySublimeNoteCommand(sublime_plugin.ApplicationCommand):

	def check_creation(self):
		if self.progress >= 3:
			self.progress = 0
		self.progress += 1
		if self.creation_thread.is_alive():
			show_message('Simply Sublime: Creating note%s' % ( '.' * self.progress) )
			sublime.set_timeout(self.check_creation, 1000)
		else:
			global notes
			note = self.creation_thread.join()
			notes.append(note)
			notes.sort(key=cmp_to_key(sort_notes), reverse=True)
			show_message('Simply Sublime: Done')
			sublime.set_timeout(remove_status, 2000)
			open_note(note)

	def run(self):
		self.progress = -1

		show_message('Simply Sublime: Creating note')
		self.creation_thread = NoteCreator()
		self.creation_thread.start()
		self.check_creation()

class DeleteSimplySublimeNoteCommand(sublime_plugin.ApplicationCommand):

	def check_deletion(self):
		if self.progress >= 3:
			self.progress = 0
		self.progress += 1
		if self.deletion_thread.is_alive():
			show_message('Simply Sublime: Deleting note%s' % ( '.' * self.progress) )
			sublime.set_timeout(self.check_deletion, 1000)
		else:
			global notes
			notes.remove(self.note)
			remove(get_path_for_note(self.note))
			close_view(self.note_view)
			show_message('Simply Sublime: Done')
			sublime.set_timeout(remove_status, 2000)

	def run(self):
		self.progress = -1
		self.note_view = sublime.active_window().active_view()
		self.note = get_note_from_path(self.note_view.file_name())
		if self.note:
			show_message('Simply Sublime: Deleting note')
			self.deletion_thread = NoteDeleter(note=self.note)
			self.deletion_thread.start()
			self.check_deletion()

def start():
	global started, simplenote_instance

	username = settings.get('username')
	password = settings.get('password')

	if (username and password):
		simplenote_instance = Simplenote(username, password)
		sublime.run_command('start_simply_sublime');
		started = True
	else:
		filepath = path.join(package_path, 'simplysublime.sublime-settings')
		sublime.active_window().open_file(filepath)
		show_message('Simply Sublime: Please configure username/password')
		sublime.set_timeout(remove_status, 2000)
		started = False

	return started

simplenote_instance = None
started = False
notes = []
package_path = path.join(sublime.packages_path(), "simplysublime")
temp_path = path.join(package_path, "temp")

settings = sublime.load_settings('simplysublime.sublime-settings')

if settings.get('autostart'):
	print('Simply Sublime: Autostarting')
	sublime.set_timeout(start, 2000) # I know...
