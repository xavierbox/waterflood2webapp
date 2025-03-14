import pandas as pd, numpy as np, json, math   
from datetime import date, datetime
from copy import copy, deepcopy
from collections.abc import Iterable

from wf_lib2.crm_definitions import * 

             
# this is obsolete. Use the CrmDataset check instead 
def check_if_time_gaps( df:pd.DataFrame,sampling_frequency ='D' )->bool:
        
    col = find_column( df, DATE_KEYS )
    day_range = None 
    if not col is None:
        min_date, max_date = min(df[col]),max(df[col])
        day_range = pd.date_range( min_date, max_date, freq = sampling_frequency)

    elif df.index.name in DATE_KEYS:  

        min_date, max_date = min(df.index),max(df.index)
        day_range = pd.date_range( min_date, max_date, freq = sampling_frequency)
    
    else:
        return False 
    

    if len(day_range) != df.shape[0]: 
        return True 
         
        
    return False

def fix_index_time_gaps_in_pattern( pattern:dict )->None:
         
    def fill_index_time_gaps( df1 ): 
        DATE = DATE_KEYS[0]
        DAYS = 'DAYS'
        ### Lets fix the time gaps 
        min_date, max_date = min(df1.index),max(df1.index)
        day_range = pd.date_range( min_date, max_date, freq = 'D')

        #make the index a column so it is a bit easier to work with 
        df1.reset_index( inplace = True )

        #properly format the date in case it is not
        df1[DATE] =  pd.to_datetime(df1[DATE])

        #create a column of days-since 01-15-1950. We will use it later....
        date_str = '01-15-1950'
        date_object = datetime.strptime(date_str, '%m-%d-%Y').date()
        df1['DAYS'] = ( df1[DATE].dt.date - date_object ).dt.days 

        #lets create a dataframe with all the dates.  
        resampled_df = pd.DataFrame( {DATE: day_range })
        resampled_df[DAYS] = ( resampled_df[DATE].dt.date  - date_object ).dt.days

        #create a merged version, where dates shouldnt be missing 
        table = pd.merge( left = df1, right = resampled_df, left_on='DAYS', right_on='DAYS',how='right')
        table[DATE] = table[DATE+'_y']
        table.drop( [DATE+'_x', DATE+'_y', 'DAYS'], inplace=True, axis=1)
        table.set_index( DATE, drop = True, inplace = True )
        table.fillna( value = 0.0, inplace= True  )

        return table 


    for key in pattern.keys():

        df  = pattern[key]
        if df is None: 
            continue 

        if df.index.name is not None and  DATE_KEYS[0].lower() == df.index.name.lower():

            if check_if_time_gaps(df):
                pattern[key] = fill_index_time_gaps( df )
    
def find_columns(cols, keys):
    """
    Returns a list of the columns in cols that
    match any column in keys (case insensitive)
    """
    return [col for col in cols if col.upper() in [key.upper() for key in keys]]

def is_name_or_id(col):
    """
    Returns true if the string col matches either a key we consider reflects a
    name or a well id
    """
    match1 = col.upper() in NAME_KEYS if col is not None else False
    match2 = col.upper() in UBHI if col is not None else False
    return match1 or match2

def is_date(col):
    """
    We check names and dates all the time so this one just matches
    a given column name to wahtever column names that we consider
    represent a date column
    """
    return col.upper() in DATE_KEYS if col is not None else False

def dataframe_to_json(df):
    """
    Customized version of the DataFrame to json.
    Pandas provides a dataframe to json but this is more convenient to us as it exports
    the json as arrays (one per column)
    It also deals with the dates properly.

    This is mainly used to pass information to the UI

    """
    d = {}
    for col in df.columns:
        values = None
        
        if is_date(col):
            try:
                values = [str(v) for v in df[col].dt.date.values]
            except:
                values = df[col].values.tolist()
        else:
            values = df[col].values.tolist()

        d[col] = values

    # now the index if the index is named as a date
    if is_date(df.index.name):
        values = [str(x) for x in df.index.date]
        d[df.index.name] = values

    # or if the indesx is named and it is a string
    if is_name_or_id(df.index.name):
        d[df.index.name] = [x for x in df.index]

    return json.dumps(d)

