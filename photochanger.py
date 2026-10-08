# pyinstaller -c --onefile "D:\BMT 2024-2025 stage\Prototype\image_manip_dir\photochanger.py" -i "D:\BMT 2024-2025 stage\Prototype\image_manip_dir\icon.ico" --noconsole

import os
import copy
import numpy as np
import tkinter as tk
import pandas as pd

from functools import partial
from tkinter import filedialog

from PIL import Image
from PIL import ImageOps
from PIL import ImageStat
from PIL import ImageTk

class CONVERT:
    def STRtoINT(string:str) -> int:
        if string.isnumeric():
            return int(string)
        else:
            return string

    def RGBtoHEX(RGB:tuple) -> str:
        return '#%02x%02x%02x' % RGB
    
    def padString(string:str|list, targetLen:int, padChar='.') -> str:
        if type(string) == str:
            length = len(string)

            while targetLen > length:
                string += padChar
            
        else:
            for itemIdx, item in enumerate(string):
                length = len(item)

                while targetLen > length:
                    string[itemIdx] += padChar
                    length = len(string[itemIdx])
            
        return string
    
    def makeOfEqualLength(items:list, padchar:str=' ') -> list:
        listOfLengths = []
        for item in items:
            listOfLengths.append(len(item))

        trgtLength = max(listOfLengths)+2

        for itemIdx, item in enumerate(items):
            while len(item) < trgtLength:
                item += padchar
                
            items[itemIdx] = item

        return items

    def stitchList(items:list, padding:int|list=0, padchar:str='.') -> str:
        newstr = ''

        if type(padding) == list and len(items) == len(padding):
            # add padding according to list of lengths

            for itemIdx, item in enumerate(items):
                padding = [x+1 for x in padding]
                
                if pd.isna(item):
                    item = '-'

                if itemIdx == len(items)-1:
                    newstr += str(item)
                else:
                    newstr += str(item)+padchar*abs(padding[itemIdx]-len(str(item)))
            
        else:
            for itemIdx, item in enumerate(items):

                if itemIdx == len(items)-1:
                    newstr += item
                else:
                    newstr += item+padchar*abs(padding-len(item))

        return newstr

