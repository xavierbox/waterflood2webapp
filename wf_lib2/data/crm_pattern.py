  
import datetime 
import pickle, pandas as pd, numpy as np 
from collections.abc import Iterable

from wf_lib2.crm_definitions import *
from wf_lib2.crm_helper import CRMHelper 

import copy 


class CRMPattern (dict):
   
    """
    Description:
        A Pattern is an abstraction of the data referent to a number of injectors and producers.
        The CRM processes (CRM-P, IP, T, Kovalc, etc) operate on patterns and it is assumed that 
        every injector is connected to every producer in the same pattern.

        The implementation is a simple subclass of a dictionary but includes some goodies that are 
        used all across the program. For instance, when retieving the information about an specific 
        variable such as the water injected in the pattern injectors, the set of synonim keys defined 
        in the crm_definitions module is used. 

        Other quick-access proerties such as the number and names of injectors and producers are also 
        implemented. 

    Generation of patterns:
    
        The user is not expected to generate patterns by itself. Instead, the clients are expected to 
        retrieve these patterns directly from the methods provided in the dataset class (generate patterns 
        by names, well distance, regions, etc). However, for the sake of consistency, the class also 
        provides a defaul pattern and default arguments for its creation: 

        get_default_pattern() and get_default_params()

        The example patterns does not include pressures or well locations. 
    
    Information stored:
    
        Note that there is not a constrain on what information is stored in the Pattern dictionary. Yet 
        if the Pattern is created by the CRM engine via the CRMDataset, then the information stored for 
        each well consists on the water injection and water production rates, well locations, well names.
        For producers, it may incluse the BHP and other time series such as the oil/gas production rates
        and the fractional water produced.
        
    Author: 
            Xavier Garcia Teijeiro
            xteijeiro@slb.com
            xavierbox@gmail.com 
    Date: 2023  
        
    """


    ####################################
    ##########  public API #############
    ####################################
    
    def copy( self ):
        return CRMPattern( copy.deepcopy( super() ) )
    
    def __copy__(self):
        return CRMPattern( copy.copy( super() ) )
        
        
    def __deepcopy__(self, memo):
        return CRMPattern( copy.deepcopy( super() ))
        
    
    
    def save_file( self,file_name:str )->None:
        '''
        Trys to save a binary representation of the object in a file. 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (string):  the complete file path  
        '''
        
        with open( file_name, 'wb') as f: pickle.dump(self, f)
            
    @staticmethod 
    def load_file( file_name:str ):
        '''
        Trys to load a binary file (serialized object). 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (string):  the complete file path  
        '''
        with open(file_name, 'rb') as f:  return pickle.load(f)   
               
    def save_file_desriptor( self, file_stream )->None:  
        '''
        Trys to save a model into an open file (or download stream as in Dataikui) 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (stream):  the complete file path  
        '''
        pickle.dump(self, file_stream)
          
    def load_file_descriptor( self, file_stream ): 
        '''
        Trys to load the object from an open file (or download stream as in Dataikui) 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (stream):  the open file descriptor
        '''
        return pickle.load(file_stream)

    @property
    def water_injection( self )->pd.DataFrame:   return self._find( WATER_INJECTION_KEYS)
             
    @property
    def liquid_production( self )->pd.DataFrame: return self._find(LIQUID_PRODUCTION_KEYS)
    
    @property
    def oil_production( self )->pd.DataFrame:    return self._find(OIL_PRODUCTION_KEYS)
    
    @property
    def water_production( self )->pd.DataFrame:    return self._find(WATER_PRODUCTION_KEYS)
    
    @property
    def gas_production( self )->pd.DataFrame:    return self._find(GAS_PRODUCTION_KEYS)
    
    @property
    def producer_pressure( self )->pd.DataFrame: return self._find(PRODUCER_PRESSURE_KEYS)
    
    @property
    def locations( self )->pd.DataFrame: return self._find(LOCATION_KEYS)
   
    @property
    def location( self )->pd.DataFrame: return self._find(LOCATION_KEYS)
    
    @property
    def well_names( self)->list:
        return self.injector_names + self.producer_names 
    
    @property
    def injector_names( self ): 
        inj = self.water_injection
        if isinstance( inj, pd.DataFrame):
            return list(inj.columns) 
        
        return  None 
   
    @property
    def producer_names( self ): 
        inj = self.liquid_production
        if isinstance( inj, pd.DataFrame):
            return list(inj.columns) 
        return None 
        
    @property
    def num_injectors( self )->int: 
        inj = self.water_injection
        return inj.shape[1] if inj is not None else None 
    
    @property
    def injector_locations(self): 
        names, locs = self.injector_names, self.locations
        return locs[ locs[NAME_KEYS[0]].isin(names) ] if locs is not None else None 
        
    @property
    def producer_locations(self):
        names, locs = self.producer_names, self.locations
        return locs[ locs[NAME_KEYS[0]].isin(names) ] if locs is not None else None
        
   
    @property
    def num_producers( self )->int: 
        prd = self.liquid_production
        return prd.shape[1] if prd is not None else None 
    
    #for    testing and debugging 
    @staticmethod 
    def get_default_params()->dict:
        config = {
            'days': 350,
            'allocation': [0.60, 0.50, 0.4,0.3], #num injectors, each element is a producer-injector pair   
            'tau': 15.00 , #one producer 
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
            'primary_production': {'qo': 0.00008e3, 'taup':15.0}
        }
        return config 
    
    
    @staticmethod 
    def generate_default_pattern( input_config:dict = None, seed:int = None ):

        config = CRMPattern.get_default_params() if input_config is None else input_config  
        
        inj, prod, loc = CRMHelper.generate_crmp_example_data( config,seed )
        dates = CRMHelper.get_dates( inj.shape[0])
     

        
        date_col_name = DATE_KEYS[0]
        
        inj[date_col_name] = dates 
        prod[date_col_name] = dates 
        inj.set_index( date_col_name, drop = True, inplace=True)
        prod.set_index( date_col_name, drop = True, inplace=True)
        
        input_data = {
              WATER_INJECTION_KEYS[0]:   inj, 
              LIQUID_PRODUCTION_KEYS[0]: prod, 
              LOCATION_KEYS[0]: loc 
             }
        return CRMPattern( input_data )
    
    @staticmethod 
    def generate_default_multiwell_pattern( crm_config:dict  = None ):
        pattern =  CRMPattern.generate_default_pattern(crm_config)
        pattern.liquid_production['Producer1']  =  pattern.liquid_production['Producer']  
        pattern.liquid_production['Producer2']  =  pattern.liquid_production['Producer']*0.5
        pattern.liquid_production['Producer3']  =  pattern.liquid_production['Producer']*0.25
        pattern.liquid_production.drop(['Producer'], inplace=True, axis = 1 )

        a = pattern.locations.copy()
        a.loc[4,:]=['Producer1',  0,0]
        a.loc[5,:]=['Producer2', 500,500]
        a.loc[6,:]=['Producer3', 1000,1000]
        pattern['location'] = a 

        return CRMPattern( pattern )

    #####################################
    ################ private ############
    #####################################
    def __getitem__(self, key:str)->pd.DataFrame:
        
        if key in self.keys(): return super().__getitem__( key )
    
        for key_set in ALL_KEYWORDS:
            if key in key_set: return self._find( key_set )
        
        return None 
    
    
    def _find( self, KNOWN_KEYWORDS:Iterable )->pd.DataFrame:
        keys = list( self.keys())
        
        for word in KNOWN_KEYWORDS: 
            if word in keys: return self[word]
            if word.lower() in keys: return self[word.lower()]
            if word.upper() in keys: return self[word.upper()]

        return None 
    
         
    def get_distances( self ):
            
            LOCATION = LOCATION_KEYS[0]
            NAME = NAME_KEYS[0]
            if self[LOCATION] is None: return None 
            

            prod_loc = self.producer_locations
            inj_loc  = self.injector_locations

 
       
            df = pd.DataFrame( {}, columns =   self.injector_names )
            df['Producer'] = self.producer_names 
            df.set_index( 'Producer', drop=True, inplace= True)

            for index, row in prod_loc.iterrows():
                name,x,y = row[NAME], row['X'], row['Y']
                for index2, row2 in inj_loc.iterrows():
                    name2,x2,y2 = row2[NAME], row2['X'], row2['Y']
                    d = ((x2 - x)**2 + (y2-y)**2)**0.5
                    df.loc[name,name2] = d 
            
            self[ DISTANCE_KEYS[0]] = df
            

    def multi_well_to_single( self ):
        # from a multi-well pattern create a list of single-well patterns 
        p = self 
        producer_names = list(p.producer_names) 
          
        
        injector_names = list(p.injector_names) 
        patterns_list = [] 

        for n in range( len(producer_names)):

            x= CRMPattern()
            for key in p.keys():
                data = p[ key ]

                #these are all the rates 
                if producer_names[n] in data.columns:
                    x_data = data[ producer_names[n] ]
                    x[key] = pd.DataFrame( x_data.copy() )
                    
 
                #these may be distances and locations 
                else:
                    x[key] = data.copy() 

            #now the distances and locations 
            #locations 
            names = injector_names + [producer_names[n]]
            locs_df = p[LOCATION_KEYS[0]]
            NAME = NAME_KEYS[0]
            locs_view = locs_df[ locs_df[NAME].isin(names) ]
            x[ LOCATION_KEYS[0]  ] = locs_view.copy() 

            #distances 
            x.get_distances()
            patterns_list.append( x )


        return patterns_list 
        

    def delete_wells( self, well_names:Iterable )->None:

        p = self 
        for table_name in  p.keys():
            p[ table_name  ].drop( well_names, inplace=True, errors='ignore',  axis= 1 )

        col = get_column_for_meaning( list(p.keys()), LOCATION_KEYS[0]  )[0]
        p[col] = p[col] [ ~p[col]['NAME'].isin( well_names ) ].copy()
        p.get_distances()

    def slice_dates( self, date1:str , date2:str )->None:

        #convert everything to timestamp if they are strings 
        if isinstance( date1, str ): #assume both are 
            date1, date2 = datetime.datetime.strptime(date1, '%Y-%m-%d').date(),datetime.datetime.strptime(date2, '%Y-%m-%d').date()
            date1, date2 = pd.Timestamp(date1),pd.Timestamp(date2)

        elif isinstance( date1, pd.Timestamp ):
            #nothing to do, we have a datatype we cazan work with 
            pass 

        elif isinstance( date1, datetime.date ):
            date1, date2 = pd.Timestamp(date1),pd.Timestamp(date2)

        elif isinstance( date1, np.datetime64 ):
            #nothing to do, we have a datatype we cazan work with 
            pass 

        else:
            raise ValueError(f'[slice_dates] date1{type(date1)} and date2{type(date2)} must be str or timestamps') 

        for table_name in  self.keys():
            index = self[table_name].index 

            if index.name is not None and index.name.upper()=="DATE":
                dates = pd.to_datetime(index).values
                mask = (dates >= np.datetime64(date1)) & (dates <= np.datetime64(date2))
                self[table_name] = self[table_name] [ mask ].copy()

 
 
