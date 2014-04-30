import sublime, sublime_plugin
from simplenote import Simplenote

from collections import deque
from os import path, makedirs, remove, listdir
from datetime import datetime

from operations import NoteCreator, NoteDownloader, GetNotesDelta, NoteDeleter, NoteUpdater

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
                currentView.set_status('QuickSimplenote', message)

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

class OperationManager:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(OperationManager, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.operations = deque([])
        self.running = False
        self.current_operation = None

    def add_operation(self, operation):
        self.operations.append(operation)
        if (not self.running):
            self.run()

    def check_operations(self):

        if self.current_operation == None:
            return

        # If it's still running, update the status
        if self.current_operation.is_alive():
            text = self.current_operation.get_update_run_text()
        else:
            # If not running, show finished text
            # call callback with result and do the
            # next operation
            text = self.current_operation.get_run_finished_text()
            self.current_operation.join()
            if len( self.operations ) > 0:
                self.start_next_operation()
            else:
                self.running = False
                sublime.set_timeout(remove_status, 1000)

        show_message(text)
        if self.running:
            sublime.set_timeout(self.check_operations, 1000)

    def run(self):
        self.start_next_operation()
        sublime.set_timeout(self.check_operations, 1000)
        self.running = True

    def start_next_operation(self):
        self.current_operation = self.operations.popleft()
        self.current_operation.start()

class HandleNoteViewCommand(sublime_plugin.EventListener):

    def handle_note_changed(self, modified_note_resume):
        global notes
        # We get all data back except the content of the note
        # we need to merge it ourselves
        for index, note in enumerate(notes):
            if note['key'] == modified_note_resume['key']:
                modified_note_resume['content'] = note['content']
                notes[index] = modified_note_resume
                break
        notes.sort(key=cmp_to_key(sort_notes), reverse=True)

    def on_post_save(self, view):
        view_filepath = view.file_name()
        note = get_note_from_path(view_filepath)
        if note:
            note['content'] = view.substr(sublime.Region(0, view.size())).encode('utf-8')
            update_op = NoteUpdater(note=note, simplenote_instance=simplenote_instance)
            update_op.set_callback(self.handle_note_changed)
            OperationManager().add_operation(update_op)

class ShowQuickSimplenoteNotesCommand(sublime_plugin.ApplicationCommand):

    def get_note_name(self, note):
        try:
            content = note['content']
        except Exception, e:
            return 'untitled'
        index = content.find('\n');
        if index > -1:
            title = content[:index]
        else:
            if content:
                title = content
            else:
                title = 'untitled'
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
        for note in notes:
            i += 1
            title = self.get_note_name(note)
            keys.append(title)
        sublime.active_window().show_quick_panel(keys, self.handle_selected)

import pickle
class StartQuickSimplenoteCommand(sublime_plugin.ApplicationCommand):

    def load_notes(self):
        with open(path.join(package_path, 'note_cache'),'rb') as cache_file:
            try:
                notes = pickle.load(cache_file)
            except EOFError, e:
                notes = []
        return notes

    def save_notes(self, notes):
        cache_file = open(path.join(package_path, 'note_cache'),'r+b')
        pickle.dump(notes, cache_file)

    def set_result(self, new_notes):
        global notes
        notes = new_notes
        notes.sort(key=cmp_to_key(sort_notes), reverse=True)
        self.save_notes(self.notes2)

    def merge_delta(self, updated_note_resume):
        # Here we create the note_resume we use on the rest of the app.
        # The note_resume we store consists of:
        # The note Id, the note resume as it comes from the simplenote api, the title, the filename
        # the last modified date (from the server) and the last modified date (from local)
        self.save_notes(self.notes2)

    def notes_synch(self, note_resume):
        # Here we synch updated notes in order of priority.
        # Open notes:
        #   Locally unsaved
        #   Locally saved
        # Locally existing closed notes
        # New notes
        pass

    def run(self):
        show_message('QuickSimplenote: Setting up')

        if not path.exists(temp_path):
            makedirs(temp_path)

        self.notes2 = self.load_notes()

        for f in listdir(temp_path):
            remove(path.join(temp_path, f))

        show_message('QuickSimplenote: Downloading notes')
        get_delta_op = GetNotesDelta(simplenote_instance=simplenote_instance)
        get_delta_op.set_callback(self.set_result)
        OperationManager().add_operation(get_delta_op)

class CreateQuickSimplenoteNoteCommand(sublime_plugin.ApplicationCommand):

    def handle_new_note(self, result):
        if result:
            global notes
            notes.append(result)
            notes.sort(key=cmp_to_key(sort_notes), reverse=True)
            show_message('QuickSimplenote: Done')
            sublime.set_timeout(remove_status, 2000)
            open_note(result)

    def run(self):
        creation_op = NoteCreator(simplenote_instance=simplenote_instance)
        creation_op.set_callback(self.handle_new_note)
        OperationManager().add_operation(creation_op)

class DeleteQuickSimplenoteNoteCommand(sublime_plugin.ApplicationCommand):

    def handle_deletion(self, result):
        global notes
        notes.remove(self.note)
        remove(get_path_for_note(self.note))
        close_view(self.note_view)

    def run(self):

        self.note_view = sublime.active_window().active_view()
        self.note = get_note_from_path(self.note_view.file_name())
        if self.note:
            deletion_op = NoteDeleter(note=self.note, simplenote_instance=simplenote_instance)
            deletion_op.set_callback(self.handle_deletion)
            OperationManager().add_operation(deletion_op)

def reload_if_needed():
    global settings, started, reload_calls

    # Sublime calls this twice for some reason :(
    reload_calls = reload_calls + 1
    if (reload_calls % 2 != 0):
        return

    if settings.get('autostart'):
        sublime.set_timeout(start, 2000) # I know...
        print('QuickSimplenote: Autostarting')

def start():
    global started, simplenote_instance, settings

    username = settings.get('username')
    password = settings.get('password')

    if (username and password):
        simplenote_instance = Simplenote(username, password)
        sublime.run_command('start_quick_simplenote');
        started = True
    else:
        filepath = path.join(package_path, 'quick_simplenote.sublime-settings')
        sublime.active_window().open_file(filepath)
        show_message('QuickSimplenote: Please configure username/password')
        sublime.set_timeout(remove_status, 2000)
        started = False

    return started

reload_calls = -1
simplenote_instance = None
started = False
notes = []
package_path = path.join(sublime.packages_path(), "QuickSimplenote")
temp_path = path.join(package_path, "temp")

settings = sublime.load_settings('quick_simplenote.sublime-settings')
settings.clear_on_change('username')
settings.clear_on_change('password')
settings.add_on_change('username', reload_if_needed)
settings.add_on_change('password', reload_if_needed)

reload_if_needed()