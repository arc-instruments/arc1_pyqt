####################################

# (c) Spyros Stathopoulos
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
from functools import partial
import sys
import os
import time
import numpy as np
import scipy.stats as stat
import scipy.version
from scipy.optimize import curve_fit, leastsq, least_squares
import pyqtgraph
import copy

from arc1pyqt import Graphics
from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.GeneratedUiElements.pf import Ui_PFParent
from arc1pyqt.GeneratedUiElements.fitdialog import Ui_FitDialogParent
from arc1pyqt.Globals import fonts, styles, functions
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag


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


def _curve_fit(func, x, y, **kwargs):
    v = scipy.version.short_version.split('.')
    if int(v[0]) == 0 and int(v[1]) <= 16:
        if 'method' in kwargs.keys():
            kwargs.pop('method')
    return curve_fit(func, x, y, **kwargs)


class ModelWidget(QtWidgets.QWidget):

    def __init__(self, parameters, func, expression="", parent=None):
        super().__init__(parent=parent)
        self.expressionLabel = QtWidgets.QLabel("Model expression: %s" % expression)
        self.parameterTable = QtWidgets.QTableWidget(len(parameters), 2, parent=self)
        self.parameterTable.horizontalHeader().setVisible(True)
        self.parameterTable.setVerticalHeaderLabels(parameters)
        self.parameterTable.setHorizontalHeaderLabels(["> 0 branch","< 0 branch"])
        self.parameterTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.parameterTable.setSelectionMode(QtWidgets.QTableWidget.NoSelection)

        self.func = func

        container = QtWidgets.QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(self.expressionLabel)
        container.addWidget(self.parameterTable)

        self.setLayout(container)

        for (i, p) in enumerate(parameters):
            pos = QtWidgets.QTableWidgetItem("1.0")
            neg = QtWidgets.QTableWidgetItem("1.0")
            self.parameterTable.setItem(i, 0, pos)
            self.parameterTable.setItem(i, 1, neg)


    def updateValues(self, pPos, pNeg):
        for (i, val) in enumerate(pPos):
            self.parameterTable.setItem(i, 0, QtWidgets.QTableWidgetItem(str(val)))
        for (i, val) in enumerate(pNeg):
            self.parameterTable.setItem(i, 1, QtWidgets.QTableWidgetItem(str(val)))

    def modelFunc(self):
        return self.func

