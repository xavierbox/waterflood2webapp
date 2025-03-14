
'''

Variable names: 

    Previous versions of the code, naming convenctions in some database used and 
    files comming from Petrel or other sources refer to the same variables with 
    different names,capitalizations, etc. 

    In this package, it is encouraged to hamonize the naming of variables. By default, 
    the program  will use the first keyword listed in each of the arrays below to refer 
    to the variable at the left. Yet, when trying to retrieve information from 
    files/databases/previous work, it will also search when possible for 
    the other keywords when the default option fails. 

    For example, when retrieving the well name in a table (simulation, dataset, pattern, 
    result etc), the engine will searh for key-value pairs { NAME: xxx }. If not found, 
    the engine will use the alternative WELL_NAME and ITEM_NAME. 

    Capitalization is encouraged to denote variables that do not change, such as the 
    well name. A more pythonic style is used for other variables that change -i.e. are computed- 
    or are inputs to calculations, such as the predicted rates for instance. 

    In every case, when models, results, datasets or patterns are saved, the default 
    naming (first key) will always be used. 

Naming convention optimizers and pre-optimizers:

    The program use several libraries and in some cases, the input parameters to part of those libraries
    is exposed to the user. The problem is that naming conventions are not standard. The library 
    Scikit-learn for instance, follows the PEP style closely (lower cases and _ between words, 
    capitalized classes, etc.In other cases, such as in Scipy, the same convention is largely used but not 
    always.
    
    In this program, the user is encouraged to use only lower cased options and no dashed or symbols other
    than the underscore to separate words. The name of some optimizers, however, is supported as used in 
    those 3rd party libraries. The dictionary of optimizer names below has the sole purpose of mapping 
    between different names and the name expected by Scipy
    
        Example: 
        
            NAME_KEYS   = ['NAME', 'WELL_NAME', 'ITEM_NAME']

            WATER_INJECTION_KEYS   = ['water_injection', 'WATER_VOL_RATE', 'WATER_INJ_RATE']
            LIQUID_PRODUCTION_KEYS = ['liquid_production','ACT_LIQ_VOL']
            OIL_PRODUCTION_KEYS    = ['oil_production','ACT_OIL_VOL']

            (etc)


Note on optimizers:
    Note that the program combines the use of two optimizers, one for global and one for local optimization.
    The user is allowed to choose combinations. Yet, it is the user responsibility to select 
    combinations that make sense. We recommend Nelder-Mead as the local optimizer and either TNC, or Powell 
    for the pre-optimizer (global scope)
    
        Example: 
        
            optimizers_name_map ={
                'auto': "Nelder-Mead",
                "nelder-mead" : "Nelder-Mead",
                "neldermead" : "Nelder-Mead",
                "Nelder-Mead" : "Nelder-Mead",

                "powell" : "Powell",
                "Powell" : "Powell",

                "cg" : "CG",
                "bfgs" : "BFGS",
                "newtoncg" : "Newton-CG",
                "l-bfgs-b" : "L-BFGS-B",
                "lbfgsb" : "L-BFGS-B",

                "tnc" : "TNC",
                "TNC" : "TNC",
                "newton-cg" : "Newton-CG",

                "cobyla" : "COBYLA", 
                "slsqp" : "SLSQP"
                }
    
    Note that NOT ALL THE OPTIMIZERS SUPPORT constraints but these are needed in our CRM implementation.
    Hence the list provided here is significanlty smaller than the list provided in the libraries used. 


Contstants:

    CRM uses very few constants. Most of them are mathematical constants defined in standard libraries.
    The very few extra ones are defined here.

'''

import pathlib

DATE_FORMAT = "%d/%m/%Y"
RANDOM_SEED = 42

#these are the accepted synonims for different variables of the model
MIN_UPTICK_INJECTOR = 0.3
MIN_INJECTION_LEVEL = 10.0
MIN_PRODUCTION_LEVEL = 30.0

UBHI = ["UBHI", "WELL_UWI", "UWI", "WELLID", "WELL_ID"]
NAME_KEYS   = ['NAME', 'WELL', 'WELL_NAME', 'UBHI', 'ITEM_NAME']
WATER_INJECTION_KEYS   = ['WATER_INJECTION_VOLUME','INJECTION_VOLUME','WATER_INJECTION', 'water_injection', 'WATER_VOL_RATE', 'WATER_INJ_RATE']


