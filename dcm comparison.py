#Target is to carry out a dicom file comparison. 
#a template is used to extract the data that'll be compared 
#ideal aim :
# towardsdatascience.com/building-a-python-ui-for-comparing-data-13c10693d9e4


from pydicom.filereader import dcmread

try:
    import Tkinter
    from Tkinter import Tk, Label, Entry, Toplevel, Canvas
    from Tkinter import *
    import tkFont

    from Tkconstants import CENTER, LEFT, N, E, W, S
    from Tkinter import StringVar
    import Tkinter as tk
    import ttk
    import tkFileDialog as filedialog

#reference for tkinter modules: https://docs.python.org/2.4/lib/node715.html

except ImportError:
    from tkinter import Tk, Label, Entry, Toplevel, Canvas, font
    from tkinter import *
    from tkinter import StringVar
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog

from os import path as osPath
import threading

#refrence for threading 
# https://realpython.com/intro-to-python-threading/#what-is-a-thread
# https://www.youtube.com/watch?v=cdPZ1pJACMI

root = tk.Tk()
root.title("DICOM file comparison")
width, height = 840,650
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width / 2) - (width / 2)
y = (screen_height / 2) - (height / 2)
root.geometry("%dx%d+%d+%d" % (width, height, x,y-30))

#https://stackoverflow.com/questions/14910858/how-to-specify-where-a-tkinter-window-opens/14910894


# Create variables to save the path of files
file1 = StringVar()
file2 = StringVar()

# Create variables to save the state of check or not check state of keys
pNameCheck = IntVar()
numBeamsCheck = IntVar()
bNameCheck = IntVar()
typeCheck = IntVar()
gAngleCheck = IntVar()
cAngleCheck = IntVar()
bMetersetUnitCheck = IntVar()
bMetersetCheck = IntVar()
numCPCheck = IntVar()
EnCheck = IntVar()


###  a small function to read in a file name and to split it into
  #  the directory it is stored in, and the file name
def chooseFile(title='Please select file'):
    file = filedialog.askopenfilename(title=title)
    root.destroy()

    fPath, fName = osPath.split(file)[0], osPath.split(file)[1]

    return(file, fPath, fName)



###  uses the file reading function to select a dicom file
  #  then uses the pydicom function to read in the dicom data
#complete function will not work if not dcm file because of dcmread module
def dicomRead(file=None, title=None):

    if file == None:
        file, fpath, fname = chooseFile(title)
    else:
        fPath, fName = osPath.split(file)[0], osPath.split(file)[1]

    dcmFullData=dcmread(file)

    return(dcmFullData)


###  There's a lot of extra data in a dicom file
  #  I've created these data classes to recreate the baic structure of
  #  a dicom file, but to only contain the data elements that I'm
  #  most interested in for the kind of work we are doing
class PLANdata:
    def __init__(self):
        self.pName = ''  # the name of the plan
        self.numBeams = ''  # number of beams
        self.beam = []  # list container to expand for each beam

class BEAMdata:
    def __init__(self):
        self.bName = ''  # beam name
        self.type = ''  # beam type (TREATMENT or SETUP)
        self.gAngle = ''  # gantry angle for this beam
        self.cAngle = ''  # couch angle for this beam
        self.bMetersetUnit = ''  # what units the Meterset parameter corresponds to
        self.bMeterset = ''  # the beam meterset
        self.numCP = ''  # number of control points for the beam
                         # each pair CP is an energy layer
        self.CP = []

class SPOTdata:
    def __init__(self):
        self.En = ''  # energy for that CP (== layer)
        self.X = []  # X position for each spot in layer
        self.Y = []  # Y position for each spot in layer
        self.sizeX = []  # TPS X FWHM (mm)
        self.sizeY = []  # TPS Y FWHM (mm)
        self.sMeterset = []  # meterset value for each spot
        self.sMU = [] # spot MU, this is calculated later but required at initialisation






###  the main fucntion I have written to extract out the information
  #  from the dicom file that I am interested in and feed it into
  #  the data structures as defined above.
  #  It returns not just the full dicom dataset, but also the condensed
  #  version that I will use for most purposes.

