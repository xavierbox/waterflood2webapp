#from __future__ import annotations
import math 
import pandas as pd, numpy as np, json  
from scipy.spatial import cKDTree

from wf_lib2.crm_definitions import * 
from wf_lib2.data.crm_pattern import CRMPattern
from wf_lib2.data.crm_data_utils   import * 

from  pydantic import BaseModel, Field, ConfigDict 

class CRMDataset:
    '''
    A class to represent a CRM dataset containing injection, production, and well location data.

    This class manages three main DataFrames: `injectors_df`, `producers_df`, and `locations_df`. It
    provides methods to manipulate the data, perform checks, slice data by dates and coordinates, 
    calculate well distances, and more.
    
    There three datasets can be accessed via public properties of the CRMDataset 
    and manipulated like any other pandas dataframe.
    
    The dataset oibject also provides a number of methods to manipulate the data, such as 
    filtering out wells, slicing data by well location, region, time, etc. The dataset provides
    methods to fetch the well names, copy data from another dataset, extract sectors, etc.

    As any other object in the library, the CRMDataset contains two methods that will produce 
    an example dataset (see below generate_default_multiwell_dataset and generate_default_dataset).
     
    Attributes:
        injectors_df (pd.DataFrame): DataFrame containing injector well data.
        producers_df (pd.DataFrame): DataFrame containing producer well data.
        locations_df (pd.DataFrame): DataFrame containing well location data (X, Y coordinates).
        events_df (pd.DataFrame): DataFrame for event data (optional).
        distances_df (pd.DataFrame): DataFrame containing well-to-well distances (optional).
        name (str): Name of the dataset (optional).
        
    '''
    def __init__(self):
        '''
        Initializes an empty CRMDataset instance.
        All attributes are set to None by default.
        '''
        self.injectors_df = None 
        self.producers_df = None 
        self.locations_df = None 
        self.events_df    = None 
        self.distances_df = None 
        self.name = None 
        
    @staticmethod
    def generate_default_multiwell_dataset(input_config: dict = None):
        '''
        Generates a default multiwell dataset based on the provided input configuration.

        Args:
            input_config (dict, optional): Configuration for dataset generation.
            
            For one single well, the input config is as follows.  
            input_config = {
                'days': 350,
                'allocation': [0.60,0.50, 0.4,0.3], #num injectors, each element is a producer-injector pair   
                'tau': 16.43 , #one producer 
                'dt': 1.0, 
                'inj_noise_level': 0.0000050, 
                'injectors': [ {'max_rate': 0.40e3, 'min_rate': 0.25e3, 'internal_length':4, 'location':  (1000,0) }
                                ,{'max_rate': 0.3e3, 'min_rate': 0.15e3, 'internal_length':8, 'location' :  (0,1000)},
                                {'max_rate': 0.4e3, 'min_rate': 0.1e3, 'internal_length':8, 'location' :  (-1000,0)},
                                {'max_rate': 0.23e3, 'min_rate': 0.15e3, 'internal_length':12, 'location':  (0,-1000)}
                                
                                ],
                'prod_noise_level': 0.000008, 
                'prod_outlier_freq': 0.000008 ,
                'producer_location' : (0,0),
                'primary_production': {'qo': 0.8e3, 'taup':13.5}
            }  

        Returns:
            CRMDataset: A new CRMDataset instance with default multiwell data.
        '''
        return CRMDataset._generate_dataset(input_config, CRMPattern.generate_default_multiwell_pattern)

    @staticmethod
    def generate_default_dataset(input_config: dict = None):
        '''
        Generates a default dataset based on the provided input configuration.

        Args:
            input_config (dict, optional): Configuration for dataset generation.

        Returns:
            CRMDataset: A new CRMDataset instance with default data.
        '''
        return CRMDataset._generate_dataset(input_config, CRMPattern.generate_default_pattern)

    def check_dataset( self ):
        '''
        Checks the consistency and completeness of the dataset.
        Validates the presence of required columns, well names, and non-negative values.
        Also checks for time gaps and converts the dataset to a pattern representation.

        Returns:
            list: A list of error messages if issues are found; an empty list otherwise.
        '''
       
        
        def check_date_column(df, table_name, errors, importance='critical'):
            if df.index.name != DATE_KEYS[0] and len(find_columns(df, DATE_KEYS)) == 0:
                
                error = f'{table_name}: Date column was not found. The name of the column missing is one of these: {",".join(DATE_KEYS)}'
                errors.append( (error, importance) )
                return False
            return True  
        
        def check_required( table_name, df, keys, errors, importance='critical' ):
            for key in keys:
                if len( find_columns(df, key) ) == 0:
                    error = f'{table_name} table: {key[0]} column was not found. '  
                    errors.append( (error, importance) )   
                    return False
            return True 
        
        def _check_if_time_gaps( df:pd.DataFrame, sampling_frequency ='D' )->bool:
                
            #if sampling_frequency != 'D': 
            #    #print('If the frequency isnt daily, time-gaps cant be checked')
                #print('unless for each date, the day is the last one of the month ("28,30,31,...)')
            #    return False
                
            
            
            DATE = DATE_KEYS[0]

            if df.index.name == DATE:
                #print('Date is index')
                SUBZONE_COL = find_column( df, SUBZONE_KEYS )
                if SUBZONE_COL:
                    for s in df[SUBZONE_COL].unique():
                        xdf = df[ df[SUBZONE_COL] == s ]
                        min_date, max_date = min(xdf.index),max(xdf.index)
                        day_range = pd.date_range( min_date, max_date, freq = sampling_frequency)
                        if len(day_range) != xdf.shape[0]: 
                            return True 
                    return False
                
                min_date, max_date = min(df.index),max(df.index)
                day_range = pd.date_range( min_date, max_date, freq = sampling_frequency)
                if len(day_range) != df.shape[0]: 
                    return True 
                else:
                    return False

            elif DATE in df.columns:
                
                SUBZONE_COL = find_column( df, SUBZONE_KEYS )
                if SUBZONE_COL:
                    for s in df[SUBZONE_COL].unique():
                        xdf = df[ df[SUBZONE_COL] == s ]
                        min_date, max_date = min(xdf[DATE]),max(xdf[DATE])
                        day_range = pd.date_range( min_date, max_date, freq = sampling_frequency)
                        #print( len(day_range),xdf.shape )
                        if abs(len(day_range) - xdf.shape[0])>1: 
                            
                            #print(xdf)
                            #print(xdf['NAME'].unique())
                            
                            return True 
                    return False
                        
             
                min_date, max_date = min(df[DATE]),max(df[DATE])
                day_range = pd.date_range( min_date, max_date, freq = sampling_frequency, closed='left')
                if abs(len(day_range) - df.shape[0]) > 1: 
                    return True 
                else:
                    return False 
                
            raise ValueError('DATE column or index not found')
                
        crm_dataset = self 
        unknown_colums = [] 
     

        
        errors = []
        warnings = [] 
        checks_passed = [ ]
        injector_names, producer_names = None, None 
        inj, prd, loc = crm_dataset.injectors_df, crm_dataset.producers_df,crm_dataset.locations_df  
        
        #report unknown columns  as a warning 
        ALL_KEYWORDS_flat = [ key for key_set in ALL_KEYWORDS for key in key_set   ]
        unknown_colums.extend( [ key for key in inj.columns if not key in ALL_KEYWORDS_flat ] )
        unknown_colums.extend( [ key for key in prd.columns if not key in ALL_KEYWORDS_flat ] )    
        unknown_colums.extend( [ key for key in loc.columns if not key in ALL_KEYWORDS_flat ] )    
        unknown_colums = list( set( unknown_colums ) )
        
        for unknown in unknown_colums:
            warnings.append( (f'Unknown column {unknown} in the dataset', 'warning') )
        
        
        #ALL_KEYWORDS_flat = [ key for key_set in ALL_KEYWORDS for key in key_set   ]
        #for key, columns in self.get_column_names().items():
        #    temp  = [ col for col in columns if not col in ALL_KEYWORDS_flat]
        #    unknown_columns.append( temp ) 
        #print( unknown_columns )
        
        
        # When creating it, some missing columns ar given default values 
        # This simplifies the multi-zone and multi-reservoir handling later 
        dfs = [ inj, prd, loc ]
        x = ['injectors', 'producers']
        for df in dfs: 
            if not find_column( df, ZONE_KEYS ):
                df[ZONE_KEYS[0]]='Unique'
            if not find_column( df, SUBZONE_KEYS ):
                df[SUBZONE_KEYS[0]]='Unique'
            if not find_column( df, SECTOR_KEYS ):
                df[SECTOR_KEYS[0]] = 0
            if not find_column( df, RESERVOIR_KEYS ):
                df[RESERVOIR_KEYS[0]] = 'Unique'                
           
        
        #there are REQUIRED columns in each dataset table 
        location_required_keys   = NAME_KEYS, X_KEYS, Y_KEYS
        importance = 'critical'
        check_required('Locations', loc, location_required_keys, errors ,importance )
        
        production_required_keys =  NAME_KEYS,WATER_PRODUCTION_KEYS, GAS_PRODUCTION_KEYS, OIL_PRODUCTION_KEYS, LIQUID_PRODUCTION_KEYS       
        check_required('Producers', prd, production_required_keys, errors,importance )
                
        injection_required_keys =  NAME_KEYS,WATER_INJECTION_KEYS      
        check_required('Injectors', inj, injection_required_keys, errors,importance )
               
        # any error up to here is critical 
        if len( errors ) > 0:
            return errors, warnings, checks_passed  
                         
        #dates are special, they could be an index or a column
        dates_there = check_date_column(prd, 'Producers', errors) & check_date_column(inj, 'Injectors', errors)
        if not dates_there:
            return errors, warnings, checks_passed   
        
        checks_passed.append( 'Required columns present in the dataset' )
     
        #key columns must have the same name in all the three tables.
        if not (find_column(loc,NAME_KEYS) == find_column(inj,NAME_KEYS) == find_column(prd,NAME_KEYS)):
            errors.append( ('The NAME column is not the same in all tables', importance) )
        if not (find_column(inj,DATE_KEYS) == find_column(prd,DATE_KEYS)):
            errors.append( ('The DATE column is not the same in the injectors and producers tables', importance) )
        if not (find_column(loc,ZONE_KEYS) == find_column(inj,ZONE_KEYS) == find_column(prd,ZONE_KEYS)):
            errors.append( ('The ZONE column is not the same in all tables', importance) )
        if not (find_column(loc,SUBZONE_KEYS) == find_column(inj,SUBZONE_KEYS) == find_column(prd,SUBZONE_KEYS)):
            errors.append( ('The SUBZONE column is not the same in all tables', importance) )
        if not (find_column(loc,SECTOR_KEYS) == find_column(inj,SECTOR_KEYS) == find_column(prd,SECTOR_KEYS)):  
            errors.append( ('The SECTOR column is not the same in all tables', importance) )
                
        if len(errors) > 0:
           
            errors.append( ('Key columns are present but have different names in across the tables', importance) )
            return errors, warnings, checks_passed  
                
        checks_passed.append( 'Key columns have the same name in all the tables' )
     


        # well names must be there in all tables and the methods to retieve them must work 
        try:
            #these use the producers_df and injectors_df tables 
            producer_names = set(crm_dataset.producer_names) 
            injector_names = set(crm_dataset.injector_names) 
            
        except Exception as e:
             error = f'Cannot fetch the producer names or injector names. Internal methods failed due to an unknown reason'
             errors.append( (error, 'critical')) 
             return errors, warnings, checks_passed  
         
        try:
            
            col = find_column(loc,NAME_KEYS)
            location_names = set(loc[col].unique())
        
        except Exception as e:
             errors.append((f'Failed to fetch well names in the locations table due to an unknown reason', importance))
             return errors, warnings, checks_passed  
         
        #every injector,producer must have a location
        if injector_names.issubset( location_names ) is False:
            errors.append(('The location for all injectors is not available in the locations table',importance))
        if producer_names.issubset( location_names ) is False:
            errors.append(('The location for all producers is not available in the locations table',importance))

        #now it becomes tricky, because the locations must be known for each subzone.
        #each subzone in the producers and locations must also be in the locations table 
        temp_dfs = [prd,inj]
        WELL_TYPE_COL = find_column( loc, WELL_TYPE )
        NAME_COL = find_column( loc, NAME_KEYS )
        names = ['producer','injector']
        for n, tdf in enumerate(temp_dfs):
            
            SUBZONE_COL = find_column( tdf, SUBZONE_KEYS )
            for subzone in tdf[SUBZONE_COL].unique():

                tmp_prd = tdf[ tdf[SUBZONE_COL] == subzone ]
                tmp_loc = loc[ (loc[SUBZONE_COL] == subzone) & (loc[WELL_TYPE_COL].str.lower()==names[n])]
                tmp_names = set(tmp_prd[NAME_COL].unique())
                loc_names = set(tmp_loc[NAME_COL].unique())
                if tmp_names.issubset( loc_names ) is False:
                    error = f'The location for all {names[n]}s in {subzone} is not available in the locations table'
                    errors.append((error,importance))
                    
         
         
        checks_passed.append( 'Well locations found for all listed producers and injectors' )
     
 
         
        try:
            letter   = self.mode_sampling_frequency()
            checks_passed.append( 'Sampling frequency appears to be ' + letter )
            if not letter == 'D': 
                print('If the frequency isnt daily, time-gaps cant be checked in this version')
                
            else:
                # checking for time-gaps 
                NAME_COL = find_column( prd, NAME_KEYS )
            
                for producer_name in producer_names:
                    df1 = prd[ prd[NAME_COL] == producer_name ]
                    if _check_if_time_gaps(df1, letter):
                        errors.append(('There are time-gaps in the producers data', importance))
                        #raise ValueError('Time gaps found for producer ' + producer_name) 
                        break 
                
                            
                for injector_name in injector_names:
                    df2 = inj[ inj[NAME_COL] == injector_name ]
                    if _check_if_time_gaps(df2, letter):
                        errors.append(('There are time-gaps in the injectors data', importance))
                   #raise ValueError('Time gaps found for injector ' + injector_name) 
                        break 
                
                if len(errors) > 0:
                     return errors, warnings, checks_passed  
                 
        except Exception as e:
             errors.append('Unexpected error when checking for time-gaps or sampling frequency')
             errors.append( (str(e),importance  ) )
             
             return errors, warnings, checks_passed  
         
        checks_passed.append( 'No time-gaps found' )
             
                    
        # some columns must have strickly possitive values 
        raise_error = False 
        col = find_column(inj,WATER_INJECTION_KEYS) 
        negative_count = (inj[col] < 0).sum()
        if negative_count > 0:
            errors.append(('Negative values found in column ' + col + ' in the injectors table', importance))
            raise_error = True 
                
        cols = find_columns(prd,WATER_PRODUCTION_KEYS)[0],\
               find_columns(prd,LIQUID_PRODUCTION_KEYS)[0],\
               find_columns(prd,GAS_PRODUCTION_KEYS)[0],\
               find_columns(prd,OIL_PRODUCTION_KEYS)[0]
                
        for col in cols:
            negative_count = (prd[col] < -0.0000001).sum()
            if negative_count > 0:
                errors.append(('Negative values found in column ' + col + ' in the producers table',importance))
                raise_error = True 
                    
        if raise_error:
            return errors, warnings, checks_passed   

        checks_passed.append( 'Not found negative rates' )
     
     
 
        #the dataset needs to be convertible to a pattern
        try:
            print('checking if a pattern can be created. This might take some time...')
            num_wells = len(crm_dataset.injector_names + crm_dataset.producer_names)
            print('num wells', num_wells )
            if num_wells < 100:
                p = crm_dataset.get_pattern(fix_time_gaps=False, fill_nan = np.nan)
            else:
                print('bypassing the check beause there are too many wells')
            #water_inj, liquid_prod, water_prod, gas_prod, oil_prod = p.water_injection, p.liquid_production, p.water_production, p.gas_production,p.oil_production 
        
            #names  = ['Water injection','Liquid production', 'Water production','Gas production','Oil production']
            #tables = [water_inj, liquid_prod, water_prod, gas_prod, oil_prod]
            
            #for n, table in enumerate( tables ) :
            #    if check_if_time_gaps( table ) is True:
            #        errors.append('There are time gaps in the table: ' + names[n] )
        
        except Exception as e:
            errors.append(('The dataset cannot be converted to a pattern representaion. Potentially, some data is missing or there are  time gaps ', importance))
            errors.append(('The error reported was ' + str(e), importance))
            return errors, warnings, checks_passed  

     
        checks_passed.append( 'Dataset can be converted to a pattern' )
     
   
     
        return errors, warnings, checks_passed   
               
    def get_column_names( self )->dict:
        '''
        Retrieves the column names of the DataFrames in the dataset.

        Returns:
            dict: A dictionary with keys ('injectors', 'producers', 'locations') and values as 
            lists of column names from the respective DataFrames.
        '''
        
        d = {} 
        
        if self.injectors_df is not None: d['injectors'] = self.injectors_df.columns.tolist()
        if self.producers_df is not None: d['producers'] = self.producers_df.columns.tolist()
        if self.locations_df is not None: d['locations'] = self.locations_df.columns.tolist()
        
        return d 
                    
    def copy_from(self, other) -> None:
        '''
        Copies data from another CRMDataset instance into this instance.

        Args:
            other (CRMDataset): The source dataset to copy data from.
        '''
        self.injectors_df = other.injectors_df.copy() if other.injectors_df is not None else None
        self.producers_df = other.producers_df.copy() if other.producers_df is not None else None
        self.locations_df = other.locations_df.copy() if other.locations_df is not None else None
        self.events_df = other.events_df.copy() if other.events_df is not None else None
        self.distances_df = other.distances_df.copy() if other.distances_df is not None else None
        self.name = other.name if other.name is not None else None
                             
    def __getitem__( self, key:str )->pd.DataFrame:
        '''
        Retrieves a specific DataFrame or column based on the provided key.

        Args:
            key (str): The key indicating which DataFrame or column to retrieve.

        Returns:
            pd.DataFrame: The corresponding DataFrame or column data.
        '''
        if key.lower() in ['producers', 'producers_df']: return self.producers_df 
        if key.lower() in ['locations', 'locations_df']: return self.locations_df
        if key.lower() in ['injectors', 'injectors_df']: return self.injectors_df
            
    
        if key.lower() in ['distance', 'distances', 'distance_df']:
            if self.distances_df is None: self.get_distances()
            return self.distances_df 
 
        
        def _find( KNOWN_KEYWORDS ):
            keys = { }
            
            #assume that for all tables the name of the date column and well name column is the same 
            DATE, NAME = find_columns(self.injectors_df, DATE_KEYS), find_columns(self.injectors_df, NAME_KEYS)[0] 
            
            if len(DATE) > 0: 
                DATE = [DATE[0]] 
            else: DATE = []
            
            for column in self.injectors_df: keys[ column ] = self.injectors_df
            for column in self.producers_df: keys[ column ] = self.producers_df
            for word in KNOWN_KEYWORDS: 
    
                #this works if the DATE is a column or  an index
                if word in keys: return keys[word][ DATE + [NAME, word] ]  
                if word.lower() in keys: return  keys[word.lower()][ DATE + [ NAME,word.lower()] ]
                if word.upper() in keys: return  keys[word.upper()][ DATE + [ NAME,word.upper()] ]
                
                
            return None 
        
    
        for key_set in RATE_KEYWORDS:
            if key in key_set: return _find( key_set )
          
        return None 
    
    def get_producer_injectors_distances_flat( self, max_distance:float = 2500.00 ) -> list:
    
        df = self.locations_df
        WELL_TYPE = find_column( df.columns, WELL_TYPE_KEYS)
        NAME = find_column( df.columns, NAME_KEYS)
        X = find_column( df.columns, X_KEYS)
        Y = find_column( df.columns, Y_KEYS)
        
        
        injectors = df[df[WELL_TYPE].str.lower()  == "injector"].reset_index(drop=True)
        producers = df[df[WELL_TYPE].str.lower()  == "producer"].reset_index(drop=True)

        # Split DataFrame
        injectors = df[df[WELL_TYPE].str.lower()  == "injector"].reset_index(drop=True)
        producers = df[df[WELL_TYPE].str.lower()  == "producer"].reset_index(drop=True)

        # Extract names and coordinates
        injector_coords = injectors[[X, Y]].to_numpy()
        producer_coords = producers[[X, Y]].to_numpy()

        injector_names = injectors[NAME].to_numpy()
        producer_names = producers[NAME].to_numpy()

        # Build KDTree for fast spatial lookup
        tree = cKDTree(injector_coords)

        # Query all producers for neighbors within max_distance
        result = []
        for i, (p_name, p_coord) in enumerate(zip(producer_names, producer_coords)):
            indices = tree.query_ball_point(p_coord, r=max_distance)
            for j in indices:
                i_name = injector_names[j]
                i_coord = injector_coords[j]
                distance = np.hypot(p_coord[0] - i_coord[0], p_coord[1] - i_coord[1])
                result.append({
                    "producer": p_name,
                    "injector": i_name,
                    "distance": distance
                })
        return result    
            
        '''
        df = self['distance']
        if df is None: return None
           
        flats =  [ {"producer": producer, "injector": injector, "distance": df.loc[producer, injector]  }
        for producer in df.index
        for injector in df.columns if df.loc[producer, injector] < max_distance
        ]
        
        return flats
        '''
              
    def get_all_distances_flat(self, max_distance:float = 2500.00 ) -> list:
        
        df=  self.locations_df 
        # Build coordinate array and name list
        coords = df[['X', 'Y']].to_numpy()
        names = df['NAME'].to_numpy()

        # types map for quick search later
        well_type_dict = {} 
        for name in self.injector_names: 
            well_type_dict[name] = 'Injector'
        for name in self.producer_names:
            well_type_dict[name] = 'Producer'


        # Create KDTree, very fast unique pairs. 
        tree = cKDTree(coords)
        max_distance = 1500
        pairs = tree.query_pairs(r=max_distance, output_type='set')

        # Build bidirectional list
        well_pairs = []
        for i, j in pairs:
            for a, b in [(i, j), (j, i)]:
                name1, name2 = names[a], names[b]
                type1, type2 = well_type_dict[name1], well_type_dict[name2]
                distance = np.linalg.norm(coords[a] - coords[b])

                well_pairs.append({
                    'name1': name1,
                    'type1': type1,
                    'name2': name2,
                    'type2': type2,
                    'distance': distance
                })
        
        
        return well_pairs 
    
        '''
        Returns an array of these items: 
        [{
        "well_1": "AG4353",
        "type_1": "Producer",
        "well_2": "I32-001",
        "type_2": "Injector",
        "distance": 1000.0
        }, {} ] 
        '''
        
        xx = self.get_producer_injectors_distances_flat( max_distance )
            
         
        def to_bidirectional(data):
            result = []
            for entry in data:
                p = entry['producer']
                i = entry['injector']
                d = entry['distance']
                result.append({'well1': p, 'well2': i, 'distance': d})
                result.append({'well1': i, 'well2': p, 'distance': d})
            return result
        
        return to_bidirectional(xx)
         
        
    
        df = self.locations_df
        WELL_TYPE = find_column( df.columns, WELL_TYPE_KEYS)
        NAME = find_column( df.columns, NAME_KEYS)
        X = find_column( df.columns, X_KEYS)
        Y = find_column( df.columns, Y_KEYS)
        
          
          
        well_coords = df[[X, Y]].to_numpy()
        well_names = df[NAME].to_numpy()
        well_types = df[WELL_TYPE].to_numpy()

        # Build KDTree on all wells
        tree = cKDTree(well_coords)

        # Query: find all well pairs within max_distance
        result = []
        for i, (name_i, coord_i, type_i) in enumerate(zip(well_names, well_coords, well_types)):
            nearby_indices = tree.query_ball_point(coord_i, r=max_distance)
            for j in nearby_indices:
                if j <= i:
                    continue  # avoid self and duplicate pairs
                name_j = well_names[j]
                type_j = well_types[j]
                coord_j = well_coords[j]
                distance = np.hypot(*(coord_i - coord_j))
                result.append({
                    "well_1": name_i,
                    "type_1": type_i,
                    "well_2": name_j,
                    "type_2": type_j,
                    "distance": distance
                })
                
        return result# to_bidirectional(result)
    
                
              
    def get_distances( self )->None:
        '''
        Helper method to compute the inter-well distances. 
        These are computed based on the location data stored in the dataset.
        
        The client is not expected to call this method. It will be called behind 
        the scenes when needed. However, it is exposed here (without the underscores)
        for debugging purposes. 
        
        After this method is called, the field distance (or distances or any key 
        defined in the crm_definitions) can be used to recover the distances dataframe.
        
        Example of use.
        
        ...
        dataset['distance'] #calls this method if needed and returns a dataframe
        
        '''

        self.distances_df = None 
        if self.locations_df is None: return None 
        if self.producers_df is None: return None 
        if self.injectors_df is None: return None       


        self.distances_df = None 
        prod_loc = self.producer_locations()
        inj_loc  = self.injector_locations()

        df = pd.DataFrame( {}, columns =  ['Producer'] + self.injector_names )
        df['Producer'] = self.producer_names 
        df.set_index( 'Producer', drop=True, inplace= True)


 
        NAME = NAME_KEYS[0]
        for index, row in prod_loc.iterrows():
            name,x,y = row[NAME], row['X'], row['Y']



            for index2, row2 in inj_loc.iterrows():
                name2,x2,y2 = row2[NAME], row2['X'], row2['Y']
                d = ((x2 - x)**2 + (y2-y)**2)**0.5

                df.loc[name,name2] = d 
                    
        self.distances_df = df 
           
    def _slice_dates_dataset( self, df,  DATE1: str, DATE2: str):
        """
        Slices the dataset for rows between the specified dates (DATE1, DATE2).
        The DATE column can either be the index or a column in the DataFrame.
        
        Args:
            DATE1 (str): The start date as a string (inclusive).
            DATE2 (str): The end date as a string (inclusive).
            
        Note:
        if DATE is the index, it MUST be of the type: DatetimeIndex (use pd.to_datetime)
        
        Returns:
            CRMDataset 
        """
        DATE1 = pd.to_datetime(DATE1)
        DATE2 = pd.to_datetime(DATE2)
    
        # Check if DATE is the index or a column
        if df.index.name in DATE_KEYS or isinstance(df.index, pd.DatetimeIndex):
            # If DATE is the index, slice using index
            date_index = df.index
        elif any(col in DATE_KEYS for col in df.columns):
            # If any column name matches a value in DATE_KEYS, use that column for slicing
            # Find the first matching column name in DATE_KEYS
            date_column = next(col for col in df.columns if col in DATE_KEYS)
            date_index = df[date_column]
        else:
            raise ValueError(f"The DataFrame must have a 'DATE' column or the index must be one of {NAME_KEYS}.")

        # Convert the dates to pandas datetime objects
        DATE1 = pd.to_datetime(DATE1)
        DATE2 = pd.to_datetime(DATE2)
        
        # Slice based on the index (date column or index)
        sliced_df = df[(date_index >= DATE1) & (date_index <= DATE2)].copy()

        return sliced_df

    def slice_dates_dataset( self, date1:str, date2:str ):
        '''
        Slices the dataset for data within the specified date range.

        Args:
            date1 (str): The start date (inclusive).
            date2 (str): The end date (inclusive).

        Returns:
            CRMDataset: A new dataset instance containing sliced data.
        '''
        inj_sliced = self._slice_dates_dataset( self.injectors_df,date1,date2)
        prd_sliced = self._slice_dates_dataset( self.producers_df,date1,date2)
            
 
        NAME = NAME_KEYS[0]
        names = list( set( inj_sliced[NAME]))
        names.extend( list( set( prd_sliced[NAME])))
        locs = self.locations_df[ self.locations_df[NAME].isin(names) ]

        return CRMDataset.instance( inj_sliced, prd_sliced, locs, self.name ) 

    def slice_coordinates_dataset( self, xlimits:tuple, ylimits:tuple ):
        '''
        Slices the dataset based on specified X and Y coordinate ranges.

        Args:
            xlimits (tuple): A tuple (x1, x2) defining the X-coordinate range.
            ylimits (tuple): A tuple (y1, y2) defining the Y-coordinate range.

        Returns:
            CRMDataset: A new dataset instance containing data within the coordinate range.
        '''
        
        x1,x2,y1,y2 = xlimits[0], xlimits[1], ylimits[0], ylimits[1]
        subset = self.locations_df[  (self.locations_df.X >= x1) 
                                   & (self.locations_df.X <= x2) 
                                   & (self.locations_df.Y >= y1) 
                                   & (self.locations_df.Y <= y2) 
                                  ]
        NAME = NAME_KEYS[0]
        return self.filter_by(NAME,subset[NAME].values)
      

    @staticmethod
    def instance(inj_df:pd.DataFrame = None, 
                 prod_df:pd.DataFrame = None, 
                 loc_df:pd.DataFrame=None, 
                 events_df:pd.DataFrame=None, 
                 name:str= None,
                 time_format = None):
        '''
        Creates a dataset based on the dataframes passed
        
        Args:
            inj_df  (DataFramet): The injectors dataframe.
            prod_df (DataFramet): The producers dataframe.
            loc_df  (DataFramet): The locations dataframe.
            events_df  (DataFrame): The events( optional )
            name  (string): The name property of the dataset (optional)
            time_format (string): Format in the saphe of '%d/%m/%Y' or similar to parse the DATE columns (optinal)
             
            
            
        Returns:
            CRMDataset: A new dataset instance containing sliced data.
        '''
        class DatasetInstanceTypes(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            
            inj_df:pd.DataFrame    
            prod_df:pd.DataFrame 
            loc_df:pd.DataFrame = Field(default = None, description = 'Optional table with Name, X, Y for each well')
                        
        types = DatasetInstanceTypes( inj_df= inj_df, prod_df=prod_df, loc_df = loc_df )
        
        ret = CRMDataset()
        ret.injectors_df = types.inj_df
        ret.producers_df = types.prod_df
        ret.locations_df = types.loc_df
        ret.events_df    = events_df
        ret.name = name 
        
        # When creating it, some missing columns ar given default values 
        # This implifies the multi-zone and multi-reservoir handling later 
        dfs = [ ret.injectors_df, ret.producers_df, ret.locations_df ]
        x = ['injectors', 'producers']
        for df in dfs: 
            if not find_column( df, ZONE_KEYS ):
                df[ZONE_KEYS[0]]='Unique'
            if not find_column( df, SUBZONE_KEYS ):
                df[SUBZONE_KEYS[0]]='Unique'
            if not find_column( df, SECTOR_KEYS ):
                df[SECTOR_KEYS[0]] = 0
            if not find_column( df, RESERVOIR_KEYS ):
                df[RESERVOIR_KEYS[0]] = 'Unique'                
             
      
        # if a time form at is passed.      
        if not time_format is None:
           
            print('time format passed', time_format)
         
            for n, df in enumerate([ ret.injectors_df,ret.producers_df]):
            
                date_column = find_column( df, DATE_KEYS )
                if date_column: 
                    df[ date_column] = pd.to_datetime(df[date_column], format=time_format)
                elif df.index.name.lower() in [ key.lower() for key in DATE_KEYS]: 
                    df.index = pd.to_datetime(df.index, format=time_format)
                else:
                    raise ValueError(f'Cannot create the dataset. DATE column not found in the {x[n]} table') 
            
        # try to guess the date format and use dayfirst or yearfirst 
        # keywords from the poducers data     
        else:
  
            for n,df in enumerate(dfs[0:2]):
                date_column = find_column( df, DATE_KEYS )
                sample_data = None 
               
                if date_column: 
                    sample_data = df[ date_column ]
                elif df.index.name and df.index.name.lower() in [ key.lower() for key in DATE_KEYS]: 
                    sample_data = df.index 
                else: 
                    raise ValueError(f'Cannot create the dataset. DATE column not found in the {x[n]} table')
            
         
            
            if not sample_data is None:
             
                dayfirst_dates_count     = pd.to_datetime(sample_data, dayfirst=True,  errors='coerce').notnull().sum()
                not_dayfirst_dates_count = pd.to_datetime(sample_data, dayfirst=False, errors='coerce').notnull().sum()
                print( dayfirst_dates_count, not_dayfirst_dates_count)
                
                # Compare parsing success
                dayfirst = True if dayfirst_dates_count > not_dayfirst_dates_count else False
                print('Tying to guess the DATE format. dayforst ?',dayfirst)
                for df in [ ret.injectors_df, ret.producers_df ]:
                    if date_column:
                        df[ date_column ] = pd.to_datetime( df[ date_column ], dayfirst =dayfirst ) 
                    else:
                        df.index = pd.to_datetime(df.index, dayfirst =dayfirst )
            
       
        
        return ret 


    @staticmethod
    def from_pattern( pattern:CRMPattern ):
        
        inj = pattern.water_injection
        dates = inj.index#.values.tolist()

        DATE   = DATE_KEYS[0]
        NAME   = NAME_KEYS[0]
        FIELD  = FIELD_KEYS[0]
        REGION = REGION_KEYS[0]


        injectors_df = pd.DataFrame({}, columns = [DATE,NAME,WATER_INJECTION_KEYS[0] ])
        for well_name in inj.columns:
            tmp = pd.DataFrame({} )
            tmp[DATE] = dates 
            tmp[NAME] = well_name 
            tmp[WATER_INJECTION_KEYS[0]] = inj[well_name].values
            tmp[FIELD] = well_name[0:3]
            tmp[REGION] = well_name[-2:]
            injectors_df = pd.concat( [injectors_df, tmp], axis = 0 )


        liquid   =  get_column_for_meaning( pattern.keys(), LIQUID_PRODUCTION_KEYS[0])    
        oil      =  get_column_for_meaning( pattern.keys(), OIL_PRODUCTION_KEYS[0])    
        water    =  get_column_for_meaning( pattern.keys(), WATER_PRODUCTION_KEYS[0])    
        gas      =  get_column_for_meaning( pattern.keys(), GAS_PRODUCTION_KEYS[0])    
        pressure =  get_column_for_meaning( pattern.keys(), PRODUCER_PRESSURE_KEYS[0])    

        cols = [ liquid, oil, water, gas, pressure]
        cols = [ col[0] for col in cols if len(col) > 0 ]

        tables = [] 
        for i,col in enumerate( cols ):

            liquid = pattern[col]
            df = pd.DataFrame( {} )
            dates = liquid.index
            for well_name in sorted(liquid.columns):
                tmp = pd.DataFrame({} )# 

                if i == 0 :
                    tmp[DATE] = dates 
                    tmp[NAME] = well_name 


                tmp[ col ] = liquid[well_name].values
                df = pd.concat( [df, tmp], axis = 0 )

            tables.append( df.copy() )

        producers_df = pd.concat( tables, axis = 1)
        producers_df[FIELD]  = [name[0:3] for name in producers_df[NAME]]
        producers_df[REGION] = [name[-2:] for name in producers_df[NAME]]
               
        return CRMDataset.instance( injectors_df, producers_df, pattern['locations'])
        
    """
    #optional properties in the datasets. REGION, FIELD, ZONE, SUBZONE
    def _list_properties( self, key ):
  
        r1 = set(self.injectors_df[key].values) if key in self.injectors_df else set(['UNIQUE'])
        r2 = set(self.producers_df[key].values) if key in self.producers_df else set(['UNIQUE'])
        return list(r1.union( r2 ))
    
    @property
    def regions( self )->list:
        key=REGION_KEYS[0]
        return self._list_properties( key )
    
    @property
    def fields( self )->list:
        key=FIELD_KEYS[0]
        return self._list_properties( key )
       
    @property
    def reservoirs( self )->list:
        key=RESERVOIR_KEYS[0]
        return self._list_properties( key )
    
    @property
    def zones( self )->list:
        key=ZONE_KEYS[0]
        return self._list_properties( key )
    
       
    @property
    def rmus( self )->list:
        key=SUBZONE_KEYS[0]
        return self._list_properties( key )
    """      
          
    @property
    def injector_names(self)->list:
        '''
        Returns:
            list of the injector names 
        '''
        
        if isinstance( self.injectors_df, pd.DataFrame):
            col = get_column_for_meaning( self.injectors_df.columns, NAME_KEYS[0])[0]
            return list( self.injectors_df[col].unique() )
        return None 
  
    @property
    def producer_names(self)->list:
        '''
        Returns:
            list of the producer names 
        '''
        
        if isinstance( self.producers_df, pd.DataFrame):
            col = get_column_for_meaning( self.producers_df.columns, NAME_KEYS[0])[0]
            return list( self.producers_df[col].unique() )
        return None 
         
    def injector_locations( self )->pd.DataFrame:  
        '''
        Returns:
            Dataframe with injector locations 
        '''
        
        s = self.locations_df
        injs =  s[ s[NAME_KEYS[0]].isin( self.injector_names)]
        return injs.copy()
        
    def producer_locations( self )->pd.DataFrame:
        '''
        Returns:
            Dataframe with producer locations 
        '''
        
        s = self.locations_df
        prods = s[ s[NAME_KEYS[0]].isin( self.producer_names)]
        return prods.copy()
        
    def filter_by( self, column_name, values,negate = False ):
        
        if not negate:
            inj = self.injectors_df[ self.injectors_df[column_name].isin(values)].copy()
            pro = self.producers_df[ self.producers_df[column_name].isin(values)].copy()
            loc = self.locations_df[ self.locations_df[column_name].isin(values)].copy()
        else: 
            inj = self.injectors_df[ ~self.injectors_df[column_name].isin(values)].copy()
            pro = self.producers_df[ ~self.producers_df[column_name].isin(values)].copy()
            loc = self.locations_df[ ~self.locations_df[column_name].isin(values)].copy()
        
        return CRMDataset().instance( inj,pro,loc)
           
    def get_pattern( self, fix_time_gaps = True, fill_nan = 0.0 ):
        '''
        This function converts the CRMDataset to a CRMPattern as the later can be used in 
        the simulations.
        The pattern extraction makes no assumptions on the connectivity between producers 
        and injectors but other modules of the library might. 
        In this function, all the injectors and all the producers are part of the returned 
        single pattern for this dataset (see also distance patterns)
        
            Exaple code:
            
            pattern = dataset.get_pattern()
            
            returns an instance of the class CRMPattern that can be fed directly to 
            CRM-P or CRM-IP
        '''
        def _aggregate_column( df, column_name, fill_nan = 0.0): #, keep_date = False):

            dfp = df.pivot_table(index = DATE_KEYS[0], columns = NAME_KEYS[0], values = column_name, fill_value = fill_nan)
            col_list=[DATE_KEYS[0]]
            col_list.extend(list(dfp))
            dfp[DATE_KEYS[0]]=dfp.index
            dfp = dfp[col_list]
            dfp.reset_index(inplace=True,drop=True)

            #we will always keep the date but if the option is there then: if not keep_date: dfp.drop( ['DATE'], axis=1,inplace=True)
            dfp.set_index(  DATE_KEYS[0] , drop = True, inplace = True )

            dfp.rename_axis(None, axis=1,inplace=True)
            dfp.fillna(value = fill_nan, axis = 0, inplace=True ) 
            return dfp 

        
        #known names for quantitites that are aggregatable in a dataset object 
        #these come from the crm_definitions 
        meanings = [WATER_INJECTION_KEYS,LIQUID_PRODUCTION_KEYS,OIL_PRODUCTION_KEYS,
                    GAS_PRODUCTION_KEYS,WATER_PRODUCTION_KEYS,PRODUCER_PRESSURE_KEYS,
                    #ZONE_KEYS, SUBZONE_KEYS,SECTOR_KEYS, WELL_TYPE
                   ]

        d = {}
        dfs = [ self.injectors_df, self.producers_df]
        #self.get_distances()

        for df in dfs:
            if df is None:
                continue 
            for column_name in df.columns:
                meaning = name_to_meaning( column_name, meanings )
                if meaning is not None:
                    table = _aggregate_column( df, column_name,fill_nan )
                    table.fillna( fill_nan, inplace=True)
                    d[ meaning ] = table#
                    #print( table.sort_values(by='DATE') )
                    #print() 
                    
                    
            
                    
        pattern = CRMPattern( d )
        pattern[DISTANCE_KEYS[0]] = self.distances_df
        pattern[LOCATION_KEYS[0]] = self.locations_df 
        frequency =  self.mode_sampling_frequency()

        if fix_time_gaps:
            frequency = self.mode_sampling_frequency()
            print('We have a fix-time gaps instruction')
            if frequency == 'D':
                fix_index_time_gaps_in_pattern( pattern, frequency )
            else:
                print('Cannot fix time-gaps for frequency ', frequency)
        
        
        #pattern=pattern
        return pattern 

    def get_distance_patterns( self, distance:float, fix_time_gaps = True, fill_nan=0.0 ):
       
        '''
        Patterns here is just a list of dictionaries. One item in the list per pattern 
        Each item contains the list of injectors and producer names. From that list, 
        we slice the dataset by names and call the get_pattern on it.
        
        Example code:
        
            patterns = dataset.get_distance_patterns( distance = 1500.00 )
            
            returns a list of patterns if any was found. 
        '''
        pattern_well_names = self._get_distance_patterns_helper( distance )

        to_return_patterns = [ ]
        for item in pattern_well_names:
            
            if any( item['producers'] ) and any( item['injectors'] ):
                names = item['producers'] + item['injectors']
                new_dataset = self.filter_by(NAME_KEYS[0], names )
                to_return_patterns.append(new_dataset.get_pattern(fix_time_gaps, fill_nan))
 
 
        return to_return_patterns

    def get_explicit_pattern( self, names):
        '''
        The method creates a pattern for simulation based only on well names 
        as those can be selected in a UI, for instance.
        '''
        new_dataset = self.filter_by(NAME_KEYS[0], names )
        new_dataset.get_distances()
        return new_dataset.get_pattern()
  
 
    @staticmethod
    def _generate_dataset(input_config, pattern_method):
        p = pattern_method(input_config)
        water_injection = WATER_INJECTION_KEYS[0]
        liquid_production = LIQUID_PRODUCTION_KEYS[0]

        inj, prd = p[water_injection], p[liquid_production]
        injectors_df, producers_df = None, None

        keys = [water_injection, liquid_production]
        for n in [0, 1]:
            x = inj if n == 0 else prd

            dfs = []
            for col in x.columns:
                key = keys[n]
                df = x[[col]].copy()
                df[NAME_KEYS[0]] = col
                df[key] = df[col]
                df.drop([col], inplace=True, axis=1)
                df.reset_index(inplace=True, drop=False)
                dfs.append(df.copy())

            if n == 0:
                injectors_df = pd.concat(dfs, axis=0)
            else:
                producers_df = pd.concat(dfs, axis=0)

 
        producers_df[WATER_PRODUCTION_KEYS[0]] = producers_df[ find_columns(producers_df,LIQUID_PRODUCTION_KEYS)[0]]
        producers_df[GAS_PRODUCTION_KEYS[0]] = 0.0 
        producers_df[OIL_PRODUCTION_KEYS[0]] = 0.0   
        
        injectors_df['DATE'] = pd.to_datetime( injectors_df['DATE']  )
        producers_df['DATE'] = pd.to_datetime( producers_df['DATE']  )
        
        dataset = CRMDataset.instance(injectors_df, producers_df, p.locations)         
        dataset.locations_df['TYPE'] = dataset.locations_df['NAME'].apply( lambda name: 'Injector' if name in dataset.injector_names else 'Producer' )
        return dataset

    '''
    def locations_summary( self ) ->dict:
        inj_names, prd_names, well_names = self.injector_names, self.producer_names, self.injector_names + self.producer_names
        num_injectors, num_producers, num_wells = len(inj_names), len(prd_names),len(inj_names) + len(prd_names) 

        FIELD='FIELD'
        f1 = self.injectors_df[FIELD].values if FIELD in self.injector_names else [ name[0:3] for name in self.injector_names]
        f2 = self.producers_df[FIELD].values if FIELD in self.producer_names else [ name[0:3] for name in self.producer_names]
        f1.extend(f2)


        REGION='REGION'
        r1 = self.injectors_df[REGION].values if REGION in self.injector_names else [ name[0:3] for name in self.injector_names]
        r2 = self.producers_df[REGION].values if REGION in self.producer_names else [ name[0:3] for name in self.producer_names]
        r1.extend(r2)
        

        d = dict(
        name = self.name if self.name is not None else 'Dataset', 
        injector_names = inj_names, producer_names = prd_names, well_names = inj_names + prd_names,
        num_injectors= len(inj_names), num_producer = len(prd_names),  num_wells = len(inj_names) + len(prd_names), 
        distances = self['distance'].to_dict(orient='index'), 
        fields = f1, 
        regions = r1, 
        injector_locations =  dict(x = self.injector_locations()['X'].tolist(), y = self.injector_locations()['Y'].tolist() ),
        producer_locations =  dict(x = self.producer_locations()['X'].tolist(), y = self.producer_locations()['Y'].tolist() )   
        
        )
  
        return d 
    

    def locations_summary_as_json( self )->str:

        class json_serialize(json.JSONEncoder):
            
            def default(banana, obj):
                if isinstance(obj, np.ndarray): 
                    if np.issubdtype(obj.dtype, np.datetime64): 
                        return [x.strftime("%Y-%m-%d") for x in pd.to_datetime(obj)] ##############obj ]
                    return obj.tolist()           
                    
                return json.JSONEncoder.default(banana, obj)

        summary_json = json.dumps( self.locations_summary() , cls=json_serialize)
        return summary_json


    def get_data_rates_summary( self ):#, filters:dict = None  ):

        """
        Returns a field summary and a well injection/production summary

        for field:

            field[Liquid] ={ values: [x1,x12....] Date: [d1,d2,....]
            field[Oil, W.Inj, Water] just as above. Note that datesmay not be the same

        for each fluid we also have 

            well_summary[fluid] = {  Date:[....], well_name1:[....], well_name2:[....], etc....}

        
        Filters could be 
        dates: [date1 (string), date2(string) ] in the format YYYY-MM-DD
        fields: [string, string.,...]
        regions: [string, string.,...]
        """

        field_summary = {}
        well_production = {}

        p = self.get_pattern() 
       
        dfs = {LIQUID_PRODUCTION_KEYS[0]:p.liquid_production,
               WATER_PRODUCTION_KEYS[0]:p.water_production, 
               OIL_PRODUCTION_KEYS[0]: p.oil_production, 
               WATER_INJECTION_KEYS[0]:p.water_injection 
              }
        
        field_summary['fluids'] = list( dfs.keys() )
        num_producers, num_injectors = len( self.producer_names),len( self.injector_names)
        field_summary['num_wells'] = num_producers + num_injectors
        field_summary['num_producers'] = num_producers  
        field_summary['num_injectors'] =   num_injectors
        field_summary['producer_names'] =   self.producer_names 
        field_summary['injector_names'] =   self.injector_names 

        well_production['producer_names'] =   self.producer_names 
        well_production['injector_names'] =   self.injector_names 

        
        
        for fluid_name, df in dfs.items():

            if df is None:
                continue 

            quantity_aggregated = df.sort_values(by='DATE').sum(axis=1) 
            field_summary[fluid_name]= {
            'values':quantity_aggregated.values,#.tolist()
            'Date':  df.sort_values(by='DATE').index.values                      
            }
            
            well_production[fluid_name]={} 
            well_production[fluid_name]['Date'] = df.index.values#.date#values
            for col in df.columns: 
                well_production[fluid_name][col]=df[col].values#tolist()




     
        return {'field_summary': field_summary, 'well_production': well_production }
        

    def get_data_rates_summary_as_json( self ):# add later filters:dict = None  ):

        class json_serialize(json.JSONEncoder):
            def default(banana, obj):
                if isinstance(obj, np.ndarray): 
                    if np.issubdtype(obj.dtype, np.datetime64): 
                        return [x.strftime("%Y-%m-%d") for x in pd.to_datetime(obj) ]
                    return obj.tolist()           
                
                return json.JSONEncoder.default(banana, obj)


        d = self.get_data_rates_summary(    )
        field_summary, well_production = d['field_summary'],d['well_production']
        
        fluids =  field_summary['fluids']
        for fluid in fluids:
            dates = field_summary[fluid]['Date'] 
            field_summary[fluid]['Date'] = np.datetime_as_string(dates, unit='D')
        
        #this could be field_summary['Date'] = np.datetime_as_string(field_summary['Date'], unit='D') #[x.strftime("%Y-%m-%d") for x in field_summary['Date'] ]
        for fluid in fluids:
            dates = well_production[fluid]['Date'] 
            well_production[fluid]['Date'] =  np.datetime_as_string(dates, unit='D')
            
        summary_json = json.dumps({'field_summary':field_summary,'well_production':well_production}, cls=json_serialize)
        
        return  summary_json
    ''' 

    def mode_sampling_frequency(self):
        """
        Compute the mode of the difference in the number of days between consecutive values in the 'DATE' column
        or index of the producers DataFrame.

        Returns: 
        - 'D' if closer to 1,
        - 'M' if closer to 30,
        - 'W' otherwise (closer to 7).
        
        """
        df = self.producers_df 
        # Check if DATE is in the columns or the index
        if 'DATE' in df.columns:
            date_series = pd.to_datetime(df['DATE'])
        elif df.index.name and df.index.name.upper() == 'DATE':
            date_series = pd.Series(df.index).astype('datetime64[ns]')
        else:
            raise ValueError("The DataFrame does not have a 'DATE' column or 'DATE' as an index.")
        
        
        # Calculate the differences in days between consecutive dates
        date_diffs = date_series.diff().dt.days.dropna()
        
        # Compute the mode of the differences
        # this would be something close to 1 (Daily) 7 (weekly) or 30 (monthly)
        mode_diff = date_diffs.mode().iloc[0] if not date_diffs.mode().empty else None
        
        #Returns:
        #- 'D' if closer to 1,
        #- 'M' if closer to 30,
        #- 'W' otherwise (closer to 7).
        #"""
        
        thresholds = [1, 7, 30]
        labels = ['D', 'W', 'M']

        # Find the index of the closest value in thresholds
        closest_index = min(range(len(thresholds)), key=lambda i: abs(thresholds[i] - mode_diff))

        return labels[closest_index]
        
        #return mode_diff
   
    def _get_distance_patterns_helper( self, distance_threshold):
        """
        Find patterns of producers and injectors based on a distance threshold.
        A pattern is a group of producers and injectors where each producer is
        within the distance threshold of all injectors in the same pattern.
        
        A producer can belong to only one pattern, but a pattern can contain multiple producers.

        Parameters:
        - distance_threshold: The maximum allowable distance between a producer and an injector to be in the same pattern.

        Returns:
        - A list of patterns, where each pattern is a dictionary containing a list of producer names and injector names.
        """
        
        # Initialize a list to hold the patterns
        patterns = []
        distances = self['distances']
        
        # Track which producers have been assigned to patterns
        assigned_producers = set()
        
        # Iterate over each producer
        for producer in distances.index:
            if producer in assigned_producers:
                continue  # Skip if the producer has already been assigned to a pattern
            
            # Find the injectors within the threshold distance for this producer
            within_threshold = distances.loc[producer] <= distance_threshold
            injectors_in_pattern = within_threshold[within_threshold].index.tolist()

            # Initialize the current pattern with this producer
            current_pattern = {'producers': [producer], 'injectors': injectors_in_pattern}
            assigned_producers.add(producer)
            
            # Try to add more producers to the current pattern
            for other_producer in distances.index:
                if other_producer in assigned_producers:
                    continue  # Skip if the producer has already been assigned to a pattern
                
                # Check if this producer can be added to the current pattern
                all_in_pattern = True
                for injector in injectors_in_pattern:
                    if distances.loc[other_producer, injector] > distance_threshold:
                        all_in_pattern = False
                        break
                
                # If the producer can be added to the pattern, add it
                if all_in_pattern:
                    current_pattern['producers'].append(other_producer)
                    assigned_producers.add(other_producer)
            
            # Add the final pattern to the list of patterns
            patterns.append(current_pattern)
        
        # Return the identified patterns
        return patterns
        
    def very_old_get_distance_patterns( self, distance:float,fix_time_gaps = True, fill_nan=0.0 ):
       
        '''
        Patterns here is just a list of dictionaries. One item in the list per pattern 
        Each item contains the list of injectors and producer names. From that list, 
        we slice the dataset by names and call the get_pattern on it.
        
        Example code:
        
            patterns = dataset.get_distance_patterns( distance = 1500.00 )
            
            returns a list of patterns if any was found. 
        '''
        pattern_well_names = self.very_old_get_distance_patterns_helper( distance )

        to_return_patterns = [ ]
        for item in pattern_well_names:
            names = item['producers'] + item['injectors']
            new_dataset = self.filter_by(NAME_KEYS[0], names )
            to_return_patterns.append(new_dataset.get_pattern(fix_time_gaps, fill_nan))
 
        return to_return_patterns

   
    def very_old_get_distance_patterns_helper(self, distance):
        def add_code_column( x ):
            vals =  x.shape[0]*['0']
            i = -1 
            for index,row in x.iterrows(): 
                i = i+1
                vals[i] = "".join( [str(value) for value in row.values  ] )

            x['code'] = vals  
            return x 

        def encode_distance( df, distance ):
            mask1 = df >= distance
            mask2 = df <  distance
            x = df.copy()
            x[  mask1 ] = 0 
            x[  mask2 ] = 1 
            x = x.astype(int)
            x = add_code_column(x)
            return x

        def extract_patterns( x, add_code=True ):
            
            patterns = x.groupby( by = 'code', sort=False )
            producers = []
            for i,v in patterns:
                prod = v.index
                producers.append( prod.values )

            crm_patterns = [ ] 
    

            injector_names = x.columns.values
            for item in producers:
                producer_names = list(item)
                injectors = x.loc[ producer_names[0],: ].values.astype(bool)
                injectors = injector_names[ injectors ]
                injectors = list(injectors[ injectors!='code'] )
               
                
                if (len(producer_names) > 0) and (len(injectors) > 0):
                    p = dict(producers = producer_names, injectors = injectors )
                    crm_patterns.append( p )


            x.sort_values(by = ['code'], inplace=True)
            if 'code' in x.columns and not add_code: 
                x.drop( ['code'], axis = 1, inplace=True)


            return crm_patterns

        self.get_distances()
        df = self['distance'].copy()
        x = encode_distance( df, distance ) #0 1 1 0 1  1 1 0 0 1 1 ....
        x = add_code_column( x ) # 001100  11100 01101 etc 

        #patterns here is just a list of dictionaries. One item per pattern 
        #and each item contains the list of injectors and producer names.
        #from that list, we slice the dataset by names and call the get_pattern 
        #on it
        pattern_wells = extract_patterns(x, add_code = False )
        
        
        return pattern_wells 
    