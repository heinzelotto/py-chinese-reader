import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango
import itertools
import unittest

class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="国语")

        self.set_default_size(600, 500)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.create_textview()
        self.config_textview()

        self.clickManager = ClickManager(self.textview)

    def create_textview(self):
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        self.grid.attach(scrolledwindow, 0, 1, 3, 1)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.CHAR)
              
        self.textbuffer = self.textview.get_buffer()
        scrolledwindow.add(self.textview)

    def config_textview(self):
        self.loadDocumentIntoViewer('/home/felix/Projects/pychinese/santi4.txt')
        self.setViewerFontSize(32)

        self.textview.connect('button-press-event', self.clickedViewer)

    def loadDocumentIntoViewer(self, filename):
        with open(filename, 'r') as content_file:
            content = content_file.read()
        self.textbuffer.set_text(content)
        #self.textbuffer.set_text("你好你好你好你好")
        
    def setViewerFontSize(self, size_in_points):
        self.font_size_tag = self.textbuffer.create_tag("font_size", size_points=size_in_points)
        self.textbuffer.apply_tag(self.font_size_tag, self.textbuffer.get_start_iter(), self.textbuffer.get_end_iter())

    def clickedViewer(self, widget, event):
        buffer_x, buffer_y = self.textview.window_to_buffer_coords(Gtk.TextWindowType.TEXT, event.x, event.y)
        print(buffer_x, buffer_y)

        results = self.clickManager.getResultsForClick(buffer_x, buffer_y)


class ClickManager():
    def __init__(self, textview):
        self.textview = textview
        self.lastClicked = False

    def getResultsForClick(self, buffer_x, buffer_y):
        i, it, tr = self.textview.get_iter_at_position(buffer_x, buffer_y)

        #if self.lastClickedIter == 

        # prepare to call smarter lookup of a word around char at curser position
        context_radius = 4
        
        it_start_context = it.copy()
        it_start_zi = it.copy()
        it_end_zi = it.copy()
        it_end_context = it.copy()

        it_start_context.backward_chars(context_radius)
        it_end_zi.forward_chars(1)        
        it_end_context.forward_chars(context_radius+1)

        context_before = it_start_context.get_slice(it_start_zi)
        zi = it_start_zi.get_slice(it_end_zi)
        context_after = it_end_zi.get_slice(it_end_context)

        #print(zi, context)
        #print(context_before, zi, context_after)
        #r = cedict.lookupWordInContext(zi, context_before, context_after)

        rs = cedict.findEntriesContainingCharacter(zi)
        matches = []
        for wmbl in rs:
            #entry = r[0]
            #posInEntry = r[1]
            leftChars = wmbl.posInEntry
            rightChars = len(wmbl.word) - leftChars - 1

            match = True
            it_left = it.copy()
            for i in range(leftChars):
                if(it_left.backward_char()):
                    #print(it_left.get_char(), entry[posInEntry-1 - i])
                    if it_left.get_char() != wmbl.word[wmbl.posInEntry-1 - i]:
                        match = False
                        break
                else:
                    # iterator is at end of text and repeats itself
                    match = False
                    break
                    
            it_right = it.copy()        
            for i in range(rightChars):
                if(it_right.forward_char()):
                    #print(it_right.get_char(), entry[posInEntry+1 + i])
                    if it_right.get_char() != wmbl.word[wmbl.posInEntry+1 + i]:
                        match = False
                        break
                else:
                    # iterator is at beginning of text
                    match = False
                    break

            if match == True:
                matches.append(wmbl)

        #print(matches)
        lookup_matches = map(lambda wmbl : cedict.lookupByIdx(wmbl.dictIdx), matches)

        print()
        for m in lookup_matches:
            print (m)

        
def filterLines(content):
    return content

class WordMatchByLetter():
    def __init__(self, word, posInEntry, dictIdx):
        self.word = word
        self.posInEntry = posInEntry
        self.dictIdx = dictIdx

class CeDict():
    def __init__(self):
        with open("/home/felix/Projects/pychinese/cedict_1_0_ts_utf-8_mdbg.txt.simp") as f:
            content = f.readlines()
            content = [x.strip() for x in content]

            lines = filterLines(content)
            self.prepareDict(content)

    def prepareDict(self, lines):
        self.entries = lines
        
        self.characterOccurences = {}
        for entryidx, l in enumerate(lines):
            ci = l[:l.find(' ')]
            for letterposition, zi in enumerate(ci):
                if zi not in self.characterOccurences:
                    self.characterOccurences[zi] = []
                self.characterOccurences[zi].append((ci, letterposition, entryidx))
        
    def findEntriesContainingCharacter(self, zi):
        if zi in self.characterOccurences:
            return map(lambda ar : WordMatchByLetter(*ar),self.characterOccurences[zi])
        else:
            return False
    
    def lookup(self, ci):
        raise NotImplementedError('Need to change this')
        if ci in self.dictionary:
            return self.dictionary[ci]
        else:
            return False

    def lookupByIdx(self, idx):
        if idx < len(self.entries):
            return self.entries[idx]
        else:
            return False

    def lookupWordInContext(self, zi, context_before, context_after):
        """Given character zi, and characters before and after zi,

        this will:

        1. find the longest dictionary word that contains zi and is contained
        in the context

        2. also try to find one starting at zi and spanning to context_after

        returns a dict {"longest_matches" : list(), "start_matches" : list()}
        or False if nothing is found."""
        
        return {"longest_matches" : "你好", "start_matches" : "好"}

    def unicodePinyinFromNumbers(pinyin):
        return "ā á ǎ à" # TODO
            
cedict = CeDict()
        
win = MainWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()

class TestCeDict(unittest.TestCase):
    def test(self):
        print(cedict.characterOccurences['你'])
