from threading import Thread
from abc import ABCMeta, abstractmethod
import time

class Operation(Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, verbose=None):
        super(Operation, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.callback = None
        self.exception_callback = None

    def set_callback(self, callback, kwargs={}):
        self.callback = callback
        self.callback_kwargs = kwargs

    def set_exception_callback(self, callback):
        self.exception_callback = callback

    def join(self):
        Thread.join(self)
        if self.callback:
            result = self.get_result()
            if not isinstance(result, Exception):
                self.callback( result, **self.callback_kwargs )
            elif self.exception_callback:
                self.exception_callback( result )
            else:
                print(str(result))

    def get_result(self):
        return None

    def get_run_finished_text(self):
        return None

    def get_update_run_text(self):
        return None

class NoteCreator(Operation):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, verbose=None, simplenote_instance=None):
        super(NoteCreator, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.simplenote_instance = simplenote_instance

    def run(self):
        print('QuickSimplenote: Creating note')
        operation_result = self.simplenote_instance.add_note('')
        if operation_result[1] == 0:
            self.result = operation_result[0]
        else:
            self.result = Exception("Error creating note")

    def get_run_finished_text(self):
        return 'QuickSimplenote: Done'

    def get_update_run_text(self):
        return 'QuickSimplenote: Creating note'

    def get_result(self):
        return self.result

class NoteDownloader(Thread):
    def __init__(self, note_id, semaphore, group=None, target=None, name=None, args=(), kwargs={}, verbose=None, simplenote_instance=None):
        super(NoteDownloader, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.note_id = note_id
        self.semaphore = semaphore
        self.simplenote_instance = simplenote_instance
    
    def run(self):
        self.semaphore.acquire()
        print('QuickSimplenote: Downloading %s' % self.note_id)
        operation_result = self.simplenote_instance.get_note(self.note_id)
        if operation_result[1] == 0:
            self.result = operation_result[0]
        else:
            self.result = Exception("Error getting note")
        self.semaphore.release()

    def join(self):
        Thread.join(self)
        return self.result
        
class MultipleNoteContentDownloader(Operation):

    def __init__(self, semaphore, group=None, target=None, name=None, args=(), kwargs={}, verbose=None, simplenote_instance=None, notes=None):
        super(MultipleNoteContentDownloader, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.notes = notes
        self.semaphore = semaphore
        self.simplenote_instance = simplenote_instance

    def run(self):
        threads = []
        for current_note in self.notes:
            new_thread = NoteDownloader(current_note['key'], self.semaphore, simplenote_instance=self.simplenote_instance)
            threads.append(new_thread)
            new_thread.start()

        operation_result = [thread.join() for thread in threads]

        error = False
        for an_object in operation_result:
            if isinstance(an_object, Exception):
                error = True
        if not error:
            self.result = operation_result
        else:
            self.result = Exception("Error getting note")

    def get_result(self):
        return self.result

    def get_run_finished_text(self):
        return 'QuickSimplenote: Done'

    def get_update_run_text(self):
        return 'QuickSimplenote: Downloading contents'

class GetNotesDelta(Operation):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, verbose=None, simplenote_instance=None):
        super(GetNotesDelta, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.note_resume = []
        self.simplenote_instance = simplenote_instance

    def run(self):
        note_resume_operation = self.simplenote_instance.get_note_list()
        if note_resume_operation[1] == 0:
            note_resume = note_resume_operation[0]
            self.result = [note for note in note_resume if note['deleted'] == 0]
        else:
            self.result = Exception("Error getting notes")

    def get_result(self):
        return self.result

    def get_run_finished_text(self):
        return 'QuickSimplenote: Done'

    def get_update_run_text(self):
        return 'QuickSimplenote: Downloading note list'

class NoteDeleter(Operation):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, verbose=None, note=None, simplenote_instance=None):
        super(NoteDeleter, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.note = note
        self.simplenote_instance = simplenote_instance

    def get_run_finished_text(self):
        return None

    def get_update_run_text(self):
        return 'QuickSimplenote: Deleting note'

    def run(self):
        print('QuickSimplenote: Deleting %s' % self.note['key'])
        deletion_operation = self.simplenote_instance.trash_note(self.note['key'])
        if deletion_operation[1] == 0:
            self.result = True
        else:
            self.result = Exception("Error deleting note")

    def get_result(self):
        return self.result

class NoteUpdater(Operation):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, verbose=None, note=None, simplenote_instance=None):
        super(NoteUpdater, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.note = note
        self.simplenote_instance = simplenote_instance

    def run(self):
        print('QuickSimplenote: Updating %s' % self.note['key'])
        self.note['modifydate'] = time.time()

        note_update_operation = self.simplenote_instance.update_note(self.note)
        if note_update_operation[1] == 0:
            self.result = note_update_operation[0]
        else:
            self.result = Exception("Error updating note")

    def get_result(self):
        return self.result

    def get_run_finished_text(self):
        return 'QuickSimplenote: Done'

    def get_update_run_text(self):
        return 'QuickSimplenote: Updating note'