def dicomDataExtract(filename):

    data = dcmread(filename)#dicomRead(title='Select the template Dicom file')

    dcmData = PLANdata()

    dcmData.pName = data.RTPlanLabel
    dcmData.numBeams = data.FractionGroupSequence[0].NumberOfBeams
    # dcmData.numBeams = data[0x300a,0x70][0][0x300a,0x80].value

    # if some beams have been deleted, or re-arranged,
    # nBeams may not equal the numerical values that identify the beams
    # as the order varies within the file, best to use beam identifiers
    nB = [int(dcmData.numBeams)]
    for b in range(dcmData.numBeams):
        nB.append(int(data.IonBeamSequence[b].BeamNumber))

    dcmData.beam = [BEAMdata() for _ in range(max(nB))]

    for b in range(dcmData.numBeams):
        Bnum = data.IonBeamSequence[b].BeamNumber - 1 # changing 1 to 0
        dcmData.beam[Bnum].bName = data.IonBeamSequence[b].BeamName
        dcmData.beam[Bnum].type = data.IonBeamSequence[b].TreatmentDeliveryType
        dcmData.beam[Bnum].bMetersetUnit = data.IonBeamSequence[b].PrimaryDosimeterUnit
        ''' to revert to full file read, remove '/2' when defining numCP and also see lower '''
        dcmData.beam[Bnum].numCP = int(data.IonBeamSequence[b].NumberOfControlPoints/2)
        # dcmData.beam[Bnum].numCP = data[0x300a,0x3a2][b][0x300a,0x110].value
    for b in range(dcmData.numBeams):
        Bnum = data.FractionGroupSequence[0].ReferencedBeamSequence[b].ReferencedBeamNumber-1
        if dcmData.beam[Bnum].type == 'TREATMENT':
            dcmData.beam[Bnum].bMeterset = data.FractionGroupSequence[0].ReferencedBeamSequence[b].BeamMeterset
            '''   working to here   '''
            dcmData.beam[Bnum].CP = [SPOTdata() for _ in range(int(dcmData.beam[Bnum].numCP))]

    for b in range(dcmData.numBeams):
        Bnum = data.IonBeamSequence[b].BeamNumber-1
        if dcmData.beam[Bnum].type == 'TREATMENT':
            ''' to revert to full file read, remove *2 from numCP in range() and '/2' when incrementing CP lower down '''
            for c in range (2*dcmData.beam[Bnum].numCP):
                # if only single spot will be float, easier to convert to list
                if type(data.IonBeamSequence[b].IonControlPointSequence[c].ScanSpotMetersetWeights) is float:
                    data.IonBeamSequence[b].IonControlPointSequence[c].ScanSpotMetersetWeights = [data.IonBeamSequence[b].IonControlPointSequence[c].ScanSpotMetersetWeights]
                # excludes every second CP as don't contain any MU,
                # just a stop criterion for RTION files
                if data.IonBeamSequence[b].IonControlPointSequence[c].ScanSpotMetersetWeights[0] > 0.0:
                    dcmData.beam[Bnum].CP[int(c/2)].En = float(data.IonBeamSequence[b].IonControlPointSequence[c].NominalBeamEnergy)
                    for _ in range(0,len(data.IonBeamSequence[b].IonControlPointSequence[c].ScanSpotPositionMap),2):
                        dcmData.beam[Bnum].CP[int(c/2)].X.append(data.IonBeamSequence[b].IonControlPointSequence[c].ScanSpotPositionMap[_])
                        dcmData.beam[Bnum].CP[int(c/2)].Y.append(data.IonBeamSequence[b].IonControlPointSequence[c].ScanSpotPositionMap[_+1])
                    dcmData.beam[Bnum].CP[int(c/2)].sizeX = data.IonBeamSequence[b].IonControlPointSequence[c].ScanningSpotSize[0]
                    dcmData.beam[Bnum].CP[int(c/2)].sizeY = data.IonBeamSequence[b].IonControlPointSequence[c].ScanningSpotSize[1]
                    dcmData.beam[Bnum].CP[int(c/2)].sMeterset = data.IonBeamSequence[b].IonControlPointSequence[c].ScanSpotMetersetWeights
    return(data, dcmData)

