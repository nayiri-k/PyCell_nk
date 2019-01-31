__version__ = "1.0"
__author__ = ""

from cni.dlo import *
from cni.geo import *
from cni.constants import *

from Mosfet_vtl import *
from Via import *

class MyInverter(DloGen):
    gateLayer = "poly"
    diffLayer = "active"
    nwellLayer = "nwell"
    pwellLayer = "pwell"
    implant   = "pimplant"
    contact   = "contact"
    metal1Layer = "metal1"
    nimpLayer = "nimplant"
    pimpLayer = "pimplant"
    contactLayer = "contact"

    @classmethod
    # code to define parameters
    def defineParamSpecs(cls, specs):
	oxide = "thin"
	mosType = "nmos_vtl"

        # first use variables to set default values for all parameters
        length = specs.tech.getMosfetParams(mosType, oxide, "minLength")
        width = specs.tech.getMosfetParams(mosType, oxide, "minWidth")
	
	
        # now use these default parameter values in the parameter definitions
        specs('length', length, 'device length', constraint=RangeConstraint(length, 10*length, USE_DEFAULT))
        specs('width', width, 'device width', constraint=RangeConstraint(width, 10*width, USE_DEFAULT))

    # code to process parameter values
    def setupParams(self, params):
        # save parameter values using class variables
        self.length = params['length']
        self.width = params['width']

        # Set up layers using class variables
        self.gateLayer      	= self.tech.getLayer( self.gateLayer    )
        self.diffLayer 		= self.tech.getLayer( self.diffLayer    )
        self.implant  		= self.tech.getLayer( self.implant   	)
        self.contact   		= self.tech.getLayer( self.contact   	)
        self.metal1Layer    	= self.tech.getLayer( self.metal1Layer  )
        self.nwellLayer    	= self.tech.getLayer( self.nwellLayer   )
        self.pwellLayer    	= self.tech.getLayer( self.pwellLayer   )
        self.nimpLayer     	= self.tech.getLayer( self.nimpLayer    )
        self.pimpLayer     	= self.tech.getLayer( self.pimpLayer    )
        self.contactLayer     	= self.tech.getLayer( self.contactLayer )

    def gate(self):
        # Stretch handles for width & length
        stretchHandle(
            shape       = gateRect,
            name        = ("stretch%d" % self.instance),
            parameter   = "width",
            location    = Location.UPPER_CENTER,
            direction   = Direction.NORTH_SOUTH,
            display     = ("w = %.2f" % self.w),
            stretchType = "relative",
            userScale   = "1.0",
            userSnap    = "0.0025",
        )

        stretchHandle(
            shape       = gateRect,
            name        = ("stretch%d" % self.instance),
            parameter   = "length",
            location    = Location.CENTER_RIGHT,
            direction   = Direction.EAST_WEST,
            display     = ("l = %.2f" % self.l),
            stretchType = "relative",
            userScale   = "1.0",
            userSnap    = "0.0025",
        )

    def dcont(self, x, y):
        # metal1
        metal1Box = Box(x + -.0325, y + -.0675, x + .0325, y + .0675)
        Rect(self.metal1Layer, metal1Box)
        # active
        diffBox = Box(x + -.0375, y + -.0375, x + .0375, y + .0375)
        Rect(self.diffLayer, diffBox)
        # contact
        contactBox = Box(x + -.0325, y + -.0325, x + .0325, y + .0325)
        Rect(self.contactLayer, contactBox)

    def pcont(self, x, y):
        # metal
        metal1Box = Box(x + -.0325, y + -.0675, x + .0325, y + .0675)
        Rect(self.metal1Layer, metal1Box)
        # gate
        gateBox = Box(x + -.0375, y + -.0375, x + .0375, y + .0375)
        Rect(self.gateLayer, gateBox)
        # contact
        contactBox = Box(x + -.0325, y + -.0325, x + .0325, y + .0325)
        Rect(self.contactLayer, contactBox)

    def nmos_vtl(self, x, y):
        # gate
        gateBox = Box(x + 0, y + -.055, x + 0.05, y + 0.145)
        Rect(self.gateLayer, gateBox)
        # diffusion
        diffBox = Box(x + -.105, y + 0, x + .155, y + self.width)
        Rect(self.diffLayer, diffBox)
        Rect(self.nimpLayer, diffBox)
        # well
        pwellBox = Box(x + -.16, y + -.055, x + .21, y + 0.145)
        Rect(self.pwellLayer, pwellBox)
        #dcont - x2
        self.dcont(x + -.105 + .0375, y + .0375)
        self.dcont(x + .155 - .0375, y + .0375)

    def pmos_vtl(self, x, y):
        # gate
        gateBox = Box(x + 0, y + -.055, x + self.length, y + 0.145 + self.width)
        Rect(self.gateLayer, gateBox)
        # diffusion
        diffBox = Box(x + -.105, y + 0, x + .155, y + self.width*2)
        Rect(self.diffLayer, diffBox)
        Rect(self.pimpLayer, diffBox)
        # well
        pwellBox = Box(x + -.16, y + -.055, x + .21, y + 0.145 + self.width)
        Rect(self.nwellLayer, pwellBox)
        #dcont - x2
        self.dcont(x + -.105 + .0375, y + .0375)
        self.dcont(x + .155 - .0375, y + .0375)

    def pdcont(self, x, y):
        # well
        pwellBox = Box(x + -.0925, y + -.0925, x + .0925, y + .0925)
        Rect(self.pwellLayer, pwellBox)
        # diffusion
        diffBox = Box(x + -.0375, y + -self.width/2, x + .0375, y + self.width/2)
        Rect(self.diffLayer, diffBox)
        Rect(self.pimpLayer, diffBox)
        # metal1
        metal1Box = Box(x + -.0325, y + -.0675, x + .0325, y + .0675)
        Rect(self.metal1Layer, metal1Box)
        # contact
        contactBox = Box(x + -.0325, y + -.0325, x + .0325, y + .0325)
        Rect(self.contactLayer, contactBox)

    def ndcont(self, x, y):
        # well
        nwellBox = Box(x + -.0925, y + -.0925, x + .0925, y + .0925)
        Rect(self.nwellLayer, nwellBox)
        # diffusion
        diffBox = Box(x + -.0375, y + -self.width/2, x + .0375, y + self.width/2)
        Rect(self.diffLayer, diffBox)
        Rect(self.nimpLayer, diffBox)
        # metal1
        metal1Box = Box(x + -.0325, y + -.0675, x + .0325, y + .0675)
        Rect(self.metal1Layer, metal1Box)
        # contact
        contactBox = Box(x + -.0325, y + -.0325, x + .0325, y + .0325)
        Rect(self.contactLayer, contactBox)

    # code to generate transistor layout
    def genLayout(self):
        self.nmos_vtl(.335, .1575)
        self.pmos_vtl(.335, .5825)
        self.pdcont(.1025, .2)
        self.ndcont(.1025, .7175)
        self.pcont(.2975, .4125)

        # metal wiring
        metal1Box = Box(.01, .755, .5425, .83)
        Rect(self.metal1Layer, metal1Box)
        metal1Box = Box(.2325, .6425, .2975, .7825)
        Rect(self.metal1Layer, metal1Box)
        metal1Box = Box(.0725, .0175, .0725 + .065, .2325)
        Rect(self.metal1Layer, metal1Box)
        metal1Box = Box(.4225, .1275, .4825, .6725)
        Rect(self.metal1Layer, metal1Box)
        metal1Box = Box(.0675, .005, .55, .0775)
        Rect(self.metal1Layer, metal1Box)
        metal1Box = Box(.235, .05, .3, .145)
        Rect(self.metal1Layer, metal1Box)

        # gate connection
        gateBox = Box(.335, .3025, .335 + self.length, 0.5275)
        Rect(self.gateLayer, gateBox)

        # select all components and move together
        #all = Grouping( "all", self.getComps())
        #all.moveBy(1,1)