class FitDialog(Ui_FitDialogParent, QtWidgets.QDialog):

    resistances = []
    voltages = []
    pulses = []
    modelData = []
    mechanismParams = {'pos': None, 'neg': None}

    def __init__(self, w, b, raw_data, parent=None):
        Ui_FitDialogParent.__init__(self)
        QtWidgets.QDialog.__init__(self, parent=parent)
        self.setupUi(self)
        self.setWindowTitle("Parameter fit for W=%d | B=%d" % (w, b))
        self.setWindowIcon(Graphics.getIcon('appicon'))

        self.numPulsesEdit.setValidator(QtGui.QIntValidator())

        self.fitButton.clicked.connect(self.fitClicked)
        self.exportModelDataButton.clicked.connect(self.exportClicked)
        self.exportVerilogButton.clicked.connect(self.exportVerilogClicked)
        self.fitMechanismModelButton.clicked.connect(self.fitMechanismClicked)
        self.mechanismModelCombo.currentIndexChanged.connect(self.mechanismModelComboIndexChanged)

        self.resistances[:] = []
        self.voltages[:] = []
        self.pulses[:] = []
        self.modelData[:] = []
        self.modelParams = {}
        self.IVs = []

        unique_pos_voltages = set()
        unique_neg_voltages = set()

        in_ff = True
        currentIV = { "R0": -1.0, "data": [[],[]] }

        for line in raw_data:
            if str(line[3]).split("_")[1] == 'FF':
                in_ff = True
                self.resistances.append(line[0])
                self.voltages.append(line[1])
                if line[1] >= 0:
                    unique_pos_voltages.add(line[1])
                else:
                    unique_neg_voltages.add(line[1])
                self.pulses.append(line[2])
            else:
                if in_ff:
                    if len(currentIV["data"][0]) > 0 and len(currentIV["data"][1]) > 0:
                        self.IVs.append(currentIV)
                    currentIV = { "R0": self.resistances[-1], "data": [[],[]] }
                in_ff = False

                voltage = float(line[5])
                current = float(line[5])/float(line[0])
                currentIV["data"][0].append(voltage)
                currentIV["data"][1].append(current)

        self.resistancePlot = self.responsePlotWidget.plot(self.resistances, clear=True,
            pen=pyqtgraph.mkPen({'color': 'F00', 'width': 1}))

        self.fitPlot = None

        self.responsePlotWidget.setLabel('left', 'Resistance', units=u"Ω")
        self.responsePlotWidget.setLabel('bottom', 'Pulse')
        self.mechanismPlotWidget.setLabel('left', 'Current', units="A")
        self.mechanismPlotWidget.setLabel('bottom', 'Voltage', units="V")

        self.curveSelectionSpinBox.setMinimum(1)
        self.curveSelectionSpinBox.setMaximum(len(self.IVs))
        self.curveSelectionSpinBox.valueChanged.connect(self.IVSpinBoxValueChanged)
        self.IVSpinBoxValueChanged(1)

        for v in sorted(unique_pos_voltages):
            self.refPosCombo.addItem(str(v), v)
        for v in sorted(unique_neg_voltages, reverse=True):
            self.refNegCombo.addItem(str(v), v)

        self.modelWidgets = {}

        self.modelWidgets["sinh"] = ModelWidget(["a","b"],
                lambda p, x: p[0]*np.sinh(p[1]*x), "y = a*sinh(b*x)")

        self.modelWidgets["linear"] = ModelWidget(["a"],
                lambda p, x: p[0]*x, "y=a*x")

        for (k, v) in self.modelWidgets.items():
            self.modelStackedWidget.addWidget(v)
            self.mechanismModelCombo.addItem(k, v)

        if len(self.IVs) < 1:
            mechanismTab = self.tabWidget.findChild(QtWidgets.QWidget, \
                "mechanismTab")
            idx = self.tabWidget.indexOf(mechanismTab)
            if idx > 0:
                self.tabWidget.setTabEnabled(idx, False)

    def exportClicked(self):
        saveCb = partial(functions.writeDelimitedData, self.modelData)
        functions.saveFuncToFilename(saveCb, title="Save data to...", parent=self)

    def IVSpinBoxValueChanged(self, value):

        if len(self.IVs) < 1:
            return

        R0 = self.IVs[value-1]["R0"]
        x = np.array(self.IVs[value-1]["data"][0])
        y = np.array(self.IVs[value-1]["data"][1])

        self.mechanismPlotWidget.plot(x,y, clear=True, pen=None, symbol='o', symbolSize=5)

        if self.mechanismParams['pos'] is not None:
            p0 = self.mechanismParams['pos'][0]
            p1 = self.mechanismParams['pos'][1]
            lxPos = np.linspace(np.min(x[x > 0]), np.max(x[x > 0]))
            self.mechanismPlotWidget.plot(lxPos, p0*np.sinh(lxPos*p1)/R0)

        if self.mechanismParams['neg'] is not None:
            p0 = self.mechanismParams['neg'][0]
            p1 = self.mechanismParams['neg'][1]
            lxNeg = np.linspace(np.min(x[x < 0]), np.max(x[x < 0]))
            self.mechanismPlotWidget.plot(lxNeg, p0*np.sinh(lxNeg*p1)/R0)

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
        functions.saveFuncToFilename(saveModel, title="Save Verilog-A model to...",
                parent=self)

    def mechanismModelComboIndexChanged(self, index):
        self.modelStackedWidget.setCurrentIndex(index)

    def fitMechanismClicked(self):

        # all IVs are in self.IVs
        # self.IVs is a list of lists containing the I-V data
        # for example self.IVs[0] is the first I-V obtained
        # the x-data is self.IVs[0][0] and the y-data is self.IVs[0][1]
        # For the second IV the data are x: self.IVs[1][0] y: self.IVs[1][1]
        # For the third IV the data are x: self.IVs[2][0] y: self.IVs[2][1]
        # etc.

        xPos = []
        yPos = []
        xNeg = []
        yNeg = []

        for (id, curve) in enumerate(self.IVs):
            R0 = curve["R0"]
            ndata = np.array(curve["data"]).transpose()
            posData = ndata[np.where(ndata[:,0] > 0)].transpose()
            xPos.extend(posData[0])
            yPos.extend(posData[1]*R0)

            negData = ndata[np.where(ndata[:,0] < 0)].transpose()
            xNeg.extend(negData[0])
            yNeg.extend(negData[1]*R0)

        idx = self.mechanismModelCombo.currentIndex()
        widget = self.mechanismModelCombo.itemData(idx).toPyObject()
        func = widget.modelFunc()
        errFunc = lambda p, x, y: y - func(p, x)

        resPos = least_squares(errFunc, (1.0, 1.0), method='lm', args=(np.array(xPos), np.array(yPos)))
        resNeg = least_squares(errFunc, (1.0, 1.0), method='lm', args=(np.array(xNeg), np.array(yNeg)))

        self.mechanismParams['pos'] = resPos.x
        self.mechanismParams['neg'] = resNeg.x

        self.IVSpinBoxValueChanged(self.curveSelectionSpinBox.value())
        widget.updateValues(resPos.x, resNeg.x)

    def fitClicked(self):
        self.parameterResultLabel.setText("")
        numPoints = int(self.numPulsesEdit.text())
        posRef = float(self.refPosCombo.itemData(self.refPosCombo.currentIndex()))
        negRef = float(self.refNegCombo.itemData(self.refNegCombo.currentIndex()))

        try:
            (Spos, Sneg, tp, tn, a0p, a1p, a0n, a1n, sgnPOS, sgnNEG, tw) = self.fit(posRef, negRef, numPoints)
        except RuntimeError:
            self.parameterResultLabel.setText("Convergence error!")
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
            self.fitPlot = self.responsePlotWidget.plot(self.modelData,pen=pyqtgraph.mkPen({'color': '00F', 'width': 1}))
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

    # Rinit: initial memristor resistance (Ohm)
    # t: pulse width (s)
    # tx: tp (positive) or tn (negative) (V)
    # A: Ap (positive) or An (negative) (Ohm/s)
    # a0: a0p (positive) or a0n (negative) (Ohm)
    # a1: a1p (positive) or a1n (negative) (Ohm/v)
    # sgn: +1 (positive) -1 (negative)
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

        R = np.array(self.resistances[:])
        V = np.array(self.voltages[:])
        t = np.array(self.pulses[:])

        time = np.arange(t[0], (numPoints+1)*t[0], t[0])
        time = time[:numPoints]

        # find all unique voltages
        posVOL = np.unique(V[V > 0])
        negVOL = np.unique(V[V < 0])

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

        NEGlimitPOSITION = np.where(np.abs(negVOL-NEGlimit) < 1e-6)[0][0]
        POSlimitPOSITION = np.where(np.abs(posVOL-POSlimit) < 1e-6)[0][0]

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

        RmaxSET=np.empty(len(posVOL[:(POSlimitPOSITION+1)]))

        # Rm for each set
        for i in range(len(posVOL[:(POSlimitPOSITION+1)])):
            def funPOSfinal(t,Rm):
                return (R0pos[:(POSlimitPOSITION+1)][i]+(Spos*(-1+np.exp(posVOL[:(POSlimitPOSITION+1)][i]/tp)))*(Rm**2)*t-(Spos*(-1+np.exp(posVOL[:(POSlimitPOSITION+1)][i]/tp)))*Rm*R0pos[:(POSlimitPOSITION+1)][i]*t)/(1+(Spos*(-1+np.exp(posVOL[:(POSlimitPOSITION+1)][i]/tp)))*(Rm-R0pos[:(POSlimitPOSITION+1)][i])*t)
            a=_curve_fit(funPOSfinal, time, positiveDATAarray[:(POSlimitPOSITION+1)][i][:,1], p0=(Rmpos[i]),method='lm')
            RmaxSET[i] = a[0][0]

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

        RminSET=np.empty(len(negVOL[(NEGlimitPOSITION):]))
        for i in range(len(negVOL[(NEGlimitPOSITION):])):
            def funNEGfinal(t,Rm):
                return (R0neg[(NEGlimitPOSITION):][i]+(Sneg*(-1+np.exp(-negVOL[(NEGlimitPOSITION):][i]/tn)))*(Rm**2)*t-(Sneg*(-1+np.exp(-negVOL[(NEGlimitPOSITION):][i]/tn)))*Rm*R0neg[(NEGlimitPOSITION):][i]*t)/(1+(Sneg*(-1+np.exp(-negVOL[(NEGlimitPOSITION):][i]/tn)))*(Rm-R0neg[(NEGlimitPOSITION):][i])*t)
            a=_curve_fit(funNEGfinal, time, negativeDATAarray[(NEGlimitPOSITION):][i][:,1], p0=(Rmneg[(NEGlimitPOSITION):][i]),method='lm')
            RminSET[i] = a[0][0]

        def RminFIT(x,a,b):
            return a*x+b

        params1N=_curve_fit(RminFIT, negVOL[(NEGlimitPOSITION):], RminSET, method='lm')

        a0n=params1N[0][1] #value for the a0n parameter in (4)
        a1n=params1N[0][0] #value for the a1n parameter in (4)

        return (Spos, Sneg, tp, tn, a0p, a1p, a0n, a1n, sgnPOS, sgnNEG, t[0])


