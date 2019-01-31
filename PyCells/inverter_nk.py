__version__ = "1.0"
__author__ = ""

from cni.dlo import *
from cni.geo import *
from cni.constants import *

from Mosfet_vtl import *
from Via import *

class MyInverter(DloGen):
    poly      = "poly"
    diff      = "active"
    nwell     = "nwell"
    pwell     = 'pwell'
    implant   = "pimplant"
    contact   = "contact"
    metal1    = "metal1"
    boundary  = "prBoundary"
    
    #Instances  = []
    LogicGate  = []

    @classmethod
    # code to define parameters
    def defineParamSpecs(cls, specs):
        oxide = "thin"
        mosType = "nmos_vtl"

        # first use variables to set default values for all parameters
        l = specs.tech.getMosfetParams('nmos_vtl', oxide, 'minLength')
        l = .15
        n_w = specs.tech.getMosfetParams('pmos_vtl', oxide, 'minWidth')
        p_w = 2*n_w
        
        cellHeight = .75
    
    
        # now use these default parameter values in the parameter definitions
        specs('l', l, 'device length', constraint=RangeConstraint(l, 10*l, USE_DEFAULT))
        specs('n_w', n_w, 'nmos device width', constraint=RangeConstraint(n_w, 10*n_w, USE_DEFAULT))
        specs('p_w', p_w, 'pmos device width', constraint=RangeConstraint(p_w, 10*p_w, USE_DEFAULT))
        specs('cellHeight', cellHeight, 'standard cell height', constraint=RangeConstraint(cellHeight, 2*cellHeight, USE_DEFAULT))

    # code to process parameter values
    def setupParams(self, params):
        
        # save parameter values using class variables
        self.l = params['l']
        self.n_w = params['n_w']
        self.p_w = params['p_w']
        self.cellHeight = params['cellHeight']

        # set up layers using class variables
        self.poly      = self.tech.getLayer( self.poly      )
        self.diff      = self.tech.getLayer( self.diff    )
        self.implant   = self.tech.getLayer( self.implant   )
        self.contact   = self.tech.getLayer( self.contact   )
        self.metal1    = self.tech.getLayer( self.metal1    )
        self.nwell     = self.tech.getLayer( self.nwell    )
        self.pwell     = self.tech.getLayer( self.pwell    )
        self.boundary     = self.tech.getLayer( self.boundary    )
        
        # get sizing/spacing rules
        self.endcap = self.tech.getPhysicalRule('minEnclosure', self.poly, self.diff) # determine minimum extension for gate poly layer
        self.metal1Width = self.tech.getPhysicalRule('minWidth', self.metal1)
        self.wellSpacing = self.tech.getPhysicalRule('minSpacing', self.nwell)
        self.diffSpacing = self.tech.getPhysicalRule('minSpacing', self.diff)
        self.contactWidth = self.tech.getPhysicalRule('minWidth', self.contact)
        self.contactSpacing = self.tech.getPhysicalRule('minSpacing', self.contact)
        self.powerMetalWidth = self.metal1Width*1.25;

    # code to size different devices
    def sizeDevices(self):
        M0params = ParamArray()
        
        # pmos
        self.M0_pmos.getParams(M0params, True)
        M0params.set('l',self.l)
        M0params.set('w',self.p_w)
        M0params.set('diffContactLeft',True)
        M0params.set('diffContactRight',True)
        self.M0_pmos.setParams(M0params)

        # nmos
        self.M0_nmos.getParams(M0params, True)
        M0params.set('l',self.l)
        M0params.set('w',self.n_w)
        M0params.set('diffContactLeft',True)
        M0params.set('diffContactRight',True)
        self.M0_nmos.setParams(M0params)
      
    def genTopology(self): 
        self.Instances = []       
        self.M0_pmos = Instance('pmos_vtl')
        self.Instances.append(self.M0_pmos) 
        self.M0_nmos = Instance('nmos_vtl')
        self.Instances.append(self.M0_nmos)
        self.M0_pcontact = Instance('pcont')
        self.Instances.append(self.M0_pcontact)
        self.M0_ntap = Instance('ndcont')
        self.Instances.append(self.M0_ntap)
        self.M0_ptap = Instance('pdcont')
        self.Instances.append(self.M0_ptap)
    
    def genStdLayout(self):
        # cell boundary
        self.cellBoundary = Rect(self.boundary, Box(0, 0, 2*self.cellHeight, self.cellHeight))
        
        # first make power rails
        self.VDD = Rect(self.metal1, Box(0, self.cellHeight-self.powerMetalWidth/2, 2*self.cellHeight, self.cellHeight+self.powerMetalWidth/2))
        self.VSS = Rect(self.metal1, Box(0, -self.powerMetalWidth/2, 2*self.cellHeight, self.powerMetalWidth/2))
           
    def genLogicLayout(self):
    
        # place nmos in std cell layout
        self.M0_nmos.alignEdge(SOUTH,self.VSS,refDir=NORTH)
        self.M0_nmos.alignEdge(EAST,self.cellBoundary,refDir=EAST)
        
        #fgPlace(Direction dir, PhysicalComponent refComp, ShapeFilter filter=ShapeFilter(),
        #PhysicalComponent env=None, Bool align=True, ShapeFilter refFilter=None, dict
        #options=None)
        
        # ptap
        self.M0_ptap.alignEdge(EAST,self.M0_nmos,refDir=WEST,filter=ShapeFilter(self.diff),refFilter=ShapeFilter(self.diff))
        self.M0_ptap.alignEdge(SOUTH,self.M0_nmos,refDir=SOUTH,filter=ShapeFilter(self.pwell),refFilter=ShapeFilter(self.pwell))
        self.M0_ptap.moveBy(-self.diffSpacing,0)
        
        # pmos
        #self.M0_pmos.fgPlace(NORTH, self.M0_nmos)
        self.M0_pmos.mirrorY()
        self.M0_pmos.alignEdge(SOUTH,self.M0_nmos,refDir=NORTH,filter=ShapeFilter(self.nwell),refFilter=ShapeFilter(self.pwell))
        self.M0_pmos.moveBy(self.l,self.wellSpacing)
        self.M0_pmos.alignEdge(EAST,self.M0_nmos,refDir=EAST,filter=ShapeFilter(self.nwell),refFilter=ShapeFilter(self.pwell))
        
        # ntap
        self.M0_ntap.alignEdge(EAST,self.M0_ptap,refDir=EAST,filter=ShapeFilter(self.diff),refFilter=ShapeFilter(self.diff))
        self.M0_ntap.alignEdge(NORTH,self.M0_pmos,refDir=NORTH,filter=ShapeFilter(self.nwell),refFilter=ShapeFilter(self.nwell))
        #self.M0_ntap.moveBy(-self.diffSpacing,0)
 
        # get terminals and pins from the pmos and nmos devices
        self.M0_pmosTerms = self.M0_pmos.getInstTerms() 
        self.M0_nmosTerms = self.M0_nmos.getInstTerms() 
            # >> [InstTerm('G',<Instance 'I__0'>), InstTerm('S',<Instance 'I__0'>), InstTerm('D',<Instance 'I__0'>)]
        
        self.M0_pmosPins = self.M0_pmos.getInstPins()
        self.M0_nmosPins = self.M0_nmos.getInstPins()
            # >> [InstPin('GN1',<Instance 'I__0'>), InstPin('GS1',<Instance 'I__0'>), 
            #       InstPin('S',<Instance 'I__0'>),   InstPin('D',<Instance 'I__0'>)]
    
    def genRouting(self):  
        # ROUTE DEVICES TOGETHER
        # gate
        self.M0_gate = RoutePath().Connect(RouteTarget(self.M0_nmosPins[0]), RouteTarget(self.M0_pmosPins[1]), self.poly, self.l, genContact=False)
        self.LogicGate.append(self.M0_gate)
        
        # metal wiring
        RoutePath().Connect(RouteTarget(self.M0_nmosPins[3]), RouteTarget(self.M0_pmosPins[2]), self.metal1, self.metal1Width, genContact=False)
        RoutePath().Connect(RouteTarget(self.M0_pmosPins[3]), RouteTarget(self.VDD), self.metal1, self.metal1Width, genContact=True)
        RoutePath().Connect(RouteTarget(self.M0_nmosPins[2]), RouteTarget(self.VSS), self.metal1, self.metal1Width, genContact=True)
        RoutePath().Connect(RouteTarget(self.M0_ptap.getCompRefs()[0]),RouteTarget(self.VSS), self.metal1, self.metal1Width, genContact=False)
        RoutePath().Connect(RouteTarget(self.M0_ntap.getCompRefs()[0]),RouteTarget(self.VDD), self.metal1, self.metal1Width, genContact=False)
        
        # pcontact
        self.M0_pcontact.alignEdge(SOUTH,self.M0_nmos,refDir=NORTH,filter=ShapeFilter(self.poly),refFilter=ShapeFilter(self.pwell))
        self.M0_pcontact.alignEdge(EAST,self.M0_gate,refDir=WEST,filter=ShapeFilter(self.poly),refFilter=ShapeFilter(self.poly))
        self.M0_pcontact.moveBy(0,self.wellSpacing/2-self.contactSpacing/2)
        
    # code to generate transistor layout
    def genLayout(self):
        # already generated topology & sized devices
        self.genStdLayout()
        self.genLogicLayout() 
        self.genRouting()
        
        # flatten all instances
        for x in self.Instances:
            x.flatten()
        
        # relevant functions:
        #       PhysicalComponent().abut(Direction dir, PhysicalComponent refComp, ShapeFilter filter, Bool align=True, ShapeFilter refFilter=None)
        #       PhysicalComponent().alignEdge(Direction dir, PhysicalComponent refComp, Direction refDir=None,ShapeFilter filter=ShapeFilter(), ShapeFilter refFilter=None, Coord offset=None)
        #       RoutePath().Connect(RouteTarget fromTarg, RouteTarget toTarg, Layer layer=None, Coord width=0, Bool genContact=True, string name='')
        #       getBBox(ShapeFilter filter=ShapeFilter())
 
        # tried renaming master, didn't work
        # syntax: self.M0_pmos.setMaster(libName='NCSU_TechLib_FreePDK45', viewName='layout', cellName='pmos_vtl') #sets the master design for this Instance object
      



