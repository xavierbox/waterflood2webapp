
import dataiku
import pickle, json, os, pandas as pd, numpy as np  
from typing   import Union  
#from datetime import date

import datetime


#from wf_lib2.data.raw_data_processing import RawDataProcessing
from wf_lib2.data.crm_dataset import CRMDataset 
from wf_lib2.crm_definitions import * 

import warnings
warnings.filterwarnings(action='ignore', category=UserWarning) 




class DataikuStorageAPI:
    
    '''
    This class defines all the methods needed for the Ui and the workflows
    
    The derived classes implement some specializations needed if calling the class from 
    outside Dataiku (remote folder)
    '''

    
    def __init__(self, **kwargs  ):
        
        self.args = {} 
        for kwarg, value in kwargs.items(): 
            self.args[kwarg] = value 
            

    def list_managed_folders(self):
        names = [ item['name'] for item in dataiku.api_client().get_default_project().list_managed_folders() ] 
        return names 
    
    
    def list_contents( self ): 
        print( self._get_handle().list_contents())
    
    def list_projects(self):
        
        #we are looking for the subfolders inside the projects_base_address
        preffix = self.projects_base_address+'/'
        preffix = preffix.replace('\\','/').replace('//','/')
        
        return self.list_subfolders_in( preffix )
   

    def list_project_datasets( self, project_name ): 
        preffix = self.data_folder_path( project_name )+'/'
        preffix = preffix.replace('\\','/').replace('//','/')
 
        return self.list_subfolders_in( preffix )
  
    
    def list_dataset_files( self,project_name, dataset_name ):
        path =  os.path.join(self.data_folder_path( project_name ), dataset_name)+'/'
        path=path.replace('\\','/').replace('//','/')
        return self.list_files_in( path  )
    
    
    def create_project( self, project_name, description=None ):
        
        target_path = self.project_folder_path( project_name ) + '/timestamp.cfg'
        target_path = target_path.replace('\\','/').replace('//','/')
        
        obj = { 
              'project_name': project_name
        }
        
        if project_name not in self.list_projects():
            obj['creation_date'] = str(datetime.date.today())
           
        if description: obj.update( description )
            
        #project 
        self._create_path( target_path, obj )
        
        #data folder inside 
        data_path = self.data_folder_path( project_name )+ '/timestamp.cfg'
        self._create_path( data_path,obj )

        #studies folder inside 
        studies_path = self.studies_folder_path( project_name )+ '/timestamp.cfg'
        self._create_path( studies_path,obj )

        
    def delete_project( self, project_name ):
        
        target_path = self.project_folder_path( project_name ) 
        target_path=target_path.replace('\\','/').replace('//','/')
        handle = self._get_handle()
        files = [ f['path'] for f in handle.list_contents()['items'] if target_path in f['path']  ] 
        
        for path in files:  self._delete_path( path )
        
        self._delete_path( target_path )
    
    
    #delete
    def delete_dataset( self,project_name, dataset_name ):
        path =  os.path.join(self.data_folder_path( project_name ), dataset_name)
        path=path.replace('\\','/').replace('//','/')
        self._delete_path(path)
        
    #create
    def create_dataset( self, project_name, data_name, description=None, overwrite = True ):
        '''
        Creates a study folder passing an optional json description that describes the study. 
        If the study exists, it gets overwritten according to an overwrite flag.
        The description file will be named study_name.cfg 
        '''
        if data_name in self.list_project_datasets( project_name ):
            if not overwrite:
                return  False 
            
            else:
                self.delete_dataset( project_name,data_name )
        
        
        target_path = os.path.join( self.data_folder_path( project_name ),data_name,data_name+'.cfg'  )
        target_path=target_path.replace('\\','/').replace('//','/')
        self._create_path( target_path, description )
        return True 

    
    def save_dataset( self, name, project, dataset ):

        self.create_project( project )
        self.create_dataset( project, name )
        
        path = self.data_folder_path( project) + '/'+ name 
        
        self.write_csv( path + '/injectors.csv',  dataset.injectors_df)
        self.write_csv( path + '/producers.csv',  dataset.producers_df)
        self.write_csv( path + '/locations.csv',  dataset.locations_df)
 
    
    def get_dataset( self, project_name, dataset_name, filter_by = None, nrows = None, meaning_columns = None ):  


        preffix = os.path.join(self.data_folder_path(project_name),dataset_name).replace('//','/').replace('\\','/')
        paths   = [preffix + '/'+ f for f in self.list_files_in(preffix) ] 
        
 
        inj,prod,loc,events = None, None, None, None
        csv_files = [f for f in paths if '.csv' in f] 
        parse_dates = True 
        for file_name in csv_files:
            if 'injectors' in file_name.lower(): inj    = self.read_csv( file_name, parse_dates=parse_dates, nrows=nrows )
            if 'producers' in file_name.lower(): prod   = self.read_csv( file_name, parse_dates=parse_dates, nrows=nrows )
            if 'locations' in file_name.lower(): loc    = self.read_csv( file_name, parse_dates=parse_dates, nrows=nrows )
            if 'events'    in file_name.lower(): events = self.read_csv( file_name, parse_dates=parse_dates, nrows=nrows )

        
        
        data = CRMDataset.instance( inj,prod,loc,events)

        if filter_by is not None: 
            for key,value in filter_by.items(): data = data.filter_by( key, value )
        
        
        if meaning_columns is not None:
            known_columns = meaning_columns.copy()
            for word in meaning_columns:
                for keys in ALL_KEYWORDS: # keys = a list of strings 

                    if word in keys:  known_columns.extend(keys) 
                    elif word.lower() in keys: known_columns.extend(keys)  
                    elif word.upper() in keys: known_columns.extend(keys)   
                    else:
                        #nothing to do, it isnt there 
                        pass 
                    
            known_columns = set(known_columns)
            known_columns1 = list( set(data.injectors_df.columns).intersection(known_columns) )
            data.injectors_df = data.injectors_df[ known_columns1 ].copy()  
            
            
            known_columns2 = list( set(data.producers_df.columns).intersection(known_columns) )
            data.producers_df = data.producers_df[ known_columns2 ].copy()
            
            known_columns3 = list( set(data.locations_df.columns).intersection(known_columns) )
            data.locations_df = data.locations_df[ known_columns3 ].copy()
            
            if data.events_df is not None: 
                known_columns4 = list( set(data.events_df.columns).intersection(known_columns) )
                data.events_df = data.events_df[  known_columns4 ].copy()
                if len(data.events_df.columns) < 1: data.events_df = pd.DataFrame( {} )
          
        if len(data.injectors_df.columns) < 1: data.injectors_df = pd.DataFrame( {} )
        if len(data.producers_df.columns) < 1: data.producers_df = pd.DataFrame( {} )
        if len(data.locations_df.columns) < 1: data.locations_df = pd.DataFrame( {} )
            
                    
        data.name = dataset_name  
        return data 
  

    def read_csv( self, path, parse_dates=False, nrows = None ):

 
        target_path=path.replace('\\','/').replace('//','/')
        date_format = DATE_FORMAT 
        
        try:
            handle = self._get_handle()
            
            with handle.get_file( target_path ) as fd:
                df = pd.read_csv(fd.raw, nrows = nrows,parse_dates=parse_dates )#, encoding='utf-8-sig' )
                
                if parse_dates:
                
                    date_cols = [col_name for col_name in df.columns if 'date' in col_name.lower()]
                    if len(date_cols)>0: 
                        for date_col in  date_cols:
                            #df[date_col] = pd.to_datetime( df[date_col], format = "%Y-%m-%d").astype('datetime64[D]')
                            df[date_col] = pd.to_datetime( df[date_col], format = date_format).astype('datetime64[D]')
                            
                            
                
                #        RawDataProcessing().process_dates( df )
                
                return df 
        except:
            print('error reading file ', target_path )
            raise 
   
    
    #create
    def create_study( self, project_name, study_name, description=None, overwrite = True ):
        '''
        Creates a study folder passing an optional json description that describes the study. 
        If the study exists, it gets overwritten according to an overwrite flag.
        The description file will be named study_name.cfg 
        '''
        if study_name in self.list_project_studies( project_name ):
            
      
            if not overwrite:
                return  False 
            
            #delete the study (overwrite )
            else:
                self.delete_study( project_name,study_name )
        
        
        target_path = os.path.join( self.studies_folder_path( project_name ),study_name,study_name+'.cfg'  )
        target_path=target_path.replace('\\','/').replace('//','/')
        self._create_path( target_path, description)
        return True 
    
    #delete
    def delete_study( self,project_name, study_name ):
        path =  os.path.join(self.studies_folder_path( project_name ), study_name)
        path=path.replace('\\','/').replace('//','/')                                   
        self._delete_path(path)
      
    
    def list_study_files( self,project_name, study_name ):
        path =  os.path.join(self.studies_folder_path( project_name ), study_name)+'/'
        path=path.replace('\\','/').replace('//','/')
        return self.list_files_in( path )


    def list_project_studies( self, project_name ): 
        preffix = self.studies_folder_path( project_name )+'/'
        preffix = preffix.replace('\\','/').replace('//','/')
        
        return self.list_subfolders_in( preffix )

    
    def list_files_in( self, preffix ):

        handle = self._get_handle();
        files = [file['path'].replace(preffix, '') for file in  handle.list_contents()['items'] if preffix in file['path']  ]
        return files 

 
    def list_subfolders_in( self, preffix ):

        files = self.list_files_in(preffix) 
        files = list(set( file[0:file.find('/')].strip() for file in  files if '/' in file))
        files = [f for f in files if len(f)>1]
        return files 
                             
  
    def crm_dataset_from_dataiku_tables( self,inj_table_name, prod_table_name, loc_table_name, set_dates_as_index= False ):
    
        inj  = self.fetch_dataiku_dataset_by_name( inj_table_name,set_dates_as_index)
        prod = self.fetch_dataiku_dataset_by_name( prod_table_name,set_dates_as_index)
        loc  = self.fetch_dataiku_dataset_by_name( loc_table_name,set_dates_as_index)
        
        return CRMDataset.instance( inj, prod, loc )
        
        
    def create_dataset_from_dataframes( self,project_name, dataset_name, inj_df, prod_df, loc_df ):
    
        crm_dataset = CRMDataset.instance( inj_df, prod_df, loc_df )
    
        self.save_dataset( dataset_name, project_name, crm_dataset )
        
        return crm_dataset 
        

    def restore_simulation_model_from_path( self, target_path ):
        #private not public
        target_path=target_path.replace('\\','/').replace('//','/')
        
        restored = None 
        try:
            handle = self._get_handle() 
            with handle.get_file( target_path ) as fd:
                restored = pickle.loads(fd.content)
        except Exception as e:
            pass 

        return restored 
     
        
    def save_simulation_model_to_path( self, model, path ):
        self.upload_binary_data( path, pickle.dumps(model) )
        
                           
      
    def list_dataiku_tables(self):
        
        client = self._get_client()
        return [item['name'] for item in client.get_default_project().list_datasets() ] 
            
            

    ###############################################
    #      support methods and private methods   #
    ###############################################
    
    def _delete_path( self, path ): 
        self._get_handle().delete_file( path )

    def _create_path( self, target_path, obj=None):
        '''
        Creates a path --FILE--  within a managed folder. PRIVATE 
        '''
        self._get_handle().put_file(target_path, json.dumps( obj ))
  
        
    @property
    def app_base_adress(self):
        path = '/'.join([ self._app_name])
        return path.replace('//','/').replace('\\','/')

    
    @property
    def projects_base_address(self) :
        path = '/'+'/'.join([self.app_base_adress,self._projects_folder_name])
        return path.replace('//','/').replace('\\','/')

     
    def project_folder_path( self,project_name ): 
        '''
        Returns the full path of the project subfolder within the apprication and managed local folder
        '''
        return os.path.join( self.projects_base_address, project_name ).replace('//','/').replace('\\','/')
    
    def data_folder_path( self,project_name ): 
        '''
        Returns the full path of the data subfolder within a project folder
        '''
        return os.path.join( self.projects_base_address, project_name, self._data_folder_name ).replace('//','/').replace('\\','/')
    
    def studies_folder_path( self,project_name ): 
        '''
        Returns the full path of the studies subfolder within a project folder
        '''
        return os.path.join( self.projects_base_address, project_name, self._studies_folder_name ).replace('//','/').replace('\\','/')
      
    def study_folder_path( self,project_name, study_name ): 
        return os.path.join( self.studies_folder_path(project_name),study_name).replace('//','/').replace('\\','/')
        
    def dataset_folder_path( self,project_name, dataset_name ): 
        return os.path.join( self.data_folder_path(project_name),dataset_name).replace('//','/').replace('\\','/')
       
    def upload_binary_data(self, target_path, binary_data):
        
        target_path = target_path.replace('\\','/').replace('//','/')
        
        handle = self._get_handle()     
        handle.put_file(target_path, binary_data)
             
    def write_csv( self, target_path, df:[ pd.DataFrame, str ], index=False ):
        
        target_path = target_path.replace('\\','/').replace('//','/')
        
        
        if isinstance( df, pd.DataFrame ):
            self.upload_binary_data( target_path, df.to_csv(date_format=DATE_FORMAT, index=index))
        else: 
            self.upload_binary_data( target_path, df)             
        
    def read_json( self, path ):
        
        handle = self._get_handle() 
        try:
            ret = handle.get_file( path )
            if ret.status_code == 200:
                return ret.json()
            else:
                raise ValueError('Couldnt fetch the description')
            
        except:
            return {}
   
    def get_sim_results( self, project, sim_name ):

        known_files = ['crm.csv', 'rates.csv', 'optimization.txt' ]  
        files = [ f for f in self.list_study_files( project, sim_name) if f in known_files ]
 
        data = {} 
        crm, rates = None,None  
        parse_dates = True 
        nrows = None 
        data = {} 
        crm, rates = None,None  
        parse_dates = True 
        nrows = None 

        for file_name in files:
            path = self.studies_folder_path(project) + '/'+sim_name+'/' + file_name
          
            if 'crm' in file_name.lower(): 
                crm    = self.read_csv( path, parse_dates=parse_dates, nrows=nrows )
                ####PATCH####
                col_weird = [ col for col in crm.columns if 'unnamed' in col.lower()]
                if any( col_weird ):
                    crm.drop( col_weird,inplace=True, axis = 1 )
                #END OF PATCH 
                data['crm'] = crm
                
            if 'rates' in file_name.lower(): 
                rates  = self.read_csv( path, parse_dates=parse_dates, nrows=nrows )
                rates.reset_index( inplace=True, drop = True ) 
                data['rates'] = rates 


            if 'optimization.txt' in file_name.lower(): 
                print('parsing here ')
                opt = self.read_json( path )#, 'optimization.txt' )
                data['optimization'] = opt        
        
        inj,prod,loc,events = None,None,None,None
        files = [ f for f in self.list_study_files( project, sim_name) if 'dataset' in f ]
        for file_name in files:
          
            path = self.studies_folder_path(project) + '/'+sim_name+'/' + file_name

            if 'dataset/injectors_df.csv'==file_name.lower():
                inj = self.read_csv( path, parse_dates=parse_dates)
            if 'dataset/producers_df.csv' in file_name:
                prod = self.read_csv(path, parse_dates=parse_dates )
            if 'dataset/locations_df.csv' in file_name:
                loc = self.read_csv( path, parse_dates=parse_dates )
            if 'dataset/events_df.csv' in file_name:
                events = self.read_csv( path, parse_dates=parse_dates )
            
        if (inj is not None) and (prod is not None) and (loc is not None):
            data['dataset'] = CRMDataset.instance( inj, prod, loc, events) 
            
        return data      
        

        
    #def write_dataset_csv( self, project_name, dataset_name, file_name, binary_data, index = False ):
    #    target_path = os.path.join( self.data_folder_path( project_name ),dataset_name,file_name  )
    #    target_path=target_path.replace('\\','/').replace('//','/')
    #    self._create_path( target_path, description ) 
    #    
    #    self.write_csv( target_path, binary_data, index=index ) 
        
    
        
    def fetch_dataiku_dataset_by_name(self, path, set_dates_as_index= False ):
    
        _df =  dataiku.Dataset( path ).get_dataframe()#sampling='head', limit=3000)

        for c in _df.columns:  # date_columns:
            if c in DATE_KEYS:
                _dates =  pd.to_datetime(_df[c], format=DATE_FORMAT)#.values.astype('datetime64[D]')
                _df[c] = _dates.values.astype('datetime64[D]')
      

        if "DATE" in _df.columns:
            if set_dates_as_index is True:
                _df.set_index("DATE", inplace=True, drop=True)

        return _df
   