def startThread():

    if str(file1.get()) != "" and str(file2.get()) != "":
        # file.get() will get all the text from the text field
        text.delete(1.0, "end-1c") # when browsing file- make anything after space in path is void
        ERROR_LBL.config(text="Please Wait While Processing The Data...", fg="black")
        data1, objects1 = dicomDataExtract(file1.get())
        data2, objects2 = dicomDataExtract(file2.get())
        # the data being the file and objects being the elements named in the class (used in dicomDataExtract) we want to extract

        # Create Header for top Text
        # \t is used for tab space
        # \n is used for new line
        #END is a positional argument to append text to the textbox/widget.

        text.insert(END, '\n---------------- Start Comparing ----------------\n\n')
        text.insert(END, 'Class \t\t File 1 \t\t\t File 2 \t\t\t Comparison\n')

        # Check if pNameCheck key is checked by user - .get() is a tk.function that'll get user input
        if pNameCheck.get()==1: # ==1 is true 
            #Knowing that False==0 and True==1 makes it easier to count how many bools in a sequence are true: 
            # You can just write sum(bool_list) / bool_list.count(True). 
            # Otherwise, you'd have to write sum(1 for 'x' bool_list if 'x').
            if str(objects1.pName) == str(objects2.pName):
                text.insert(END, 'Pname \t\t' + str(objects1.pName) + '\t\t\t' + str(objects2.pName) + ' \t\t\t Same\n')
            else:
                text.insert(END,
                            'Pname \t\t' + str(objects1.pName) + '\t\t\t' + str(objects2.pName) + ' \t\t\t Not Same\n')
 
        if numBeamsCheck.get() == 1:
            if str(objects1.numBeams) == str(objects2.numBeams):
                text.insert(END, 'Num Of Beams \t\t' + str(objects1.numBeams) + '\t\t\t' + str(
                    objects2.numBeams) + ' \t\t\t Same\n')
            else:
                text.insert(END, 'Num Of Beams \t\t' + str(objects1.numBeams) + '\t\t\t' + str(
                    objects2.numBeams) + ' \t\t\t Not Same\n')

        beams_file_1 = objects1.beam.copy() # copying the objects in the list 'beam[]'
        beams_file_2 = objects2.beam.copy() # each numbered beam object has beam[] list, as specified in line 154

        text.insert(END, '\n---------------- ---------------- ----------------\n\n')
        total_beams=str(len(beams_file_1)) #spot_data_size = len(beams_file_1[i].CP)
        for i in range(len(beams_file_1)): #loop for all beams

            text.insert(END, '\t\t\t\tBeam '+str(i+1)+' Of '+total_beams+' \n\n')
            if bNameCheck.get() == 1:
                if str(beams_file_1[i].bName) == str(beams_file_2[i].bName):
                    text.insert(END, 'Beam (B Name) \t\t' + str(beams_file_1[i].bName) + '\t\t\t' + str(beams_file_2[i].bName) + ' \t\t\t Same\n')
                else:
                    text.insert(END, 'Beam (B Name) \t\t' + str(beams_file_1[i].bName) + '\t\t\t' + str(beams_file_2[i].bName) + ' \t\t\t Not Same\n')
                text.insert(END, '\n')

            if typeCheck.get() == 1:
                if str(beams_file_1[i].type) == str(beams_file_2[i].type):
                    text.insert(END, 'Beam (Type) \t\t' + str(beams_file_1[i].type) + '\t\t\t' + str(beams_file_2[i].type) + ' \t\t\t Same\n')
                else:
                    text.insert(END, 'Beam (Type) \t\t' + str(beams_file_1[i].type) + '\t\t\t' + str(beams_file_2[i].type) + ' \t\t\t Not Same\n')
                text.insert(END, '\n')

            if gAngleCheck.get() == 1:
                if str(beams_file_1[i].gAngle) == str(beams_file_2[i].gAngle):
                    text.insert(END, 'Beam (G Angle) \t\t' + str(beams_file_1[i].gAngle) + '\t\t\t' + str(beams_file_2[i].gAngle) + ' \t\t\t Same\n')
                else:
                    text.insert(END, 'Beam (G Angle) \t\t' + str(beams_file_1[i].gAngle) + '\t\t\t' + str(beams_file_2[i].gAngle) + ' \t\t\t Not Same\n')
                text.insert(END, '\n')

            if cAngleCheck.get() == 1:
                if str(beams_file_1[i].cAngle) == str(beams_file_2[i].cAngle):
                    text.insert(END, 'Beam (C Angle) \t\t' + str(beams_file_1[i].cAngle) + '\t\t\t' + str(
                        beams_file_2[i].cAngle) + ' \t\t\t Same\n')
                else:
                    text.insert(END, 'Beam (C Angle) \t\t' + str(beams_file_1[i].cAngle) + '\t\t\t' + str(
                        beams_file_2[i].cAngle) + ' \t\t\t Not Same\n')
                text.insert(END, '\n')

            if bMetersetUnitCheck.get() == 1:
                if str(beams_file_1[i].bMetersetUnit) == str(beams_file_2[i].bMetersetUnit):
                    text.insert(END, 'Beam (B MetersetUnit) \t\t' + str(beams_file_1[i].bMetersetUnit) + '\t\t\t' + str(
                        beams_file_2[i].bMetersetUnit) + ' \t\t\t Same\n')
                else:
                    text.insert(END, 'Beam (B MetersetUnit) \t\t' + str(beams_file_1[i].bMetersetUnit) + '\t\t\t' + str(
                        beams_file_2[i].bMetersetUnit) + ' \t\t\t Not Same\n')


                    # for j in range(len(beams_file_1[i].CP)):
                    #    print(beams_file_1[i].CP[j].X)
                text.insert(END, '\n')

            if bMetersetCheck.get() == 1:
                if str(beams_file_1[i].bMeterset) == str(beams_file_2[i].bMeterset):
                    text.insert(END, 'Beam (B Meterset) \t\t' + str(beams_file_1[i].bMeterset) + '\t\t\t' + str(
                        beams_file_2[i].bMeterset) + ' \t\t\t Same\n')
                else:
                    text.insert(END, 'Beam (B Meterset) \t\t' + str(beams_file_1[i].bMeterset) + '\t\t\t' + str(
                        beams_file_2[i].bMeterset) + ' \t\t\t Not Same\n')
                text.insert(END, '\n')

            if numCPCheck.get() == 1:
                if str(beams_file_1[i].numCP) == str(beams_file_2[i].numCP):
                    text.insert(END, 'Beam (Num CP) \t\t' + str(beams_file_1[i].numCP) + '\t\t\t' + str(
                        beams_file_2[i].numCP) + ' \t\t\t Same\n')
                else:
                    text.insert(END, 'Beam (Num CP) \t\t' + str(beams_file_1[i].numCP) + '\t\t\t' + str(
                        beams_file_2[i].numCP) + ' \t\t\t Not Same\n')
                text.insert(END, '\n')


            if EnCheck.get() == 1:
                text.insert(END, '\n---------------- ---------------- ----------------\n\n')
                spot_data_size = len(beams_file_1[i].CP) # length equal to the number of control points for each beam 
                if spot_data_size > 0: # no importance if layer energy is 0 -- second layer is normally zero 
                    # This is the Spot Class Data
                    for j in range(len(beams_file_1[i].CP)):
                        if str(beams_file_1[i].CP[j].En) == str(beams_file_1[i].CP[j].En):
                            text.insert(END, 'Spot Data (EN) \t\t' + str(beams_file_1[i].CP[j].En) + '\t\t\t' + str(
                                beams_file_2[i].CP[j].En) + ' \t\t\t Same\n')
                        else:
                            text.insert(END, 'Spot Data (EN) \t\t' + str(beams_file_1[i].CP[j].En) + '\t\t\t' + str(
                                beams_file_2[i].CP[j].En) + ' \t\t\t Not Same\n')
                        text.insert(END, '\n')



                        # print(beams_file_1[i].CP[j].X)
                # print(beams_file_1[i].CP[j].Y)
                # print(beams_file_1[i].CP[j].sizeX)
                # print(beams_file_1[i].CP[j].sizeY)
                # print(beams_file_1[i].CP[j].sMeterset)
                # print(beams_file_1[i].CP[j].sMU)

        ERROR_LBL.config(text="Done", fg="black")
    else:
        ERROR_LBL.config(text="Please Select Files",fg="red")

