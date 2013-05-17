from swig_generated.SphSim import UnitInfo

direct = ['x', 'y', 'z', 'vx', 'vy', 'vz', 'ax', 'ay', 'az',
          'm', 'h', 'rho', 'u', 'dudt']

derived_fetchers = {}

def get_fetcher(quantity):
    '''Given a quantity, return a fetcher that we can query to get that quantity'''
    if quantity in direct:
        return DirectDataFetcher(quantity)
    elif quantity in derived_fetchers:
        return derived_fetchers[quantity]
    else:
        raise Exception("We don't know how to compute " + quantity)
    
from formula_parser import evaluateStack, exprStack, varStack, pattern    


def set_fetcher(name, formula, unitlabel='', unitname='',scaling_factor=1):
    #TODO: set label
    '''Given a mathematical formula, build a data fetcher from it'''
    fetcher = FormulaDataFetcher(name, formula, unitlabel, unitname, scaling_factor)
    derived_fetchers[name] = fetcher
    return fetcher


def check_requested_quantity(quantity, snap):
    '''Check the requested quantity exists, depending on the dimensionality of the snapshot.
    Also return information about the kind of the quantity (direct or derived)'''
    
    #check dimensionality
    twod = ('y', 'vy', 'ay')
    threed = ('z', 'vz', 'az')
    minus3 = quantity in threed+('r','theta') and snap.ndim<3
    minus2 = quantity in twod+('R','phi') and snap.ndim<2
    if minus3 or minus2:
        raise Exception("Error: you requested the quantity " + quantity + ", but the simulation is only in " + str(snap.ndim) + " dims")
    
    #if it's not a live snapshot, check that we are not requesting quantities defined only for live snapshots
    if not snap.live:
        if quantity in ('ax', 'ay', 'az'):
            raise Exception ("Error: accelerations are available only for live snapshots")
        elif quantity in ('dudt'):
            raise Exception ("Error: dudt is available only for live snapshots")
    
    #check that we know how to compute the quantity
    if quantity in direct:
        return "direct"
    elif quantity in derived_fetchers:
        return "derived"
    else:
        raise Exception("We don't know how to compute " + quantity)
    
    
class DirectDataFetcher:
    
    def __init__(self, quantity):
        
        if quantity not in direct:
            raise Exception ("Error: the quantity" + quantity + " is not a direct quantity!")
        self._quantity = quantity
        
    def fetch(self, snap, unit):
        
        kind = check_requested_quantity(self._quantity, snap)
        if kind != "direct":
            raise Exception ("Error: the quantity" + quantity + " is not a direct quantity!")
        
        return snap.ExtractArray(self._quantity, unit)
    
class FormulaDataFetcher:
    
    def __init__(self, name, formula, unitlabel='', unitname='',scaling_factor=1):
        self.scaling_factor=int(scaling_factor)
        self._name = name
        exprStack[:]=[]
        pattern.parseString(formula)
        self._stack = list(exprStack)
        self.unitinfo = UnitInfo()
        self.unitinfo.label=unitlabel
        self.unitinfo.name=unitname
        
    def fetch(self, snap, unit):
        result = evaluateStack(list(self._stack), snap)
        return self.unitinfo, result, self.scaling_factor
    
    
def initialize():
    set_fetcher('r','sqrt(x^2+y^2+z^2)')
    set_fetcher('R','sqrt(x^2+y^2)')
    set_fetcher('phi','arctan2(y,x)')
    set_fetcher('theta','arccos(z/r)')
    set_fetcher('vr','sin(theta)*cos(phi)*vx+sin(theta)*sin(phi)*vy+cos(theta)*vz')
    set_fetcher('ar','sin(theta)*cos(phi)*ax+sin(theta)*sin(phi)*ay+cos(theta)*az')

#if we are being imported, initialize quantities
initialize()