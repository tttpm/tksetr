import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter.filedialog import askopenfilename

from weakref import ref
from base64 import b64encode, b64decode
from zlib import decompress, compressobj, MAX_WBITS, DEFLATED
import copy


CLEAR_COLOR = '\033[0m'
LOOPER_WIDTH = 20
LOOPER_HEIGHT = 18

class Color():
    
    '''literally color!!'''
    
    def __init__(self, red: int, green: int, blue: int, alpha = 1):
        
        '''create Color using red, green, and alpha values'''
        
        try:
            assert type(red) == int and 0 <= red <= 255
            self.red = red
            
        except:
            raise ValueError('invalid red value')

        try:
            assert type(green) == int and 0 <= green <= 255
            self.green = green
            
        except:
            raise ValueError('invalid green value')


        try:
            assert type(blue) == int and 0 <= blue <= 255
            self.blue = blue
            
        except:
            raise ValueError('invalid blue value')
        
        try:
            if alpha > 1: alpha /= 255
            assert (type(alpha) == float or type(alpha) == int) and 0 <= alpha <= 1
            self.alpha = alpha
            
        except:
            raise ValueError('invalid alpha value')
        


        
    @classmethod
    def create_from_rgba(cls, r: int, g: int, b: int, a: int):
        
        '''create Color using red, green, blue and alpha values'''
        
        return Color(r, g, b, a)



    @classmethod
    def create_from_hex(cls, hex_: str):

        '''create Color using six- or eight-digit HEX'''
        
        hex_ = hex_.replace('#', '')
        
        try:
            
            r = int(hex_[:2], 16)
            g = int(hex_[2:4], 16)
            b = int(hex_[4:6], 16)
            a = 1
            if len(hex_) > 6: a = int(hex_[6:8], 16)  / 255

            
        except:
            raise ValueError('invalid HEX')
        
        return Color(r, g, b, a)



    @classmethod
    def create_from_ansi(cls, ansi: str):

        '''create Color using ANSI code'''
        
        try:
            ansi = ansi.split(';') 
            r = int(ansi[2])
            g = int(ansi[3])
            b = int(ansi[4][:-1])
            
        except:
            raise ValueError('invalid ANSI code')
        
        return Color(r, g, b)


    def get_hex(self):

        '''get eight-digit HEX from Color'''
    
        alphabet = '0123456789abcdef'
        
        return (alphabet[self.red // 16] + alphabet[self.red % 16] +
               alphabet[self.green // 16] + alphabet[self.green % 16] +
               alphabet[self.blue // 16] + alphabet[self.blue % 16] +
               alphabet[round(self.alpha * 255) // 16] + alphabet[round(self.alpha * 255) % 16])

    def get_ansi(self, back = 0, fore = 1):
        
        '''get ANSI code from Color'''
        
        return ((f"\033[38;2;{self.red};{self.green};{self.blue}m" if fore else '') +
               (f"\033[48;2;{self.red};{self.green};{self.blue}m" if back else ''))



    def __eq__(self, other):
        if type(other) != Color or not(self.red == other.red and self.blue == other.blue and self.green == other.green and self.alpha == other.alpha):
            return False 
        return True



    def __str__(self):
        return self.get_ansi(back = True)


    def __add__(self, other):

        if type(other) == Color:
            
            a = other.alpha + self.alpha * (1 - other.alpha)

            if not a:
                return Color(0,0,0,0)
    
            r = round((other.alpha * other.red + self.alpha * self.red * (1 - other.alpha)) / a)
        
            g = round((other.alpha * other.green + self.alpha * self.green * (1 - other.alpha)) / a)
        
            b = round((other.alpha * other.blue + self.alpha * self.blue * (1 - other.alpha)) / a)
          
            return Color(r, g, b, a)

    def __iter__(self): 
        return iter((self.red, self.green, self.blue, self.alpha))

  



class Cursor():

    def __init__(self, row: int, column: int, maxrow: int, maxcolumn: int, color: Color):
        
        self.row = row
        self.column = column
        self.maxrow = maxrow
        self.maxcolumn = maxcolumn
        self.color = color

    def up(self): self.row -= 1 if self.row > 0 else 0
    
    def left(self): self.column -= 1 if self.column > 0 else 0
    
    def down(self): self.row += 1 if self.row < self.maxrow - 1 else 0

    def right(self): self.column += 1 if self.column < self.maxcolumn - 1 else 0




class ColorArray():
    
    '''array of Colors'''

    def __init__(self, size: int, color: Color, cursor = None, index = 0):

        self.size = size
        self.index = index
        self.cursor = cursor
        
        if type(color) != Color:
            raise ValueError('ColorArray can only contain Color objects')
        
        self.__content = [color] * size
        

    def __setitem__(self, index, value):
        
        if type(value) != Color:
            raise ValueError('ColorArray can only contain Color objects')
        
        self.__content[index] = value


        
    def __getitem__(self, index):
        return self.__content[index]



    def __str__(self):
        
        res = ''
        
        for i in range(self.size):
            
            c = self[i]
            
            if self.cursor and self.cursor.column == i and self.cursor.row == self.index:
                c = self.cursor.color
    
            res += str(c) + '##'

            
        return res + CLEAR_COLOR



    def __len__(self):
        return len(self.__content)







class ColorMatrix(): 

    '''array of ColorArrays'''
    
    def __init__(self, width: int, height: int, color: Color, cursor = None, side_text: str = ''):

        self.width = width
        self.height = height
        self.cursor = cursor
        
        self.history = []
        self.hist_pos = -1
        
        self.side_text = side_text.strip('\n').split('\n')

        

        self.__content = []
        
        for i in range(height):
            
            self.__content.append(ColorArray(width, color, cursor = self.cursor, index = i))

        self.__record()

    def set_cursor(self, cursor):
        self.cursor = cursor
        for i in range(self.height):
            self.__content[i].cursor = cursor()
            
    def __getitem__(self, index):
        return self.__content[index]



    def __setitem__(self, index, value):
        
        if type(value) != ColorArray:
            raise ValueError('ColorMatrix can only contain ColorArray objects')
        self[index] = value

    def paint(self, row = None, column = None, new_color = None):
        row = row if row != None else self.cursor.row
        column = column if column != None else self.cursor.column
        new_color = new_color if new_color != None else self.cursor.color
        self.__content[row][column] = new_color
        self.__record()

    def __str__(self):
        
        res =   '##' * (self.width + 2)  + '\n'
        
        for i in range(self.height):
            res += '##' + str(self[i]) + '##' + (self.side_text[i] if i < len(self.side_text) else '') + '\n'
        return res + '##' * (self.width + 2)
    



    def __add__(self, other):

        if type(other) != ColorMatrix:
            raise TypeError("can only add ColorMatrix to ColorMatrix")
        
        result = ColorMatrix(max(self.width, other.width), max(self.height, other.height), Color(0,0,0,0), self.cursor if self.cursor else other.cursor)


        for i in range(result.height):
            
            for j in range(result.width):

                first, second = Color(0,0,0,0), Color(0,0,0,0)

                if i < self.height and j < self.width:
                    first = self[i][j]
                    
                if i < other.height and j < other.width:
                    second = other[i][j]
                
                result[i][j] = first + second
                
        result.side_text = None       
        if self.side_text:
            result.side_text = self.side_text
        if other.side_text:
            result.side_text = other.side_text
            
        return result   


        

    def __fill(self, row: int, column: int, new_color: Color):
        
        filling = [(row, column)]
        checked = [[0] * self.width for _ in range(self.height)]
        
        while filling:

            to_fill = []
            for elem in filling:
                x, y = elem
                
                if x > 0 and not checked[x-1][y]:
                    checked[x-1][y] = 1
                    if self[x-1][y] == self[x][y]: to_fill.append((x-1, y))

                if y > 0 and not checked[x][y-1]:
                    checked[x][y-1] = 1
                    if self[x][y-1] == self[x][y]: to_fill.append((x, y-1))


                if x < (self.height - 1) and not checked[x+1][y]:
                    checked[x+1][y] = 1
                    if self[x+1][y] == self[x][y]: to_fill.append((x+1, y))

                if y < (self.width - 1) and not checked[x][y + 1]:
                    checked[x][y+1] = 1
                    if self[x][y+1] == self[x][y]: to_fill.append((x, y+1))
                    
                self[x][y] = new_color

            filling = to_fill[::]

    def fill(self, row = None, column = None, new_color = None):
        row = row if row != None else self.cursor.row
        column = column if column != None else self.cursor.column
        new_color = new_color if new_color != None else self.cursor.color
        self.__fill(row, column, new_color)
        self.__record()

    def get_trskin(self):
        res = ''
        for i in range(LOOPER_HEIGHT):
            for j in range(LOOPER_WIDTH):
                res += self[i][j].get_hex() + ';'
                
        deflate_compress = compressobj(9, DEFLATED, -MAX_WBITS)
        compressed = deflate_compress.compress(bytes(res, encoding ='utf-8')) + deflate_compress.flush()
        encrypted = b64encode(compressed)
        return "trSkin1" + encrypted.decode()


    @classmethod
    def create_from_trskin(cls, skin: str, cursor=None, side_text=''):
        res = ColorMatrix(LOOPER_WIDTH, LOOPER_HEIGHT, Color(0,0,0,0), cursor, side_text)
        compressed = b64decode(skin[7:])
        hexes = str(decompress(compressed, -MAX_WBITS).decode()).split(';')
        hexes.pop()
        i, j = 0, 0
        for h in hexes:
            if j == 20:
                i += 1
                j = 0
            res[i][j] = Color.create_from_hex(h)
            j += 1
            
        return res



    @classmethod
    def create_from_list(cls, source: list, cursor=None, side_text=''):

        result = ColorMatrix(len(max(source, key = len)), len(source), Color(0,0,0,0), cursor, side_text)

        for i in range(result.height):

            for j in range(result.width):

                if j < len(source[i]):

                    if type(source) != Color:
                        result[i][j] = source[i][j]
        return result
                        

    @classmethod
    def create_looper(cls, primary_color = Color(255, 255, 255), secondary_color = Color(0, 0, 0), background = Color(0,0,0,0), cursor=None, side_text=''):
        e = background
        p, s = primary_color, secondary_color
        x, y = p + Color(0,0,0,68), s + Color(0,0,0,68)
        return ColorMatrix.create_from_list([
            
            [e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e],
            [e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e, e],
            [e, e, e, x, x, p, p, p, p, p, p, p, p, p, p, p, p, e, e, e],
            [e, e, x, x, p, p, p, p, p, p, p, p, p, p, p, p, p, p, e, e],
            [e, e, x, x, p, p, p, p, p, p, p, p, p, p, p, p, p, p, e, e],
            [e, e, x, x, p, p, p, p, p, s, s, p, p, p, s, s, p, p, e, e],
            [e, e, x, x, p, p, p, p, p, s, s, p, p, p, s, s, p, p, e, e],
            [e, e, x, x, p, p, p, p, p, s, s, p, p, p, s, s, p, p, e, e],
            [e, e, x, x, p, p, p, p, p, s, s, p, p, p, s, s, p, p, e, e],
            [e, e, x, x, p, p, p, p, p, p, p, p, p, p, p, p, p, p, e, e],
            [e, e, x, x, p, p, p, p, p, p, p, p, p, p, p, p, p, p, e, e],
            [e, e, y, y, s, s, s, s, s, s, s, s, s, s, s, s, s, s, e, e],
            [e, e, y, y, s, s, s, s, s, s, s, s, s, s, s, s, s, s, e, e],
            [e, e, y, y, s, s, s, s, s, s, s, s, s, s, s, s, s, s, e, e],
            [e, e, y, y, s, s, s, s, s, s, s, s, s, s, s, s, s, s, e, e],
            [e, e, e, y, y, s, s, s, s, s, s, s, s, s, s, s, s, e, e, e],
            [e, e, e, e, e, e, s, s, s, e, e, e, e, s, s, s, e, e, e, e],
            [e, e, e, e, e, e, s, s, s, e, e, e, e, s, s, s, e, e, e, e]
            
            ], cursor, side_text)

    def get_list(self):
        return self.__content

    def __record(self): #he rember :D
        if self.hist_pos != -1:
            self.history = self.history[:self.hist_pos+1]
        self.hist_pos = -1
        self.history.append(copy.deepcopy(self.get_list()))

    def __restore(self, index): #why.
        cm = self.history[index]
        for i in range(self.height):
            for j in range(self.width):
                self[i][j] = cm[i][j]

    def undo(self):
        if len(self.history) <= -self.hist_pos:
            return 0
        self.hist_pos -= 1
        self.__restore(self.hist_pos)
        return 1

    def redo(self):
        if self.hist_pos == -1:
            return 0
        self.hist_pos += 1
        self.__restore(self.hist_pos)
        return 1        

bkg = ColorMatrix(20, 18, Color(255, 255, 255))
canv = ColorMatrix(20, 18, Color(0,0,0,0))

mode = 'brush'
color = Color.create_from_hex('#000000')

def UAHAHHAAHAHAHH(r, c):
    if mode == 'brush':
        canv.paint(r, c, color)
    if mode == 'eraser':
        canv.paint(r, c, Color(0,0,0,0))
    if mode == 'fill':
        canv.fill(r, c, color)
    draw()


def EHEHEHHEHEHE():
    global color
    color = Color.create_from_hex(askcolor()[1])
    colorlab.configure(background='#'+color.get_hex()[:-2])
    
def draw():
    m = bkg+canv
    for i in range(18):
        for j in range(20):
            exec(f"lab_{i}_{j}.configure(background='#{m[i][j].get_hex()[:-2]}')")

def fhgfnjkmk():
    global canv
    a = gimme_skin()
    canv = a 
    draw()


def gimme_skin():
    ans = []
    rt = tk.Toplevel(root)
    lbl = tk.Label(rt, text='ну давай сюда свой скин')
    lbl.grid()
    entr = tk.Entry(rt)
    entr.grid(row = 1)
    err = tk.Label(rt)
    err.grid(row = 2)


    def prikol():
        skin = entr.get()
        try:
            ans.append(ColorMatrix.create_from_trskin(skin))

            rt.destroy()
        except:
            err.configure(text='это не скин.')
            
    confirm = tk.Button(rt, text = 'на', command = prikol)
    confirm.grid(row=3)
    
    rt.wait_window()
    return ans[0]

def ghnggbfbgn():
    rt = tk.Toplevel(root)
    tk.Label(rt, text = 'ну держи свой скин').grid(row=0,column=0)
    entr = tk.Entry(rt)
    entr.insert(0, canv.get_trskin())
    entr.grid(row=1)
    btn = tk.Button(rt, text = 'ок', command=lambda:rt.destroy())
    btn.grid(row=2)
    rt.wait_window()
    
def qwerfghn():
    path = askopenfilename(filetypes=('пээнгэшки', '*.png'))
    canv = ColorMatrix.create_from_img(path)
    draw()

def suka(m):
    global mode
    mode = m
    modelab.configure(text=f"режим: {mode}")
    
def suka1():
    global canv
    canv.undo()
    draw()

def suka2():
    global canv
    canv.redo()
    draw()
    
root = tk.Tk()
root.resizable(0,0)
root.title("skin editor")
labframe = tk.Frame(root)
sqr = tk.PhotoImage(width=20,height=20)
lab_0_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 0))
lab_0_0.grid(row=0, column=0)
lab_0_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 1))
lab_0_1.grid(row=0, column=1)
lab_0_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 2))
lab_0_2.grid(row=0, column=2)
lab_0_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 3))
lab_0_3.grid(row=0, column=3)
lab_0_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 4))
lab_0_4.grid(row=0, column=4)
lab_0_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 5))
lab_0_5.grid(row=0, column=5)
lab_0_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 6))
lab_0_6.grid(row=0, column=6)
lab_0_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 7))
lab_0_7.grid(row=0, column=7)
lab_0_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 8))
lab_0_8.grid(row=0, column=8)
lab_0_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 9))
lab_0_9.grid(row=0, column=9)
lab_0_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 10))
lab_0_10.grid(row=0, column=10)
lab_0_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 11))
lab_0_11.grid(row=0, column=11)
lab_0_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 12))
lab_0_12.grid(row=0, column=12)
lab_0_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 13))
lab_0_13.grid(row=0, column=13)
lab_0_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 14))
lab_0_14.grid(row=0, column=14)
lab_0_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 15))
lab_0_15.grid(row=0, column=15)
lab_0_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 16))
lab_0_16.grid(row=0, column=16)
lab_0_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 17))
lab_0_17.grid(row=0, column=17)
lab_0_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 18))
lab_0_18.grid(row=0, column=18)
lab_0_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(0, 19))
lab_0_19.grid(row=0, column=19)
lab_1_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 0))
lab_1_0.grid(row=1, column=0)
lab_1_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 1))
lab_1_1.grid(row=1, column=1)
lab_1_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 2))
lab_1_2.grid(row=1, column=2)
lab_1_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 3))
lab_1_3.grid(row=1, column=3)
lab_1_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 4))
lab_1_4.grid(row=1, column=4)
lab_1_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 5))
lab_1_5.grid(row=1, column=5)
lab_1_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 6))
lab_1_6.grid(row=1, column=6)
lab_1_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 7))
lab_1_7.grid(row=1, column=7)
lab_1_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 8))
lab_1_8.grid(row=1, column=8)
lab_1_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 9))
lab_1_9.grid(row=1, column=9)
lab_1_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 10))
lab_1_10.grid(row=1, column=10)
lab_1_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 11))
lab_1_11.grid(row=1, column=11)
lab_1_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 12))
lab_1_12.grid(row=1, column=12)
lab_1_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 13))
lab_1_13.grid(row=1, column=13)
lab_1_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 14))
lab_1_14.grid(row=1, column=14)
lab_1_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 15))
lab_1_15.grid(row=1, column=15)
lab_1_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 16))
lab_1_16.grid(row=1, column=16)
lab_1_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 17))
lab_1_17.grid(row=1, column=17)
lab_1_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 18))
lab_1_18.grid(row=1, column=18)
lab_1_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(1, 19))
lab_1_19.grid(row=1, column=19)
lab_2_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 0))
lab_2_0.grid(row=2, column=0)
lab_2_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 1))
lab_2_1.grid(row=2, column=1)
lab_2_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 2))
lab_2_2.grid(row=2, column=2)
lab_2_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 3))
lab_2_3.grid(row=2, column=3)
lab_2_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 4))
lab_2_4.grid(row=2, column=4)
lab_2_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 5))
lab_2_5.grid(row=2, column=5)
lab_2_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 6))
lab_2_6.grid(row=2, column=6)
lab_2_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 7))
lab_2_7.grid(row=2, column=7)
lab_2_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 8))
lab_2_8.grid(row=2, column=8)
lab_2_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 9))
lab_2_9.grid(row=2, column=9)
lab_2_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 10))
lab_2_10.grid(row=2, column=10)
lab_2_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 11))
lab_2_11.grid(row=2, column=11)
lab_2_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 12))
lab_2_12.grid(row=2, column=12)
lab_2_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 13))
lab_2_13.grid(row=2, column=13)
lab_2_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 14))
lab_2_14.grid(row=2, column=14)
lab_2_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 15))
lab_2_15.grid(row=2, column=15)
lab_2_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 16))
lab_2_16.grid(row=2, column=16)
lab_2_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 17))
lab_2_17.grid(row=2, column=17)
lab_2_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 18))
lab_2_18.grid(row=2, column=18)
lab_2_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(2, 19))
lab_2_19.grid(row=2, column=19)
lab_3_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 0))
lab_3_0.grid(row=3, column=0)
lab_3_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 1))
lab_3_1.grid(row=3, column=1)
lab_3_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 2))
lab_3_2.grid(row=3, column=2)
lab_3_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 3))
lab_3_3.grid(row=3, column=3)
lab_3_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 4))
lab_3_4.grid(row=3, column=4)
lab_3_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 5))
lab_3_5.grid(row=3, column=5)
lab_3_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 6))
lab_3_6.grid(row=3, column=6)
lab_3_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 7))
lab_3_7.grid(row=3, column=7)
lab_3_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 8))
lab_3_8.grid(row=3, column=8)
lab_3_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 9))
lab_3_9.grid(row=3, column=9)
lab_3_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 10))
lab_3_10.grid(row=3, column=10)
lab_3_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 11))
lab_3_11.grid(row=3, column=11)
lab_3_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 12))
lab_3_12.grid(row=3, column=12)
lab_3_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 13))
lab_3_13.grid(row=3, column=13)
lab_3_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 14))
lab_3_14.grid(row=3, column=14)
lab_3_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 15))
lab_3_15.grid(row=3, column=15)
lab_3_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 16))
lab_3_16.grid(row=3, column=16)
lab_3_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 17))
lab_3_17.grid(row=3, column=17)
lab_3_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 18))
lab_3_18.grid(row=3, column=18)
lab_3_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(3, 19))
lab_3_19.grid(row=3, column=19)
lab_4_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 0))
lab_4_0.grid(row=4, column=0)
lab_4_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 1))
lab_4_1.grid(row=4, column=1)
lab_4_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 2))
lab_4_2.grid(row=4, column=2)
lab_4_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 3))
lab_4_3.grid(row=4, column=3)
lab_4_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 4))
lab_4_4.grid(row=4, column=4)
lab_4_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 5))
lab_4_5.grid(row=4, column=5)
lab_4_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 6))
lab_4_6.grid(row=4, column=6)
lab_4_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 7))
lab_4_7.grid(row=4, column=7)
lab_4_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 8))
lab_4_8.grid(row=4, column=8)
lab_4_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 9))
lab_4_9.grid(row=4, column=9)
lab_4_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 10))
lab_4_10.grid(row=4, column=10)
lab_4_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 11))
lab_4_11.grid(row=4, column=11)
lab_4_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 12))
lab_4_12.grid(row=4, column=12)
lab_4_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 13))
lab_4_13.grid(row=4, column=13)
lab_4_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 14))
lab_4_14.grid(row=4, column=14)
lab_4_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 15))
lab_4_15.grid(row=4, column=15)
lab_4_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 16))
lab_4_16.grid(row=4, column=16)
lab_4_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 17))
lab_4_17.grid(row=4, column=17)
lab_4_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 18))
lab_4_18.grid(row=4, column=18)
lab_4_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(4, 19))
lab_4_19.grid(row=4, column=19)
lab_5_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 0))
lab_5_0.grid(row=5, column=0)
lab_5_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 1))
lab_5_1.grid(row=5, column=1)
lab_5_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 2))
lab_5_2.grid(row=5, column=2)
lab_5_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 3))
lab_5_3.grid(row=5, column=3)
lab_5_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 4))
lab_5_4.grid(row=5, column=4)
lab_5_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 5))
lab_5_5.grid(row=5, column=5)
lab_5_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 6))
lab_5_6.grid(row=5, column=6)
lab_5_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 7))
lab_5_7.grid(row=5, column=7)
lab_5_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 8))
lab_5_8.grid(row=5, column=8)
lab_5_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 9))
lab_5_9.grid(row=5, column=9)
lab_5_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 10))
lab_5_10.grid(row=5, column=10)
lab_5_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 11))
lab_5_11.grid(row=5, column=11)
lab_5_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 12))
lab_5_12.grid(row=5, column=12)
lab_5_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 13))
lab_5_13.grid(row=5, column=13)
lab_5_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 14))
lab_5_14.grid(row=5, column=14)
lab_5_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 15))
lab_5_15.grid(row=5, column=15)
lab_5_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 16))
lab_5_16.grid(row=5, column=16)
lab_5_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 17))
lab_5_17.grid(row=5, column=17)
lab_5_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 18))
lab_5_18.grid(row=5, column=18)
lab_5_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(5, 19))
lab_5_19.grid(row=5, column=19)
lab_6_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 0))
lab_6_0.grid(row=6, column=0)
lab_6_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 1))
lab_6_1.grid(row=6, column=1)
lab_6_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 2))
lab_6_2.grid(row=6, column=2)
lab_6_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 3))
lab_6_3.grid(row=6, column=3)
lab_6_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 4))
lab_6_4.grid(row=6, column=4)
lab_6_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 5))
lab_6_5.grid(row=6, column=5)
lab_6_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 6))
lab_6_6.grid(row=6, column=6)
lab_6_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 7))
lab_6_7.grid(row=6, column=7)
lab_6_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 8))
lab_6_8.grid(row=6, column=8)
lab_6_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 9))
lab_6_9.grid(row=6, column=9)
lab_6_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 10))
lab_6_10.grid(row=6, column=10)
lab_6_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 11))
lab_6_11.grid(row=6, column=11)
lab_6_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 12))
lab_6_12.grid(row=6, column=12)
lab_6_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 13))
lab_6_13.grid(row=6, column=13)
lab_6_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 14))
lab_6_14.grid(row=6, column=14)
lab_6_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 15))
lab_6_15.grid(row=6, column=15)
lab_6_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 16))
lab_6_16.grid(row=6, column=16)
lab_6_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 17))
lab_6_17.grid(row=6, column=17)
lab_6_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 18))
lab_6_18.grid(row=6, column=18)
lab_6_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(6, 19))
lab_6_19.grid(row=6, column=19)
lab_7_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 0))
lab_7_0.grid(row=7, column=0)
lab_7_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 1))
lab_7_1.grid(row=7, column=1)
lab_7_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 2))
lab_7_2.grid(row=7, column=2)
lab_7_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 3))
lab_7_3.grid(row=7, column=3)
lab_7_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 4))
lab_7_4.grid(row=7, column=4)
lab_7_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 5))
lab_7_5.grid(row=7, column=5)
lab_7_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 6))
lab_7_6.grid(row=7, column=6)
lab_7_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 7))
lab_7_7.grid(row=7, column=7)
lab_7_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 8))
lab_7_8.grid(row=7, column=8)
lab_7_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 9))
lab_7_9.grid(row=7, column=9)
lab_7_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 10))
lab_7_10.grid(row=7, column=10)
lab_7_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 11))
lab_7_11.grid(row=7, column=11)
lab_7_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 12))
lab_7_12.grid(row=7, column=12)
lab_7_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 13))
lab_7_13.grid(row=7, column=13)
lab_7_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 14))
lab_7_14.grid(row=7, column=14)
lab_7_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 15))
lab_7_15.grid(row=7, column=15)
lab_7_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 16))
lab_7_16.grid(row=7, column=16)
lab_7_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 17))
lab_7_17.grid(row=7, column=17)
lab_7_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 18))
lab_7_18.grid(row=7, column=18)
lab_7_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(7, 19))
lab_7_19.grid(row=7, column=19)
lab_8_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 0))
lab_8_0.grid(row=8, column=0)
lab_8_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 1))
lab_8_1.grid(row=8, column=1)
lab_8_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 2))
lab_8_2.grid(row=8, column=2)
lab_8_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 3))
lab_8_3.grid(row=8, column=3)
lab_8_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 4))
lab_8_4.grid(row=8, column=4)
lab_8_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 5))
lab_8_5.grid(row=8, column=5)
lab_8_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 6))
lab_8_6.grid(row=8, column=6)
lab_8_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 7))
lab_8_7.grid(row=8, column=7)
lab_8_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 8))
lab_8_8.grid(row=8, column=8)
lab_8_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 9))
lab_8_9.grid(row=8, column=9)
lab_8_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 10))
lab_8_10.grid(row=8, column=10)
lab_8_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 11))
lab_8_11.grid(row=8, column=11)
lab_8_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 12))
lab_8_12.grid(row=8, column=12)
lab_8_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 13))
lab_8_13.grid(row=8, column=13)
lab_8_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 14))
lab_8_14.grid(row=8, column=14)
lab_8_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 15))
lab_8_15.grid(row=8, column=15)
lab_8_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 16))
lab_8_16.grid(row=8, column=16)
lab_8_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 17))
lab_8_17.grid(row=8, column=17)
lab_8_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 18))
lab_8_18.grid(row=8, column=18)
lab_8_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(8, 19))
lab_8_19.grid(row=8, column=19)
lab_9_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 0))
lab_9_0.grid(row=9, column=0)
lab_9_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 1))
lab_9_1.grid(row=9, column=1)
lab_9_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 2))
lab_9_2.grid(row=9, column=2)
lab_9_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 3))
lab_9_3.grid(row=9, column=3)
lab_9_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 4))
lab_9_4.grid(row=9, column=4)
lab_9_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 5))
lab_9_5.grid(row=9, column=5)
lab_9_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 6))
lab_9_6.grid(row=9, column=6)
lab_9_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 7))
lab_9_7.grid(row=9, column=7)
lab_9_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 8))
lab_9_8.grid(row=9, column=8)
lab_9_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 9))
lab_9_9.grid(row=9, column=9)
lab_9_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 10))
lab_9_10.grid(row=9, column=10)
lab_9_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 11))
lab_9_11.grid(row=9, column=11)
lab_9_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 12))
lab_9_12.grid(row=9, column=12)
lab_9_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 13))
lab_9_13.grid(row=9, column=13)
lab_9_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 14))
lab_9_14.grid(row=9, column=14)
lab_9_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 15))
lab_9_15.grid(row=9, column=15)
lab_9_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 16))
lab_9_16.grid(row=9, column=16)
lab_9_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 17))
lab_9_17.grid(row=9, column=17)
lab_9_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 18))
lab_9_18.grid(row=9, column=18)
lab_9_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(9, 19))
lab_9_19.grid(row=9, column=19)
lab_10_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 0))
lab_10_0.grid(row=10, column=0)
lab_10_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 1))
lab_10_1.grid(row=10, column=1)
lab_10_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 2))
lab_10_2.grid(row=10, column=2)
lab_10_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 3))
lab_10_3.grid(row=10, column=3)
lab_10_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 4))
lab_10_4.grid(row=10, column=4)
lab_10_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 5))
lab_10_5.grid(row=10, column=5)
lab_10_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 6))
lab_10_6.grid(row=10, column=6)
lab_10_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 7))
lab_10_7.grid(row=10, column=7)
lab_10_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 8))
lab_10_8.grid(row=10, column=8)
lab_10_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 9))
lab_10_9.grid(row=10, column=9)
lab_10_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 10))
lab_10_10.grid(row=10, column=10)
lab_10_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 11))
lab_10_11.grid(row=10, column=11)
lab_10_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 12))
lab_10_12.grid(row=10, column=12)
lab_10_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 13))
lab_10_13.grid(row=10, column=13)
lab_10_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 14))
lab_10_14.grid(row=10, column=14)
lab_10_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 15))
lab_10_15.grid(row=10, column=15)
lab_10_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 16))
lab_10_16.grid(row=10, column=16)
lab_10_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 17))
lab_10_17.grid(row=10, column=17)
lab_10_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 18))
lab_10_18.grid(row=10, column=18)
lab_10_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(10, 19))
lab_10_19.grid(row=10, column=19)
lab_11_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 0))
lab_11_0.grid(row=11, column=0)
lab_11_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 1))
lab_11_1.grid(row=11, column=1)
lab_11_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 2))
lab_11_2.grid(row=11, column=2)
lab_11_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 3))
lab_11_3.grid(row=11, column=3)
lab_11_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 4))
lab_11_4.grid(row=11, column=4)
lab_11_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 5))
lab_11_5.grid(row=11, column=5)
lab_11_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 6))
lab_11_6.grid(row=11, column=6)
lab_11_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 7))
lab_11_7.grid(row=11, column=7)
lab_11_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 8))
lab_11_8.grid(row=11, column=8)
lab_11_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 9))
lab_11_9.grid(row=11, column=9)
lab_11_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 10))
lab_11_10.grid(row=11, column=10)
lab_11_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 11))
lab_11_11.grid(row=11, column=11)
lab_11_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 12))
lab_11_12.grid(row=11, column=12)
lab_11_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 13))
lab_11_13.grid(row=11, column=13)
lab_11_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 14))
lab_11_14.grid(row=11, column=14)
lab_11_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 15))
lab_11_15.grid(row=11, column=15)
lab_11_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 16))
lab_11_16.grid(row=11, column=16)
lab_11_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 17))
lab_11_17.grid(row=11, column=17)
lab_11_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 18))
lab_11_18.grid(row=11, column=18)
lab_11_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(11, 19))
lab_11_19.grid(row=11, column=19)
lab_12_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 0))
lab_12_0.grid(row=12, column=0)
lab_12_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 1))
lab_12_1.grid(row=12, column=1)
lab_12_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 2))
lab_12_2.grid(row=12, column=2)
lab_12_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 3))
lab_12_3.grid(row=12, column=3)
lab_12_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 4))
lab_12_4.grid(row=12, column=4)
lab_12_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 5))
lab_12_5.grid(row=12, column=5)
lab_12_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 6))
lab_12_6.grid(row=12, column=6)
lab_12_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 7))
lab_12_7.grid(row=12, column=7)
lab_12_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 8))
lab_12_8.grid(row=12, column=8)
lab_12_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 9))
lab_12_9.grid(row=12, column=9)
lab_12_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 10))
lab_12_10.grid(row=12, column=10)
lab_12_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 11))
lab_12_11.grid(row=12, column=11)
lab_12_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 12))
lab_12_12.grid(row=12, column=12)
lab_12_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 13))
lab_12_13.grid(row=12, column=13)
lab_12_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 14))
lab_12_14.grid(row=12, column=14)
lab_12_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 15))
lab_12_15.grid(row=12, column=15)
lab_12_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 16))
lab_12_16.grid(row=12, column=16)
lab_12_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 17))
lab_12_17.grid(row=12, column=17)
lab_12_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 18))
lab_12_18.grid(row=12, column=18)
lab_12_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(12, 19))
lab_12_19.grid(row=12, column=19)
lab_13_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 0))
lab_13_0.grid(row=13, column=0)
lab_13_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 1))
lab_13_1.grid(row=13, column=1)
lab_13_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 2))
lab_13_2.grid(row=13, column=2)
lab_13_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 3))
lab_13_3.grid(row=13, column=3)
lab_13_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 4))
lab_13_4.grid(row=13, column=4)
lab_13_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 5))
lab_13_5.grid(row=13, column=5)
lab_13_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 6))
lab_13_6.grid(row=13, column=6)
lab_13_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 7))
lab_13_7.grid(row=13, column=7)
lab_13_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 8))
lab_13_8.grid(row=13, column=8)
lab_13_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 9))
lab_13_9.grid(row=13, column=9)
lab_13_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 10))
lab_13_10.grid(row=13, column=10)
lab_13_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 11))
lab_13_11.grid(row=13, column=11)
lab_13_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 12))
lab_13_12.grid(row=13, column=12)
lab_13_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 13))
lab_13_13.grid(row=13, column=13)
lab_13_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 14))
lab_13_14.grid(row=13, column=14)
lab_13_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 15))
lab_13_15.grid(row=13, column=15)
lab_13_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 16))
lab_13_16.grid(row=13, column=16)
lab_13_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 17))
lab_13_17.grid(row=13, column=17)
lab_13_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 18))
lab_13_18.grid(row=13, column=18)
lab_13_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(13, 19))
lab_13_19.grid(row=13, column=19)
lab_14_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 0))
lab_14_0.grid(row=14, column=0)
lab_14_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 1))
lab_14_1.grid(row=14, column=1)
lab_14_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 2))
lab_14_2.grid(row=14, column=2)
lab_14_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 3))
lab_14_3.grid(row=14, column=3)
lab_14_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 4))
lab_14_4.grid(row=14, column=4)
lab_14_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 5))
lab_14_5.grid(row=14, column=5)
lab_14_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 6))
lab_14_6.grid(row=14, column=6)
lab_14_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 7))
lab_14_7.grid(row=14, column=7)
lab_14_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 8))
lab_14_8.grid(row=14, column=8)
lab_14_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 9))
lab_14_9.grid(row=14, column=9)
lab_14_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 10))
lab_14_10.grid(row=14, column=10)
lab_14_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 11))
lab_14_11.grid(row=14, column=11)
lab_14_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 12))
lab_14_12.grid(row=14, column=12)
lab_14_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 13))
lab_14_13.grid(row=14, column=13)
lab_14_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 14))
lab_14_14.grid(row=14, column=14)
lab_14_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 15))
lab_14_15.grid(row=14, column=15)
lab_14_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 16))
lab_14_16.grid(row=14, column=16)
lab_14_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 17))
lab_14_17.grid(row=14, column=17)
lab_14_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 18))
lab_14_18.grid(row=14, column=18)
lab_14_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(14, 19))
lab_14_19.grid(row=14, column=19)
lab_15_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 0))
lab_15_0.grid(row=15, column=0)
lab_15_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 1))
lab_15_1.grid(row=15, column=1)
lab_15_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 2))
lab_15_2.grid(row=15, column=2)
lab_15_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 3))
lab_15_3.grid(row=15, column=3)
lab_15_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 4))
lab_15_4.grid(row=15, column=4)
lab_15_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 5))
lab_15_5.grid(row=15, column=5)
lab_15_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 6))
lab_15_6.grid(row=15, column=6)
lab_15_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 7))
lab_15_7.grid(row=15, column=7)
lab_15_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 8))
lab_15_8.grid(row=15, column=8)
lab_15_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 9))
lab_15_9.grid(row=15, column=9)
lab_15_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 10))
lab_15_10.grid(row=15, column=10)
lab_15_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 11))
lab_15_11.grid(row=15, column=11)
lab_15_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 12))
lab_15_12.grid(row=15, column=12)
lab_15_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 13))
lab_15_13.grid(row=15, column=13)
lab_15_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 14))
lab_15_14.grid(row=15, column=14)
lab_15_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 15))
lab_15_15.grid(row=15, column=15)
lab_15_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 16))
lab_15_16.grid(row=15, column=16)
lab_15_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 17))
lab_15_17.grid(row=15, column=17)
lab_15_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 18))
lab_15_18.grid(row=15, column=18)
lab_15_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(15, 19))
lab_15_19.grid(row=15, column=19)
lab_16_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 0))
lab_16_0.grid(row=16, column=0)
lab_16_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 1))
lab_16_1.grid(row=16, column=1)
lab_16_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 2))
lab_16_2.grid(row=16, column=2)
lab_16_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 3))
lab_16_3.grid(row=16, column=3)
lab_16_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 4))
lab_16_4.grid(row=16, column=4)
lab_16_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 5))
lab_16_5.grid(row=16, column=5)
lab_16_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 6))
lab_16_6.grid(row=16, column=6)
lab_16_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 7))
lab_16_7.grid(row=16, column=7)
lab_16_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 8))
lab_16_8.grid(row=16, column=8)
lab_16_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 9))
lab_16_9.grid(row=16, column=9)
lab_16_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 10))
lab_16_10.grid(row=16, column=10)
lab_16_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 11))
lab_16_11.grid(row=16, column=11)
lab_16_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 12))
lab_16_12.grid(row=16, column=12)
lab_16_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 13))
lab_16_13.grid(row=16, column=13)
lab_16_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 14))
lab_16_14.grid(row=16, column=14)
lab_16_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 15))
lab_16_15.grid(row=16, column=15)
lab_16_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 16))
lab_16_16.grid(row=16, column=16)
lab_16_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 17))
lab_16_17.grid(row=16, column=17)
lab_16_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 18))
lab_16_18.grid(row=16, column=18)
lab_16_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(16, 19))
lab_16_19.grid(row=16, column=19)
lab_17_0 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 0))
lab_17_0.grid(row=17, column=0)
lab_17_1 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 1))
lab_17_1.grid(row=17, column=1)
lab_17_2 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 2))
lab_17_2.grid(row=17, column=2)
lab_17_3 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 3))
lab_17_3.grid(row=17, column=3)
lab_17_4 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 4))
lab_17_4.grid(row=17, column=4)
lab_17_5 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 5))
lab_17_5.grid(row=17, column=5)
lab_17_6 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 6))
lab_17_6.grid(row=17, column=6)
lab_17_7 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 7))
lab_17_7.grid(row=17, column=7)
lab_17_8 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 8))
lab_17_8.grid(row=17, column=8)
lab_17_9 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 9))
lab_17_9.grid(row=17, column=9)
lab_17_10 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 10))
lab_17_10.grid(row=17, column=10)
lab_17_11 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 11))
lab_17_11.grid(row=17, column=11)
lab_17_12 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 12))
lab_17_12.grid(row=17, column=12)
lab_17_13 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 13))
lab_17_13.grid(row=17, column=13)
lab_17_14 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 14))
lab_17_14.grid(row=17, column=14)
lab_17_15 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 15))
lab_17_15.grid(row=17, column=15)
lab_17_16 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 16))
lab_17_16.grid(row=17, column=16)
lab_17_17 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 17))
lab_17_17.grid(row=17, column=17)
lab_17_18 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 18))
lab_17_18.grid(row=17, column=18)
lab_17_19 = tk.Button(labframe,image=sqr,background='#ffffff',borderwidth=0,command=lambda:UAHAHHAAHAHAHH(17, 19))
lab_17_19.grid(row=17, column=19)

