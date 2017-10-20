import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, Gdk
import itertools
import unittest
import collections

class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="国语")

        self.set_default_size(700, 400)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.create_textview()
        self.config_textview()

        self.clickManager = ClickManager(self.textview)
        self.history = LookupHistory()

        self.connect("delete-event", self.shutdown)

    def shutdown(self, bla1, bla2):
        print(self.history.exportHistory())
        Gtk.main_quit()

    def create_textview(self):
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        self.grid.attach(scrolledwindow, 0, 1, 3, 1)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.CHAR)

        # eventbox to intercept/trap textview events
        self.eventbox = Gtk.EventBox()
        scrolledwindow.add(self.eventbox)

        self.textbuffer = self.textview.get_buffer()
        self.eventbox.add(self.textview)
        self.eventbox.set_above_child(True)

        # tag to highlight current word
        self.curHlTag = self.textbuffer.create_tag("curHl", background="red")

    def config_textview(self):
        self.loadDocumentIntoViewer('/home/felix/Projects/pychinese/santi5.txt')
        self.setViewerFontSize(32)

        self.eventbox.connect('button-press-event', self.clickedViewer)

    def loadDocumentIntoViewer(self, filename):
        with open(filename, 'r') as content_file:
            content = content_file.read()
        self.textbuffer.set_text(content)
        #self.textbuffer.set_text("你好你好你好你好")
        
    def setViewerFontSize(self, size_in_points):
        self.font_size_tag = self.textbuffer.create_tag("font_size", size_points=size_in_points)
        self.textbuffer.apply_tag(self.font_size_tag, self.textbuffer.get_start_iter(), self.textbuffer.get_end_iter())

    def clickedViewer(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            return True
            
        buffer_x, buffer_y = self.textview.window_to_buffer_coords(Gtk.TextWindowType.TEXT, event.x, event.y)
        #print(buffer_x, buffer_y)
        i, it, tr = self.textview.get_iter_at_position(buffer_x, buffer_y)

        result = self.clickManager.getResultForClick(it)

        # highlight new word
        if result != False:
            #print(result)
            word = result[0]

            self.history.addEntry(word)
            #print(self.history.exportHistory())
            
            wmbl_list = list(result[1])
            self.highlightNewWord(it, wmbl_list[0])

            dict_entries = list(map(lambda wmbl: cedict.lookupByIdx(wmbl.dictIdx), wmbl_list))
            print()
            print(*dict_entries, sep="\n")
            
            

    def highlightNewWord(self, it, wmbl):
        self.textbuffer.remove_tag(self.curHlTag, self.textbuffer.get_start_iter(), self.textbuffer.get_end_iter())

        start_it = it.copy()
        start_it.backward_chars(wmbl.posInEntry)
        end_it = it.copy()
        end_it.forward_chars(len(wmbl.word) - wmbl.posInEntry)
        self.textbuffer.apply_tag(self.curHlTag, start_it, end_it)


class LookupHistory():
    def __init__(self):
        #self.counter = 0
        self.history = collections.OrderedDict.fromkeys([])

    def addEntry(self, word):
        self.history[word] = None
        
        # if word not in self.history: # this is if we want them to have order of last-clicked, as opposed to first-clicked. but we don't
        #     self.counter += 1
        #     self.history[word] = self.counter

    def exportHistory(self):
        return list(self.history.keys())

class ClickManager():
    def __init__(self, textview):
        self.textview = textview

        # machinery to cycle through results on repeated click
        self.lastClickedIdx = None
        self.multiClickResults = None # either is None or a cyclic generator
        #self.lastMultiClickResults = None # to show overlaps from new and last one at the end of cycling

        self.curPositionResultHistory = set()

        #self.lastResult = None
        # two clicks on different characters of the same word would yield the same result word
        # even though we can guess that this is not the desired result. We save it so we can queue it last when this happens

    def getResultForClick(self, it):
        """finds dictionary entries for words around the character at it
        Returns tuple of such a word match and a list of all its dict entries
        repeated clicks on the same character cycle through the other word matches"""
        
        # repeated click
        if self.lastClickedIdx == it.get_offset():
            if self.multiClickResults == False:
                return False

        else:
            self.clickAtNewPosition(it)

        # update fields and return
        nextRes = next(self.multiClickResults)
        self.curPositionResultHistory.add(nextRes[0])
        return nextRes

    def clickAtNewPosition(self, it):
        # click at new position
        self.lastClickedIdx = it.get_offset()   

        rs = cedict.findEntriesContainingCharacter(it.get_char())
        matches = []
        for wmbl in rs:
            leftChars = wmbl.posInEntry
            rightChars = len(wmbl.word) - leftChars - 1
            
            match = True
            it_left = it.copy()
            for i in range(leftChars):
                if(it_left.backward_char()):
                    if it_left.get_char() != wmbl.word[wmbl.posInEntry-1 - i]:
                        match = False
                        break
                else: # iterator is at end of text and repeats itself
                    match = False
                    break
                    
            it_right = it.copy()        
            for i in range(rightChars):
                if(it_right.forward_char()):
                    if it_right.get_char() != wmbl.word[wmbl.posInEntry+1 + i]:
                        match = False
                        break
                else: # iterator is at beginning of text
                    match = False
                    break

            if match == True:
                matches.append(wmbl)

        # sort matches:
        # major sort criterion is match word length
        # prioritizes matches starting closer to click point
        # that is: longest match, if equal length, rightmost match
        sort_minor = sorted(matches, key=lambda m: m.posInEntry, reverse=False)
        matchesSorted = sorted(sort_minor, key=lambda m: len(m.word), reverse=True)

        # group multiple entries for the same word
        matchesBatches = itertools.groupby(matchesSorted, lambda m: m.word)

        # make this permanent, since groupby entries are lost after one access
        matchesBatchesList = list(map(lambda m: (m[0], list(m[1])), matchesBatches))

        # filter those matches that are common to the last (different) clicked opsition.
        # move them to the end, since if someone clicked a different letter he wants to see different matches
        l_recently_seen = [m for m in matchesBatchesList if m[0] in self.curPositionResultHistory]
        l_fresh = [m for m in matchesBatchesList if m[0] not in self.curPositionResultHistory]
        matchesBatchesListFiltered = l_fresh + l_recently_seen
        #assert (set(map(lambda m: m[0], matchesBatchesList)) == set(map(lambda m: m[0], matchesBatchesListFiltered)))

        # update class fields
        self.curPositionResultHistory = set() # reset the variable used for this detection
        self.multiClickResults = itertools.cycle(matchesBatchesListFiltered) # put results in our cycle

        
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
#win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()

class TestCeDict(unittest.TestCase):
    def test(self):
        print(cedict.characterOccurences['你'])
