#from __future__ import annotations
import pandas as pd, numpy as np, json  

from wf_lib2.crm_definitions import * 
from wf_lib2.data.crm_pattern import CRMPattern
from wf_lib2.data.crm_data_utils   import * 


class CRMDataset:
    '''
    A CRMDtaset represents the injection data, producion data and the well locations.
    The information is gathered in three dataframes:
     
      injectors_df, producers_df, locations_df. 
      
    There three can be accessed via public properties of the CRMDataset 
    and manipulated like any other pandas dataframe. However:
    
    The dataset oibject also provides a number of methods to manipulate the data, such as 
    filtering out wells, slicing data by well location, region, time, etc. The dataset provides
    methods to fetch the well names, copy dat afrom another dataset, extract sectors, etc.

    As any other object in the library, the CRMDataset contains two methods that will produce 
    an example dataset (see below generate_default_multiwell_dataset and generate_default_dataset).
     
    '''
    def __init__(self):
        self.injectors_df = None 
        self.producers_df = None 
        self.locations_df = None 
        self.events_df    = None 
        self.distances_df = None 
        self.name = None 
        
        
    def check_dataset( self ):
        
        crm_dataset = self 
        errors,warnings = [],[]
        injector_names, producer_names = None, None 
        try:
            producer_names = set(crm_dataset.producer_names) 
            injector_names = set(crm_dataset.injector_names) 
            location_names = set(crm_dataset.locations_df['NAME'].unique())
            
        except:
            errors.append('Well names are not found in at least one table. Missing column: NAME')
            return errors 
        
        #every injector,producer must have a location
        if injector_names.issubset( location_names ) is False:
            errors.append('The location for all injectors is not available ')
        if producer_names.issubset( location_names ) is False:
            errors.append('The location for all producers is not available ')

        
        #there are REQUIRED columns in each dataset table 
        inj,prd,loc = crm_dataset.injectors_df, crm_dataset.producers_df,crm_dataset.locations_df  
        
        if len( find_columns(inj,WATER_INJECTION_KEYS) ) == 0:
            errors.append('Injectors: Water injection column was not found. The name of the column missing is one of these: ' + ",".join(WATER_INJECTION_KEYS))   
        if len( find_columns(prd,WATER_PRODUCTION_KEYS) ) == 0:
            errors.append('Producers: Liquid production column was not found. The name of the column missing is one of these: ' + ",".join(WATER_PRODUCTION_KEYS))
        if len( find_columns(prd,GAS_PRODUCTION_KEYS) ) == 0:
            errors.append('Producers: Gas production column was not found. The name of the column missing is one of these: ' + ",".join(GAS_PRODUCTION_KEYS))
        if len( find_columns(prd,OIL_PRODUCTION_KEYS) ) == 0:
            errors.append('Producers: Oil production column was not found. The name of the column missing is one of these: ' + ",".join(OIL_PRODUCTION_KEYS))
        if len( find_columns(prd,LIQUID_PRODUCTION_KEYS) ) == 0:
            errors.append('Producers: Liquid production column was not found. The name of the column missing is one of these: ' + ",".join(LIQUID_PRODUCTION_KEYS))
        
        if len( find_columns(prd,NAME_KEYS) ) == 0:
                errors.append('Producers: Well name column was not found. The name of the column missing is one of these: ' + ",".join(NAME_KEYS))
        if len( find_columns(prd,NAME_KEYS) ) == 0:
                errors.append('Injectors: Well name column was not found. The name of the column missing is one of these: ' + ",".join(NAME_KEYS))
        
        
        if len( find_columns(loc,NAME_KEYS) ) == 0:
            errors.append('Locations: Well name column was not found. The name of the column missing is one of these: ' + ",".join(NAME_KEYS))

                    
        if prd.index.name!='DATE':
            if len( find_columns(prd,DATE_KEYS) ) == 0:
                    errors.append('Producers: Date column was not found. The name of the column missing is one of these: ' + ",".join(DATE_KEYS))
        
        if inj.index.name!='DATE':    
            if len( find_columns(inj,DATE_KEYS) ) == 0:
                    errors.append('Injectors: Date column was not found. The name of the column missing is one of these: ' + ",".join(DATE_KEYS))
        
            
        #the dataset needs to be convertible to a pattern
        try:
            p = crm_dataset.get_pattern(fix_time_gaps=False, fill_nan = np.nan)
            
        except Exception as e:
            errors.append('The dataset cannot be converted to a pattern representaion. Potentially, some data is missing or  there are  time gaps ')
            errors.append('The error reported was ' + str(e))

        #there can be no time gaps in the daily data 
        try:
            p = crm_dataset.get_pattern(fix_time_gaps=False, fill_nan = np.nan )
            water_inj, liquid_prod, water_prod, gas_prod, oil_prod = p.water_injection, p.liquid_production, p.water_production, p.gas_production,p.oil_production 
        
            names  = ['Water injection','Liquid production', 'Water production','Gas production','Oil production']
            tables = [water_inj, liquid_prod, water_prod, gas_prod, oil_prod]
            
            for n, table in enumerate( tables ) :
                if check_if_time_gaps( table ) is True:
                    errors.append('There are time gaps in the table: ' + names[n] )
    
            
                table = table.select_dtypes( np.number )
                pod = table.lt(0.000).sum().sum()
                if pod > 0.000001:
                    errors.append('There are negative rates or negative pressures in the table ' + names[n] )
                    
                
    
        except Exception as e:
            errors.append('The dataset cannot be converted to a pattern representaion. Potentially, some data is missing ')
            errors.append('The error was ' + str(e))
            
        #numerical columns cannot be less than zero
        

        print(errors)
    
           
    def get_column_names( self )->dict:
        
        '''
        Returns:
        
        d (dict): A dictionary woth keys injectors,producers,locations and values
        equalt to the columns of the respective dataframes
        '''
        
        d = {} 
        
        if self.injectors_df is not None: d['injectors'] = self.injectors_df.columns
        if self.producers_df is not None: d['producers'] = self.producers_df.columns
        if self.locations_df is not None: d['locations'] = self.locations_df.columns
        
        return d 
        
             
    def copy_from( self, other )->None :
        
        if other.injectors_df is not None: 
            self.injectors_df = other.injectors_df.copy() 
        else: self.injectors_df = None 
        
        if other.producers_df is not None: 
            self.producers_df = other.producers_df.copy()  
        else: self.producers_df = None 
    
        if other.locations_df is not None: 
            self.locations_df = other.locations_df.copy()  
        else: self.locations_df = None 
            
        if other.events_df is not None: 
            self.events_df    = other.events_df.copy()  
        else: self.events_df = None 
            
        if other.distances_df is not None: 
            self.distances_df = other.distances_df.copy()  
        else: self.distances_df = None 
        
        if other.name is not None: self.name = other.name  
        else: self.name = None 
              
                
    def __getitem__( self, key:str )->pd.DataFrame:
        
        if key.lower() in ['producers', 'producers_df']: return self.producers_df 
        if key.lower() in ['locations', 'locations_df']: return self.locations    
    
        if key.lower() in ['distance', 'distances', 'distance_df']:
            if self.distances_df is None: self.get_distances()
            return self.distances_df 
 
        
        def _find( KNOWN_KEYWORDS ):
            keys = { }
            
            DATE, NAME = DATE_KEYS[0], NAME_KEYS[0]
            
            for column in self.injectors_df: keys[ column ] = self.injectors_df
            for column in self.producers_df: keys[ column ] = self.producers_df
            for word in KNOWN_KEYWORDS: 
             
                if word in keys: return keys[word][ [DATE, NAME, word] ]
                if word.lower() in keys: return  keys[word.lower()][ [DATE, NAME,word.lower()] ]
                if word.upper() in keys: return  keys[word.upper()][ [DATE, NAME,word.upper()] ]
            return None 
        
    
        for key_set in RATE_KEYWORDS:
            if key in key_set: return _find( key_set )
        
        
        
        
        return None 
              
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
           
    @staticmethod
    def instance( inj_df:pd.DataFrame = None, prod_df:pd.DataFrame = None, loc_df:pd.DataFrame=None, events_df:pd.DataFrame=None, name:str= None ):
        ret = CRMDataset()
        ret.injectors_df = inj_df
        ret.producers_df = prod_df
        ret.locations_df = loc_df
        ret.events_df    = events_df
        ret.name = name 
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
        
    
    def slice_dates_dataset( self, date1:str, date2:str ):
        
        dfs = [ self.injectors_df, self.producers_df]

        for n,df in enumerate(dfs):
            date_col = [col for col in df.columns if 'date' in col.lower() ]
            
            
            #the date column is part of the columns, not the index 
            if len(date_col)>0:
                dates = df[date_col[0]]
            elif df.index.name.lower() == 'date':
                dates = df.index
            else:
                return None 
            
            mask =  (dates >= date1) & (dates <= date2)
            dfs[n] = df[ mask ].copy()

        NAME = NAME_KEYS[0]
        names = list( set( dfs[0][NAME]))
        names.extend( list( set( dfs[1][NAME])))
        locs = self.locations_df[ self.locations_df[NAME].isin(names) ]
        
        return CRMDataset.instance( dfs[0], dfs[1], locs, self.name ) 



    def slice_coordinates_dataset( self, xlimits:tuple, ylimits:tuple ):
        x1,x2,y1,y2 = xlimits[0], xlimits[1], ylimits[0], ylimits[1]
        subset = self.locations_df[  (self.locations_df.X > x1) 
                                   & (self.locations_df.X < x2) 
                                   & (self.locations_df.Y > y1) 
                                   & (self.locations_df.Y < y2) 
                                  ]
        NAME = NAME_KEYS[0]
        return self.filter_by(NAME,subset[NAME].values)
        
    @property
    def regions( self )->list:
        REGION=REGION_KEYS[0]

        r1 = set(self.injectors_df[REGION].values) if REGION in self.injector_names else set([ name[-2:] for name in self.injector_names])
        r2 = set(self.producers_df[REGION].values) if REGION in self.producer_names else set([ name[-2:] for name in self.producer_names])
      
        
        return list(r1.union( r2 ))
    
    @property
    def fields( self )->list:
        FIELD=FIELD_KEYS[0]
        r1 = set(self.injectors_df[FIELD].values) if FIELD in self.injector_names else set([ name[0:3] for name in self.injector_names])
        r2 = set(self.producers_df[FIELD].values) if FIELD in self.producer_names else set([ name[0:3] for name in self.producer_names])
      
      
        
        
        return list(r1.union( r2 ))
       
    @property
    def injector_names(self)->list:
        if isinstance( self.injectors_df, pd.DataFrame):
            col = get_column_for_meaning( self.injectors_df.columns, NAME_KEYS[0])[0]
            return list( self.injectors_df[col].unique() )
        return None 
  
    @property
    def producer_names(self)->list:
        if isinstance( self.producers_df, pd.DataFrame):
            col = get_column_for_meaning( self.producers_df.columns, NAME_KEYS[0])[0]
            return list( self.producers_df[col].unique() )
        return None 
 

          
    def injector_locations( self )->pd.DataFrame:  
        s = self.locations_df
        injs =  s[ s[NAME_KEYS[0]].isin( self.injector_names)]
        return injs.copy()
        
    def producer_locations( self )->pd.DataFrame:
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
           
    def get_pattern( self, fix_time_gaps = True,fill_nan = 0.0 ):
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
        self.get_distances()

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
                    
                    
        #.sort_values( by='DATE')
                    
                     
                    
        pattern = CRMPattern( d )
        pattern[DISTANCE_KEYS[0]] = self.distances_df
        pattern[LOCATION_KEYS[0]] = self.locations_df 

        if fix_time_gaps:
            fix_index_time_gaps_in_pattern( pattern )
        
        #pattern=pattern
        return pattern 

    def _get_distance_patterns_helper(self, distance):
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
    
    def get_distance_patterns( self, distance:float,fix_time_gaps = True, fill_nan=0.0 ):
       
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
    def generate_default_multiwell_dataset( input_config:dict = None ):

        p = CRMPattern.generate_default_multiwell_pattern( input_config )
        water_injection = WATER_INJECTION_KEYS[0]
        liquid_production = LIQUID_PRODUCTION_KEYS[0]
        
        
        inj, prd = p[water_injection], p[liquid_production]
        injectors_df, producers_df = None, None 

        keys = [water_injection, liquid_production]
        for n in [0,1]:

            x = inj if n ==0 else prd  

            dfs = [ ] 
            for col in x.columns:
                key = keys[n]
                df = x[[col]].copy()
                df[NAME_KEYS[0]] = col
                df[key] = df[col]
                df.drop( [ col ], inplace = True, axis = 1 )
                df.reset_index(inplace=True, drop = False )
                dfs.append( df.copy() )

            if n ==0: injectors_df = pd.concat ( dfs , axis = 0 ) 
            else:   producers_df   = pd.concat ( dfs , axis = 0 ) 


        default_dataset = CRMDataset.instance(injectors_df, producers_df, p.locations )
        return default_dataset

    @staticmethod 
    def generate_default_dataset( input_config:dict = None ):

        p = CRMPattern.generate_default_pattern( input_config )
        water_injection = WATER_INJECTION_KEYS[0]
        liquid_production = LIQUID_PRODUCTION_KEYS[0]
        
        
        inj, prd = p[water_injection], p[liquid_production]
        injectors_df, producers_df = None, None 

        keys = [water_injection, liquid_production]
        for n in [0,1]:

            x = inj if n ==0 else prd  

            dfs = [ ] 
            for col in x.columns:
                key = keys[n]
                df = x[[col]].copy()
                df[NAME_KEYS[0]] = col
                df[key] = df[col]
                df.drop( [ col ], inplace = True, axis = 1 )
                df.reset_index(inplace=True, drop = False )
                dfs.append( df.copy() )

            if n ==0: injectors_df = pd.concat ( dfs , axis = 0 ) 
            else:   producers_df   = pd.concat ( dfs , axis = 0 ) 


        default_dataset = CRMDataset.instance(injectors_df, producers_df, p.locations )
        return default_dataset


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

        '''
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
        '''

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



    


    


    
    
    