class IMG:
    def __init__(self, img):
        if type(img) == str:
            self.img = Image.open(img).convert('RGBA')
        else:
            self.img = img

    def cNormalize(value, adder:int=0):
        minVal = 0
        maxVal = 255

        value += adder

        if value > maxVal:
            value = maxVal
        elif value < minVal:
            value = minVal

        return value

    def getSize(self):
        return self.img.size
    
    def getStats(self, figRound:int=None, doPrint:bool=False) -> dict:
        source = ImageStat.Stat(self.img)

        keys = ['count','extrema','mean','median','rms','stddev','sum','var']
        vals = [source.count[0],source.extrema[0],source.mean[0],source.median[0],
                source.rms[0],source.stddev[0],source.sum[0],source.var[0]]
        
        dictStats = {}
        for sourceIdx, key in enumerate(keys):
            dictStats[key] = vals[sourceIdx]

        if doPrint:
            for key in dictStats:
                fig = dictStats[key]

                try:
                    fig = round(fig, figRound)
                except: ...

                print(key, '\t', fig)

        return dictStats
        
    def resize(self, XYorF:float|tuple[int|float,int|float]):
        ogSize = self.getSize()
        ogSizeX = ogSize[0]
        ogSizeY = ogSize[1]
        
        if type(XYorF) == float or type(XYorF) == int:
            # scale the entire image along a factor F.

            self.img = ImageOps.scale(self.img, factor=XYorF)

            return self.img
        
        elif type(XYorF) == tuple:
            # shrink or expand given image to new dimensions XY.
            newX = XYorF[0]
            newY = XYorF[1]

            TnewX = type(newX)
            TnewY = type(newY)

            if TnewX == int and TnewY == int:
                # assume pixel format
                print('assuming pixel format...')

                if newX <= 0:
                    newX = 1
                
                if newY <= 0:
                    newY = 1

                self.img = self.img.resize((newX, newY))
                return self.img
            
            elif TnewX == float and TnewY == float:
                # assume factor format
                print('assuming factor format...')

                newSizeX = int(ogSizeX * newX)
                newSizeY = int(ogSizeY * newY)

                self.img = self.img.resize((newSizeX, newSizeY))

                return self.img

            else:
                # input error
                print('Mixed rescaling input is not supported.')
                return 0
            
    def crop(self, border:int, mode:str='border', maskValue:int=0):
        # imageops crop
        self.img = ImageOps.crop(self.img, border)
        return self.img

    def expand(self, border, fillvalue:int|tuple[int,...]=0):
        # imageops expand
        self.img = ImageOps.expand(self.img, border, fill=fillvalue)
        return self.img
    
    def place(self, bounds:tuple[int,int]=(500,500), fillvalue:None|int|tuple[int,int,int]=None):
        # stretches or shrinks any given image to fit the bounds, while protecting its aspect ratio.
        # what falls outside of its scope will be filled with fillvalue.
        # if no fillvalue given, an appropriate grey value will be calculated based on the mean color value.
        boundX = bounds[0]
        boundY = bounds[1]
        
        size = self.getSize()
        sizeX = size[0]
        sizeY = size[1]

        FactorX = boundX / sizeX
        FactorY = boundY / sizeY
        factor = min(FactorX, FactorY)

        # resizes at least one side to its intended bounds.
        self.resize(factor)

        size = self.getSize()
        sizeX = size[0]
        sizeY = size[1]

        if fillvalue == None:
            value = int(np.mean(np.asarray(self.img)))

            fillvalue = (value, value, value)

        background = Image.new('RGBA', (boundX, boundY), fillvalue)

        # check success. Add fillvalue borders if not
        if sizeX != boundX:
            diffX = boundX - sizeX
            borderWidth = diffX // 2

            background.paste(self.img, (borderWidth, 0))

            self.img = background
            return self.img

        elif sizeY != boundY:
            diffY = boundY - sizeY
            borderHeight = diffY // 2

            background.paste(self.img, (0, borderHeight))

            self.img = background
            return self.img

        else:
            return self.img
    
    def makeTransparent(self, cMask:tuple[int,int,int,int]=(255,255,255,0)):
        channels = self.img.getdata()

        mRed = cMask[0]
        mGreen = cMask[1]
        mBlue = cMask[2]
        mAlpha = cMask[3]

        updatedPicture = []

        for channel in channels:
            cRed = channel[0]
            cGreen = channel[1]
            cBlue = channel[2]

            # append channels == mask as transparant value
            if cRed == mRed and cGreen == mGreen and cBlue == mBlue:
                updatedPicture.append((cRed,cGreen,cBlue,mAlpha))
            else:
                updatedPicture.append(channel)

        self.img.putdata(updatedPicture)
        return self.img
        
    def recolor(self, scale:tuple[int,int,int,int]=(0,0,0,0), swapChannels=''):
        r = scale[0]
        g = scale[1]
        b = scale[2]
        a = scale[3]

        R, G, B, A = self.img.split()

        R = R.point(lambda p: IMG.cNormalize(p, r))
        G = G.point(lambda p: IMG.cNormalize(p, g))
        B = B.point(lambda p: IMG.cNormalize(p, b))
        A = A.point(lambda p: IMG.cNormalize(p, a))

        if swapChannels == '':
            self.img = Image.merge('RGBA', (R, G, B, A))
        elif swapChannels == 'rg':
            self.img = Image.merge('RGBA', (G, R, B, A))
        elif swapChannels == 'rb':
            self.img = Image.merge('RGBA', (B, G, R, A))
        elif swapChannels == 'gb':
            self.img = Image.merge('RGBA', (R, B, G, A))

        return self.img
    
    def get(self):
        return self.img

    def show(self):
        self.img.show()