def aggregate_column(df, column_name, fill_nan=np.nan):  # , keep_date = False):

    name_col = [c for c in df.columns if c in NAME_KEYS][0]

    date_col = [c for c in df.columns if c in DATE_KEYS]
    if any(date_col):
        date_col = date_col[0]
    elif df.index.name in DATE_KEYS:
        date_col = df.index.name
        df = df.reset_index(inplace=False)
    else:
        print("cannot aggregate table ", column_name)
        return None

    dfp = df.pivot_table(index=date_col, columns=name_col, values=column_name, fill_value=fill_nan)
    col_list = [date_col]
    col_list.extend(list(dfp))
    dfp[date_col] = dfp.index
    dfp = dfp[col_list]
    dfp.reset_index(inplace=True, drop=True)

    # we will always keep the date but if the option is there then: if not keep_date: dfp.drop( ['DATE'], axis=1,inplace=True)
    dfp.set_index(date_col, drop=True, inplace=True)

    dfp.rename_axis(None, axis=1, inplace=True)
    dfp.fillna(value=fill_nan, axis=0, inplace=True)
    return dfp

 
################  UI support ########################
def get_injector_producer_locations_filtered( dataset, filters = None ):

    ''' 
    receives filters =  
    {
    'subzone': ['WARA-BOTTOM'], 
    'sector': ['1', '2', '8', '5', '4']
    'name':[name1, name2,...] (optional)
    }

    fetches the locations, injectors and producers and returns the slice copy of them that 
    satifies the filters. 
    
    Example of use:
    
    from wf_lib2.data.dataiku_local_folder_connector import KOCDataikuLocalStorageConnector
    from wf_lib2.data.crm_data_utils import *
     
    data_server_config = {
            'managed_folder_name':'azFolder', 
            
            'app_name':'WF',
            'data_folder_name':'data', #(optional,if not given it is set to data. It is relative to the project path )
            'projects_folder_name':'projects', #(optional,if not given it is set to projects )
            'studies_folder_name':'studies' #(optional,if not given it is set to studies. It is relative to the project )
         }
         
    filters =  {
        'subzone': ['WARA2','WARA1'], 
        'sector': ['1', '2', '8', '5', '4'],
        'name':['Producer1-1','Producer1-2', 'Inj0-1','Inj0-2'] #(optional)
        }

    # get the crm dataset  
    data_server_config['project_name'] = project_name 
    storage = KOCDataikuLocalStorageConnector( data_server_config )
    crm_dataset = storage.get_project_dataset()

    #get the separated dataframes 
    inj, prod, locs =  get_injector_producer_locations_filtered( crm_dataset, filters )
    inj['NAME'].unique(), prod['NAME'].unique()

    
    
    
    ''' 

    def _filter_by( df, keywords, in_values ):
        
        values = in_values 
        if not isinstance(in_values,list):
            values=[in_values]
        
        column_name = find_columns(df.columns, keywords)[0]
        df = df[df[column_name].isin( values )].copy()

        return df 
    
    
    if filters is None:
        filters = {} 

    locs_filtered = dataset.locations_df

    keys = list(filters.keys())
    subzone_key = None 

    for key in keys:

        cols  =  find_columns( [key], NAME_KEYS )
        if len(cols) > 0:
            name_key = cols[0] 
            if filters[ name_key ] is None: continue 

            locs_filtered = _filter_by( locs_filtered, NAME_KEYS, filters[name_key] )

        cols  =  find_columns( [key], SUBZONE_KEYS )
        if len(cols) > 0:
            subzone_key = cols[0] 
            if filters[ subzone_key ] is None: 
                subzone_key = None
                continue 

            locs_filtered = _filter_by( locs_filtered, SUBZONE_KEYS, filters[subzone_key] )

        cols  =  find_columns( [key], SECTOR_KEYS )
        if len(cols) > 0:
            sector_key = cols[0] 
            if filters[ sector_key ] is None: continue 

            sectors = [int(s) for s in  filters[sector_key] ]
            locs_filtered = _filter_by( locs_filtered, SECTOR_KEYS, sectors )

    name_col= find_columns( locs_filtered.columns, NAME_KEYS )[0]
    names = list( locs_filtered[name_col].unique() )

    name_col= find_columns( dataset.injectors_df.columns, NAME_KEYS )[0]
    inj = dataset.injectors_df[ dataset.injectors_df[name_col].isin(names) ]

    name_col= find_columns( dataset.producers_df.columns, NAME_KEYS )[0]
    prod = dataset.producers_df[ dataset.producers_df[name_col].isin(names) ]

    # BUG: and patch 
    # one well, has only one name and belongs to only one sector but it might 
    # belog to different subzones. In the code above, we filtered all the names 
    # Yet, we forgot to filter the producers and injectors by subzone if there is 
    # any filter. That creates a problem down the line 
    # so we added this patch here 
    # print('-------------------------------------')
    if not subzone_key is None: 
        #print('path applied here ')
        find_columns( [key], SUBZONE_KEYS )
        prod = _filter_by( prod, SUBZONE_KEYS, filters[subzone_key] )
        inj = _filter_by( inj, SUBZONE_KEYS, filters[subzone_key] )
    # print('-------------------------------------')
    
    
    
    return inj, prod, locs_filtered


