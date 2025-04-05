
import re,typing, os, pandas as pd 
from typing   import Union  


from wf_lib2.crm_definitions import * 


class RawDataProcessing:
    
    def __init__(self):
        self.reference_date = '31/12/1950'
    
    def read_csv( self, input_file:Union[str,typing.TextIO], header=0, sep=',', skiprows=0):
        return pd.read_csv( filepath_or_buffer=input_file,header=header, skiprows=skiprows,sep=sep) if os.path.splitext( input_file )[1]=='.csv' else pd.read_excel( io=input_file,header=header)
        
    def harmonize_names( self, df ):
        '''
        Removes straneous characters such as the Bite-ordering indicator at the beginning of files moved between 
        linux/windows. This function operates in place and returns the calling object (this)

        Takes a dataset and renames the columns to a default name for the given column meaning if the meaning of the 
        column is known. 
        '''
        #this removes straneous characters
        for column in df.columns: #Need to remove Byte Order Marker at beginning of first column name
            new_column_name = re.sub(r"[^0-9a-zA-Z.,-/_ ]", "", column)
            df.rename(columns={column: new_column_name}, inplace=True)

        if int(pd.__version__[0])>=1: 
             df.rename(  columns_to_meaning_map( df.columns ), inplace=True, axis=1, errors='ignore')

        else:
            df.rename(  columns_to_meaning_map(df.columns ), inplace=True, axis=1 )
            
        return self 
 
    def process_types( self, df ):
            '''
            All the columns except for those considered date or name must be numeric.
            These can be NaN but cannot be an object. This method enforces that and if not possible 
            an exception is raised
            '''
            known_numeric_columns = RATE_KEYWORDS + X_KEYS + Y_KEYS # list of lists [ [list], [list], [list] ]
            for column_set in known_numeric_columns: 
                for col in column_set:
                    if col in df.columns: df[col] = pd.to_numeric( df[col] )
                        
            return self 


    def process_acronysms( self, df):
            '''
            Add columns of FIELD and REGION only if those arent present
            first three letters in name is field
            last two letters name is region
            ''' 
            #columns that have the substring NAME
            named_cols = [col_name for col_name in df.columns if 'NAME' in col_name.upper()]

            if any(named_cols):
                names = df[named_cols[0]]
                names =[name +'XXX' for name in names] #added some characters because we need at least three 
                if FIELD_KEYS[0] not in [c.upper() for c in df.columns]:
                    preffix = [s[0:3] for s in names]
                    df[FIELD_KEYS[0] ] = preffix

                if REGION_KEYS[0] not in [c.upper() for c in df.columns]:
                    suffix = [s[-2:] for s in names]
                    df[REGION_KEYS[0]] = suffix
                    
            return self 
        

    def process_dates(self, df):
        '''
        Dates are properly formatted. 
        '''

        date_column_name = DATE_KEYS[0].lower()
        cols = [name for name in df.columns if date_column_name in name.lower()]
        if not any(cols): return self 

        
        # try to parse dates
        col_name = cols[0]
        try:
 
            dates = pd.to_datetime(df[col_name])#.apply(lambda x: x.date())
            # drop any column called DATE or similar from the processed
            # add it again but with the right format and in column index 1
            df.drop(col_name, inplace=True, errors='ignore', axis=1)
            df.insert(0, DATE_KEYS[0], dates)

    
            # drop any column called DAYS or similar if it was there.
            # add it again
            df.drop('DAYS', inplace=True, errors='ignore', axis=1)


        except:
            print('Error processing dates ')
            raise  

        return self

    def run( self, dataset ):
    
        dfs = [ dataset.injectors_df, dataset.producers_df, dataset.locations_df]
        table_name = [ 'injectors', 'producers', 'locations' ]
        processor = self 
        
        try: 
            for i, df in enumerate(dfs):
                processor.harmonize_names( df ).process_dates( df ).process_acronysms( df ).process_types( df )
                
        except Exception as e:
            return False, f"Error in basic pre-processing of {table_name[i]} data"

        #returns success + error message if any 
        return True, ""