LIQUID_PRODUCTION_KEYS = ['LIQUID_VOLUME','LIQUID_PRODUCTION', 'liquid_production','ACT_LIQ_VOL']
OIL_PRODUCTION_KEYS    = ['OIL_VOLUME','OIL_PRODUCTION','ACT_OIL_VOL']
GAS_PRODUCTION_KEYS    = ['GAS_VOLUME','GAS_PRODUCTION','ACT_GAS_VOL']
WATER_PRODUCTION_KEYS    = ['WATER_VOLUME','WATER_PRODUCTION','ACT_WAT_VOL', 'ACT_WATER_VOL']
WATER_PRODUCTION_FRACTION_KEYS    = ['WATER_FRACTION', 'fw' ]


PRODUCER_PRESSURE_KEYS = ['FBHP','PRODUCER_PRESSURE','PROD_PRESS', 'PROD_PRESSURE']
CUMMULATIVE_WATER_INJECTED_KEYS    = ['CUM_WATER_INJECTED']

PRIMARY_SUPPORT_KEYS   = ['Lo','PRIMARY_SUPPORT']

DATE_KEYS = ["DATE", "START_DATE", "Last edited"]

DISTANCE_KEYS = ['distance', 'distances']

ALLOCATION_KEYS = ['allocation']

PRODUCTIVITY_KEYS =['productivity']

TAU_KEYS =['tau']

TAUP_KEYS = ['taup']

X_KEYS = ['X']
Y_KEYS = ['Y']

LOCATION_KEYS=['location', 'locations', 'loc'] 

REGION_KEYS =[ 'REGION'  ]
FIELD_KEYS = ['FIELD','FLD','FIELD_NAME']
RESERVOIR_KEYS = ['RESERVOIR','RESERVOIR_NAME']
LAYER_KEYS = ['LAYER_NAME','LAYER_ID']

INJECTOR_WELL_TYPES = ["Injector","InjectorWater", "Injector-Water-Deviated"]
PRODUCER_WELL_TYPES = ["Producer","OilWellDeviated", "OilWell"]
KNOWN_WELL_TYPES = INJECTOR_WELL_TYPES + PRODUCER_WELL_TYPES

ZONE_KEYS = ["ZONE", "RESERVOIR"]
SUBZONE_KEYS = ["SUBZONE", "SUB_ZONE"]
SECTOR_KEYS = ["SECTOR"]
LAT_KEYS = ["LAT"]
LONG_KEYS = ["LONG"]


#the potential name of the columns in datasets that refer to the well type 
WELL_TYPE = ["WELL_TYPE", "TYPE"]
INDEX_KEYS=['INDEX']

SIM_SUFFIX = '_sim'
SIM_PREFFIX = 'SIM_'

DATA_SUFFIX = '_data'


ALL_KEYWORDS = [NAME_KEYS, 
                WATER_INJECTION_KEYS,
                LIQUID_PRODUCTION_KEYS,
                OIL_PRODUCTION_KEYS,
                GAS_PRODUCTION_KEYS,
                WATER_PRODUCTION_KEYS,
                WATER_PRODUCTION_FRACTION_KEYS,
                
                PRODUCER_PRESSURE_KEYS,CUMMULATIVE_WATER_INJECTED_KEYS,
                PRIMARY_SUPPORT_KEYS,DATE_KEYS, DISTANCE_KEYS,ALLOCATION_KEYS, 
                PRODUCTIVITY_KEYS, TAU_KEYS, TAUP_KEYS,
                LOCATION_KEYS,X_KEYS,Y_KEYS,
                REGION_KEYS, FIELD_KEYS ,
                RESERVOIR_KEYS      
               ]

RATE_KEYWORDS = [
                WATER_INJECTION_KEYS,
                LIQUID_PRODUCTION_KEYS,
                OIL_PRODUCTION_KEYS,
                GAS_PRODUCTION_KEYS,
                WATER_PRODUCTION_KEYS,
                WATER_PRODUCTION_FRACTION_KEYS,
                PRODUCER_PRESSURE_KEYS,
                CUMMULATIVE_WATER_INJECTED_KEYS
               ]
           
# utility functions.
# moved to data utils 
#def find_columns(cols, keys):
#    """
#    Returns a list of the columns in cols that
#    match any column in keys (case insensitive)
#    """
#    return [col for col in cols if col.upper() in keys]
         
