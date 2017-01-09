import numpy as np
from memristor import memristor
import time

#from PIL import Image
#import PIL

import Queue

readNoise=0.01
write_scheme={'V/2':0.5}
Vread=0.5

class virtualArC(object):
	
	def __init__(self, option):
		super(virtualArC, self).__init__()

		self.port="not none"
		print "initialised"
		self.crossbar=[[] for x in range(33)]
		self.counter=0
		self.w=0
		self.b=0
		self.q_in=Queue.Queue()
		self.q_out=Queue.Queue()
		self.dt=1e-6
		self.Vread=0.5
		self.initialise()

	def initialise(self):
		for w in range(32+1):
			self.crossbar[w].append(0)
			for b in range(32):
				mx=memristor()
				mx.initialise(mx.Ron+5e5+(1-2*np.random.rand())*5e5)
				self.crossbar[w].append(mx)

		# basewidth = 32
		# img = Image.open('5.png')
		# wpercent = (basewidth / float(img.size[0]))
		# hsize = int((float(img.size[1]) * float(wpercent)))
		# img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
		# img.save('resized_image.png')

		# mat=(np.asarray(Image.open('resized_image.png').convert('L')))/255.0

		# blurFactor=1

		# Roff=1e7
		# Ron=1e4

		# mat2=(mat-(mat-0.5)/blurFactor)*(Roff-Ron)+Ron

		# for w in range(32+1):
		# 	self.crossbar[w].append(0)
		# 	for b in range(32):
		# 		mx=memristor()
		# 		mx.initialise(mat2[w-1,b-1]+(1-2*np.random.rand())*Ron)
		# 		self.crossbar[w].append(mx)



		pass
		#print self.crossbar

	def base_readline(self):
		print "100\n"
		return "100\n"
		pass

	def readline(self):
		#time.sleep(0.001)
		value=self.q_out.get()
		#print value
		return str(value)+"\n"
		pass


	def base_write(self,value):
		job=value.rstrip()
		if job=="1":
			self.write=self.get_readSingle

		if job=="2":
			self.write=self.get_readAll

		if job=="3":
			self.write=self.get_pulse
		if job=="19":
			self.write=self.get_endurance
		if job=="152":
			self.write=self.get_switchseeker_slow
		if job=="15":
			self.write=self.get_switchseeker_fast

		if job=="201":
			self.write=self.get_curvetracer

		if job=="14":
			self.write=self.get_formfinder

		if job=="14":
			self.write=self.get_formfinder

		if job=="33":
			pass

		print "Task received:", job


	def write(self,value):
		job=value.rstrip()
		if job=="1":
			self.write=self.get_readSingle

		if job=="2":
			self.write=self.get_readAll

		if job=="3":
			self.write=self.get_pulse

		if job=="19":
			self.write=self.get_endurance

		if job=="152":
			self.write=self.get_switchseeker_slow

		if job=="15":
			self.write=self.get_switchseeker_fast

		if job=="201":
			self.write=self.get_curvetracer

		if job=="14":
			self.write=self.get_formfinder

		if job=="33":
			pass

		print "Task received:",job

	################################################## CURVETRACER ####
	def get_formfinder(self, value):
		self.counter+=1
		print "counter at: ", self.counter
		self.q_in.put(value.rstrip())
		if self.counter==12:
			#self.execute_endurance()
			self.FF_Vmin=float(self.q_in.get())
			self.FF_Vstep=float(self.q_in.get())
			self.FF_Vmax=float(self.q_in.get())
			self.FF_pwmin=float(self.q_in.get())
			self.FF_pwstep=float(self.q_in.get())
			self.FF_pwmax=float(self.q_in.get())
			self.FF_interpulse=float(self.q_in.get())
			self.FF_nrP=int(float(self.q_in.get()))

			self.FF_Rthr=float(float(self.q_in.get()))
			self.FF_Rthr_p=int(float(self.q_in.get()))

			self.pSR=int(float(self.q_in.get()))

			self.nr_of_devices=int(float(self.q_in.get()))

			self.counter=0
			self.write=self.get_formfinder_device

	def get_formfinder_device(self, value):
		self.counter+=1
		self.q_in.put(value.rstrip())
		if self.counter==2:
			self.w=int(float(self.q_in.get()))
			self.b=int(float(self.q_in.get()))
			print "Executing for device: ", self.w, self.b
			self.counter=0
			self.execute_formfinder()

	def execute_formfinder(self):
		self.nr_of_devices-=1
		Vmin=self.FF_Vmin
		Vstep=self.FF_Vstep
		Vmax=self.FF_Vmax
		pwmin=self.FF_pwmin
		pwstep=self.FF_pwstep
		pwmax=self.FF_pwmax
		interpulse=self.FF_interpulse
		nrP=self.FF_nrP
		Rthr=self.FF_Rthr
		Rthr_p=self.FF_Rthr_p

		exitFlag=0

		Vp=Vmin
		pw=pwmin

		self.tripleSend(read(self.crossbar,self.w,self.b), 0.5, 0.0)
		Mstart=read(self.crossbar,self.w,self.b)

		print Rthr_p, Mstart, Rthr

		if Rthr_p==0 and Mstart<Rthr:
			exitFlag=1
			self.tripleSend(0.0, 0.0, 0.0)

		while not exitFlag:
			for i in range(1,nrP+1):
				if exitFlag==0:
					pulse(self.crossbar, self.w, self.b, Vp, pw, self.dt)
					Mnow=read(self.crossbar,self.w,self.b)
					self.tripleSend(read(self.crossbar,self.w,self.b), Vp, pw)
					if (Rthr_p==0):
						if (Mnow<Rthr):
							exitFlag=1
							self.tripleSend(0.0, 0.0, 0.0)
					else:
						if (abs(Mnow-Mstart)/Mstart>Rthr_p/100.0):
							exitFlag=1
							self.tripleSend(0.0, 0.0, 0.0)

			if exitFlag==0:
				if (pw*(1+pwstep/100.0)>pwmax):
					if (abs(Vp+Vstep)>abs(Vmax)):
						exitFlag=1
						self.tripleSend(0.0, 0.0, 0.0)
					else:
						Vp=Vp+Vstep
						pw=pwmin
				else:
					pw=pw*(1+pwstep/100.0)

		if self.nr_of_devices==0:
			self.write=self.base_write
		else:
			self.write=self.get_formfinder_device






	################################################## CURVETRACER ####
	def get_curvetracer(self, value):
		self.counter+=1
		print "counter at: ", self.counter
		self.q_in.put(value.rstrip())
		if self.counter==13:
			#self.execute_endurance()
			self.Vpos=float(self.q_in.get())
			self.Vneg=float(self.q_in.get())
			self.Vstart=float(self.q_in.get())
			self.Vstep=float(self.q_in.get())
			self.pwstep=float(self.q_in.get())
			self.interpulse=float(self.q_in.get())
			self.CSp=float(self.q_in.get())
			self.CSn=float(self.q_in.get())

			self.cycles=int(float(self.q_in.get()))
			self.type=int(float(self.q_in.get()))

			self.option=int(float(self.q_in.get()))
			self.return_option=int(float(self.q_in.get()))

			self.nr_of_devices=int(float(self.q_in.get()))

			self.counter=0
			self.write=self.get_curvetracer_device
			print "pwstep is: ", self.pwstep
	
	def get_curvetracer_device(self, value):
		self.counter+=1
		self.q_in.put(value.rstrip())
		if self.counter==2:
			self.w=int(float(self.q_in.get()))
			self.b=int(float(self.q_in.get()))
			print "Executing for device: ", self.w, self.b
			self.counter=0
			self.execute_curvetracer()

	def execute_curvetracer(self):
		self.nr_of_devices-=1
		Vpos_max=self.Vpos
		Vneg_max=self.Vneg
		Vstep=self.Vstep
		Vstart=self.Vstart
		option=self.option
		cycles=self.cycles


		i=0
		run=1
		holder_Vread=0

		firstCS=0
		secondCS=0
		optionCS=0

		firstV=0
		secondV=0
		polarity=1

		if self.option==0:
			firstV=int(abs(Vpos_max-Vstart)/Vstep)
			secondV=int(abs(abs(Vneg_max)-Vstart)/Vstep)			
		if self.option==1:
			firstV=int(abs(abs(Vneg_max)-Vstart)/Vstep)
			secondV=int(abs(Vpos_max-Vstart)/Vstep)
		if self.option==2:
			firstV=int(abs(Vpos_max-Vstart)/Vstep)
			secondV=0	
		if self.option==3:
			firstV=int(abs(abs(Vneg_max)-Vstart)/Vstep)
			secondV=0

		print "option is ", option
		print firstV, secondV
		#First Ru
		for run in range(1,cycles+1):
			if option==0:
				polarity=1
			if option==1:
				polarity=-1
			if option==2:
				polarity=1
			if option==3:
				polarity=-1

			for i in range(firstV+1):
				Vread=(i*Vstep+Vstart)*polarity
				pulse(self.crossbar, self.w, self.b, Vread, self.pwstep, self.dt)
				self.tripleSend(read(self.crossbar,self.w,self.b), Vread, 0.0) 

			for i in range(firstV,0,-1):
				Vread=((i-1)*Vstep+Vstart)*polarity
				pulse(self.crossbar, self.w, self.b, Vread, self.pwstep, self.dt)
				self.tripleSend(read(self.crossbar,self.w,self.b), Vread, 0.0) 

			if option==0:
				polarity=-1
			if option==1:
				polarity=1
			if option==2:
				polarity=-1
			if option==3:
				polarity=1

			if (option!=2 and option!=3):
				for i in range(secondV+1):
					Vread=(i*Vstep+Vstart)*polarity;
					pulse(self.crossbar, self.w, self.b, Vread, self.pwstep, self.dt)
					self.tripleSend(read(self.crossbar,self.w,self.b), Vread, 0.0) 

				for i in range(secondV,0,-1):
					Vread=((i-1)*Vstep+Vstart)*polarity
					pulse(self.crossbar, self.w, self.b, Vread, self.pwstep, self.dt)
					self.tripleSend(read(self.crossbar,self.w,self.b), Vread, 0.0) 

			self.tripleSend(0.0, 0.0, 0.0) 

		if self.nr_of_devices==0:
			self.write=self.base_write
		else:
			self.write=self.get_curvetracer_device

	################################################## SWITCHSEEKER FAST ###
	def get_switchseeker_fast(self, value):
		self.counter+=1
		print "counter at: ", self.counter
		self.q_in.put(value.rstrip())
		if self.counter==13:
			self.pw=float(self.q_in.get())
			self.Vmin=float(self.q_in.get())
			self.Vstep=float(self.q_in.get())
			self.Vmax=float(self.q_in.get())
			self.interpulse=float(self.q_in.get())
			self.thr=float(self.q_in.get())
			self.reads_in_trailercard=int(float(self.q_in.get()))
			self.pPulses=int(float(self.q_in.get()))
			self.cycles=int(float(self.q_in.get()))
			self.tol=float(self.q_in.get())

			self.checkRead=int(float(self.q_in.get()))
			self.skipStage1=int(float(self.q_in.get()))

			self.nr_of_devices=int(float(self.q_in.get()))

			self.counter=0
			self.write=self.get_switchseeker_fast_device

	def get_switchseeker_fast_device(self, value):
		self.counter+=1
		self.q_in.put(value.rstrip())
		if self.counter==2:
			self.w=int(float(self.q_in.get()))
			self.b=int(float(self.q_in.get()))
			print "Executing for device: ", self.w, self.b
			self.counter=0
			self.execute_switchseeker_fast()

	def execute_switchseeker_fast(self):
		self.nr_of_devices-=1
		baseline=0
		
		currR=0
		exitFlag=False
		terminate=False
		Vbias=self.Vmin
		RES=[[0,0,0,0] for x in range(100)]

		#maxSteps=int((self.Vmax-self.Vmin)/self.Vstep)
		#maxSteps_i=0
		polarity=1
		inverse=0
		i=0
		n=0


		for dev in range(self.reads_in_trailercard):
			self.tripleSend(read(self.crossbar,self.w,self.b),self.Vread,0.0)
			baseline+=read(self.crossbar,self.w,self.b)
		baseline/=self.reads_in_trailercard

		if self.skipStage1!=0:
			exitFlag=True
			RES[0][0]=Vbias*(-1*self.skipStage1)
			RES[0][1]=self.pw
			RES[0][3]=currR

		while not exitFlag:
			currR=self.SS_BasicUnit(self.reads_in_trailercard, self.pPulses, \
								Vbias, self.pw, self.checkRead, self.interpulse)

			RES[0][0]=Vbias
			RES[0][1]=self.pw
			RES[0][3]=currR

			if ((currR/baseline<=(1+self.tol/100.0)) and (currR > baseline) or \
				((currR/baseline >= (1/(1+self.tol/100))) and (currR<baseline))):

				if Vbias>0:
					Vbias*=-1
				else:
					Vbias*=-1
					Vbias+=self.Vstep

				if abs(Vbias)>self.Vmax:
					RES[0][2]=0
					exitFlag=True
					terminate=True

			else:
				if (currR/baseline >= (1+self.tol/100)):
					RES[n][2]=1
				else:
					RES[n][2]=-1
				exitFlag=True

		if not terminate:
			self.SS_round2(self.reads_in_trailercard, self.pPulses, self.checkRead, \
							self.pw, self.interpulse, self.tol, self.cycles, self.Vmin, \
							self.Vstep, self.Vmax, RES)

		if self.nr_of_devices==0:
			self.write=self.base_write
		else:
			self.write=self.get_switchseeker_fast_device
		self.tripleSend(0.0,0.0,0.0)


	################################################## SWITCHSEEKER SLOW ###
	def get_switchseeker_slow(self, value):
		self.counter+=1
		print "counter at: ", self.counter
		self.q_in.put(value.rstrip())
		if self.counter==13:
			#self.execute_endurance()
			self.pw=float(self.q_in.get())
			self.Vmin=float(self.q_in.get())
			self.Vstep=float(self.q_in.get())
			self.Vmax=float(self.q_in.get())
			self.interpulse=float(self.q_in.get())
			self.thr=float(self.q_in.get())
			self.reads_in_trailercard=int(float(self.q_in.get()))
			self.pPulses=int(float(self.q_in.get()))
			self.cycles=int(float(self.q_in.get()))
			self.tol=float(self.q_in.get())

			self.checkRead=int(float(self.q_in.get()))
			self.skipStage1=int(float(self.q_in.get()))

			self.nr_of_devices=int(float(self.q_in.get()))

			self.counter=0
			self.write=self.get_switchseeker_slow_device

	def get_switchseeker_slow_device(self, value):
		self.counter+=1
		self.q_in.put(value.rstrip())
		if self.counter==2:
			self.w=int(float(self.q_in.get()))
			self.b=int(float(self.q_in.get()))
			print "Executing for device: ", self.w, self.b
			self.counter=0
			self.execute_switchseeker_slow()

	def execute_switchseeker_slow(self):
		self.nr_of_devices-=1
		baseline=0
		
		currR=0
		exitFlag=False
		exitFlag2=False
		terminate=False
		Vbias=self.Vmin
		RES=[[0,0,0,0] for x in range(100)]

		maxSteps=int((self.Vmax-self.Vmin)/self.Vstep)
		maxSteps_i=0
		polarity=1
		inverse=0
		n=0


		for dev in range(self.reads_in_trailercard):
			self.tripleSend(read(self.crossbar,self.w,self.b),self.Vread,0.0)
			baseline+=read(self.crossbar,self.w,self.b)
		baseline/=self.reads_in_trailercard

		if self.skipStage1!=0:
			exitFlag2=1
			RES[0][0]=Vbias
			RES[0][1]=self.pw
			RES[0][3]=currR

		while not exitFlag2:
			i=0
			Vbias=self.Vmin*polarity
			exitFlag=False

			while not exitFlag:
				currR=self.SS_BasicUnit(self.reads_in_trailercard, self.pPulses, \
									Vbias, self.pw, self.checkRead, self.interpulse)
				print "Read resistance is:",currR,self.tol/100.0

				RES[0][0]=Vbias
				RES[0][1]=self.pw
				RES[0][3]=currR

				if ((currR/baseline<=(1+self.tol/100.0)) and (currR > baseline) or \
					((currR/baseline >= (1/(1+self.tol/100))) and (currR<baseline))):

					if (i >= maxSteps_i):
						if (inverse == 1):
							inverse=0
							polarity*=-1
							maxSteps_i+=1
							if (maxSteps_i>maxSteps):
								exitFlag=1
								exitFlag2=1
								terminate=1
								RES[0][2]=0
							else:
								exitFlag=1
								baseline=currR
						else:
							polarity*=-1
							inverse=1
							exitFlag=1
							baseline=currR
					else:
						i+=1
						Vbias=(self.Vmin+i*self.Vstep)*polarity
				else:
					if (currR/baseline >= (1+self.tol/100)):
						RES[n][2]=1
					else:
						RES[n][2]=-1
					exitFlag=1
					exitFlag2=1

		if not terminate:
			self.SS_round2(self.reads_in_trailercard, self.pPulses, self.checkRead, \
							self.pw, self.interpulse, self.tol, self.cycles, self.Vmin, \
							self.Vstep, self.Vmax, RES)

		if self.nr_of_devices==0:
			self.write=self.base_write
		else:
			self.write=self.get_switchseeker_slow_device
		self.tripleSend(0.0,0.0,0.0)

	def SS_BasicUnit(self, M, N, Vbias, T, rw, interpulse):
		outcome=0
		print "Basic unitting..."
		for i in range(N):
			pulse(self.crossbar,self.w,self.b,Vbias,T,self.dt)
			if True:
				self.tripleSend(read(self.crossbar,self.w,self.b),Vbias,T)
		for i in range(M):
			Rmem=read(self.crossbar,self.w,self.b)
			self.tripleSend(read(self.crossbar,self.w,self.b),Vread,0.0)
			outcome+=Rmem/M

		return outcome

	def SS_round2(self, M, N, rw, T, interpulse, Band, Cycles, Vinit, Vstep, Vmax, RES):
		terminate=False
		baseline=0.0
		exitFlag=0
		n=0
		i=0
		Vbias=0.0
		currR=0.0

		semiterm=0.0

		while not terminate:
			exitFlag=0
			n+=1
			if (n>Cycles):
				terminate=1
			else:
				baseline=0
				for i in range(M):
					Rmem=read(self.crossbar,self.w,self.b)
					baseline+=Rmem/M

				Vbias=-Vinit*(RES[n-1][0]/abs(RES[n-1][0]))

				while not exitFlag:
					currR=self.SS_BasicUnit(M,N,Vbias,T,rw,interpulse)
					RES[n][0]=Vbias
					RES[n][1]=T
					RES[n][3]=currR
					if ((currR/baseline<=(1+self.tol/100.0)) and (currR > baseline)) or \
						(((currR/baseline >= (1/(1+self.tol/100))) and (currR<baseline))):
						Vbias+=Vstep*(Vbias/abs(Vbias))

						print "   - applied Vbias:",Vbias,Vmax

						if abs(Vbias)>Vmax:
							RES[n][2]=0
							exitFlag=1
							Cycles+=1
							semiterm+=0.5

						if semiterm==1.0:
							terminate=1

					else:
						if currR/baseline >=(1+Band/100.0):
							RES[n][2]=1
						else:
							RES[n][2]=0
						exitFlag=1
						semiterm=0





	################################################## ENDURANCE #####
	def get_endurance(self, value):
		self.counter+=1
		self.q_in.put(value.rstrip())
		if self.counter==7:
			#self.execute_endurance()
			self.Vp=float(self.q_in.get())
			self.Vn=float(self.q_in.get())
			self.pw=float(self.q_in.get())
			self.interpulse=float(self.q_in.get())
			self.pulseRepetitions=int(float(self.q_in.get()))
			self.cycles=int(float(self.q_in.get()))

			self.nr_of_devices=int(float(self.q_in.get()))
			self.counter=0
			self.write=self.get_endurance_device

	def get_endurance_device(self, value):
		self.counter+=1
		self.q_in.put(value.rstrip())
		if self.counter==2:
			self.w=int(float(self.q_in.get()))
			self.b=int(float(self.q_in.get()))
			self.counter=0
			self.execute_endurance()

	def execute_endurance(self):
		self.nr_of_devices-=1
		for cycle in range(self.cycles):
			for p in range(self.pulseRepetitions):
				self.crossbar=pulse(self.crossbar,self.w,self.b,self.Vp,self.pw,self.dt)
				self.tripleSend(read(self.crossbar,self.w,self.b),self.Vp,self.pw)

			for p in range(self.pulseRepetitions):
				self.crossbar=pulse(self.crossbar,self.w,self.b,self.Vn,self.pw,self.dt)
				self.tripleSend(read(self.crossbar,self.w,self.b),self.Vn,self.pw)


		if self.nr_of_devices==0:
			self.write=self.base_write
		else:
			self.write=self.get_endurance_device
		self.tripleSend(0,0,0)


	################################################## READ SINGLE ###
	def get_readSingle(self, value):
		self.counter+=1
		self.q_in.put(int(value.rstrip()))
		if self.counter==2:
			self.compute_readSingle()
			self.counter=0
			self.write=self.base_write

	def compute_readSingle(self):
		self.w=int(self.q_in.get())
		self.b=int(self.q_in.get())
		self.q_out.put(str(read(self.crossbar,self.w,self.b))+"\n")
		self.write=self.base_write


	################################################## READ ALL #######
	def get_readAll(self, value):
		self.counter+=1
		self.q_in.put(float(value.rstrip()))
		if self.counter==3:
			self.compute_readAll()
			self.counter=0

	def compute_readAll(self):
		type_of_readAll=int(self.q_in.get())
		wline_nr=int(self.q_in.get())
		bline_nr=int(self.q_in.get())

		for w in range(1,wline_nr+1):
			for b in range(1,bline_nr+1):
				self.q_out.put(read(self.crossbar,w,b))
		self.write=self.base_write


	################################################## SINGLE PULSE ###
	def get_pulse(self, value):
		self.counter+=1
		self.q_in.put(value.rstrip())
		if self.counter==4:
			self.compute_pulse()
			self.counter=0		

	def compute_pulse(self):
		w=int(self.q_in.get())
		b=int(self.q_in.get())		
		ampl=float(self.q_in.get())
		pw=float(self.q_in.get())

		self.crossbar=pulse(self.crossbar,w,b,ampl,pw,self.dt)
		self.q_out.put(str(read(self.crossbar,w,b))+"\n")
		self.write=self.base_write


	def close(self):
		print "ser closed"

	def tripleSend(self, Mnow, ampl, pw):
		self.q_out.put(str(Mnow)+"\n")
		self.q_out.put(str(ampl)+"\n")
		self.q_out.put(str(pw)+"\n")


def pulse(crossbar, w, b, ampl, pw, dt):
	global write_scheme

	b_inactive=range(1,33)
	b_inactive.remove(b)

	w_inactive=range(1,33)
	w_inactive.remove(w)

	for timestep in range(int(pw/dt)):
		crossbar[w][b].step_dt(ampl,dt)
		for i in b_inactive:
			crossbar[w][i].step_dt(ampl/2, dt)
		for i in w_inactive:
			crossbar[i][b].step_dt(ampl/2, dt)
	return crossbar

def read(crossbar, w, b):
	global readNoise
	Rmem=crossbar[w][b].Rmem
	return Rmem+readNoise*Rmem*(2*np.random.random()-1)