def get_injector_producer_pairs_filtered( crm_dataset, filters = None, distance = 999999, return_distances=False  ):
    ''' 
    receives filters =  
    {
    'subzone': ['WARA-BOTTOM'], 
    'sector': ['1', '2', '8', '5', '4']
    'name':[name1, name2,...] (optional)
    }

    fetches the locations, injectors and producers and returns a list of pairs per subzone in which the 
    producers are at a distanxce < threshold from the injectors listed for each producer. 
    
    Example of use 

        from wf_lib2.data.dataiku_local_folder_connector import KOCDataikuLocalStorageConnector
        from wf_lib2.data.crm_data_utils import *


        data_server_config = {
                'managed_folder_name':'azFolder', 

                'app_name':'WF',
                'data_folder_name':'data', #(optional,if not given it is set to data. It is relative to the project path )
                'projects_folder_name':'projects', #(optional,if not given it is set to projects )
                'studies_folder_name':'studies' #(optional,if not given it is set to studies. It is relative to the project )
             }

        # get the crm dataset  
        data_server_config['project_name'] = project_name 
        storage = KOCDataikuLocalStorageConnector( data_server_config )
        crm_dataset = storage.get_project_dataset()

        #get a list of pairs producer: [injectors] at a distance less than the limit and per subzone  
        get_injector_producer_pairs_filtered( crm_dataset, filters = None, distance = 800, return_distances=False )


    
    '''
    
    
    # these are the ones that satisfy all the filters. Their distance to others is not accounted for. 
    inj, prod, locs =  get_injector_producer_locations_filtered( crm_dataset, filters )
    
    
    # the names of the columns to look for 
    NAMECOL, XCOL, YCOL = find_columns( locs.columns, NAME_KEYS )[0],find_columns( locs.columns, X_KEYS )[0],find_columns( locs.columns, Y_KEYS)[0] 
    SUBZONECOL = find_columns( locs.columns, SUBZONE_KEYS )[0]
    

    # this is the variable to be returned 
    pairs = {}
    subzones = locs[ SUBZONECOL].unique() 
    
    producer_names = set()
    injector_names = set() 
    # we will return the list of pairs per subzone. 
    for subzone_name  in subzones:
        
        #print( 'doing pairs for subzone ', subzone_name )
        
        subzone_pairs = {} 
        
        inj_subzone  = inj [ inj[SUBZONECOL] == subzone_name ]
        prod_subzone = prod[ prod[SUBZONECOL] == subzone_name ]
        locs_subzone = locs[ locs[SUBZONECOL] == subzone_name ]
        well_names,x,y   = locs_subzone[ NAMECOL ].values, locs_subzone[XCOL].values, locs_subzone[YCOL].values 
        
        # aux to compute distabnces easier later.  
        xy = {} 
        for i in range(0,len(well_names)): 
            xy[well_names[i]] = [ x[i], y[i] ]
            
        inj_names = inj_subzone[ NAMECOL ].unique()
   


        # now for every producer, check all the ibnjectors and see which ones are withinb the distance
        for producer_name in prod_subzone[NAMECOL].unique():
            x1,y1  = xy[producer_name ]
                
            for inj_name in inj_names:

                x2,y2  = xy[inj_name ]

                d2 = ((x1-x2)**2) + ((y1-y2)**2) 
                if d2 < distance * distance:

                    neighbours =  subzone_pairs.get( producer_name, [] )
                  
                    if return_distances:
                        neighbours.append( (inj_name, math.sqrt( d2 )) )
                    else:
                        neighbours.append( inj_name )
                        injector_names.update( [inj_name] )

                    producer_names.update( [producer_name] )
                    
                    subzone_pairs[ producer_name ] = neighbours

        #for name, value in subzone_pairs.items():
        #    subzone_pairs[name] = {'injectors': value} 
            
        pairs[subzone_name] = subzone_pairs
        
        
        
    return { SUBZONECOL : pairs }, list(producer_names), list(injector_names)   
        

