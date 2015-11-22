QuickSimplenote
=============

Sublime Text 2/3 plugin for Simplenote.

Overview
---------
Hit Command+Shift+S (OSX) or Windows+Shift+S (Windows) twice to start. First time it will open the settings to setup the credentials.
After setting them it will download the notes.
![Alt Settings](http://i.imgur.com/q6elJOi.png "Settings files")

Hit the shortcut again after the download is done (check the message bar) and it will **show a list of the notes**:
![Alt Notes](http://i.imgur.com/YTcngPw.png "Note List")

It will download notes every time sublime text is launched and every now and then if the _sync_every_ configuration is enabled (has a positive value), so take a look at the bar to check the status.

If a note gets updated from somewhere else
![Alt External Update](http://i.imgur.com/p9pAY6z.png "External Update")
After the next sync it will be updated on sublime as well
![Alt External Update Replicated](http://i.imgur.com/kiwCcwT.png "External Update Replicated")

If you change something on sublime the note will be updated after you save the file:
![Alt Sublime Update](http://i.imgur.com/FZVEoef.png "Sublime Update")

You can **create a note** with Command+Shift+S and then Command+Shift+N (OSX) or Windows+Shift+S and then Windows+Shift+N (Windows), a name is assigned according to the first line of the note (remember to save!)
![Alt Sublime New Note on List](http://i.imgur.com/vH5POCU.png "Sublime New Note on List")

You can **delete notes** with Command+Shift+S and then Command+Shift+D (OSX) or Windows+Shift+S and then Windows+Shift+D (Windows) while seeing the note
![Alt Sublime Delete Note](http://i.imgur.com/3htEmBm.png "Sublime Delete Note")

All those commands are also accesible from the command palette:
![Alt Command Palette](http://i.imgur.com/n0tROSK.png "Command Palette")

Conflict Resolution
---------
If a change is made on a different client
![Alt Remote change](http://i.imgur.com/WjRAccA.png "Remote change")
And in the middle of that change and a sync we have made local changes in sublime
![Alt Local change](http://i.imgur.com/8YRoAmt.png "Local change")

We get a dialog asking what we want to do to resolve the conflict
![Alt Dialog](http://i.imgur.com/FUI0cFw.png "Dialog")

Selecting _Overwrite_ will discard overwrite the local changes with what the server has.

Selecting _Cancel_ instead will leave alone the local file, if you save after this the result will most likely be a merge performed by simplenote between the local data and the remote data.

There are two options that automate the conflict resolution mode: _on_conflict_use_server_ and _on_conflict_leave_alone_ for _Overwrite_ and _Cancel_ respectively.

Beta Features
---------
The options _autosave_debounce_time_ and title_extension_map are on beta.

Uncommenting **autosave_debounce_time** makes Sublime Text behave similarly to a simplenote client, saving data after each change. The value of the option tells the plugin how much to wait after the last pressed key to save the data.

A small value might start making simplenote reject changes and a big value might make you think you saved something after closing sublime even when it wasn't saved yet.

**title_extension_map** is an array used to apply extensions to the temporal note files, so it can interact with other extensions, most notably plaintasks:
![Alt Plaintasks configuration](http://i.imgur.com/EbVj4Ul.png "Plaintasks configuration")
Each row of the array takes a regex that the plugin uses against the note title and an extension to add at the end.
![Alt Plaintasks use](http://i.imgur.com/VgGOlLf.png "Plaintasks use")

**note_syntax** is a property that accepts a sublime syntax file (e.g. "Packages/Java/Java.tmLanguage" or "Packages/MarkdownEditing/Markdown.tmLanguage" if you have MarkdownEditing installed) and makes all notes start with this syntax, so if you use Simplenote just for Java files or you want all your notes in Markdown this can help.

About your data and bugs
---------
This is a free piece of software and is distributed as is, it might contain bugs that due to the nature of the application might result in data loss, please make periodic backups of any important piece of information.

In case of data loss it might be helpful to use the real simplenote page or an official client with history capabilities to try and find the last sane version of your note. 