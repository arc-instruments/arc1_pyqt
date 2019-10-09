from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time
import socket       # Import socket module for Internet connections.
import select       # Import select module to allow 'listening' on ports.
import struct
import numpy as np
import csv
import threading

import Globals.GlobalFonts as fonts
import Globals.GlobalVars as g
import Globals.GlobalFunctions as f
import Globals.GlobalStyles as s

tag="UDP" #Tag this module as... System will know how to handle it then.
g.tagDict.update({tag:"UDPconn"})

####################################
# UDP module globals.
# ConnMat(x,y,z): x-> input neuron, y-> output neuron,
# z-> =1: connection exists (1/0),
#     =2: w address,
#     =3: b address,
#     =4: last operation pre? (0) or post? (1)
ConnMat = np.zeros((1,1,1))
# LTP/LTD parameter list.
opEdits = []
# Holds decimanl values of ASCII characters 'a' (axon), 'd' (dendrite) and 's' (synapse).
partcode = (65, 68, 83)
# Flag showing whether the UDP module should continue processing packets or simply exit.
UDPampel = 0

class getData(QtCore.QObject):

    #Define signals to be used throughout module.
    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)
    changeArcStatus=QtCore.pyqtSignal(str)

    def __init__(self, deviceList, preip, preport, postip, postport):
        #General inits.
        self.tstep = 0.00005 #Time step (s) Default: 50us.

        #Plasticity rule inits.

        #STDP related rules.
        self.LTDwin = 750
        self.LTPwin = 2000
        self.searchLim = 100 #How many elements in the past to check for 'missed plasticity opportunities'.

        #SRDP related rules.
        self.searchWin = 20000.0 #Window where avg. spike rate for SRDP calculated - in time ticks.
        self.LTPfTh =  20.0/(self.searchWin*self.tstep) #Frequency bounds above/below which LTP/LTD is triggered - in spikes/searchWin time ticks.
        self.LTDfTh = 5.0 / (self.searchWin*self.tstep)

        #Other inits.
        super(getData,self).__init__()
        self.deviceList=deviceList
        self.preip = preip
        self.preport = preport
        self.postip = postip
        self.postport = postport
        #self.secpostport = 3000
        #self.preNeurdt = 257*[[- self.LTDwin - 1]] #Matrix holding abs. timings for pre-type spikes. Mat(x,y): x-> Pre-syn. neuron ID. y-> =1: last absolute time of firing for neuron x, =0: index of neuron.
        #self.postNeurdt = 4097*[[- self.LTPwin - 1]] #Matrix holding abs. timings for post-type spikes. Mat(x,y): x-> Post-syn. neuron ID. y-> =0: last absolute time of firing for neuron x.
        self.Neurdt = 4097 * [[- self.LTPwin - 1]] #Matrix holding absolute times of spikes of any type. Mat(x,y): x-> Neuron ID. y-> =0: last absolute time of firing for neuron x.

    def runUDP(self):
        global UDPampel
        #First, set the green light for the UDP protocol.
        UDPampel = 1

        #Operational parameters.
        maxtime = 110 #Maximum time allowed for UDP operation before returning control (s).
        Rmin = float(opEdits[5].text()) #Min. and max. RS levels corresponding to weights 0 and 1. Set once only.
        Rmax = float(opEdits[4].text())
        maxlisten = 20 #Maximum time to listen on socket for events.

        #Define socket object, set-up local server to receive data coming from other computers and bind socket to local server.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create a socket object - for Internet (INET) and UDP (DGRAM).
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) #Configure socket.
        ip = ""
        port = 5005
        sock.bind((ip, port)) #Bind socket.

        #Auxiliary variables.
        tabs = 0 #Absolute time tracker.

        #Prepare instrument for operation.
        #self.disableInterface.emit(True)
        self.changeArcStatus.emit('Busy')
        global tag, packnum, ConnMat

        ### ESTABLISH CONNECTIONS WITH SENDER AND RECEIVER ###

        if self.postip: #If we have defined a POST partner.

            #Create packer through use of 'struct' library.
            packer = struct.Struct('!I I') #'!' character tells the packer this data has to be sent to a network, so the byte order has to be correctly rendered.

            #Start by sending initialiser packet.
            # Prepare to send response via UDP.
            id_res = 82  # Identify this packet as RDY (d82, ASCII 'R')
            id = 0
            tst_res = 255
            tst = 0  # Send to post side absolute time when this neuron fires.
            # Preparation for packing.
            id_int = (((id_res & 0xff) << 24) | (id & (0x00fffff)))
            tst_int = (((tst_res & 0xff) << 24) | (tst & (0x00fffff)))

            pack = (id_int, tst_int)
            pack_data = packer.pack(*pack)

            #HEADER PACKET SEND.
            #sock.sendto(pack_data, (self.postip, int(self.postport)))
            #sock.sendto(pack_data, (self.preip, int(self.preport)))

            #LISTENING MODE.
            ready = select.select([sock], [], [], maxlisten) #Non-blocking socket. Send it: 1) list of sockets to read from, 2) list of sockets to write to...
            #...3) list of sockets to check for errors, 4) time allocated to these tasks. Returns 3 lists in this order: 1) Readable socket. 2) Writable. 3) In error.

            tstart = time.clock() #Set starting point for operation. Helps for time-limiting UDP operation.

            #Initialise helper variables.
            packnum = 0
            while (time.clock()-tstart) <= maxtime and ready[0] and UDPampel:
                data, addr = sock.recvfrom(1024)
                packnum += 1 #Count arriving packets (total regardless of direction).
                unpacked_data = packer.unpack(data)

                id_res_in = (unpacked_data[0]>>24)&0xff #Sender ID.
                id_in = unpacked_data[0]&0xffffff #PRE neuron ID.
                tst_res_in = (unpacked_data[1]>>24)&0xff #From Padova: shows type of event: 0 -> PSP, 1 -> stimulated AP, 2 -> spontaneous AP.
                tst_in = unpacked_data[1]&0xffffff #Timestamp in. General relative time (time between events regardless of origin).

                print("---------------------------------------------------------------")
                print("Received ", id_res_in, " ", id_in, " ", tst_res_in, " ", tst_in, " from ", addr)

                if(id_res_in == partcode[0]):
                    print("(P1)") #Partner 1
                elif(id_res_in == partcode[1]):
                    print("(P2)") #Partner 2

                #if id_res_in == partcode[0] and (np.sum(ConnMat[id_in,:,0] > 0)): #Recognise input as presynaptic.  # PRE # ...and check it actually connects to something.

                ######################### P1 #####################

                if id_res_in == partcode[0]: #Recognise input as coming from P1.

                    # Absolute time clock.
                    tabs += tst_in  # Update absolute time clock.
                    if tabs > 1000000000000:  # Reset time counter if it gets too large.
                        tabs -= 1000000000000

                    # Register arrival of spike and store new neur. specific abs. time firing time.
                    self.Neurdt[id_in] = self.Neurdt[id_in] + [tabs]

                    ###### PRE ######
                    if (np.sum(ConnMat[id_in, :, 0] > 0)):  # Parse input as presynaptic.  # PRE # ...and check it actually connects to something.

                        #Decide which post-neurons to look at based on post neuron id.
                        postNeurIdx = np.where(ConnMat[id_in, :, 0] == 1)[0]

                        postNeurLookup = [-1]
                        for i in postNeurIdx:
                            postNeurLookup = postNeurLookup + [self.Neurdt[i]] #Generate sub-vector holding only post-neurons to be 'looked up'.
                        postNeurLookup.remove(-1) #Clean up list of lists of its initial elements.

                        id_out = postNeurIdx

                        #Determine whether plasticity should be triggered based on activity of CURR neuron as PRE.

                        #Check for LTD.
                        id_plast = [-1]
                        for i in range(len(postNeurLookup)): #For every look-upabble PRE neuron...

                            ### LTD RULES ###

                            #Simple, last-spike STDP.
                            #if postNeurLookup[i][-1] > (tabs - self.LTDwin): #...check if LAST PRE spike is within the LTD window of current PRE arrival.

                            #Complex a posteriori-calculated STDP.
                            #if any([True for e in postNeurLookup[i][-self.searchLim:] if (0 < (tabs - e) <= self.LTDwin)]):

                            #SRDP.
                            if 0: #Presynaptic activity never triggers plasticity in SRDP.

                                id_plast = id_plast + [postNeurIdx[i]]
                        id_plast = id_plast[1:]

                        #Check for LTP.
                        id_plast2 = [-1]
                        for i in range(len(postNeurLookup)): #For every look-upabble PRE neuron...

                            ### LTP RULES ###

                            #Complex a posteriori-calculated STDP.
                            #if any([True for e in postNeurLookup[i][-self.searchLim:] if (0 > (tabs - e) >= -self.LTPwin)]):

                            # SRDP.
                            if 0:  # Presynaptic activity never triggers plasticity in SRDP.

                                id_plast2 = id_plast2 + [postNeurIdx[i]]
                        id_plast2 = id_plast2[1:]


                        for elem in range(len(id_out)): #For every synapse that the incoming pre-synaptic spike affects...

                            #Determine physical device that corresponds to affected synapse.
                            w_tar = ConnMat[id_in, id_out[elem], 1] #Capture w-line & b-line.
                            b_tar = ConnMat[id_in, id_out[elem], 2]

                            #Display updates.
                            f.cbAntenna.selectDeviceSignal.emit(int(w_tar), int(b_tar))       # signal the crossbar antenna that this device has been selected
                            f.displayUpdate.updateSignal_short.emit()

                            #Select and read active device.
                            g.ser.write_b("1\n")
                            g.ser.write_b(str(int(w_tar))+"\n")
                            g.ser.write_b(str(int(b_tar))+"\n")

                            result = f.getFloats(1)[0]

                            print('--')

                            #If plasticity should be triggered carry it out.
                            if id_out[elem] in id_plast and id_out[elem] not in id_plast2:
                                self.plastfun(0, w_tar, b_tar)
                                print('LTD')
                            elif id_out[elem] in id_plast2 and id_out[elem] not in id_plast:
                                self.plastfun(1, w_tar, b_tar)
                                print('LTP')

                            result = float(result)

                            print('PRE: ' + str(result)+', '+str(tabs)+', '+str(id_in)+', '+str(id_out[elem])) #  RS | Abs. time | PRE ID | POST ID
                            print('--')

                            #Prepare to send response via UDP.
                            id_res = partcode[2] #Identify sender of this packet as SOTON (d83, ASCII 'S')
                            id = int(id_out[elem])
                            tst_res = int(np.round(np.clip((255.0/(Rmax-Rmin))*(result-Rmin), 0, 255))) #Clip & round - pretty self-explanatory.
                            tst = tabs #Send to post side absolute time when this neuron fires.
                            #Preparation for packing.
                            id_int = (((id_res&0xff)<<24)|(id&(0x00fffff)))
                            tst_int =(((tst_res&0xff)<<24)|(tst&(0x00fffff)))

                            pack = (id_int, tst_int)
                            pack_data = packer.pack(*pack)

                            sock.sendto(pack_data, (self.postip, int(self.postport)))
                            #sock.sendto(pack_data, (self.postip, int(self.secpostport)))
                            #sock.sendto(pack_data, (self.preip, int(self.preport)))

                        #ready = select.select([sock], [], [], maxlisten)

                    #elif id_res_in == partcode[1] and (np.sum(ConnMat[:,id_in,0] > 0)): #Recognise input as post-synaptic. # POST # ...and check it actually conects to something.

                    ###### POST ######
                    if (np.sum(ConnMat[:, id_in, 0] > 0)):  # Parse input as post-synaptic. # POST # ...and check it actually conects to something.

                        #Decide which pre-neurons to look at based on post neuron id.
                        preNeurIdx = np.where(ConnMat[:, id_in, 0] == 1)[0]

                        preNeurLookup = [-1]
                        for i in preNeurIdx:
                            preNeurLookup = preNeurLookup + [self.Neurdt[i]] #Generate sub-vector holding only pre-neurons to be 'looked up'.
                        preNeurLookup.remove(-1) #Clean up list of lists of its initial elements.

                        id_out = preNeurIdx

                        #Determine whether plasticity should be triggered based on activity of CURR as POST.

                        #Check for LTP.
                        id_plast = [-1]
                        for i in range(len(preNeurLookup)): #For every look-uppable PRE neuron...

                            ### LTP RULES ###

                            #Simple, last-spike STDP.
                            #if preNeurLookup[i][-1] > (tst_in - self.LTPwin): #...check if LAST PRE spike is within the LTP window of current POST arrival.

                            #Complex, a posteriori-calculated STDP.
                            #if any([True for e in preNeurLookup[i][-self.searchLim:] if (0 < (tabs - e) <= self.LTPwin)]):

                            #SRDP
                            if len([True for e in preNeurLookup[i][-self.searchLim:] if 0 <= (tabs - e) <= self.searchWin]) > self.LTPfTh:

                                id_plast = id_plast + [preNeurIdx[i]]
                        id_plast = id_plast[1:]

                        #Check for LTD.
                        id_plast2 = [-1]
                        for i in range(len(preNeurLookup)): #For every look-upabble PRE neuron...

                            ### LTD RULES ###

                            #Complex, a posteriori-calculated STDP.
                            #if any([True for e in preNeurLookup[i][-self.searchLim:] if (0 > (tabs - e) >= -self.LTDwin)]):

                            #SRDP.
                            if len([True for e in preNeurLookup[i][-self.searchLim:] if 0 <= (tabs - e) <= self.searchWin]) < self.LTDfTh:

                                id_plast2 = id_plast2 + [preNeurIdx[i]] #Result of detecting conditions for plasticity met: put neuron in list of neurons 'to be plasticised'.
                        id_plast2 = id_plast2[1:]

                        for elem in range(len(id_out)):

                            #Determine physical device that corresponds to affected synapse.
                            w_tar = ConnMat[id_out[elem], id_in, 1] #Capture w-line & b-line.
                            b_tar = ConnMat[id_out[elem], id_in, 2]

                            #Display updates.
                            f.cbAntenna.selectDeviceSignal.emit(int(w_tar), int(b_tar))       # signal the crossbar antenna that this device has been selected
                            f.displayUpdate.updateSignal_short.emit()

                            #Select device to be 'plasticised'.
                            g.ser.write_b("02\n") #Select device operation.
                            g.ser.write_b(str(int(w_tar))+"\n") #Send wordline address.
                            g.ser.write_b(str(int(b_tar))+"\n") #Send bitline address.

                            print('--')

                            if id_out[elem] in id_plast and id_out[elem] not in  id_plast2:
                                self.plastfun(1, w_tar, b_tar) #Carry out plasticity.
                                print("LTP")
                            elif id_out[elem] in id_plast2 and id_out[elem] not in  id_plast:
                                self.plastfun(0, w_tar, b_tar) #Carry out plasticity.
                                print("LTD")

                            #Select and read active device.
                            time.sleep(0.005)
                            g.ser.write_b("1\n")
                            g.ser.write_b(str(int(w_tar))+"\n")
                            g.ser.write_b(str(int(b_tar))+"\n")
                            time.sleep(0.005)
                            result = f.getFloats(1)[0]

                            result = float(result)
                            print('POST: ' + str(result)+', '+str(tabs)+', '+str(id_out[elem])+', '+str(id_in)) #  RS | Abs. time | PRE ID | POST ID
                            print('--')

                ######################### P2 #####################

                if id_res_in == partcode[1]:  # Recognise input as coming from P2.
                    # Determine whether firing neuron is post-synaptic to anything.
                    preNeurIdx = np.where(ConnMat[:, id_in, 0] == 1)[0]

                    if len(preNeurIdx) != 0: #If it is post-synaptic to something...
                        lastspks = [] #Hold last spikes from each pre-synaptic neuyron in this list.

                        #...find out what it is post-synaptic to...
                        preNeurLookup = [-1]
                        for i in preNeurIdx:
                            preNeurLookup = preNeurLookup + [self.Neurdt[i]]  # Generate sub-vector holding only pre-neurons to be 'looked up'.
                            lastspks +=  [self.Neurdt[i][-1]] #Register last spikes from every pre-synaptic neuron.
                        preNeurLookup.remove(-1)  # Clean up list of lists of its initial elements.

                        tabs_in = np.max(lastspks) + tst_in #...and then relate it to the last spike it received from those neurons.

                    else: #If it is just a pre-cell...
                        #...relate the new firing time to the cell's own previous firing time.
                        tabs_in = self.Neurdt[id_in][-1] + tst_in  # Mark arrival on absoulte time axis WITHOUT updating absolute time clock.

                    #Reset time counter if it gets too large.
                    if tabs_in > 1000000000000:
                        tabs_in -= 1000000000000

                    # Register arrival of pre-spike and store new neur. specific abs. time firing time.
                    if tst_res_in == 1 or tst_res_in == 2:  # Check that this is an AP event (spontaneous or stimulated AP).
                        self.Neurdt[id_in] = self.Neurdt[id_in] + [tabs_in]

                    ###### PRE ######
                    if (np.sum(ConnMat[id_in, :,0] > 0)):  # Parse input as presynaptic.  # PRE # ...and check it actually connects to something.

                        # Decide which post-neurons to look at based on post neuron id.
                        postNeurIdx = np.where(ConnMat[id_in, :, 0] == 1)[0]

                        postNeurLookup = [-1]
                        for i in postNeurIdx:
                            postNeurLookup = postNeurLookup + [self.Neurdt[i]]  # Generate sub-vector holding only post-neurons to be 'looked up'.
                        postNeurLookup.remove(-1)  # Clean up list of lists of its initial elements.

                        id_out = postNeurIdx

                        # Determine whether plasticity should be triggered.

                        # Check for LTP.
                        id_plast = [-1]
                        for i in range(len(postNeurLookup)):  # For every look-upabble PRE neuron...

                            ### LTP RULES ###

                            # Complex a posteriori-calculated STDP.
                            # if any([True for e in postNeurLookup[i][-self.searchLim:] if (0 > (tabs_in - e) >= -self.LTPwin)]):

                            # SRDP.
                            if 0:  # Presynaptic activity never triggers plasticity in SRDP.

                                id_plast = id_plast + [postNeurIdx[i]]
                        id_plast = id_plast[1:]

                        # Check for LTD.
                        id_plast2 = [-1]
                        for i in range(len(postNeurLookup)):  # For every look-upabble PRE neuron...

                            ### LTD RULES ###

                            # Simple, last-spike STDP.
                            # if postNeurLookup[i][-1] > (tabs - self.LTDwin): #...check if LAST PRE spike is within the LTD window of current PRE arrival.

                            # Complex a posteriori-calculated STDP.
                            # if any([True for e in postNeurLookup[i][-self.searchLim:] if (0 < (tabs_in - e) <= self.LTDwin)]):

                            # SRDP.
                            if 0:  # Presynaptic activity never triggers plasticity in SRDP.

                                id_plast2 = id_plast2 + [postNeurIdx[i]]
                        id_plast2 = id_plast2[1:]


                        for elem in range(len(id_out)):  # For every synapse that the incoming pre-synaptic spike affects...

                            # Determine physical device that corresponds to affected synapse.
                            w_tar = ConnMat[id_in, id_out[elem], 1]  # Capture w-line & b-line.
                            b_tar = ConnMat[id_in, id_out[elem], 2]

                            # Display updates.
                            f.cbAntenna.selectDeviceSignal.emit(int(w_tar), int(b_tar))  # signal the crossbar antenna that this device has been selected
                            f.displayUpdate.updateSignal_short.emit()

                            # Select and read active device.
                            g.ser.write_b("1\n")
                            g.ser.write_b(str(int(w_tar)) + "\n")
                            g.ser.write_b(str(int(b_tar)) + "\n")

                            result = f.getFloats(1)[0]

                            print('--')

                            # If plasticity should be triggered carry it out.
                            if id_out[elem] in id_plast and id_out[elem] not in id_plast2:
                                self.plastfun(0, w_tar, b_tar)
                                print('LTD')
                            elif id_out[elem] in id_plast2 and id_out[elem] not in id_plast:
                                self.plastfun(1, w_tar, b_tar)
                                print('LTP')

                            result = float(result)

                            print('PRE: ' + str(result) + ', ' + str(tabs_in) + ', ' + str(id_in) + ', ' + str(id_out[elem]))  # RS | Abs. time | PRE ID | POST ID
                            print('--')

                            # Prepare to send response via UDP.
                            id_res = partcode[2]  # Identify sender of this packet as SOTON (d83, ASCII 'S')
                            id = int(id_out[elem])
                            tst_res = int(np.round(np.clip((255.0 / (Rmax - Rmin)) * (result - Rmin), 0, 255)))  # Clip & round - pretty self-explanatory.
                            tst = tabs  # Send to post side absolute time when this neuron fires.
                            # Preparation for packing.
                            id_int = (((id_res & 0xff) << 24) | (id & (0x00fffff)))
                            tst_int = (((tst_res & 0xff) << 24) | (tst & (0x00fffff)))

                            pack = (id_int, tst_int)
                            pack_data = packer.pack(*pack)

                            #sock.sendto(pack_data, (self.postip, int(self.postport)))
                            if tst_res_in == 1 or tst_res_in == 2: #Check that this is an AP event (spontaneous or stimulated AP).
                                sock.sendto(pack_data, (self.preip, int(self.preport)))

                            # ready = select.select([sock], [], [], maxlisten)

                    # elif id_res_in == partcode[1] and (np.sum(ConnMat[:,id_in,0] > 0)): #Recognise input as post-synaptic. # POST # ...and check it actually conects to something.

                    ###### POST ######
                    if (np.sum(ConnMat[:, id_in,0] > 0)):  # Parse input as post-synaptic. # POST # ...and check it actually conects to something.

                        # Decide which pre-neurons to look at based on post neuron id.
                        preNeurIdx = np.where(ConnMat[:, id_in, 0] == 1)[0]

                        preNeurLookup = [-1]
                        for i in preNeurIdx:
                            preNeurLookup = preNeurLookup + [self.Neurdt[i]]  # Generate sub-vector holding only pre-neurons to be 'looked up'.
                        preNeurLookup.remove(-1)  # Clean up list of lists of its initial elements.

                        id_out = preNeurIdx

                        # Determine whether plasticity should be triggered.

                        # Check for LTP.
                        id_plast = [-1]
                        for i in range(len(preNeurLookup)):  # For every look-upabble PRE neuron...

                            ### LTP RULES ###

                            # Simple, last-spike STDP.
                            # if preNeurLookup[i][-1] > (tst_in - self.LTPwin): #...check if LAST PRE spike is within the LTP window of current POST arrival.

                            #Complex, a posteriori-calculated STDP.
                            #if any([True for e in preNeurLookup[i][-self.searchLim:] if (0 < (tabs_in - e) <= self.LTPwin)]):

                            # SRDP
                            if tst_res_in == 0 or tst_res_in == 2: #Check that this is a plasticity triggering event (PSP or spontaneous AP).
                                if len([True for e in preNeurLookup[i][-self.searchLim:] if 0 <= (tabs_in - e) <= self.searchWin]) > self.LTPfTh:

                                    id_plast = id_plast + [preNeurIdx[i]]
                        id_plast = id_plast[1:]

                        # Check for LTD.
                        id_plast2 = [-1]
                        for i in range(len(preNeurLookup)):  # For every look-upabble PRE neuron...

                            ### LTD RULES ###

                            # Simple, last-spike STDP.
                            # if preNeurLookup[i][-1] > (tst_in - self.LTPwin): #...check if LAST PRE spike is within the LTP window of current POST arrival.

                            # Complex, a posteriori-calculated STDP.
                            #if any([True for e in preNeurLookup[i][-self.searchLim:] if (0 > (tabs_in - e) >= -self.LTDwin)]):

                            # SRDP.
                            if tst_res_in == 0 or tst_res_in == 2: #Check that this is a plasticity triggering event (PSP or spontaneous AP).
                                if len([True for e in preNeurLookup[i][-self.searchLim:] if 0 <= (tabs_in - e) <= self.searchWin]) < self.LTDfTh:

                                    id_plast2 = id_plast2 + [preNeurIdx[i]]
                        id_plast2 = id_plast2[1:]


                        for elem in range(len(id_out)):

                            # Determine physical device that corresponds to affected synapse.
                            w_tar = ConnMat[id_out[elem], id_in, 1]  # Capture w-line & b-line.
                            b_tar = ConnMat[id_out[elem], id_in, 2]

                            # Display updates.
                            f.cbAntenna.selectDeviceSignal.emit(int(w_tar), int(b_tar))  # signal the crossbar antenna that this device has been selected
                            f.displayUpdate.updateSignal_short.emit()

                            # Select device to be 'plasticised'.
                            g.ser.write_b("02\n")  # Select device operation.
                            g.ser.write_b(str(int(w_tar)) + "\n")  # Send wordline address.
                            g.ser.write_b(str(int(b_tar)) + "\n")  # Send bitline address.

                            print('--')

                            if id_out[elem] in id_plast and id_out[elem] not in id_plast2:
                                self.plastfun(1, w_tar, b_tar)  # Carry out plasticity.
                                print("LTP")
                            elif id_out[elem] in id_plast2 and id_out[elem] not in id_plast:
                                self.plastfun(0, w_tar, b_tar)  # Carry out plasticity.
                                print("LTD")

                            # Select and read active device.
                            time.sleep(0.005)
                            g.ser.write_b("1\n")
                            g.ser.write_b(str(int(w_tar)) + "\n")
                            g.ser.write_b(str(int(b_tar)) + "\n")
                            time.sleep(0.005)
                            result = f.getFloats(1)[0]

                            result = float(result)
                            print('POST: ' + str(result) + ', ' + str(tabs_in) + ', ' + str(id_out[elem]) + ', ' + str(id_in))  # RS | Abs. time | PRE ID | POST ID
                            print('--')


                #Read next packet.
                ready = select.select([sock], [], [], maxlisten)

                #else:
                    #ready = select.select([sock], [], [], maxlisten)
                    #print("Unrecognised partner or neuron ID out of range.")

        #self.disableInterface.emit(False)
        self.changeArcStatus.emit('Ready')
        #self.displayData.emit()
        
        self.finished.emit()
        print('No. of packets throughout session: ' + str(packnum)) #Display number of packets received throughout session.
        print('Total runtime: ' + str(time.clock() - tstart)) #Display time elapsed during UDP run.
        print('Average packet rate: ' + str(packnum/(time.clock() - tstart))) #Display packets/second.
        print('Bias parameters: '+ str(float(opEdits[0].text())) + '    ' + str(float(opEdits[1].text())) + '    ' + str(float(opEdits[2].text())) + '    ' + str(float(opEdits[3].text())))
        print('RS-weight mapping (min,max): ' + str(float(opEdits[5].text())) + '    ' + str(float(opEdits[4].text())))

        return 0

    def plastfun(self, plastdir, w, b): #Plasticity function depends on pre-dt, post-dt and the direction of the plasticity (plastdir = 1 (LTP), = 0, (LTD)).
        #Plasticity parameters.

        if plastdir:
            g.ser.write_b("04\n") #Select device operation.
            g.ser.write_b(str(float(opEdits[0].text()))+"\n") #Send amplitude (V).
            time.sleep(0.005)
            g.ser.write_b(str(float(opEdits[1].text()))+"\n") #Send duration (s).
            #time.sleep(0.005)
            #g.ser.write_b(str(float("0.0"))+"\n") #ICC setting. Set to 0 for we are not using compliance current.
            #result=g.ser.readline().rstrip()     # currentline contains the new Mnow value followed by 2 \n characters
            #print(result)
        else:
            g.ser.write_b("04\n") #Select device operation.
            g.ser.write_b(str(float(opEdits[2].text()))+"\n") #Send amplitude (V).
            time.sleep(0.005)
            g.ser.write_b(str(float(opEdits[3].text()))+"\n") #Send duration (s).
            #time.sleep(0.005)
            #g.ser.write_b("0.0\n") #ICC setting. Set to 0 for we are not using compliance current.
            #result=g.ser.readline().rstrip()     # currentline contains the new Mnow value followed by 2 \n characters
            #print(result)

    def plastdec(self, tabs, NeurLookup, NeurIdx, plastWin, plastfTh): ### UNDER CONSTRUCTION ###
        # Check for LTP.
        id_plast = [-1]
        for i in range(len(NeurLookup)):  # For every look-upabble PRE neuron...

            ### LTP RULES ###

            # Simple, last-spike STDP.
            # if NeurLookup[i][-1] > (tabs - self.plastWin): #...check if LAST PRE spike is within the LTD window of current PRE arrival.

            # Complex a posteriori-calculated STDP.
            if any([True for e in NeurLookup[i][-self.searchLim:] if (0 < (tabs - e) <= plastWin)]):

            #SRDP
            #if len([True for e in NeurLookup[i][-self.searchLim:] if 0 <= (tabs - e) <= self.searchWin]) > plastfTh:

                id_plast = id_plast + [NeurIdx[i]]
        id_plast = id_plast[1:]

        # Check for LTD.
        id_plast2 = [-1]
        for i in range(len(NeurLookup)):  # For every look-upabble PRE neuron...

            ### LTD RULES ###

            #Simple, last-spike STDP.
            # if NeurLookup[i][-1] > (tabs - plastWin): #...check if LAST PRE spike is within the LTP window of current POST arrival.

            # Complex a posteriori-calculated STDP.
            if any([True for e in NeurLookup[i][-self.searchLim:] if (0 > (tabs - e) >= -plastWin)]):

            #SRDP.
            #if len([True for e in NeurLookup[i][-self.searchLim:] if 0 <= (tabs - e) <= self.searchWin]) < self.plastfTh:

                id_plast2 = id_plast2 + [NeurIdx[i]]
        id_plast2 = id_plast2[1:]

        return id_plast, id_plast2

