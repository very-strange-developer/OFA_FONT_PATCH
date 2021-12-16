# -*- coding: utf-8 -*-
from sys import byteorder
from PIL import Image, ImageFont, ImageDraw
from matplotlib import pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from tkinter import filedialog
from tkinter import messagebox

#나머지 할 일 헤더 마저 분석

#2021-10-08 바이트로 내보내기 했음
#2021-10-09 이미지 불러오기, 정보 불러오기
#2021-10-10 폰트 이미지 제작
#개별폰트 가로세로 max = 34, 34?
#2021-10-13 빅-폰트이미지 제작
#글자 겹치는거 해결해야함 (오프셋의 문제?) width가 있었죠?

MAXWIDTH = 2048
MAXHEIGHT = 2048
PATH = "고정너비글자 폰트파일 출력할 곳"
PATH3 = "가변너비글자 폰트파일 출력할 곳"
PATH2 = "가변너비글자 폰트파일 소스"
IMAGEPATH = "폰트 이미지파일 소스"
IMAGEPATH_DST = "폰트 이미지파일 출력할 곳"
FONT = "ttf폰트파일 소스"
FONTPOINT = 28 #폰트 크기

class Word:
    index = 0
    key = 0 #uint16() 이미지 유니코드 값
    fontimage = 0

    datawidth = 0 #uint8() 이미지 너비
    dataheight = 0 #uint8() 이미지 높이
    datax = 0 #uint16() 이미지 시작 x지점
    datay = 0 #uint16() 이미지 시작 y지점
    offsetx = 0 #uint16() 문장 내 폰트 가로 위치 조정
    offsety = 0 #uint16() 문장 내 폰트 세로 위치 조정
    width = 0 #uint16() 폰트 너비
    blank = 0x0000 #int16()

    left = 0xFFFFFFFF #int32() 
    right = 0xFFFFFFFF #int32()

    isEmoji = 0 #uint16() 0=False 1=True

    def __lt__(self, other):
        return self.key < other.key

def main():


    wholefont = Image.open(IMAGEPATH)
    #stringpath = selectFile()
    #print(stringpath)
    #stringset = openText(stringpath)

    stringset = set("넣을 글자들")
    stringset.remove("!")
    print(stringset)
    madeWord = buildFromString(stringset)
    Wods = readBytes(PATH2)
    Wods = extractFontImages(Wods, wholefont)

    viewfont(Wods, 0)

    words = mergeWords(Wods, madeWord)
    words = sortFonts(words)

    output = outputWord()
    root, toWrite = output.getTree(words)

    draw = drawLine()
    img, final = draw.mergeLine(toWrite)
    viewimage(img)

    final[0].datax = 65535

    writeBytes(PATH, False, final, root)
    writeBytes(PATH3, True, final, root)

    img.save(IMAGEPATH_DST, 'png')

#각 폰트데이터 바이트 조합
def buildbyte(w, isNxp) : #input word
    bytearr = bytearray()
    bytearr += (w.key.to_bytes(2, "big"))
    bytearr += (w.datawidth.to_bytes(1, "big"))
    bytearr += (w.dataheight.to_bytes(1, "big"))
    bytearr += (w.datax.to_bytes(2, "big"))
    bytearr += (w.datay.to_bytes(2, "big"))
    bytearr += (w.offsetx.to_bytes(2, "big"))
    bytearr += (w.offsety.to_bytes(2, "big"))
    if isNxp == False :
        bytearr += (b'\x00\x20')
    else :
        bytearr += (w.width.to_bytes(2, "big"))
    bytearr += (w.blank.to_bytes(2, "big"))
    bytearr += (w.left.to_bytes(4, "big"))
    bytearr += (w.right.to_bytes(4, "big"))
    bytearr += (w.isEmoji.to_bytes(2, "big"))
    bytearr += (b'\x00\x00\x00\x00\x00\x00')
        
    return bytearr