class ThreadWrapper(BaseThreadWrapper):

    sendDataCT = QtCore.pyqtSignal(int, int, float, float, float, str)

    def __init__(self, deviceList, params = {}):
        super().__init__()
        self.deviceList = deviceList
        self.params = params

    @BaseThreadWrapper.runner
    def run(self):

        global tag
        midTag = "%s_%%s_i" % tag

        DBG = bool(os.environ.get('PFDBG', False))

        voltages = []

        vpos = np.arange(self.params["vstart_pos"], self.params["vstop_pos"], self.params["vstep_pos"])
        vneg = np.arange(self.params["vstart_neg"], self.params["vstop_neg"], self.params["vstep_neg"])

        numVoltages = min(len(vpos), len(vneg))
        for i in range(numVoltages):
            voltages.append(vpos[i])
            voltages.append(vneg[i])

        for device in self.deviceList:
            w = device[0]
            b = device[1]
            self.highlight.emit(w, b)

            for (i, voltage) in enumerate(voltages):
                if i == 0:
                    startTag = "%s_%%s_s" % tag
                else:
                    startTag = "%s_%%s_i" % tag

                if i == (len(voltages)-1):
                    endTag = "%s_%%s_e" % tag
                else:
                    endTag = "%s_%%s_i" % tag

                if self.params["run_iv"]:
                    self.formFinder(w, b, voltage, self.params["pulse_width"], self.params["interpulse"],
                            self.params["pulses"], startTag % "FF", midTag % "FF", midTag % "FF")
                    self.curveTracer(w, b, self.params["ivstop_pos"], self.params["ivstop_neg"],
                            self.params["ivstart"], self.params["ivstep"],
                            self.params["iv_interpulse"], self.params["ivpw"], self.params["ivtype"],
                            midTag % "CT", midTag % "CT", endTag % "CT")
                else:
                    self.formFinder(w, b, voltage, self.params["pulse_width"], self.params["interpulse"],
                            self.params["pulses"], startTag % "FF", midTag % "FF", endTag % "FF")

            self.updateTree.emit(w, b)


    def curveTracer(self, w, b, vPos, vNeg, vStart, vStep, interpulse, pwstep, ctType, startTag, midTag, endTag):

        HW.ArC.write_b(str(201) + "\n")

        HW.ArC.write_b(str(vPos) + "\n")
        HW.ArC.write_b(str(vNeg) + "\n")
        HW.ArC.write_b(str(vStart) + "\n")
        HW.ArC.write_b(str(vStep) + "\n")
        HW.ArC.write_b(str(pwstep) + "\n")
        HW.ArC.write_b(str(interpulse) + "\n")
        time.sleep(0.01)
        HW.ArC.write_b(str(0.0) + "\n") # CSp
        HW.ArC.write_b(str(0.0) + "\n") # CSn
        HW.ArC.write_b(str(1) + "\n") # single cycle
        HW.ArC.write_b(str(ctType) + "\n") # staircase or pulsed
        HW.ArC.write_b(str(0) + "\n") # towards V+ always
        HW.ArC.write_b(str(0) + "\n") # do not halt+return

        HW.ArC.write_b(str(1) + "\n") # single device always
        HW.ArC.queue_select(w, b)

        end = False

        buffer = []
        aTag = ""
        readTag='R'+str(HW.conf.readmode)+' V='+str(HW.conf.Vread)

        while(not end):
            # curValues = []

            # curValues.append(float(HW.ArC.readline().rstrip()))
            # curValues.append(float(HW.ArC.readline().rstrip()))
            # curValues.append(float(HW.ArC.readline().rstrip()))
            curValues = list(HW.ArC.read_floats(3))

            if curValues[0] > 10e9:
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

            # flush buffer values
            self.sendDataCT.emit(w, b, buffer[0], buffer[1], buffer[2], aTag)
            buffer[0] = curValues[0]
            buffer[1] = curValues[1]
            buffer[2] = curValues[2]
            aTag = midTag
            self.displayData.emit()

    def formFinder(self, w, b, V, pw, interpulse, nrPulses, startTag, midTag, endTag):

        HW.ArC.write_b(str(14) + "\n") # job number, form finder

        HW.ArC.write_b(str(V) + "\n") # Vmin == Vmax
        if V > 0:
            HW.ArC.write_b(str(0.1) + "\n") # no step, single voltage
        else:
            HW.ArC.write_b(str(-0.1) + "\n")
        HW.ArC.write_b(str(V) + "\n") # Vmax == Vmin
        HW.ArC.write_b(str(pw) + "\n") # pw_min == pw_max
        HW.ArC.write_b(str(100.0) + "\n") # no pulse step
        HW.ArC.write_b(str(pw) + "\n") # pw_max == pw_min
        HW.ArC.write_b(str(interpulse) + "\n") # interpulse time
        #HW.ArC.write_b(str(nrPulses) + "\n") # number of pulses
        HW.ArC.write_b(str(10.0) + "\n") # 10 Ohms R threshold (ie no threshold)
        HW.ArC.write_b(str(0.0) + "\n") # 0% R threshold (ie no threshold)
        HW.ArC.write_b(str(7) + "\n") # 7 -> no series resistance
        HW.ArC.write_b(str(nrPulses) + "\n") # number of pulses
        HW.ArC.write_b(str(1) + "\n") # single device always
        HW.ArC.queue_select(w, b)

        end = False

        #data = []
        buffer = []
        aTag = ""

        while(not end):

            curValues = list(HW.ArC.read_floats(3))

            if (curValues[2] < 99e-9) and (curValues[0] > 0.0):
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

            # flush buffer values
            self.sendData.emit(w, b, buffer[0], buffer[1], buffer[2], aTag)
            buffer[0] = curValues[0]
            buffer[1] = curValues[1]
            buffer[2] = curValues[2]
            aTag = midTag
            self.displayData.emit()