class UDPstopper(QtCore.QObject):
    #Define signals to be used throughout module.
    finished=QtCore.pyqtSignal()

    def runSTOP(self):
        global UDPampel
        UDPampel = 0 #Set the UDP traffic light to 0.
        self.finished.emit()

class UDPmod(QtWidgets.QWidget): #Define new module class inheriting from QtWidgets.QWidget.
    
    def __init__(self):
        super(UDPmod, self).__init__()
        
        self.initUI()
        
    def initUI(self):      

        global opEdits

        ### Define GUI elements ###
        #Define module as a QVBox.
        vbox1=QtWidgets.QVBoxLayout()

        #Configure module title and description and text formats.
        titleLabel = QtWidgets.QLabel('UDPmod')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('UDP connectivity for neuromorphic applications.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        topLabels=['Presynaptic partner IP', 'Presynaptic partner port']
        self.topEdits=[]

        btmLabels=['Postsynaptic partner IP', 'Postsynaptic partner port']
        self.btmEdits=[]

        opLabels=['LTP voltage (V)', 'LTP duration (s)','LTD voltage (V)', 'LTD duration (s)', 'Rmax (Ohms)', 'Rmin Ohms']
        opEdits=[]

        leftInit=  ['192.168.10.1', '10000']
        rightInit= ['192.162.10.2', '25003']
        #leftInit = ['152.78.67.67', '5005']
        #rightInit = ['10.9.167.3', '5005']
        opInit=['4.0', '0.0001', '-4.0', '0.0001', '9000.0', '4000.0']

        # Setup the column 'length' ratios.
        gridLayout=QtWidgets.QGridLayout()
        gridLayout.setColumnStretch(0,1)
        gridLayout.setColumnStretch(1,1)
        #gridLayout.setSpacing(2)

        #Setup the line separators
        lineLeft=QtWidgets.QFrame()
        lineLeft.setFrameShape(QtWidgets.QFrame.HLine)
        lineLeft.setFrameShadow(QtWidgets.QFrame.Raised)
        lineLeft.setLineWidth(1)
        lineRight=QtWidgets.QFrame()
        lineRight.setFrameShape(QtWidgets.QFrame.HLine)
        lineRight.setFrameShadow(QtWidgets.QFrame.Raised)
        lineRight.setLineWidth(1)
        lineOps=QtWidgets.QFrame()
        lineOps.setFrameShape(QtWidgets.QFrame.HLine)
        lineOps.setFrameShadow(QtWidgets.QFrame.Raised)
        lineOps.setLineWidth(1)


        ### Build GUI insides ###
        gridLayout.addWidget(lineLeft, 2, 0, 1, 2)
        gridLayout.addWidget(lineRight, 5, 0, 1, 2)
        gridLayout.addWidget(lineOps, 7, 0, 1, 2)


        for i in range(len(topLabels)):
            lineLabel=QtWidgets.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(topLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setText(leftInit[i])
            #lineEdit.setValidator(isFloat)
            self.topEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,1)

        offset = len(topLabels)+1 #offset parameter is simply the first row of the bottom panel/label section.

        for i in range(len(btmLabels)):
            lineLabel=QtWidgets.QLabel()
            lineLabel.setText(btmLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, offset+i,0)

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setText(rightInit[i])
            #lineEdit.setValidator(isFloat)
            self.btmEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, offset+i,1)


        for i in range(len(opLabels)):
            opLabel=QtWidgets.QLabel()
            opLabel.setText(opLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(opLabel, 8+i,0)

            opEdit=QtWidgets.QLineEdit()
            opEdit.setText(opInit[i])
            opEdit.setValidator(isFloat)
            opEdits.append(opEdit)
            gridLayout.addWidget(opEdit, 8+i,1)

        # ============================================== #

        #Label explaining connectivity matrix boot from file.
        CMLabel=QtWidgets.QLabel()
        #lineLabel.setFixedHeight(50)
        CMLabel.setText("Connectivity matrix file: ")

        #Text field to show selected file containing SA locations for particular application.
        self.UDPmapFName=QtWidgets.QLabel()
        self.UDPmapFName.setStyleSheet(s.style1)

        #File browser. Push-button connecting to function opening file browser.
        push_browse = QtWidgets.QPushButton('...')
        push_browse.clicked.connect(self.findUDPMAPfile)    # open custom array defive position file
        push_browse.setFixedWidth(20)

        gridLayout.addWidget(CMLabel, 6,0)
        gridLayout.addWidget(self.UDPmapFName, 6, 1)
        gridLayout.addWidget(push_browse, 6, 2)

        ### Set-up overall module GUI ###
        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        self.vW=QtWidgets.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        self.scrlArea=QtWidgets.QScrollArea()
        self.scrlArea.setWidget(self.vW)
        self.scrlArea.setContentsMargins(0,0,0,0)
        self.scrlArea.setWidgetResizable(False)
        self.scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.scrlArea.installEventFilter(self) #Allow object to 'listen' for events.

        vbox1.addWidget(self.scrlArea)
        vbox1.addStretch()

        #Create graphics area that holds buttons to activate module.
        self.hboxProg=QtWidgets.QHBoxLayout()

        push_launchUDP=QtWidgets.QPushButton('Launch UDP interface') #Button to launch UDP interface.
        push_range=QtWidgets.QPushButton('Apply to Range')
        stop_udp=QtWidgets.QPushButton('STOP UDP')

        push_launchUDP.setStyleSheet(s.btnStyle)
        push_range.setStyleSheet(s.btnStyle)
        stop_udp.setStyleSheet(s.btnStyle)

        push_launchUDP.clicked.connect(self.UDPstart)
        push_range.clicked.connect(self.programRange)
        stop_udp.clicked.connect(self.UDPstop)

        self.hboxProg.addWidget(push_launchUDP)
        self.hboxProg.addWidget(push_range)
        self.hboxProg.addWidget(stop_udp)

        vbox1.addLayout(self.hboxProg)

        self.setLayout(vbox1)
        self.vW.setFixedWidth(self.size().width())
        #print('-------')
        #print(self.vW.size().width())
        #print(self.scrlArea.size().width())
        #print('-------')
        #self.vW.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.scrlArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        #self.vW.setFixedWidth(self.sizeHint().width())

    def updateStopOptions(self, event):
        print(event)

    def eventFilter(self, object, event):
        #print(object)
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width()) #Always set vW width to window width - scrollbar width.
        #if event.type()==QtCore.QEvent.Paint:
        #    self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        #print(self.vW.size().width())
        return False

    def resizeWidget(self,event): #Dummy function - unnecessary vestige.
        pass

    def sendParams(self): #UPDATE WITH RELEVANT STUFF ONCE CONNECTION TO MBED READY TO BE MADE.
        g.ser.write_b(str(float(self.topEdits[0].text()))+"\n") #Recipient partner IP.
        g.ser.write_b(str(float(self.topEdits[1].text()))+"\n") #Recipient partner port.
        g.ser.write_b(str(float(self.btmEdits[0].text()))+"\n") #Sending partner IP.
        g.ser.write_b(str(float(self.btmEdits[1].text()))+"\n") #Sending partner port.

    def UDPstart(self):

        # Capture pertinent parameters.
        preip = self.topEdits[0].text()
        preport = self.topEdits[1].text()
        postip = self.btmEdits[0].text()
        postport = self.btmEdits[1].text()

        #job="40"
        #g.ser.write_b(job+"\n")   # sends the job
        
        #self.sendParams()

        self.thread=QtCore.QThread()    #Instantiate thread object.
        self.getData=getData([[g.w,g.b]], preip, preport, postip, postport)    #Instantiate a getData object.
        self.getData.moveToThread(self.thread)      #Cause getData object to be ran in the thread object.
        self.thread.started.connect(self.getData.runUDP)     #Start thread and assign it ('connect to') task of running runUDP.
        self.getData.finished.connect(self.thread.quit)     #Once task finishes connect it to ending the thread.
        self.getData.finished.connect(self.getData.deleteLater)     #Clear some memory, again, in response to 'finished' signal (getData).
        self.thread.finished.connect(self.getData.deleteLater)      #Clear some memory, again, in response to 'finished' signal (thread).
        self.getData.sendData.connect(f.updateHistory)      #Typical example of 'signal and slot'. Function from within thread calls function outside it.
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.disable.emit)
        self.getData.changeArcStatus.connect(f.interfaceAntenna.changeArcStatus.emit)

        self.thread.start()

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    def programRange(self):

        stopTime=int(self.btmEdits[0].text())
        B=int(self.topEdits[2].text())
        stopBatchSize=int(self.btmEdits[1].text())

        A=float(self.topEdits[0].text())
        pw=float(self.topEdits[1].text())/1000000

        rangeDev=self.makeDeviceList(True)

        job="33"
        g.ser.write_b(job+"\n")   # sends the job

        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData([[g.w,g.b]], preip, preport, postip, postport)
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.runUDP)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.disable.emit)

        self.thread.start()

    def UDPstop(self):
        self.thread2=QtCore.QThread()
        self.UDPstopper=UDPstopper()
        self.UDPstopper.moveToThread(self.thread2)
        self.thread2.started.connect(self.UDPstopper.runSTOP)
        self.UDPstopper.finished.connect(self.thread2.quit)
        self.UDPstopper.finished.connect(self.UDPstopper.deleteLater)
        self.thread2.finished.connect(self.UDPstopper.deleteLater)

        self.thread2.start()

    def makeDeviceList(self,isRange):
        #if g.checkSA=False:
        rangeDev=[] # initialise list which will contain the SA devices contained in the user selected range of devices
        #rangeMax=0
        if isRange==False:
            minW=1
            maxW=g.wline_nr
            minB=1
            maxB=g.bline_nr
        else:
            minW=g.minW
            maxW=g.maxW
            minB=g.minB
            maxB=g.maxB            

        # Find how many SA devices are contained in the range
        if g.checkSA==False:
            for w in range(minW,maxW+1):
                for b in range(minB,maxB+1):
                    rangeDev.append([w,b])
            #rangeMax=(wMax-wMin+1)*(bMax-bMin+1)
        else:
            for w in range(minW,maxW+1):
                for b in range(minB,maxB+1):
                    for cell in g.customArray:
                        if (cell[0]==w and cell[1]==b):
                            rangeDev.append(cell)

        return rangeDev

    # FUNCTION FOR OPENING FILE BROWSER - UNDER CONSTRUCTION.
    def findUDPMAPfile(self):

        global ConnMat

        path = QtCore.QFileInfo(QtWidgets.QFileDialog().getOpenFileName(self, 'Open file', "*.txt")[0])
        #path=fname.getOpenFileName()

        customArray = []
        name=path.fileName()

        file=QtCore.QFile(path.filePath())
        file.open(QtCore.QIODevice.ReadOnly)

        textStream=QtCore.QTextStream(file)
        error=0
        while not textStream.atEnd():
            line = textStream.readLine()
            try:
                if (line): #Empty line check.
                    if (line[0] != '#'): #1st chacters is # -> comment; ignore.
                        preid, postid, w, b = line.split(", ")
                        customArray.append([int(preid), int(postid), int(w),int(b)])
                        if (int(w)<1 or int(w)>g.wline_nr or int(b)<1 or int(b)>g.bline_nr or preid<0 or postid<0):
                            error=1
            except ValueError:
                error=1
        file.close()

        # check if positions read are correct
        if (error==1):
            #self.errorMessage=QtWidgets.QErrorMessage()
            #self.errorMessage.showMessage("Custom array file is formatted incorrectly!")
            errMessage = QtWidgets.QMessageBox()
            errMessage.setText("Device to synapse mapping file formatted incorrectly, or selected devices outside of array range!")
            errMessage.setIcon(QtWidgets.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()
            return False
        else:
            self.UDPmapFName.setText(name)

            #Create connectivity matrix from list.
            customArray = np.array(customArray)
            ConnMat = np.zeros((np.max(customArray[:,0])+1, np.max(customArray[:,1])+1, 4)) #See globals file for  documentation.

            for element in range(len(customArray[:,0])):
                ConnMat[customArray[element, 0], customArray[element, 1], :] = [1, customArray[element, 2], customArray[element, 3], 0]

            #print(ConnMat)
            return True

