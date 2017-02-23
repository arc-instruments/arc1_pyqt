# -*- coding: utf-8 -*-
####################################

# (c) Spyros Stathopoulos
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui, QtCore
from functools import partial
import sys
import os
import time
import numpy as np
import scipy.stats as stat
import scipy.version
from scipy.optimize import curve_fit
import pyqtgraph
import copy

import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

from GeneratedUiElements.pf import Ui_PFParent
from GeneratedUiElements.fitdialog import Ui_FitDialogParent

MODEL_TMPL="""//////////////////////////////////////////////////
// VerilogA model for the
//
// Compact TiO2 ReRAM model
//
// Department of Physics, Aristotle University of Thessaloniki
// Nano Research Group, Electronics and Computer Science Department,
// University of Southampton
//
// November 2016
//
//////////////////////////////////////////////////


`include "disciplines.vams"
`include "constants.h"

module memSQUARE(p, n, rs);
	inout p, n, rs;

electrical p, n, rs, x;

//'Switching sensitivity' parameters for v>0
parameter real Ap = %e;
parameter real tp = %e;

//'Switching sensitivity' parameters for v<0
parameter real An = %e;
parameter real tn = %e;

//'Absolute threshold' parameters for v>0
parameter real a0p = %e;
parameter real a1p = %e;

//'Absolute threshold' parameters for v<0
parameter real a0n = %e;
parameter real a1n = %e;

//Initial memristance
parameter real Rinit = %e;

//Stp function parameters
parameter real c1=1e-3;
parameter real c2=1;

//reset direction under positive stimulation s=1 for DR(v>0)>0 else s=-1
parameter real s=%d;

real Rmp; 		// 'Absolute threshold' function for v>0
real Rmn; 		// 'Absolute threshold' function for v<0
real stpPOSv; 	// step function for v>0
real stpNEGv; 	// step function for v<0
real stpWFpos; 	// step function for R<Rmax
real stpWFneg; 	// step function for R>Rmin
real swSENpos; 	// 'Switching sensitivity' function for v>0
real swSENneg; 	// 'Switching sensitivity' function for v>0
real WFpos; 	// 'Window function' for v>0
real WFneg; 	// 'Window function' for v<0
real dRdtpos; 	// Switching rate function for v>0
real dRdtneg; 	// Switching rate function for v<0
real dRdt; 		// Switching rate function
real res; 		// Helping parameter that captures device RS evolution
real vin; 		// Input voltage parameter


//Switching sensitivity function definition
analog function real sense_fun;
input A,t,in;
real A,t,in;
begin
sense_fun=A*(-1+exp(abs(in)/t));
end
endfunction


analog begin

//input voltage applied on device terminals assigned on parameter vin
vin=V(p,n);

//Absolute threshold functions
Rmp=a0p+a1p*vin; //for v>0
Rmn=a0n+a1n*vin; //for v<0

// 'limexp' is used instead of 'exp' to prevent numerical overflows
// imposed by the stp functions
stpPOSv=1/(1+limexp(-vin/c1)); //implementation of smoothed step function step(vin)
stpNEGv=1/(1+limexp(vin/c1)); //implementation of smoothed step function step(-vin)

stpWFpos=1/(1+limexp(-s*(Rmp-V(x))/c2)); //implementation of smoothed step function step(Rmp-V(x))
stpWFneg=1/(1+limexp(-(-s)*(Rmn-V(x))/c2)); //implementation of smoothed step function step(Rmp-V(x))

//Switching sensitivity functions
swSENpos=sense_fun(Ap,tp,vin);
swSENneg=sense_fun(An,tn,vin);

//Implementation of switching rate "dRdt" function
WFpos=pow(Rmp-V(x),2)*stpWFpos;
WFneg=pow(Rmn-V(x),2)*stpWFneg;

dRdtpos=swSENpos*WFpos;
dRdtneg=swSENneg*WFneg;

dRdt=dRdtpos*stpPOSv+dRdtneg*stpNEGv;

//Integration of "dRdt" function
V(x) <+ idt(dRdt,Rinit);

// device RS is assigned on an internal voltage node 'x',
// this is done to perform recursive integration of internal state variable (RS)
res=V(x);

V(rs)<+res;

I(p, n)<+ V(p, n)/res; // Ohms law


end

endmodule"""

tag="MPF"
g.tagDict.update({tag:"Parameter Fit*"})