class oldDataikuStorageAPI:
    
    '''
    This class defines all the methods needed for the Ui and the workflows
    
    The derived classes implement some specializations needed if calling the class from 
    outside Dataiku (remote folder)
    '''

    
    def __init__(self, **kwargs  ):
        
        self.args = {} 
        for kwarg, value in kwargs.items(): 
            self.args[kwarg] = value 
            

    def list_managed_folders(self):
        pass

    def restore_simulation_model( self, target_path ):
        #private not public
        target_path=target_path.replace('\\','/').replace('//','/')
        
        restored = None 
        try:
            handle = self.get_handle() 
            with handle.get_file( target_path ) as fd:
                restored = pickle.loads(fd.content)
        except: 
            pass 

        return restored 
       
    def save_simulation_model( self, model, path ):
        self.upload_binary_data( path, pickle.dumps(model) )
        

    def save_dataset( self, name, project, dataset ):

        self.create_project( project )
        self.create_dataset( project, name )
        
        path = self. data_folder_path( project) + '/'+ name 
        
        self.write_csv( path + '/injectors.csv',  dataset.injectors_df)
        self.write_csv( path + '/producers.csv',  dataset.producers_df)
        self.write_csv( path + '/locations.csv',  dataset.locations_df)
 
    def list_contents( self ): 
        print( self._get_handle().list_contents())
    
    def list_files_in( self, preffix ):

        handle = self._get_handle();
        files = [file['path'].replace(preffix, '') for file in  handle.list_contents()['items'] if preffix in file['path']  ]
        return files 

    def list_subfolders_in( self, preffix ):

        files = self.list_files_in(preffix) 
        files = list(set( file[0:file.find('/')].strip() for file in  files if '/' in file))
        files = [f for f in files if len(f)>1]
        return files 
    
    
    #listing projects and contents in projects   
    def list_projects(self):
        
        #we are looking for the subfolders inside the projects_base_address
        preffix = self.projects_base_address+'/'
        preffix = preffix.replace('\\','/').replace('//','/')
        
        return self.list_subfolders_in( preffix )
          
        
    def list_project_datasets( self, project_name ): 
        preffix = self.data_folder_path( project_name )+'/'
        preffix = preffix.replace('\\','/').replace('//','/')
 
        return self.list_subfolders_in( preffix )
    
    
    def list_project_studies( self, project_name ): 
        preffix = self.studies_folder_path( project_name )+'/'
        preffix = preffix.replace('\\','/').replace('//','/')
        
        return self.list_subfolders_in( preffix )

        
    #creating and deleting a project 
    def create_project( self, project_name, description=None ):
        
        target_path = self.project_folder_path( project_name ) + '/timestamp.cfg'
        target_path = target_path.replace('\\','/').replace('//','/')
        
        obj = { 
              'project_name': project_name
        }
        
        if project_name not in self.list_projects():
            obj['creation_date'] = str(date.today())
           
        if description: obj.update( description )
            
        #project 
        self._create_path( target_path, obj )
        
        #data folder inside 
        data_path = self.data_folder_path( project_name )+ '/timestamp.cfg'
        self._create_path( data_path,obj )

        #studies folder inside 
        studies_path = self.studies_folder_path( project_name )+ '/timestamp.cfg'
        self._create_path( studies_path,obj )


    def delete_project( self, project_name ):
        
        target_path = self.project_folder_path( project_name ) 
        target_path=target_path.replace('\\','/').replace('//','/')
        handle = self._get_handle()
        files = [ f['path'] for f in handle.list_contents()['items'] if target_path in f['path']  ] 
        
        for path in files:  self._delete_path( path )
        
        self._delete_path( target_path )
    
    #delete
    def delete_dataset( self,project_name, dataset_name ):
        path =  os.path.join(self.data_folder_path( project_name ), dataset_name)
        path=path.replace('\\','/').replace('//','/')
        self._delete_path(path)
        
    #create
    def create_dataset( self, project_name, data_name, description=None, overwrite = True ):
        '''
        Creates a study folder passing an optional json description that describes the study. 
        If the study exists, it gets overwritten according to an overwrite flag.
        The description file will be named study_name.cfg 
        '''
        if data_name in self.list_project_datasets( project_name ):
            if not overwrite:
                return  False 
            
            else:
                self.delete_dataset( project_name,data_name )
        
        
        target_path = os.path.join( self.data_folder_path( project_name ),data_name,data_name+'.cfg'  )
        target_path=target_path.replace('\\','/').replace('//','/')
        self._create_path( target_path, description )
        return True 

    def list_study_files( self,project_name, study_name ):
        path =  os.path.join(self.studies_folder_path( project_name ), study_name)+'/'
        path=path.replace('\\','/').replace('//','/')
        return self.list_files_in( path )

    
    def list_dataset_files( self,project_name, dataset_name ):
        path =  os.path.join(self.data_folder_path( project_name ), dataset_name)+'/'
        path=path.replace('\\','/').replace('//','/')
        return self.list_files_in( path  )
    


    #create
    def create_study( self, project_name, study_name, description=None, overwrite = True ):
        '''
        Creates a study folder passing an optional json description that describes the study. 
        If the study exists, it gets overwritten according to an overwrite flag.
        The description file will be named study_name.cfg 
        '''
        if study_name in self.list_project_studies( project_name ):
            
      
            if not overwrite:
                return  False 
            
            #delete the study (overwrite )
            else:
                self.delete_study( project_name,study_name )
        
        
        target_path = os.path.join( self.studies_folder_path( project_name ),study_name,study_name+'.cfg'  )
        target_path=target_path.replace('\\','/').replace('//','/')
        self._create_path( target_path, description)
        return True 
    
    #delete
    def delete_study( self,project_name, study_name ):
        path =  os.path.join(self.studies_folder_path( project_name ), study_name)
        path=path.replace('\\','/').replace('//','/')                                   
        self._delete_path(path)
                                            
                                  
    def _delete_path( self, path ): 
        self._get_handle().delete_file( path )

    def _create_path( self, target_path, obj=None):
        '''
        Creates a path --FILE--  within a managed folder. PRIVATE 
        '''
        self._get_handle().put_file(target_path, json.dumps( obj ))
  

    ###############################################
    #      support methods and priovate methods   #
    ###############################################
        
    @property
    def app_base_adress(self):
        path = '/'.join([ self._app_name])
        return path.replace('//','/').replace('\\','/')

    
    
    @property
    def projects_base_address(self) :
        path = '/'+'/'.join([self.app_base_adress,self._projects_folder_name])
        return path.replace('//','/').replace('\\','/')



        
    def project_folder_path( self,project_name ): 
        '''
        Returns the full path of the project subfolder within the apprication and managed local folder
        '''
        return os.path.join( self.projects_base_address, project_name ).replace('//','/').replace('\\','/')
    
    def data_folder_path( self,project_name ): 
        '''
        Returns the full path of the data subfolder within a project folder
        '''
        return os.path.join( self.projects_base_address, project_name, self._data_folder_name ).replace('//','/').replace('\\','/')
    
    def studies_folder_path( self,project_name ): 
        '''
        Returns the full path of the studies subfolder within a project folder
        '''
        return os.path.join( self.projects_base_address, project_name, self._studies_folder_name ).replace('//','/').replace('\\','/')
      
  
    def study_folder_path( self,project_name, study_name ): 
        return os.path.join( self.studies_folder_path(project_name),study_name).replace('//','/').replace('\\','/')
        
    def dataset_folder_path( self,project_name, dataset_name ): 
        return os.path.join( self.data_folder_path(project_name),dataset_name).replace('//','/').replace('\\','/')

 

    def get_dataset( self, project_name, dataset_name, filter_by = None, nrows = None, meaning_columns = None ):  


        
        preffix = os.path.join(self.data_folder_path(project_name),dataset_name).replace('//','/').replace('\\','/')
        paths   = [preffix + '/'+ f for f in self.list_files_in(preffix) ] 
        
 
        inj,prod,loc,events = None, None, None, None
        csv_files = [f for f in paths if '.csv' in f] 
        parse_dates = True 
        for file_name in csv_files:
            if 'injectors' in file_name.lower(): inj    = self.read_csv( file_name, parse_dates=parse_dates, nrows=nrows )
            if 'producers' in file_name.lower(): prod   = self.read_csv( file_name, parse_dates=parse_dates, nrows=nrows )
            if 'locations' in file_name.lower(): loc    = self.read_csv( file_name, parse_dates=parse_dates, nrows=nrows )
            if 'events'    in file_name.lower(): events = self.read_csv( file_name, parse_dates=parse_dates, nrows=nrows )

        
        
        data = CRMDataset.instance( inj,prod,loc,events)

        if filter_by is not None: 
            for key,value in filter_by.items(): data = data.filter_by( key, value )
        
        
        if meaning_columns is not None:
            known_columns = meaning_columns.copy()
            for word in meaning_columns:
                for keys in ALL_KEYWORDS: # keys = a list of strings 

                    if word in keys:  known_columns.extend(keys) 
                    elif word.lower() in keys: known_columns.extend(keys)  
                    elif word.upper() in keys: known_columns.extend(keys)   
                    else:
                        #nothing to do, it isnt there 
                        pass 
                    
            known_columns = set(known_columns)
            known_columns1 = list( set(data.injectors_df.columns).intersection(known_columns) )
            data.injectors_df = data.injectors_df[ known_columns1 ].copy()  
            
            
            known_columns2 = list( set(data.producers_df.columns).intersection(known_columns) )
            data.producers_df = data.producers_df[ known_columns2 ].copy()
            
            known_columns3 = list( set(data.locations_df.columns).intersection(known_columns) )
            data.locations_df = data.locations_df[ known_columns3 ].copy()
            
            if data.events_df is not None: 
                known_columns4 = list( set(data.events_df.columns).intersection(known_columns) )
                data.events_df = data.events_df[  known_columns4 ].copy()
                if len(data.events_df.columns) < 1: data.events_df = pd.DataFrame( {} )
          
        if len(data.injectors_df.columns) < 1: data.injectors_df = pd.DataFrame( {} )
        if len(data.producers_df.columns) < 1: data.producers_df = pd.DataFrame( {} )
        if len(data.locations_df.columns) < 1: data.locations_df = pd.DataFrame( {} )
            
                    
        data.name = dataset_name  
        return data 
    
    
    
    def read_csv( self, path, parse_dates=False, nrows = None ):

        target_path=path.replace('\\','/').replace('//','/')
        try:
            handle = self._get_handle()
            
            with handle.get_file( target_path ) as fd:
                df = pd.read_csv(fd.raw, nrows = nrows )#, encoding='utf-8-sig' )
                
                if parse_dates:
                    date_cols = [col_name for col_name in df.columns if 'date' in col_name.lower()]
                    if len(date_cols)>0: 
                        RawDataProcessing().process_dates( df )
                
                return df 
        except:
            print('error reading file ', target_path )
            raise 
             
             
   

    def upload_binary_data(self, target_path, binary_data):
        
        target_path = target_path.replace('\\','/').replace('//','/')
        
        handle = self._get_handle()     
        handle.put_file(target_path, binary_data)
             


    def write_csv( self, target_path, df:[ pd.DataFrame, str ], index=False ):
        
        target_path = target_path.replace('\\','/').replace('//','/')
        
        
        if isinstance( df, pd.DataFrame ):
            self.upload_binary_data( target_path, df.to_csv(index=index))
        else: 
            self.upload_binary_data( target_path, df)
                
        
    def read_json( self, path ):
        
        handle = self._get_handle() 
        try:
            ret = handle.get_file( path )
            if ret.status_code == 200:
                return ret.json()
            else:
                raise ValueError('Couldnt fetch the description')
            
        except:
            return {}
   

    def get_sim_results( self, project, sim_name ):

        known_files = ['crm.csv', 'rates.csv', 'optimization.txt' ]  
        files = [ f for f in self.list_study_files( project, sim_name) if f in known_files ]
 
        data = {} 
        crm, rates = None,None  
        parse_dates = True 
        nrows = None 
        data = {} 
        crm, rates = None,None  
        parse_dates = True 
        nrows = None 

        for file_name in files:
            path = self.studies_folder_path(project) + '/'+sim_name+'/' + file_name
          
            if 'crm' in file_name.lower(): 
                crm    = self.read_csv( path, parse_dates=parse_dates, nrows=nrows )
                ####PATCH####
                col_weird = [ col for col in crm.columns if 'unnamed' in col.lower()]
                if any( col_weird ):
                    crm.drop( col_weird,inplace=True, axis = 1 )
                #END OF PATCH 
                data['crm'] = crm
                
            if 'rates' in file_name.lower(): 
                rates  = self.read_csv( path, parse_dates=parse_dates, nrows=nrows )
                rates.reset_index( inplace=True, drop = True ) 
                data['rates'] = rates 


            if 'optimization.txt' in file_name.lower(): 
                print('parsing here ')
                opt = self.read_json( path )#, 'optimization.txt' )
                data['optimization'] = opt        
        
        inj,prod,loc,events = None,None,None,None
        files = [ f for f in self.list_study_files( project, sim_name) if 'dataset' in f ]
        for file_name in files:
          
            path = self.studies_folder_path(project) + '/'+sim_name+'/' + file_name

            if 'dataset/injectors_df.csv'==file_name.lower():
                inj = self.read_csv( path, parse_dates=parse_dates)
            if 'dataset/producers_df.csv' in file_name:
                prod = self.read_csv(path, parse_dates=parse_dates )
            if 'dataset/locations_df.csv' in file_name:
                loc = self.read_csv( path, parse_dates=parse_dates )
            if 'dataset/events_df.csv' in file_name:
                events = self.read_csv( path, parse_dates=parse_dates )
            
        if (inj is not None) and (prod is not None) and (loc is not None):
            data['dataset'] = CRMDataset.instance( inj, prod, loc, events) 
            
        return data      
        
 