# utility functions.
def find_columns(cols, keys):
    """
    Returns a list of the columns in cols that
    match any column in keys (case insensitive)
    """
    return [col for col in cols if col.upper() in keys]

def find_column(cols, keys):
    """
    Returns a the first column in cols (list[str] or dataframe that
    matches any string in keys (case insensitive)
    """
    found = find_columns(cols, keys)
    return found[0] if any(found) else None  



def name_to_meaning(name, meanings = None):
    
    if meanings is None: meanings = ALL_KEYWORDS
    for keyset in meanings:
        if name in keyset or name.lower() in keyset or name.upper() in keyset: return keyset[0]
        if name.lower() in [ k.lower() for k in keyset]: return keyset[0]
        if name.upper() in [ k.upper() for k in keyset]: return keyset[0]
        
        
    return None


def name_to_key(name):
    '''
    Receives a string(word) such as: 'ACT_LIQ_VOL' that could be a column name in a dataset
    and returns the 'meaning', i.e. 'ACT_LIQ_VOL' -> 'LIQUID_PRODUCTION'
    
    The meaning is the first word in the keys array that contains the paramenter passed (name=ACT_LIQ_VOL)
    in this case, it is the LIQUID_PRODUCTION_KEYS array

    Another example:
    
    if name = PROD_PRESS, the meaning returned will be PRODUCER_PRESSURE_KEYS[0] = FBHP
    '''
    return name_to_meaning(name)


def columns_to_meaning_map( columns, meanings = None):
    '''
    Receives a list of column names (string list) and returns a mapping to the default 
    meaning keyword of that column name. If the column name has no meaning, then it 
    will map to itself 
    '''     
    if meanings is None: meanings = ALL_KEYWORDS
    
    mapping = {} 
    for column in columns: 
        for key_set in meanings:

            col = column.upper()
            if col in [ key.upper() for key in key_set]: 
                mapping[column] = key_set[0]
                break 
     
        if column not in mapping:
            mapping[ column] = column 
        
                
    return mapping 

def get_column_for_meaning(cols, meaning  ):
    '''
    get the list of columns in the array columns that are associated with a given meaning. 
    
    For instance, if columns = ['x','Y','A', 'B'] and meaning = 'location', Location, loCATion or 'LOCATION'
    the result will be [ 'x', 'Y' ]
    
    if columns = [ NAME,  DATE,  WATER_VOL_RATE,  TYPE]
    and meaning = 'water_injection' 
    
    then the result will be ['WATER_VOL_RATE']

    '''
    
    #received a keyset: FIELD_KEYS for insntance
    if isinstance(meaning,list):
        key_set = [ key.upper() for key in meaning ]  
        i = list(  set(cols).intersection( set(key_set) ) )
        
        
        if any(i): 
            return i 
        
        else:
            return [] 
        
    
    #if it is not a list, it is a word that we need to find out what keyset it belongs to.
    for key_set in ALL_KEYWORDS:

        if meaning in key_set or meaning.upper() in key_set or  meaning.lower() in key_set:
            i = list(  set(cols).intersection( set(key_set) ) )
            if any(i): return i 
            
        k = [ w.upper() for w in key_set]
        if meaning in k or meaning.upper() in k or  meaning.lower() in k:
            i = list(  set(cols).intersection( set( k )))
            if any(i):return  i 
            
        k = [ w.lower() for w in key_set]
        if meaning in k or meaning.upper() in k or  meaning.lower() in k:
            i = list(  set(cols).intersection( set( k )))
            if any(i):return  i 
            
    return []

optimizers_name_map ={'auto': "Nelder-Mead",
        "nelder-mead" : "Nelder-Mead",
        "neldermead" : "Nelder-Mead",
        "Nelder-Mead" : "Nelder-Mead",
                                    
        "powell" : "Powell",
        "Powell" : "Powell",
                                    
        "cg" : "CG",
        "bfgs" : "BFGS",
        "newtoncg" : "Newton-CG",
        "l-bfgs-b" : "L-BFGS-B",
        "lbfgsb" : "L-BFGS-B",
        
        "tnc" : "TNC",
        "TNC" : "TNC",
        "newton-cg" : "Newton-CG",
                                                  
        "cobyla" : "COBYLA", 
        "slsqp" : "SLSQP"
                     
                     }
       


    
    