import numpy as np
import collections

#with homeostasis

class BiolekDevice:

    def __init__(self, Ron=1e5, \
                       Roff=1e6, \
                       uv=0.5e-11, \
                       D=2e-8, \
                       type_f=1, \
                       Vthrp=1, \
                       Vthrn=-1, \
                       p=1):

        self.Ron=Ron
        self.Roff=Roff
        self.deltaR=self.Roff-self.Ron
        self.uv=uv
        self.D=D
        self.type_f=type_f
        self.Vthrp=Vthrp
        self.Vthrn=Vthrn
        self.K=1e-6
        self.vthr_var=0.4
        self.Gx=0

        #self.alpha=self.K*self.uv*self.Ron/(self.D**2)
        #self.f=lambda x: 1-(2*x-1)**(2*p)
        self.stp=lambda x: 0.8 if x>0 else 0
        self.f=lambda x,i: (x-self.stp(-i))**(2*p)

    def initialise(self, Rinit):
        self.x = float(self.Roff-Rinit)/(self.deltaR)
        self.Rmem = self.Roff-self.x*self.deltaR

    def step_dt(self, Vm, dt):
        #rand_p=(-1+2*np.random.random())*self.vthr_var+self.Vthrp
        #rand_n=(-1+2*np.random.random())*self.vthr_var+self.Vthrn
        Rold=self.Rmem
        if Vm>self.Vthrp or Vm<self.Vthrn:
            Imem=float(Vm)/self.Rmem
            #self.Gx=self.alpha*Vm*self.f(self.x, Imem)

            #if Vm>0:
            self.Gx=Imem*self.uv*self.Ron/(self.D**2)*self.f(self.x, Imem)
            # else:
            #   Gx=self.K*(Vm-rand_n)*self.uv*self.Ron/(self.D**2)*self.f(self.x, Imem)

            self.x=self.x+self.Gx*dt
            if self.x>1:
                self.x=1
            if self.x<0:
                self.x=0
            self.Rmem=self.Roff-self.x*self.deltaR

        return self.x, self.Rmem

    def get_Gx(self):
        return self.Gx