class mainGUI:
    clrBackground = CONVERT.RGBtoHEX((255,255,255))
    clrForeground = CONVERT.RGBtoHEX((0,0,0))

    clrScales = CONVERT.RGBtoHEX((100,100,125))
    clrStats = CONVERT.RGBtoHEX((100,100,125))
    clrImage = CONVERT.RGBtoHEX((100,100,125))
    clrDims = CONVERT.RGBtoHEX((100,100,125))
    clrBtns = CONVERT.RGBtoHEX((100,100,125))
    clrMiddle      = CONVERT.RGBtoHEX((100,100,125))
    clrTop         = CONVERT.RGBtoHEX((60,60,80))

    clrTxt         = CONVERT.RGBtoHEX((255,255,255))

    clrElements = CONVERT.RGBtoHEX((160,160,180))
    clrInside      = CONVERT.RGBtoHEX((75,75,90))

    # RELATIVE SIZES OF WINDOW
    START   = 0
    END     = 1.0

    # STYLE
    padding = 8

    FONT    = 'Consolas 14'
    FONTBOLD= FONT + ' bold'
    FONTSMALL   =  'Consolas 10'

    def __init__(self, master:tk.Tk, title='', imgBounds:tuple[int,int]=(450,450)):
        # GLOBAL
        self.master = master
        self.master.bind('<Key>', self.globalKeyTrigger)
        self.master.bind('<Return>', self.applyToImg)

        self.master.title(title)

        self.imgBounds = imgBounds
        self.previewX = imgBounds[0]
        self.previewY = imgBounds[1]

        self.filePaths = []

        self.imgIdx = tk.IntVar()
        self.imgIdx.set(0)
        
        self.frontendImages = []
        self.backendImages = []

        self.activeIdx = None

        # POSITIONING
        leftSide = 0.5
        rightSide = self.END - leftSide

        scalesX = self.START
        scalesY = self.START
        scalesW = leftSide
        scalesH = 0.4

        statsX = self.START
        statsY = self.START + scalesH
        statsW = leftSide
        statsH = 0.5

        btns1X = self.START
        btns1Y = self.START + scalesH + statsH
        btns1W = self.END / 2
        btns1H = 0.1

        imageX = self.START + leftSide
        imageY = self.START
        imageW = rightSide
        imageH = 0.8

        dimsX = self.START + leftSide
        dimsY = self.START + imageH
        dimsW = rightSide
        dimsH = 0.1

        btns2X = self.START + leftSide
        btns2Y = self.START + scalesH + statsH
        btns2W = self.END / 2
        btns2H = 0.1

        # FRAMES
        # text
        txtScales = 'Kleuren opties'
        txtStats = 'Informatie'
        txtImage = 'Afbeelding preview'
        txtDims = 'Dimensies'

        txtColors = ['Rood','Groen ','Blauw','Alpha']
        txtFunctions1 = ['Laden','Opslaan & sluiten']
        txtFunctions2 = ['Toepassen','◀','▶']
        funcsFunctions1 = [self.getFiles,self.closeWindow]
        funcsFunctions2 = [self.applyToImg,self.decreasingImgIdx,self.increasingImgIdx]

        txtTransparant = ['R:','G:','B:','A:']

        # scales
        frameScales = tk.Frame(self.master, background=self.clrScales)

        lblScales = tk.Label(frameScales, text=txtScales, font=self.FONTBOLD, foreground=self.clrTxt, background=self.clrMiddle)

        maxlist = []
        for item in txtColors:
            maxlist.append(len(item))
        maxlist = max(maxlist)
        
        scales = []
        labels = []
        variables = []
        for colorIdx, color in enumerate(CONVERT.padString(txtColors, maxlist, padChar=' ')):
            label = tk.Label(frameScales, text=color, font=self.FONT, relief='sunken', background=self.clrElements)
            label.bind('<Button-1>', partial(self.updateActiveSliders, colorIdx))
            label.bind_all('<Key>', self.scaleKeyTrigger)
            variable = tk.IntVar()
            variable.set(0)
            scale = tk.Scale(frameScales, variable=variable, from_=255, to=-255, length=144, font=self.FONT, background=self.clrElements)

            labels.append(label)
            scales.append(scale)
            variables.append(variable)

        lblScales.grid(row=0, column=0, columnspan=len(txtColors), padx=self.padding, pady=(self.padding,0), sticky='nw')

        for elementIdx in range(len(labels)):
            labels[elementIdx].grid(row=1, column=elementIdx, padx=(self.padding,0), pady=(self.padding,0), sticky='nw')
            scales[elementIdx].grid(row=2, column=elementIdx, padx=(self.padding,0), pady=(self.padding,0), sticky='nw')

        self.frameScales = frameScales
        self.labels = labels
        self.scales = scales
        self.variables = variables

        # stats
        frameStats = tk.Frame(self.master, background=self.clrStats)

        lblStats = tk.Label(frameStats, text=txtStats, font=self.FONTBOLD, foreground=self.clrTxt, background=self.clrMiddle)
        entryName = tk.Entry(frameStats, font=self.FONT, width=26, foreground=self.clrTxt, background=self.clrInside)
        boxStats = tk.Text(frameStats, font=self.FONT, width=38, height=11, foreground=self.clrTxt, background=self.clrInside)

        lblStats.grid(row=0, column=0, padx=self.padding, pady=self.padding, sticky='nw')
        entryName.grid(row=0, column=1, padx=(self.padding//2,self.padding), pady=self.padding, sticky='nw')
        boxStats.grid(row=1, column=0, columnspan=2, padx=self.padding, pady=(0,self.padding), sticky='nw')

        self.frameStats = frameStats
        self.boxStats = boxStats
        self.entryName = entryName

        # image
        frameImage = tk.Frame(self.master, background=self.clrTop)

        lblImage = tk.Label(frameImage, text=txtImage, font=self.FONTBOLD, foreground=self.clrTxt, background=self.clrTop)
        cnvsImage = tk.Canvas(frameImage, width=self.previewX, height=self.previewY, border=0, background=self.clrInside)

        labelsTransp = []
        variablesTransp = []
        entriesTransp = []
        for option in txtTransparant:
            label = tk.Label(frameImage, text=option, font=self.FONT, foreground=self.clrTxt, background=self.clrTop)
            variable = tk.IntVar()
            entry = tk.Entry(frameImage, textvariable=variable, font=self.FONT, width=3, foreground=self.clrTxt, background=self.clrInside)

            labelsTransp.append(label)
            variablesTransp.append(variable)
            entriesTransp.append(entry)

        lblImage.grid(row=0, column=0, columnspan=len(txtTransparant)*2, padx=self.padding, pady=(self.padding,0), sticky='nw')
        cnvsImage.grid(row=1, column=0, columnspan=len(txtTransparant)*2, padx=self.padding, pady=(self.padding,0), sticky='nw')

        placement = 0
        for optionIdx, option in enumerate(txtTransparant):
            label = labelsTransp[optionIdx]
            variable = variablesTransp[optionIdx]
            entry = entriesTransp[optionIdx]
            
            if optionIdx != 3:
                variable.set(0)
            else:
                variable.set(255)

            label.grid(row=2, column=placement, padx=(self.padding,0), pady=(self.padding,0), sticky='nw')
            placement += 1
            entry.grid(row=2, column=placement, padx=0, pady=(self.padding,0), sticky='nw')
            placement += 1

        self.frameImage = frameImage
        self.canvas = cnvsImage
        self.variablesTransp = variablesTransp

        # dims
        frameDims = tk.Frame(self.master, background=self.clrDims)

        lblDims = tk.Label(frameDims, text=txtDims, font=self.FONTBOLD, foreground=self.clrTxt, background=self.clrMiddle)
        lblDims1 = tk.Label(frameDims, text='x:', font=self.FONT, foreground=self.clrTxt, background=self.clrMiddle)
        lblDims2 = tk.Label(frameDims, text='y:', font=self.FONT, foreground=self.clrTxt, background=self.clrMiddle)

        entryX = tk.Entry(frameDims, width=9, font=self.FONT, disabledbackground=self.clrInside, foreground=self.clrTxt, background=self.clrInside)
        entryY = tk.Entry(frameDims, width=9, font=self.FONT, disabledbackground=self.clrInside, foreground=self.clrTxt, background=self.clrInside)

        lblDims.grid(row=0, column=0, padx=(self.padding,self.padding*3), pady=self.padding, sticky='nw')

        lblDims1.grid(row=0, column=1, pady=self.padding, sticky='nw')
        entryX.grid(row=0, column=2, padx=self.padding, pady=self.padding, sticky='nw')
        lblDims2.grid(row=0, column=3, pady=self.padding, sticky='nw')
        entryY.grid(row=0, column=4, padx=self.padding, pady=self.padding, sticky='nw')

        self.frameDims = frameDims
        self.entryX = entryX
        self.entryY = entryY

        # btns1
        frameBtns1 = tk.Frame(self.master, background=self.clrBtns)

        btns = []
        for txtIdx, txt in enumerate(txtFunctions1):
            btn = tk.Button(frameBtns1, text=txt, font=self.FONT, width=18, background=self.clrElements, command=funcsFunctions1[txtIdx])

            btns.append(btn)

        for btnIdx, btn in enumerate(btns):
            btn.grid(row=0, column=btnIdx, padx=(self.padding,0), pady=self.padding, sticky='nw')

        self.frameBtns1 = frameBtns1

        # btns2
        frameBtns2 = tk.Frame(self.master, background=self.clrBtns)
        
        btns = []
        for txtIdx, txt in enumerate(txtFunctions2):
            btn = tk.Button(frameBtns2, text=txt, font=self.FONT, width=10, background=self.clrElements, command=funcsFunctions2[txtIdx])

            btns.append(btn)

        for btnIdx, btn in enumerate(btns):
            btn.grid(row=0, column=btnIdx, padx=(self.padding,0), pady=self.padding, sticky='nw')

        self.frameBtns2 = frameBtns2
        self.btns = btns

        if len(self.filePaths) == 0:
            newstate='disabled'

            self.entryX.configure(state=newstate)
            self.entryY.configure(state=newstate)

            for scale in self.scales:
                scale.configure(state=newstate)
            
            for btn in self.btns:
                btn.configure(state=newstate)
        
        else:
            newstate='normal'

            self.entryX.configure(state=newstate)
            self.entryY.configure(state=newstate)

            for scale in self.scales:
                scale.configure(state=newstate)
            
            for btn in self.btns:
                btn.configure(state=newstate)

        # BUILD WINDOW
        self.populateStats()

        self.frameScales.place(relx=scalesX, rely=scalesY, relwidth=scalesW, relheight=scalesH)
        self.frameStats.place(relx=statsX, rely=statsY, relwidth=statsW, relheight=statsH)
        self.frameImage.place(relx=imageX, rely=imageY, relwidth=imageW, relheight=imageH)
        self.frameDims.place(relx=dimsX, rely=dimsY, relwidth=dimsW, relheight=dimsH)
        self.frameBtns1.place(relx=btns1X, rely=btns1Y, relwidth=btns1W, relheight=btns1H)
        self.frameBtns2.place(relx=btns2X, rely=btns2Y, relwidth=btns2W, relheight=btns2H)
    
    def getFiles(self, event=None):
        child = tk.Toplevel()
        child.withdraw()

        initPath = os.path.join(os.getcwd(), 'pics')

        # self.master.update_idletasks()
        filePaths = filedialog.askopenfilenames(initialdir=initPath)

        if len(filePaths) != 0:
            self.filePaths = filePaths
            self.updateElementStates()
            self.updatePics()
            self.updateCanvas()

        print('File dialog was concluded.')
    
    def closeWindow(self, event=None):
        for imageIdx, image in enumerate(self.frontendImages):
            rootPath = self.filePaths[imageIdx].replace(os.path.basename(self.filePaths[imageIdx]), '')
            filename = rootPath + self.entryName.get()
            fileext = os.path.splitext(self.filePaths[imageIdx])[1]

            if fileext != '.ico':
                filepath = filename+'.png'
                image.get().save(filepath, 'PNG')
                print('photo saved to:', filepath)

            else:
                filepath = filename+'.ico'
                image.get().save(filepath, 'ICO')

        print('Program closed normally with saving.')
        self.master.destroy()

    def updateElementStates(self, event=None):
        if len(self.filePaths) == 0:
            newstate='disabled'

            self.entryX.configure(state=newstate)
            self.entryY.configure(state=newstate)

            for scale in self.scales:
                scale.configure(state=newstate)
            
            for btn in self.btns:
                btn.configure(state=newstate)
        
        else:
            newstate='normal'

            self.entryX.configure(state=newstate)
            self.entryY.configure(state=newstate)

            for scale in self.scales:
                scale.configure(state=newstate)
            
            for btn in self.btns:
                btn.configure(state=newstate)
    
    def updatePics(self, event=None):
        # update all backend
        self.backendImages = []
        for filePath in self.filePaths:
            self.backendImages.append(IMG(filePath))

        if len(self.frontendImages) == 0:
            for filePath in self.filePaths:
                self.frontendImages.append(IMG(filePath))

        else:
            self.frontendImages = []
            for filePath in self.filePaths:
                self.frontendImages.append(IMG(filePath))
        
    def updateCanvas(self, event=None):
        idx = self.imgIdx.get()

        try:
            frontendImage = copy.copy(self.frontendImages[idx])
        except IndexError:
            frontendImage = copy.copy(self.frontendImages[0])

        frontendImage = frontendImage.place((self.previewX,self.previewY),0)
        frontendImage = ImageTk.PhotoImage(frontendImage)

        self.canvas.create_image(0, 0, image=frontendImage, anchor='nw')
        self.canvas.image = frontendImage

        self.populateStats()
        self.populateDims()

    def applyToImg(self, event=None):
        settings = []
        transpSettings = []
        idx = self.imgIdx.get()

        imgWidth = CONVERT.STRtoINT(self.entryX.get())
        imgHeight = CONVERT.STRtoINT(self.entryY.get())
        
        for scale in self.scales:
            settings.append(scale.get())
        for variable in self.variablesTransp:
            transpSettings.append(variable.get())

        frontendImage = copy.copy(self.backendImages[idx])
        frontendImage.recolor((settings[0],settings[1],settings[2],settings[3]))
        frontendImage.resize((imgWidth, imgHeight))
        frontendImage.makeTransparent((transpSettings[0],transpSettings[1],transpSettings[2],transpSettings[3]))

        self.frontendImages[idx] = frontendImage

        self.updateCanvas()
        
    def increasingImgIdx(self, event=None): 
        idx = self.imgIdx.get()

        idx += 1
        idx = idx % len(self.filePaths)

        self.imgIdx.set(idx)

        self.updateCanvas()

    def decreasingImgIdx(self, event=None): 
        idx = self.imgIdx.get()

        idx -= 1
        idx = idx % len(self.filePaths)

        self.imgIdx.set(idx)

        self.updateCanvas()
    
    def populateStats(self, event=None):
        currentIdx = self.imgIdx.get()
        imagesCount = len(self.filePaths)

        self.boxStats.delete(1.0, tk.END)
        if imagesCount == 0:
            self.entryName.delete(0, tk.END)
            self.entryName.insert(0, '-')

            self.boxStats.insert(1.0, f'# afbeelding:  {currentIdx}/{imagesCount}')
        else:
            try:
                currentImg = copy.copy(self.frontendImages[currentIdx])
            except IndexError:
                currentIdx = 0
                currentImg = copy.copy(self.frontendImages[currentIdx])

            self.entryName.delete(0, tk.END)
            self.entryName.insert(0, os.path.basename(os.path.splitext(self.filePaths[currentIdx])[0]))

            keyslist = ['afbeelding:']
            valueslist = [f'{currentIdx+1}/{imagesCount}']
            for keys, values in currentImg.getStats(figRound=2).items():
                try:
                    values = round(values, 3)
                except: ...

                keyslist.append(str(keys)+':')
                valueslist.append(str(values))

            keyslist = CONVERT.makeOfEqualLength(keyslist)
            valueslist = CONVERT.makeOfEqualLength(valueslist)

            for keyIdx, key in enumerate(keyslist):
                value = valueslist[keyIdx]

                self.boxStats.insert(tk.INSERT, f'# {key}{value}\n')
    
    def populateDims(self, event=None):
        idx = self.imgIdx.get()
        try:
            size = self.frontendImages[idx].getSize()
        except IndexError:
            size = self.frontendImages[0].getSize()

        self.entryX.delete(0, tk.END)
        self.entryX.insert(0, size[0])

        self.entryY.delete(0, tk.END)
        self.entryY.insert(0, size[1])
    
    def updateActiveSliders(self, activeIdx=None, event=None):
        self.deactivateSliders()

        self.activeIdx = activeIdx
        if self.labels[activeIdx]['relief'] == 'sunken':
            self.labels[activeIdx]['relief'] = 'raised'
    
    def deactivateSliders(self, event=None):
        self.activeIdx = None
        for labelIdx in range(len(self.labels)):
            self.labels[labelIdx].configure(relief='sunken')

    def globalKeyTrigger(self, event=None):
        key = event.keysym

        active = len(self.filePaths) > 0

        if key == 'Left':
            if active:
                self.decreasingImgIdx()
        elif key == 'Right':
            if active:
                self.increasingImgIdx()
    
    def scaleKeyTrigger(self, event=None):
        key = event.keysym

        active = len(self.filePaths) > 0

        minValue = -255
        maxValue = 255

        if key == 'Up':
            if self.activeIdx != None and active:
                currentValue = self.variables[self.activeIdx].get()
                currentValue += 1

                if currentValue > maxValue:
                    currentValue = maxValue
                elif currentValue < minValue:
                    currentValue = minValue

                self.variables[self.activeIdx].set(currentValue)

        elif key == 'Down':
            if self.activeIdx != None and active:
                currentValue = self.variables[self.activeIdx].get()
                currentValue -= 1

                if currentValue > maxValue:
                    currentValue = maxValue
                elif currentValue < minValue:
                    currentValue = minValue

                self.variables[self.activeIdx].set(currentValue)

        elif key == 'Escape':
            self.deactivateSliders()

            for variable in self.variables:
                variable.set(0)

            for varIdx, variable in enumerate(self.variablesTransp):
                if varIdx != 3:
                    variable.set(0)
                else:
                    variable.set(255)

            print('trigger clear all')

clrBackground = CONVERT.RGBtoHEX((0,0,0))

master = tk.Tk()
icon = tk.PhotoImage(file="D:\BMT 2024-2025 stage\Prototype\image_manip_dir\icon.png")
master.iconphoto(True, icon)

w = 800
h = 600

master.wm_overrideredirect(False)
master.geometry(f'{w}x{h}+100+100')

master.configure(background=clrBackground)

mainGUI(master, title='photochanger', imgBounds=(380,380))

master.mainloop()