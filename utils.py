import re
from pathlib import Path

class Folder:
    def __init__(self, name):
        self.name = name
        self.files = []
        self.folders = []

    def add_pages(self, pages):
        self.files.extend(pages)
    
    def add_folder(self, folder):
        self.folders.append(folder)  # Fixed the typo here

    def add_folders(self, folders):
        self.folders.extend(folders)

    def add_page(self, page):
        path = page.name
        content = page.content
        current_folder = self
        for folder in path.split("/")[:-1]:
            if folder not in [f.name for f in current_folder.folders]:
                new_folder = Folder(folder)
                current_folder.add_folder(new_folder)
                current_folder = new_folder
            else:
                current_folder = current_folder.get_folder(folder)
        if (path if "/" not in path else path.split("/")[-1]) == "":
            return
        current_folder.files.append(File(path if "/" not in path else path.split("/")[-1], content))


    def get_folder(self, name):
        for folder in self.folders:
            if folder.name == name:
                return folder


class File:
    def __init__(self, name, content=""):
        self.name = name
        self.content = content

class ByteFile(File):
    pass

def capatlize(word):
    return ''.join(word.capitalize() for word in word.split('_'))

def decapatlize(word):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', word)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()