def get_well_rates( dataset, subzone:str, well_names:list = None, sectors:list = None ):

    ''' 
    filters =  {
        'subzone': ['WARA2','WARA1'], 
        'sector': ['1', '2', '8', '5', '4'],
        'name':['Producer1-1','Producer1-2', 'Inj0-1','Inj0-2'] #(optional)
        }
    '''
    water_injection   = None 
    liquid_production = None 
    oil_production    = None
    gas_production    = None
    water_production  = None
            
    
    def filter_by( df, keywords, values ):
        column_name = find_columns(df.columns, keywords)[0]
        df = df[df[column_name].isin( values )]
        return df 
        
    
    filters =  {
    'subzone': subzone, 
    'sector': sectors,
    'name': well_names if well_names is not None else None  
    }

    inj, prod, loc = get_injector_producer_locations_filtered( dataset, filters )
    
    if inj.empty or prod.empty or loc.empty:
        return (
                water_injection,
                liquid_production,
                oil_production,
                gas_production,
                water_production
            )
   
    # These are pivoted tables. 

    # WATER INJECTION 
    water_injection = aggregate_column(inj, find_columns( inj, WATER_INJECTION_KEYS)[0] )

  
    # OIL_VOLUME, GAS_VOLUME
    liquid_production = aggregate_column(prod, find_columns( prod, LIQUID_PRODUCTION_KEYS)[0])
    gas_production = aggregate_column(prod, find_columns(prod,GAS_PRODUCTION_KEYS)[0])
    oil_production = aggregate_column(prod, find_columns(prod,OIL_PRODUCTION_KEYS)[0])
    water_production = aggregate_column(prod, find_columns(prod,WATER_PRODUCTION_KEYS)[0])

    oil_production = oil_production.sort_values(by=["DATE"])
    liquid_production = liquid_production.sort_values(by=["DATE"])
    gas_production = gas_production.sort_values(by=["DATE"])
    water_production = water_production.sort_values(by=["DATE"])

    return (
            water_injection,
            liquid_production,
            oil_production,
            gas_production,
            water_production
        )
 
       

    