#바이트파일 쓰기
def writeBytes(filepath, isNxp, dataToWrite, root) :
    with open(filepath, "wb") as f:
        f.write(0x70616601.to_bytes(4, "big"))
        f.write(0x0201001D.to_bytes(4, "big"))
        f.write(len(dataToWrite).to_bytes(4, "big"))
        f.write(root.to_bytes(4, "big"))
        f.write("im2nx".encode("UTF-8"))
        if isNxp is True:
            f.write(b'\x70')
        else :
            f.write(b'\x00')
        f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        f.write(b'\x00\x30\x01\x00')
        f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

        for w in dataToWrite :
            data = buildbyte(w, isNxp)
            f.write(data)

#바이트파일 읽기
def readBytes(filepath) :
    Words = []

    with open(filepath, "rb") as f:
        f.read(4)
        f.read(4)
        fontlength = int.from_bytes(f.read(4), byteorder='big')
        root = int.from_bytes(f.read(4), byteorder='big')
        print(chr(root))
        f.read(5)
        isNxp = f.read(1)
        f.read(10)
        f.read(16)

        for i in range(0, fontlength):
            tmp = Word()
            tmp.key = int.from_bytes(f.read(2), byteorder='big')
            tmp.datawidth = int.from_bytes(f.read(1), byteorder='big')
            tmp.dataheight = int.from_bytes(f.read(1), byteorder='big')
            tmp.datax = int.from_bytes(f.read(2), byteorder='big')
            tmp.datay = int.from_bytes(f.read(2), byteorder='big')
            tmp.offsetx = int.from_bytes(f.read(2), byteorder='big')
            tmp.offsety = int.from_bytes(f.read(2), byteorder='big')
            tmp.width = int.from_bytes(f.read(2), byteorder='big')
            f.read(2)
            tmp.left = int.from_bytes(f.read(4), byteorder='big')
            tmp.right = int.from_bytes(f.read(4), byteorder='big')
            tmp.isEmoji = int.from_bytes(f.read(2), byteorder='big')
            f.read(6)
            Words.append(tmp)
            print(chr(tmp.key), tmp.datax, tmp.datawidth, tmp.offsetx, tmp.datay, tmp.dataheight, tmp.offsety, tmp.width)

    return Words

def viewimage(img):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_facecolor((0,0,0,1))
    ax.imshow(img)
    ax.set_xticks([]), ax.set_yticks([])
    plt.show()

#추출 이미지 보기
def viewfont(w, startindex):  
    fig = plt.figure()
    rows = 10
    cols = 10
    plt.rc('font', family='Malgun Gothic') 
    for i in range(1, rows * cols + 1):
        if i > len(w) - startindex:
            break
        bias = startindex
        ax = fig.add_subplot(rows, cols, i)
        ax.set_facecolor((0,0,0,1))
        ax.imshow(w[i + bias - 1].fontimage)
        ax.set_xlabel(chr(w[i + bias - 1].key))
        ax.set_xticks([]), ax.set_yticks([])
    plt.show()

#전체 폰트이미지로부터 각 글자 이미지 추출
def extractFontImages(Words, fullfont):
    for w in Words:
        if w.datax == 65535:
            xs = 0
        else:
            xs = w.datax
        xe = xs + w.datawidth
        ys = w.datay % 65535
        ye = ys + w.dataheight
        w.fontimage = fullfont.crop((xs, ys, xe, ye))
        #print(w.datawidth, w.dataheight)
        #print(w.fontimage)
    return Words

#전체 텍스트 이미지화
def buildFromString(stringset):
    words = []
    for s in stringset :
        tmp = Word()
        tmp.key = ord(s)
        img = drawText(s)
        tmp.fontimage = img
        tmp.datawidth = img.size[0]
        tmp.dataheight = img.size[1]
        tmp.offsetx = 0
        tmp.offsety = int(round(65510 + (tmp.dataheight - 30)/2))
        tmp.width = 32
        words.append(tmp)
    return words

#단일 텍스트 이미지화
def drawText(s):
    font = ImageFont.truetype(FONT, FONTPOINT)
    fontsize = font.getsize(s)
    (width, baseline), (offset_x, offset_y) = font.font.getsize(s)
    img = Image.new(mode="RGBA", size=(fontsize[0], fontsize[1] + 1), color=(0, 0, 0, 0))
    #print(s, fontsize[0], fontsize[1])
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), s, (255, 255, 255), font=font)
    img = img.crop((0, offset_y -1 , fontsize[0], fontsize[1]))
    #print(str(fontsize[0]), str(fontsize[1]-offset_y+1))
    return img

