import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango
import itertools

class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="国语")

        self.set_default_size(600, 500)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.create_textview()
        self.config_textview()

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
        
    def setViewerFontSize(self, size_in_points):
        self.font_size_tag = self.textbuffer.create_tag("font_size", size_points=size_in_points)
        self.textbuffer.apply_tag(self.font_size_tag, self.textbuffer.get_start_iter(), self.textbuffer.get_end_iter())

    def clickedViewer(self, widget, event):
        buffer_x, buffer_y = self.textview.window_to_buffer_coords(Gtk.TextWindowType.TEXT, event.x, event.y)
        i, it, tr = self.textview.get_iter_at_position(buffer_x, buffer_y)

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
        r = cedict.lookupWordInContext(zi, context_before, context_after)

        # old method
        result_entry = False
        for i in range(1, 10):
            it_forward = it.copy()
            it_forward.forward_chars(i)
            ci = it.get_slice(it_forward)
            entry = cedict.lookup(ci)
            if entry != False:
                result_entry = entry
            else:
                break
        print(result_entry)

        


class CeDict():
    def __init__(self):
        with open("/home/felix/Projects/pychinese/cedict_1_0_ts_utf-8_mdbg.txt.simp") as f:
            content = f.readlines()
            content = [x.strip() for x in content]
            self.dictionary = {}
            for entry in content:
                w = entry[:entry.find(' ')]
                if w in self.dictionary:
                    self.dictionary[w] += '\n'+entry
                    #print(self.dictionary[w])
                else:
                    self.dictionary[w] = entry

    def lookup(self, ci):
        if ci in self.dictionary:
            return self.dictionary[ci]
        else:
            return False

    def lookupWordInContext(zi, context_before, context_after):
        """Given character zi, and characters before and after zi,

        this will:

        1. find the longest dictionary word that contains zi and is contained
        in the context

        2. also try to find one starting at zi and spanning to context_after

        returns a dict {"longest_matches" : list(), "start_matches" : list()}
        or False if nothing is found."""
        
        return {longest_matches : "你好", "start_matches" : "好"}

    def unicodePinyinFromNumbers(pinyin):
        return "ā á ǎ à" # TODO
            
cedict = CeDict()
        
win = MainWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