labframe.grid(row=0,column=0)

tlzfrm = tk.Frame(root)

tk.Button(tlzfrm, text = 'импорт', command=fhgfnjkmk).grid(row=0,column=0)
tk.Button(tlzfrm, text = 'экспорт', command=ghnggbfbgn).grid(row=0,column=1)

modelab = tk.Label(tlzfrm, text=f"режим: {mode}")
modelab.grid(row=1, column=0)
tk.Button(tlzfrm, text='кисть', command=lambda:suka('brush')).grid(row=1,column=1)
tk.Button(tlzfrm, text='ластик', command=lambda:suka('eraser')).grid(row=2,column=0)
tk.Button(tlzfrm, text='заливка', command=lambda:suka('fill')).grid(row=2,column=1)

tk.Button(tlzfrm, command = EHEHEHHEHEHE, text = "изменить цвет").grid(row=3, column=0)
colorlab = tk.Label(tlzfrm, background='#'+color.get_hex()[:-2], text='сейчас такой')
colorlab.grid(row=3, column = 1)

tk.Button(tlzfrm, command=suka1, text='ундо').grid(row=4, column=0)
tk.Button(tlzfrm, command=suka2, text='редо').grid(row=4, column=1)

tlzfrm.grid(row = 0, column=1)
draw()
root.mainloop()
#хочу 69 кб блин $*%($*)(&$(*#%(*$*^W&*Q(#$*%UVSFBKDJNKSMAfghn
#&^*%^*&^(*)Q&$(%*&^$(*&%)$__)*&^*()$GRfuhvdijkbcniOCUFDGBHIJDOVFDШФИГАШГТЩИПВОЩШ
#&^*%^*&^(*)Q&$(%*&^$(*&%)$__)*&^*()$GRfuhvdijkbcniOCUFDGBHIJDOVFDШФИГАШГТЩИПВОЩШ
#ertyudsfghj,kl.a