#원본 폰트에서 한자, 일본어 제거후 생성폰트와 병합
def mergeWords(base, add):
    newWords = []
    for w in base:
        newWords.append(w)
    for w in add:
        newWords.append(w)
    return newWords

def sortFonts(words):
    sortedWord = sorted(words)
    return sortedWord

def selectFile():
    files = filedialog.askopenfilenames(initialdir="/", title = "파일을 선택 해 주세요")
    return str(files)

def openText(path):
    path = path[5:]
    path = path.replace('/', "\\")
    string = ''
    f = open("C:\\" + path)
    lines = f.readlines()
    for line in lines:
        line = line + line.strip()

    return string

def onlyKR(string):
    for s in string:
        if ord(s) < 44032 or ord(s) > 55200:
            #print(s,ord(s))
            del(s)
    return string

class drawLine:
    output = []

    def buildLine(self, words, index):
        maxh = 0
        tmph = 50
        prevoffx = 0
        heights = []
        line = Image.new(mode="RGBA", size=(MAXWIDTH, tmph), color=(0, 0, 0, 0))
        words = words[index:]
        for w in words:
            if (prevoffx + w.datawidth) > MAXWIDTH:
                line = line.crop((0, tmph - maxh, line.size[0], line.size[1]))
                return line, index, heights
            line.paste(w.fontimage, (prevoffx, tmph - w.dataheight))
            self.output[w.index].datax = prevoffx
            prevoffx += w.datawidth
            heights.append(w.dataheight)
            if maxh < w.dataheight:
                maxh = w.dataheight
            index += 1
        line = line.crop((0, tmph - maxh, line.size[0], line.size[1]))
        return line, index, heights

    def mergeLine(self, words):
        self.output = words
        imgtmp = []
        bitmap = Image.new(mode="RGBA", size=(MAXWIDTH, MAXHEIGHT), color=(0, 0, 0, 0))
        index = 0
        indicex = []
        indicey = []
        heights = []
        prevoffh = 0
        while index < len(self.output):
            img, idxtmp, h = self.buildLine(self.output, index)
            heights.append(h)
            index = idxtmp
            indicex.append(index)
            imgtmp.append(img)

        for i in range(0, len(imgtmp)):
            indicey.append(prevoffh)
            bitmap.paste(imgtmp[i],(0, prevoffh))
            prevoffh += imgtmp[i].size[1]
        indicey.append(prevoffh)

        beforex = 0
        indexsum = 0
        
        for idx, x in enumerate(indicex):
            for i in range(0, x - beforex):
                self.output[indexsum + i].datay = indicey[idx+1] - heights[idx][i]
            indexsum += x-beforex
            beforex = x

        for w in self.output:
            print(chr(w.key), w.datay)

        return bitmap, self.output

class outputWord:
    output = []
    def getTree(self, words):
        for idx, w in enumerate(words):
            w.index = idx
        self.output = words
        root = self.buildTree(words)
        print(root)
        for w in self.output:
            print("_______________")
            print("index",w.index)
            print("char",chr(w.key))
            print("left",w.left)
            print("right",w.right)
        return root, self.output

    def buildTree(self, words):
       # print("length of words", len(words))
        currentNode = int(len(words)/2)
        if(len(words) == 0):
            #print("leaf")
            return 0xFFFFFFFF
        elif(len(words) == 1):
            empty = []
            self.output[words[currentNode].index].left = self.buildTree(empty)
            self.output[words[currentNode].index].right = self.buildTree(empty)
            #print(self.output[words[currentNode].index].left, self.output[words[currentNode].index].right)
            return words[currentNode].index
        #print(len(words),currentNode, words[currentNode].index)
        self.output[words[currentNode].index].left = self.buildTree(words[:currentNode])
        self.output[words[currentNode].index].right = self.buildTree(words[currentNode+1:])
        return words[currentNode].index

main()