class ParameterFit(Ui_PFParent, BaseProgPanel):

    PROGRAM_ONE = 0x1
    PROGRAM_RANGE = 0x2
    PROGRAM_ALL = 0x3

    def __init__(self, short=False):
        Ui_PFParent.__init__(self)
        BaseProgPanel.__init__(self, title="Parameter Fit", \
                description="Fit a stimulus model to memristive response", \
                short=short)

        self.setupUi(self)

        self.applyAllButton.setStyleSheet(styles.btnStyle)
        self.applyOneButton.setStyleSheet(styles.btnStyle)
        self.applyRangeButton.setStyleSheet(styles.btnStyle)
        self.titleLabel.setFont(fonts.font1)
        self.descriptionLabel.setFont(fonts.font3)

        self.applyValidators()

        self.noIVCheckBox.stateChanged.connect(self.noIVChecked)

        if not self.short:
            self.applyOneButton.clicked.connect(partial(self.programDevs, \
                    self.PROGRAM_ONE))
            self.applyAllButton.clicked.connect(partial(self.programDevs, \
                    self.PROGRAM_ALL))
            self.applyRangeButton.clicked.connect(partial(self.programDevs, \
                    self.PROGRAM_RANGE))
        else:
            for wdg in [self.applyOneButton, self.applyAllButton, \
                    self.applyRangeButton]:
                wdg.hide()

    def noIVChecked(self, state):
        checked = self.noIVCheckBox.isChecked()

        self.IVStartEdit.setEnabled(not checked)
        self.IVStepEdit.setEnabled(not checked)
        self.IVTypeCombo.setEnabled(not checked)
        self.IVPwEdit.setEnabled(not checked)
        self.IVInterpulseEdit.setEnabled(not checked)
        self.IVStopPosEdit.setEnabled(not checked)
        self.IVStopNegEdit.setEnabled(not checked)

    def applyValidators(self):
        floatValidator = QtGui.QDoubleValidator()
        intValidator = QtGui.QIntValidator()

        self.nrPulsesEdit.setValidator(intValidator)

        self.pulseWidthEdit.setValidator(floatValidator)
        self.interpulseEdit.setValidator(floatValidator)
        self.IVInterpulseEdit.setValidator(floatValidator)
        self.VStartPosEdit.setValidator(floatValidator)
        self.VStepPosEdit.setValidator(floatValidator)
        self.VStopPosEdit.setValidator(floatValidator)
        self.VStartNegEdit.setValidator(floatValidator)
        self.VStepNegEdit.setValidator(floatValidator)
        self.VStopNegEdit.setValidator(floatValidator)
        self.IVStartEdit.setValidator(floatValidator)
        self.IVStepEdit.setValidator(floatValidator)
        self.IVStopPosEdit.setValidator(floatValidator)
        self.IVStopNegEdit.setValidator(floatValidator)
        self.IVPwEdit.setValidator(floatValidator)

        self.IVTypeCombo.addItem("Staircase", 0)
        self.IVTypeCombo.addItem("Pulsed", 1)

        self.registerPropertyWidget(self.nrPulsesEdit, "pulses")
        self.registerPropertyWidget(self.pulseWidthEdit, "pulse_width")
        self.registerPropertyWidget(self.interpulseEdit, "interpulse")
        self.registerPropertyWidget(self.VStartPosEdit, "vstart_pos")
        self.registerPropertyWidget(self.VStepPosEdit, "vstep_pos")
        self.registerPropertyWidget(self.VStopPosEdit, "vstop_pos")
        self.registerPropertyWidget(self.VStartNegEdit, "vstart_neg")
        self.registerPropertyWidget(self.VStepNegEdit, "vstep_neg")
        self.registerPropertyWidget(self.VStopNegEdit, "vstop_neg")
        self.registerPropertyWidget(self.IVStartEdit, "ivstart")
        self.registerPropertyWidget(self.IVStepEdit, "ivstep")
        self.registerPropertyWidget(self.IVStopPosEdit, "ivstop_pos")
        self.registerPropertyWidget(self.IVStopNegEdit, "ivstop_neg")
        self.registerPropertyWidget(self.IVInterpulseEdit, "iv_interpulse")
        self.registerPropertyWidget(self.noIVCheckBox, "dont_run_iv")
        self.registerPropertyWidget(self.IVPwEdit, "ivpw")
        self.registerPropertyWidget(self.IVTypeCombo, "ivtype")

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
        result["ivstart"] = np.abs(float(self.IVStartEdit.text()))
        result["ivstep"] = np.abs(float(self.IVStepEdit.text()))
        result["ivstop_pos"] = np.abs(float(self.IVStopPosEdit.text()))
        result["ivstop_neg"] = np.abs(float(self.IVStopNegEdit.text()))
        result["iv_interpulse"] = np.abs(float(self.IVInterpulseEdit.text()))/1000.0
        result["run_iv"] = (not self.noIVCheckBox.isChecked())
        result["ivpw"] = np.abs(float(self.IVPwEdit.text()))/1000.0
        result["ivtype"] = int(self.IVTypeCombo.itemData(self.IVTypeCombo.currentIndex()))

        return result

    def programOne(self):
        self.programDevs(self.PROGRAM_ONE)

    def programRange(self):
        self.programDevs(self.PROGRAM_RANGE)

    def programAll(self):
        self.programDevs(self.PROGRAM_ALL)

    def programDevs(self, programType):

        if programType == self.PROGRAM_ONE:
            devs = [[CB.word, CB.bit]]
        else:
            if programType == self.PROGRAM_RANGE:
                devs = makeDeviceList(True)
            else:
                devs = makeDeviceList(False)

        allData = self.gatherData()

        wrapper = ThreadWrapper(devs, allData)
        self.execute(wrapper, wrapper.run)

    def disableProgPanel(self,state):
        if state == True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    @staticmethod
    def display(w, b, data, parent=None):
        dialog = FitDialog(w, b, data, parent)

        return dialog


tags = { 'top': ModTag(tag, "ParameterFit", ParameterFit.display) }