def compare():
    th=threading.Thread(target=startThread,args=())
    th.daemon=True
#Without daemon threads, you'd have to keep track of them, and tell them to exit, 
#before your program can completely quit. By setting them as daemon threads, you can let them run 
#and forget about them, and when your program quits, any daemon threads are killed automatically.
    th.start()



def quit():
    root.destroy()

def browse_file(file):
    def _callback():
        file_path = filedialog.askopenfile(parent=root, mode='rb',
                                           filetypes=(("DICOM Files", ".dcm"), ("DICOM Files", "*.dcm")),
                                           title="Select File 1.")
        if file_path != None:
            if file==1:
                file1.set(str(file_path.name))
            elif file==2:
                file2.set(str(file_path.name))
    return _callback


def start():
    global canvas
    canvas = Canvas(root, width=width, height=height)
    canvas.pack()

    x=50
    y=15


    entry_file1name = Entry(canvas, width=65, font=(14), bd=3, textvariable=file1, state=DISABLED)
    canvas.create_window((x, y), window=entry_file1name, anchor="nw")

    btn_Browse1 = Button(canvas, text="Browse DICOM File", width=20, background="white", command=browse_file(1))
    btn_Browse1.bind('<Return>', browse_file(1))
    canvas.create_window((x+620, y-5), window=btn_Browse1, anchor="nw")

    y = y + 40

    entry_file2name = Entry(canvas, width=65, font=(14), bd=3, textvariable=file2, state=DISABLED)
    canvas.create_window((x, y), window=entry_file2name, anchor="nw")


    btn_Browse2 = Button(canvas, text="Browse DICOM File", width=20, background="white", command=browse_file(2))
    btn_Browse2.bind('<Return>', browse_file(2))
    canvas.create_window((x + 620, y), window=btn_Browse2, anchor="nw")

    y = y + 40

    check1 = Checkbutton(canvas, text="PName", variable=pNameCheck)
    canvas.create_window(x, y, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="Num Of Beams", variable=numBeamsCheck)
    canvas.create_window(x+80, y, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="B Name", variable=bNameCheck)
    canvas.create_window(x+200, y, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="Type", variable=typeCheck)
    canvas.create_window(x+320, y, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="EN", variable=EnCheck)
    canvas.create_window(x + 410, y, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="C Angle", variable=cAngleCheck)
    canvas.create_window(x, y+30, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="G Angle", variable=gAngleCheck)
    canvas.create_window(x+80, y + 30, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="B Meterset Unit", variable=bMetersetUnitCheck)
    canvas.create_window(x+200, y+30, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="B Meterset", variable=bMetersetCheck)
    canvas.create_window(x + 320, y+30, window=check1, anchor='w')

    check1 = Checkbutton(canvas, text="Num CP", variable=numCPCheck)
    canvas.create_window(x + 410, y+30, window=check1, anchor='w')

    y = y + 50

    frame = Frame(canvas)

    canvas.create_window((x, y), window=frame, anchor="nw")

    global text
    text = Text(frame, font=("Helvetica", 12))
    text.pack(side="left", fill="y")

    scrollbar = Scrollbar(frame, orient="vertical")
    scrollbar.config(command=text.yview)
    scrollbar.pack(side="right", fill="y")

    text.config(yscrollcommand=scrollbar.set)

    y=y+440
    global ERROR_LBL
    ERROR_LBL = Label(canvas, fg='black', justify='left')
    canvas.create_window((x, y), window=ERROR_LBL, anchor="nw")

    y = y + 30

    btn_Compare = Button(canvas, text="Compare", font=(14), foreground="white", background="#062569", width=13, command=compare)
    btn_Compare.bind('<Return>', compare)
    canvas.create_window((x, y), window=btn_Compare, anchor="nw")

    btn_Exit = Button(canvas, text="Exit", font=(14), foreground="white", background="#062569", width=13,
                         command=quit)
    btn_Exit.bind('<Return>', quit)
    canvas.create_window((x+150, y), window=btn_Exit, anchor="nw")

    root.protocol("WM_DELETE_WINDOW", quit)
    root.resizable(0, 0)
    root.mainloop()


start()
