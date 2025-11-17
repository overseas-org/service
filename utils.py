import re

class Folder:
    def __init__(self, name):
        self.name = name
        self.files = []
        self.folders = []

    def add_page(self, page):
        self.files.append(page)

    def add_pages(self, pages):
        self.files.extend(pages)
    
    def add_folder(self, folder):
        self.folders.append(folder)  # Fixed the typo here

    def add_folders(self, folders):
        self.folders.extend(folders)


class File:
    def __init__(self, name, content=""):
        self.name = name
        self.content = content

def capatlize(word):
    return ''.join(word.capitalize() for word in word.split('_'))

def decapatlize(word):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', word)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()

