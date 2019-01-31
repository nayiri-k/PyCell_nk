__version__ = "$Revision: #4 $"

from cni.dlo import *
from cni.geo import *
from cni.constants import *
from tutorial2 import *

class MyTransistor(DloGen):

    @classmethod
    def defineParamSpecs(cls, specs):

        tranType = 'pmos'
        oxide = 'thin'
        width = specs.tech.getMosfetParams(tranType, oxide, 'minWidth')
        length = specs.tech.getMosfetParams(tranType, oxide, 'minLength')
  
        # define all parameters for this transistor parameterized cell
        specs('width', width, 'device width', RangeConstraint(width, 10*width, USE_DEFAULT))
        specs('length', length, 'device length', RangeConstraint(length, 10*length, USE_DEFAULT))

        specs('tranType', 'pmos', 'MOSFET type (pmos or nmos)', ChoiceConstraint(['pmos', 'nmos']))                        
        specs('oxide', 'thin', 'Oxide (thin or thick)', ChoiceConstraint(['thin', 'thick'])) 
        specs('fingers', 1, 'Number of fingers', RangeConstraint(1, 100, USE_DEFAULT))

        specs('bars', True)
        specs('substrateContact', False)


    def setupParams(self, params):

        # save parameter values using class variables
        self.width = params['width']
        self.length = params['length']
        self.oxide = params['oxide']
        self.tranType = params['tranType']
        self.fingers = params['fingers']
        self.bars = params['bars']
        self.substrateContact = params['substrateContact']
    
        # readjust width and length, as minimum values may be different
        self.width = max(self.width, self.tech.getMosfetParams(self.tranType, self.oxide, 'minWidth'))
        self.length = max(self.length, self.tech.getMosfetParams(self.tranType, self.oxide, 'minLength'))

        # also snap width and length values to nearest grid points
        grid = Grid(self.tech.getGridResolution())
        self.width = grid.snap(self.width, SnapType.ROUND)
        self.length = grid.snap(self.length, SnapType.ROUND) 

        # save layer values using class variables
        self.barLayer = Layer('metal4')
        self.gateRouteLayer = Layer('poly1')
        self.drainRouteLayer = Layer('metal3')
        self.sourceRouteLayer = Layer('metal3')
        self.strapLayer = Layer('metal1')

        # ensure that transistor fill layer is highest routing layer
        self.xtorFillLayer = Layer('metal1')
        if self.gateRouteLayer.isAbove(self.xtorFillLayer):
            self.xtorFillLayer = self.gateRouteLayer
        if self.drainRouteLayer.isAbove(self.xtorFillLayer):
            self.xtorFillLayer = self.drainRouteLayer
        if self.sourceRouteLayer.isAbove(self.xtorFillLayer):
            self.xtorFillLayer = self.sourceRouteLayer

        # define the well layer to be used for contact ring generation
        if self.tranType == 'pmos':
            self.wellLayer = Layer('nwell')
        else:
            self.wellLayer = Layer('pwell')


    def getMergeOverlap(self, tranUnitInstance, drainFlag):

        # calculate distance which transistor unit must be moved
        # to merge the drain or source with another transistor unit.

        if drainFlag:
            pinBox = tranUnitInstance.findInstPin('D').getBBox()
        else:
            pinBox = tranUnitInstance.findInstPin('S').getBBox()
    
        # compare pin bounding box with transistor unit bounding box;
        # add minimum extension to get overlap for merge operation.
        tranBox = tranUnitInstance.getBBox()
        ext1 = pinBox.bottom - tranBox.bottom
        ext2 = tranBox.top - pinBox.top
        overlap = pinBox.getHeight() + 2.0 * min(ext1, ext2)
        return(overlap)


    def genTopology(self):

        if self.tranType == 'pmos':
            baseName = 'MP'
        else:
            baseName = 'MN'

        # create grouping for transistor units
        transistorStack = Grouping('transistorStack')

        # create transistor unit for each finger of the transistor
        self.Units = []
        defaultParams = ParamArray()
   
        for i in range(self.fingers):
            name = baseName + str(i)
            # create transistor unit for this finger, and save it
            self.Units.append(Instance('MyTransistorUnit', defaultParams, ['D', 'G', 'S', 'B'], name))
            # also save this transistor unit in the Grouping object
            transistorStack.add(self.Units[i])

        # also create the terminals for this transistor
        self.addTerm('S', TermType.INPUT_OUTPUT)   # source terminal
        self.addTerm('D', TermType.INPUT_OUTPUT)   # drain terminal
        self.addTerm('G', TermType.INPUT)          # gate terminal
        self.addTerm('B', TermType.INPUT_OUTPUT)   # bulk (substrate) terminal

        self.setTermOrder(['D', 'G', 'S', 'B'])


    def sizeDevices(self):

        unitWidth = self.width/self.fingers
        unitParams = ParamArray(tranType = self.tranType,
                                width = unitWidth,
                                length = self.length,
                                oxide = self.oxide,
                                xtorFillLayer = self.xtorFillLayer)
        for unit in self.Units:
            unit.setParams(unitParams)
         

    def genLayout(self):

        # place the different transistor units, one for each finger
        self.stackUnits()

        # if bars should be generated, create bars and required routing
        if self.bars:
            self.createBars()
            self.createRouting()

        # create pins for each of the devices in this transistor
        self.createPins()

        # create possible contact ring around the final layout
        if self.substrateContact:
            self.createRing()



    def stackUnits(self):

        # flip every other unit, to properly locate sources and drains
        flip = True
        for unit in self.Units:
            if flip:
                unit.mirrorX()
            flip = not flip

        # now place transistor units, each one above the previous one;
        # adjust placement for contact overlap for multiple fingers.
        reference = self.Units[0]
        offset = - self.getMergeOverlap(reference, True)
        for i in range(1, self.fingers):
            place(self.Units[i], NORTH, reference, offset)
            reference = self.Units[i]


    def createBars(self):

        transistorStack = Grouping.find('transistorStack')

        w = self.tech.getPhysicalRule('minWidth', self.barLayer)
        l = transistorStack.getBBox().getHeight()

        # construct bars for the transistor source, drain and gate
        self.sourceBar = Bar(self.barLayer, NORTH_SOUTH, 'S', Point(0,0), Point(w,l))
        self.drainBar = Bar(self.barLayer, NORTH_SOUTH, 'D', Point(0,0), Point(w,l)) 
        self.gateBar = Bar(self.gateRouteLayer, NORTH_SOUTH, 'G', Point(0,0), Point(w,l))

        # also create gate contact to enable easier design reuse
        self.gateContact = Contact(self.gateRouteLayer, self.barLayer, 'G', NONE, NONE, Point(0,0), Point(w,l))
                         
        # create temporary contacts to "help" the "smart place" method
        self.sourceBar.addContact(self.sourceRouteLayer, Point(w,l))
        self.drainBar.addContact(self.drainRouteLayer, Point(w,l))
        self.gateBar.addContact(self.gateRouteLayer, Point(w,l))

        # "smart place" the gate bar to right of the transistor,
        # and the source and drain bars to the left side
        fgPlace(self.gateBar, EAST, transistorStack)
        fgPlace(self.drainBar, WEST, transistorStack)
        fgPlace(self.sourceBar, WEST, self.drainBar)

        # now delete these temporary contacts, since the bars have been placed
        self.sourceBar.clearContacts()
        self.drainBar.clearContacts()
        self.gateBar.clearContacts()

        # also snap bars to nearest grid points
        grid = Grid(self.tech.getGridResolution())
        self.sourceBar.snap(grid, SnapType.ROUND)
        self.drainBar.snap(grid, SnapType.ROUND)
        self.gateBar.snap(grid, SnapType.ROUND)

        # also place the gate contact right next to the gate bar
        place(self.gateContact, EAST, self.gateBar, 0, self.gateRouteLayer)

    def createRouting(self):

        # create a straight-line route between the pins and bars
        # for source, drain and gate for each transistor finger

        for i in range(self.fingers):
            RoutePath.StraightLineToBar(self.Units[i].findInstPin('S'), self.sourceBar, self.sourceRouteLayer)  
            RoutePath.StraightLineToBar(self.Units[i].findInstPin('D'), self.drainBar, self.drainRouteLayer)
            RoutePath.StraightLineToBar(self.Units[i].findInstPin('G'), self.gateBar, self.gateRouteLayer)


    def createPins(self):

        # create the pins for each of the devices in this transistor
        if self.bars:
        # also define the pins for this transistor unit
            # if bars were created, create pins from bars
            self.addPin('S', 'S', self.sourceBar.getBBox(), self.barLayer)
            self.addPin('D', 'D', self.drainBar.getBBox(), self.barLayer)
            self.addPin('G', 'G', self.gateBar.getBBox(), self.barLayer)

        else:
            # otherwise, create pins from transistor units 
            for i in range(self.fingers):
                self.addPin('S' + str(i), 'S', self.Units[i].findInstPin('S').getBBox(), self.xtorFillLayer)
                self.addPin('D' + str(i), 'D', self.Units[i].findInstPin('D').getBBox(), self.xtorFillLayer)
                self.addPin('G' + str(i), 'G', self.Units[i].findInstPin('G').getBBox(), self.xtorFillLayer)

    def createRing(self):

        # determine implant layer to be used for constructing contacts
        if self.tranType == 'pmos':
            impLayer = Layer('nimp')
        else:
            impLayer = Layer('pimp')

        # now create the contact ring structure
        ContactRing(Layer('diff'), self.strapLayer, 'B', [impLayer], 0, 0, [self.wellLayer])



