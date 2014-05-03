from threading import Thread
from abc import ABCMeta, abstractmethod
import time

class Operation(Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs, Verbose)
        self.callback = None

    def set_callback(self, callback, kwargs={}):
        self.callback = callback
        self.callback_kwargs = kwargs

    def join(self):
        Thread.join(self)
        if self.callback:
            self.callback( self.get_result(), **self.callback_kwargs )

    def get_result(self):
        return None

    def get_run_finished_text(self):
        return None

    def get_update_run_text(self):
        return None

class NoteCreator(Operation):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, simplenote_instance=None):
        Operation.__init__(self, group, target, name, args, kwargs, Verbose)
        self.simplenote_instance = simplenote_instance

    def run(self):
        print('QuickSimplenote: Creating note')
        self.note = self.simplenote_instance.add_note('')[0];

    def get_run_finished_text(self):
        return None

    def get_update_run_text(self):
        return 'QuickSimplenote: Creating note'

    def get_result(self):
        return self.note

class NoteDownloader(Thread):
    def __init__(self, note_id, semaphore, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, simplenote_instance=None):
        Thread.__init__(self, group, target, name, args, kwargs, Verbose)
        self.note_id = note_id
        self.semaphore = semaphore
        self.simplenote_instance = simplenote_instance
    
    def run(self):
        self.semaphore.acquire()
        print('QuickSimplenote: Downloading %s' % self.note_id)
        self.note = self.simplenote_instance.get_note(self.note_id)[0]
        self.semaphore.release()

    def join(self):
        Thread.join(self)
        return self.note
        
class MultipleNoteContentDownloader(Operation):

    def __init__(self, semaphore, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, simplenote_instance=None, notes=None):
        Operation.__init__(self, group, target, name, args, kwargs, Verbose)
        self.notes = notes
        self.semaphore = semaphore
        self.simplenote_instance = simplenote_instance

    def run(self):
        threads = []
        for current_note in self.notes:
            new_thread = NoteDownloader(current_note['key'], self.semaphore, simplenote_instance=self.simplenote_instance)
            threads.append(new_thread)
            new_thread.start()

        self.notes_with_content = [thread.join() for thread in threads]

    def get_result(self):
        return self.notes_with_content

    def get_run_finished_text(self):
        return 'QuickSimplenote: Done'

    def get_update_run_text(self):
        return 'QuickSimplenote: Downloading contents'

class GetNotesDelta(Operation):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, simplenote_instance=None):
        Operation.__init__(self, group, target, name, args, kwargs, Verbose)
        self.note_resume = []
        self.simplenote_instance = simplenote_instance

    def run(self):
        self.note_resume = [note for note in self.simplenote_instance.get_note_list()[0] if note['deleted'] == 0]

    def get_result(self):
        return self.note_resume

    def get_run_finished_text(self):
        return 'QuickSimplenote: Done'

    def get_update_run_text(self):
        return 'QuickSimplenote: Downloading notes'

class NoteDeleter(Operation):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, note=None, simplenote_instance=None):
        Operation.__init__(self, group, target, name, args, kwargs, Verbose)
        self.note = note
        self.simplenote_instance = simplenote_instance

    def get_run_finished_text(self):
        return None

    def get_update_run_text(self):
        return 'QuickSimplenote: Deleting note'

    def run(self):
        print('QuickSimplenote: Deleting %s' % self.note['key'])
        self.simplenote_instance.trash_note(self.note['key'])

class NoteUpdater(Operation):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None, note=None, simplenote_instance=None):
        Operation.__init__(self, group, target, name, args, kwargs, Verbose)
        self.note = note
        self.simplenote_instance = simplenote_instance

    def run(self):
        print('QuickSimplenote: Updating %s' % self.note['key'])
        self.note['modifydate'] = time.time()
        self.note = self.simplenote_instance.update_note(self.note)[0]

    def get_result(self):
        return self.note

    def get_run_finished_text(self):
        return 'QuickSimplenote: Done'

    def get_update_run_text(self):
        return 'QuickSimplenote: Updating note'