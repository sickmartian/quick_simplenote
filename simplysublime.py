import sublime, sublime_plugin
from simplenote import Simplenote

from threading import Thread
from multiprocessing.pool import ThreadPool
from os import path, makedirs, remove, listdir
from datetime import datetime

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

		pool = ThreadPool(processes=len(self.note_list))
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

class NoteUpdater(Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, note=None):
		Thread.__init__(self, group, target, name, args, kwargs, Verbose)
		self.note = note

	def run(self):
		print('Simply Sublime: Updating %s' % self.note['key'])
		simplenote_instance.update_note(self.note)

class HandleNoteViewCommand(sublime_plugin.EventListener):

	def remove_status(self):
		show_message(None)

	def check_updater(self):
		if self.progress >= 3:
			self.progress = 0
		self.progress += 1

		if self.updater.is_alive():
			show_message('Simply Sublime: Uploading note%s' % ( '.' * self.progress) )
			sublime.set_timeout(self.check_updater, 1000)
		else:
			show_message('Simply Sublime: Done')
			sublime.set_timeout(self.remove_status, 2000)

	def on_post_save(self, view):
		self.progress = -1

		view_filepath = view.file_name()
		if path.dirname(view_filepath) == temp_path:
			note_key = path.split(view_filepath)[1]
			note = [note for note in notes if note['key'] == note_key][0]
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
		filepath = path.join(temp_path, selected_note['key'])
		if not path.exists(filepath):
			f = open(filepath, 'w')
			f.write(selected_note['content'])
			f.close()
		sublime.active_window().open_file(filepath)

	def run(self):
		if not started:
			start()

		i = 0
		keys = []
		for note in	notes:
			i += 1
			title = self.get_note_name(note)
			keys.append(title)
		sublime.active_window().show_quick_panel(keys, self.handle_selected)

class StartSimplySublimeCommand(sublime_plugin.ApplicationCommand):

	def remove_status(self):
		show_message(None)

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
			sublime.set_timeout(self.remove_status, 2000)

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

def start():
	sublime.run_command('start_simply_sublime');
	started = True

started = False
notes = []
package_path = path.join(sublime.packages_path(), "simplysublime")
temp_path = path.join(package_path, "temp")

settings = sublime.load_settings('simplysublime.sublime-settings')

simplenote_instance = Simplenote(settings.get('username'), settings.get('password'))

if settings.get('autostart'):
	print('Simply Sublime: Autostarting')
	sublime.set_timeout(start, 2000) # I know...
