exec(open("./simplenote.py").read())
simplenote_instance = Simplenote('test_user2@mailinator.com','testPassword')
new_note = simplenote_instance.add_note('new test note')[0]
print('New note:')
print(new_note)
note_list = simplenote_instance.get_note_list()[0]
print('We have:')
print(note_list)
simplenote_instance.trash_note(new_note['key'])
note_list = simplenote_instance.get_note_list()[0]
print('Trashed note:')
print(note_list)

for note in note_list:
    simplenote_instance.delete_note(note['key'])
note_list = simplenote_instance.get_note_list()[0]
print('Deleted note:')
print(note_list)

# note = simplenote_instance.get_note('agtzaW1wbGUtbm90ZXIRCxIETm90ZRiAgIDvovS2CQw')[0]
# note['content'] = 'new content'
# result = simplenote_instance.update_note(note)