def _curve_fit(func, x, y, **kwargs):
    v = scipy.version.short_version.split('.')
    if int(v[1]) <= 16:
        if 'method' in kwargs.keys():
            kwargs.pop('method')
    return curve_fit(func, x, y, **kwargs)

class FitDialog(Ui_FitDialogParent, QtGui.QDialog):

    resistances = []
    voltages = []
    pulses = []
    modelData = []

    def __init__(self, w, b, raw_data, parent=None):
        super(FitDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.setWindowTitle("Parameter fit for W=%d | B=%d" % (w, b))
        self.setWindowIcon(QtGui.QIcon(os.getcwd()+'/Graphics/'+'icon3.png'))

        self.VPosRefEdit.setValidator(QtGui.QDoubleValidator())
        self.VNegRefEdit.setValidator(QtGui.QDoubleValidator())
        self.numPulsesEdit.setValidator(QtGui.QIntValidator())

        self.fitButton.clicked.connect(self.fitClicked)
        self.exportModelDataButton.clicked.connect(self.exportClicked)
        self.exportVerilogButton.clicked.connect(self.exportVerilogClicked)

        self.resistances[:] = []
        self.voltages[:] = []
        self.pulses[:] = []
        self.modelData[:] = []
        self.modelParams = {}

        for line in raw_data:
            self.resistances.append(line[0])
            self.voltages.append(line[1])
            self.pulses.append(line[2])

        self.resistancePlot = self.plotWidget.plot(self.resistances, clear=True,
            pen=pyqtgraph.mkPen({'color': 'F00', 'width': 1}))

        self.fitPlot = None

        self.plotWidget.setLabel('left', 'Resistance', units=u"Ω")
        self.plotWidget.setLabel('bottom', 'Pulse')

    def exportClicked(self):
        saveCb = partial(f.writeDelimitedData, self.modelData)
        # print(self.modelData)
        f.saveFuncToFilename(saveCb, title="Save data to...", parent=self)

    def exportVerilogClicked(self):
        aPos = self.modelParams["aPos"]
        aNeg = self.modelParams["aNeg"]
        a0p = self.modelParams["a0p"]
        a0n = self.modelParams["a0n"]
        a1p = self.modelParams["a1p"]
        a1n = self.modelParams["a1n"]
        txp = self.modelParams["txp"]
        txn = self.modelParams["txn"]
        s = self.modelParams["sgnPOS"]
        R = self.modelParams["R0"]

        model = (MODEL_TMPL % (aPos, txp, aNeg, txn, a0p, a1p, a0n, a1n, R, s))
        def saveModel(fname):
            with open(fname, 'w') as f:
                f.write(model)
        f.saveFuncToFilename(saveModel, title="Save Verilog-A model to...", parent=self)

    def fitClicked(self):
        numPoints = int(self.numPulsesEdit.text())
        posRef = float(self.VPosRefEdit.text())
        negRef = float(self.VNegRefEdit.text())

        (Spos, Sneg, tp, tn, a0p, a1p, a0n, a1n, sgnPOS, sgnNEG, tw) = self.fit(posRef, negRef, numPoints)
        (Rinit, result) = self.response(Spos, Sneg, tp, tn, a0p, a1p, a0n, a1n, sgnPOS, sgnNEG, tw)

        self.modelParams["aPos"] = Spos
        self.modelParams["aNeg"] = Sneg
        self.modelParams["txp"] = tp
        self.modelParams["txn"] = tn
        self.modelParams["a0p"] = a0p
        self.modelParams["a1p"] = a1p
        self.modelParams["a0n"] = a0n
        self.modelParams["a1n"] = a1n
        self.modelParams["sgnPOS"] = sgnPOS
        self.modelParams["sgnNEG"] = sgnNEG
        self.modelParams["R0"] = Rinit
        self.modelData = result

        if self.fitPlot is None:
            self.fitPlot = self.plotWidget.plot(self.modelData,pen=pyqtgraph.mkPen({'color': '00F', 'width': 1}))
        else:
            self.fitPlot.setData(self.modelData)

        self.aPosEdit.setText(str(Spos))
        self.aNegEdit.setText(str(Sneg))
        self.a0PosEdit.setText(str(a0p))
        self.a0NegEdit.setText(str(a0n))
        self.a1PosEdit.setText(str(a1p))
        self.a1NegEdit.setText(str(a1n))
        self.txPosEdit.setText(str(tp))
        self.txNegEdit.setText(str(tn))

    def analytical(self, t, Rinit, A, tx, a0, a1, Vb, sgn):
        return (Rinit+(A*(-1+np.exp(np.abs(Vb/tx))))*(a0+a1*Vb)*((a0+a1*Vb)-Rinit)*(0.5*(np.sign(sgn*((a0+a1*Vb)-Rinit))+1))*t)/(1+(A*(-1+np.exp(np.abs(Vb/tx))))*((a0+a1*Vb)-Rinit)*(0.5*(np.sign(sgn*((a0+a1*Vb)-Rinit))+1))*t)

    def response(self, Spos, Sneg, tp, tn, a0p, a1p, a0n, a1n, sgnPOS, sgnNEG, tw):
        RSSIMresponse = []

        V = np.array(self.voltages[1:])
        R = np.array(self.resistances[1:])

        R0 = R[0]
        Rinit = copy.copy(R0)

        for (i, v) in enumerate(V):
            if v < 0:
                R0 = self.analytical(tw, R0, Sneg, tn, a0n, a1n, v, sgnNEG)
            else:
                R0 = self.analytical(tw, R0, Spos, tp, a0p, a1p, v, sgnPOS)
            RSSIMresponse.append(R0)

        return (Rinit, RSSIMresponse)

    def fit(self, POSlimit, NEGlimit, numPoints=500):
        #R = np.array(self.resistances[1:])
        #V = np.array(self.voltages[1:])
        #t = np.array(self.pulses[1:])
        R = np.array(self.resistances[:])
        V = np.array(self.voltages[:])
        t = np.array(self.pulses[:])

        time = np.arange(t[0], (numPoints+1)*t[0], t[0])
        time = time[:numPoints]

        # find all unique voltages
        posVOL = np.unique(V[V > 0])
        # print(posVOL)
        negVOL = np.unique(V[V < 0])
        # print(negVOL)

        # preallocate the pos/neg arrays: len(posVOL) x numPoints x 3
        positiveDATAarray = np.ndarray((len(posVOL), numPoints, 3))
        negativeDATAarray = np.ndarray((len(posVOL), numPoints, 3))

        # per column assignment
        for (i, voltage) in enumerate(posVOL):
            indices = np.where(V == voltage)
            positiveDATAarray[i][:,0] = time # column 0
            positiveDATAarray[i][:,1] = np.take(R, indices) # column 1
            positiveDATAarray[i][:,2] = np.take(V, indices) # column 2

        for (i, voltage) in enumerate(negVOL):
            indices = np.where(V == voltage)
            negativeDATAarray[i][:,0] = time
            negativeDATAarray[i][:,1] = np.take(R, indices)
            negativeDATAarray[i][:,2] = np.take(V, indices)

        # initial and final resistance values
        R0pos = np.ndarray(len(positiveDATAarray))
        Rmpos = np.ndarray(len(positiveDATAarray))
        R0neg = np.ndarray(len(negativeDATAarray))
        Rmneg = np.ndarray(len(negativeDATAarray))

        for (i, _) in enumerate(positiveDATAarray):
            R0pos[i] = positiveDATAarray[i][0,1]
            Rmpos[i] = positiveDATAarray[i][-1,1]

        for (i, _) in enumerate(negativeDATAarray):
            R0neg[i] = negativeDATAarray[i][0,1]
            Rmneg[i] = negativeDATAarray[i][-1,1]

        stepPOS = np.absolute(posVOL[1] - posVOL[0])
        stepNEG = np.absolute(negVOL[1] - negVOL[0])

        NEGlimitPOSITION = np.where(negVOL == NEGlimit)[0][0]
        POSlimitPOSITION = np.where(posVOL == POSlimit)[0][0]

        sgnPOS = np.sign(Rmpos[-1] - R0pos[-1])
        sgnNEG = np.sign(Rmneg[0] - R0neg[0])


        def funPOSinit(t,S,Rm):
            return (R0pos[POSlimitPOSITION]+S*(Rm**2)*t-S*Rm*R0pos[POSlimitPOSITION]*t)/(1+S*(Rm-R0pos[POSlimitPOSITION])*t)

        params = _curve_fit(funPOSinit, time, positiveDATAarray[POSlimitPOSITION][:,1], p0=(sgnPOS,Rmpos[POSlimitPOSITION]),method='lm')

        Spos=params[0][0] #value for the Ap parameter in (2)
        Rmpos0=params[0][1]

        def funPOSnext(t,tp):
            return (R0pos[POSlimitPOSITION]+(Spos*(-1+np.exp(posVOL[POSlimitPOSITION]/tp)))*(Rmpos0**2)*t-(Spos*(-1+np.exp(posVOL[POSlimitPOSITION]/tp)))*Rmpos0*R0pos[POSlimitPOSITION]*t)/(1+(Spos*(-1+np.exp(posVOL[POSlimitPOSITION]/tp)))*(Rmpos0-R0pos[POSlimitPOSITION])*t)

        params0=_curve_fit(funPOSnext, time, positiveDATAarray[POSlimitPOSITION][:,1], p0=(1),method='lm')

        tp=params0[0][0] # value for the tp parameter in (2)

        fit=[]

        # Rm for each set
        for i in range(len(posVOL[:(POSlimitPOSITION+1)])):
            def funPOSfinal(t,Rm):
                return (R0pos[:(POSlimitPOSITION+1)][i]+(Spos*(-1+np.exp(posVOL[:(POSlimitPOSITION+1)][i]/tp)))*(Rm**2)*t-(Spos*(-1+np.exp(posVOL[:(POSlimitPOSITION+1)][i]/tp)))*Rm*R0pos[:(POSlimitPOSITION+1)][i]*t)/(1+(Spos*(-1+np.exp(posVOL[:(POSlimitPOSITION+1)][i]/tp)))*(Rm-R0pos[:(POSlimitPOSITION+1)][i])*t)
            a=_curve_fit(funPOSfinal, time, positiveDATAarray[:(POSlimitPOSITION+1)][i][:,1], p0=(Rmpos[i]),method='lm')
            fit.append(a)

        RmaxSET=(np.asarray(fit))[:,0][:,0]

        def RmaxFIT(x,a,b):
            return a*x+b

        params1=_curve_fit(RmaxFIT, posVOL[:(POSlimitPOSITION+1)], RmaxSET, method='lm')

        a0p=params1[0][1] #value for the a0p parameter in (4)
        a1p=params1[0][0] #value for the a1p parameter in (4)

        def funNEGinit(t,S,Rm):
            return (R0neg[NEGlimitPOSITION]+S*(Rm**2)*t-S*Rm*R0neg[NEGlimitPOSITION]*t)/(1+S*(Rm-R0neg[NEGlimitPOSITION])*t)

        paramsN = _curve_fit(funNEGinit, time, negativeDATAarray[NEGlimitPOSITION][:,1], p0=(sgnNEG,Rmneg[NEGlimitPOSITION]),method='lm')
        Sneg=paramsN[0][0] #value for the An parameter in (2)
        Rmneg0=paramsN[0][1]


        def funNEGnext(t,tp):
            return (R0neg[NEGlimitPOSITION]+(Sneg*(-1+np.exp(-negVOL[NEGlimitPOSITION]/tp)))*(Rmneg0**2)*t-(Sneg*(-1+np.exp(-negVOL[NEGlimitPOSITION]/tp)))*Rmneg0*R0neg[NEGlimitPOSITION]*t)/(1+(Sneg*(-1+np.exp(-negVOL[NEGlimitPOSITION]/tp)))*(Rmneg0-R0neg[NEGlimitPOSITION])*t)
        params0N=_curve_fit(funNEGnext, time, negativeDATAarray[NEGlimitPOSITION][:,1], p0=(1),method='lm')
        tn=params0N[0][0] #value for the tp parameter in (2)

        fitN=[]
        for i in range(len(negVOL[(NEGlimitPOSITION):])):
            def funNEGfinal(t,Rm):
                return (R0neg[(NEGlimitPOSITION):][i]+(Sneg*(-1+np.exp(-negVOL[(NEGlimitPOSITION):][i]/tn)))*(Rm**2)*t-(Sneg*(-1+np.exp(-negVOL[(NEGlimitPOSITION):][i]/tn)))*Rm*R0neg[(NEGlimitPOSITION):][i]*t)/(1+(Sneg*(-1+np.exp(-negVOL[(NEGlimitPOSITION):][i]/tn)))*(Rm-R0neg[(NEGlimitPOSITION):][i])*t)
            a=_curve_fit(funNEGfinal, time, negativeDATAarray[(NEGlimitPOSITION):][i][:,1], p0=(Rmneg[(NEGlimitPOSITION):][i]),method='lm')
            fitN.append(a)

        RminSET=(np.asarray(fitN))[:,0][:,0]


        def RminFIT(x,a,b):
            return a*x+b

        params1N=_curve_fit(RminFIT, negVOL[(NEGlimitPOSITION):], RminSET, method='lm')

        a0n=params1N[0][1] #value for the a0n parameter in (4)
        a1n=params1N[0][0] #value for the a1n parameter in (4)

        return (Spos, Sneg, tp, tn, a0p, a1p, a0n, a1n, sgnPOS, sgnNEG, t[0])

class ThreadWrapper(QtCore.QObject):

    finished = QtCore.pyqtSignal()
    sendData = QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight = QtCore.pyqtSignal(int,int)
    displayData = QtCore.pyqtSignal()
    updateTree = QtCore.pyqtSignal(int, int)
    disableInterface = QtCore.pyqtSignal(bool)
    getDevices = QtCore.pyqtSignal(int)

    def __init__(self, deviceList, params = {}):
        super(ThreadWrapper, self).__init__()
        self.deviceList = deviceList
        self.params = params

    def run(self):

        global tag
        midTag = "%s_i" % tag

        self.disableInterface.emit(True)

        DBG = bool(os.environ.get('PFDBG', False))

        voltages = []

        vpos = np.arange(self.params["vstart_pos"], self.params["vstop_pos"], self.params["vstep_pos"])
        vneg = np.arange(self.params["vstart_neg"], self.params["vstop_neg"], self.params["vstep_neg"])

        numVoltages = min(len(vpos), len(vneg))
        for i in range(numVoltages):
            voltages.append(vpos[i])
            voltages.append(vneg[i])
        # print(voltages)

        for device in self.deviceList:
            w = device[0]
            b = device[1]
            self.highlight.emit(w, b)

            for (i, voltage) in enumerate(voltages):
                # print("Running voltage %d (%d) from %d"  % (i, i+1, len(voltages)))
                if i == 0:
                    startTag = "%s_s" % tag
                else:
                    startTag = "%s_i" % tag

                if i == (len(voltages)-1):
                    endTag = "%s_e" % tag
                else:
                    endTag = "%s_i" % tag

                # print("%d: %s %s %s" % (i, startTag, midTag, endTag))
                self.formFinder(w, b, voltage, self.params["pulse_width"], self.params["interpulse"],
                        self.params["pulses"], startTag, midTag, endTag)

            self.updateTree.emit(w, b)

        self.disableInterface.emit(False)

        self.finished.emit()

    def formFinder(self, w, b, V, pw, interpulse, nrPulses, startTag, midTag, endTag):

        g.ser.write(str(14) + "\n") # job number, form finder

        g.ser.write(str(V) + "\n") # Vmin == Vmax
        if V > 0:
            g.ser.write(str(0.1) + "\n") # no step, single voltage
        else:
            g.ser.write(str(-0.1) + "\n")
        g.ser.write(str(V) + "\n") # Vmax == Vmin
        g.ser.write(str(pw) + "\n") # pw_min == pw_max
        g.ser.write(str(100.0) + "\n") # no pulse step
        g.ser.write(str(pw) + "\n") # pw_max == pw_min
        g.ser.write(str(interpulse) + "\n") # interpulse time
        g.ser.write(str(nrPulses) + "\n") # number of pulses
        g.ser.write(str(10.0) + "\n") # 10 Ohms R threshold (ie no threshold)
        g.ser.write(str(0.0) + "\n") # 0% R threshold (ie no threshold)
        g.ser.write(str(7) + "\n") # 7 -> no series resistance
        g.ser.write(str(1) + "\n") # single device always
        g.ser.write(str(int(w)) + "\n") # word line
        g.ser.write(str(int(b)) + "\n") # bit line

        end = False

        #data = []
        buffer = []
        aTag = ""

        while(not end):
            curValues = []

            curValues.append(float(g.ser.readline().rstrip()))
            curValues.append(float(g.ser.readline().rstrip()))
            curValues.append(float(g.ser.readline().rstrip()))

            if (curValues[2] < 99e-9) and (curValues[0] > 0.0):
                # print("spurious read")
                continue

            if (int(curValues[0]) == 0) and (int(curValues[1]) == 0) and (int(curValues[2]) == 0):
                end = True
                aTag = endTag

            if (not end):
                if len(buffer) == 0: # first point!
                    buffer = np.zeros(3)
                    buffer[0] = curValues[0]
                    buffer[1] = curValues[1]
                    buffer[2] = curValues[2]
                    aTag = startTag
                    continue

            #data.append(buffer)
            #print(buffer[0], buffer[1], buffer[2], aTag)
            # flush buffer values
            self.sendData.emit(w, b, buffer[0], buffer[1], buffer[2], aTag)
            buffer[0] = curValues[0]
            buffer[1] = curValues[1]
            buffer[2] = curValues[2]
            aTag = midTag
            self.displayData.emit()


class ParameterFit(Ui_PFParent, QtGui.QWidget):

    PROGRAM_ONE = 0x1;
    PROGRAM_RANGE = 0x2;
    PROGRAM_ALL = 0x3;

    def __init__(self, short=False):
        super(ParameterFit, self).__init__()
        self.short = short

        self.setupUi(self)

        self.applyAllButton.setStyleSheet(s.btnStyle)
        self.applyOneButton.setStyleSheet(s.btnStyle)
        self.applyRangeButton.setStyleSheet(s.btnStyle)
        self.titleLabel.setFont(fonts.font1)
        self.descriptionLabel.setFont(fonts.font3)

        self.applyValidators()

        self.applyOneButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ONE))
        self.applyAllButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ALL))
        self.applyRangeButton.clicked.connect(partial(self.programDevs, self.PROGRAM_RANGE))

    def applyValidators(self):
        floatValidator = QtGui.QDoubleValidator()
        intValidator = QtGui.QIntValidator()

        self.nrPulsesEdit.setValidator(intValidator)

        self.pulseWidthEdit.setValidator(floatValidator)
        self.interpulseEdit.setValidator(floatValidator)
        self.VStartPosEdit.setValidator(floatValidator)
        self.VStepPosEdit.setValidator(floatValidator)
        self.VStopPosEdit.setValidator(floatValidator)
        self.VStartNegEdit.setValidator(floatValidator)
        self.VStepNegEdit.setValidator(floatValidator)
        self.VStopNegEdit.setValidator(floatValidator)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width() - object.verticalScrollBar().width())
        return False

    def gatherData(self):
        result = {}

        result["pulses"] = int(self.nrPulsesEdit.text())
        result["pulse_width"] = float(self.pulseWidthEdit.text())/1.0e6
        result["interpulse"] = float(self.interpulseEdit.text())/1.0e3
        result["vstart_pos"] = float(self.VStartPosEdit.text())
        result["vstep_pos"] = float(self.VStepPosEdit.text())
        result["vstop_pos"] = float(self.VStopPosEdit.text())
        result["vstart_neg"] = np.abs(float(self.VStartNegEdit.text()))*(-1.0)
        result["vstep_neg"] = np.abs(float(self.VStepNegEdit.text()))*(-1.0)
        result["vstop_neg"] = np.abs(float(self.VStopNegEdit.text()))*(-1.0)

        return result

    def programDevs(self, programType):

        self.thread=QtCore.QThread()

        if programType == self.PROGRAM_ONE:
            devs = [[g.w, g.b]]
        else:
            if programType == self.PROGRAM_RANGE:
                devs = self.makeDeviceList(True)
            else:
                devs = self.makeDeviceList(False)

        allData = self.gatherData()

        self.threadWrapper = ThreadWrapper(devs, allData)

        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(self.threadWrapper.run)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.finished.connect(self.threadWrapper.deleteLater)
        self.thread.finished.connect(self.threadWrapper.deleteLater)
        self.threadWrapper.sendData.connect(f.updateHistory)
        self.threadWrapper.highlight.connect(f.cbAntenna.cast)
        self.threadWrapper.displayData.connect(f.displayUpdate.cast)
        self.threadWrapper.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.threadWrapper.disableInterface.connect(f.interfaceAntenna.disable.emit)

        self.thread.start()

    def disableProgPanel(self,state):
        if state == True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    def makeDeviceList(self,isRange):
        rangeDev = []
        if isRange == False:
            minW = 1
            maxW = g.wline_nr
            minB = 1
            maxB = g.bline_nr
        else:
            minW = g.minW
            maxW = g.maxW
            minB = g.minB
            maxB = g.maxB

        # Find how many SA devices are contained in the range
        if g.checkSA == False:
            for w in range(minW, maxW + 1):
                for b in range(minB, maxB + 1):
                    rangeDev.append([w, b])
        else:
            for w in range(minW, maxW + 1):
                for b in range(minB, maxB + 1):
                    for cell in g.customArray:
                        if (cell[0] == w and cell[1] == b):
                            rangeDev.append(cell)

        return rangeDev

    @staticmethod
    def display(w, b, data, parent=None):
        dialog = FitDialog(w, b, data, parent)

        return dialog

# Add the display function to the display dictionary
g.DispCallbacks[tag] = ParameterFit.display
