import  dataikuapi
import pandas as pd 

from wf_lib2.data.crm_dataset import CRMDataset 
from wf_lib2.data.dataiku_storage_api import DataikuStorageAPI #


import warnings
warnings.filterwarnings(action='ignore', category=UserWarning) 


class DataikuRemoteFolderConnector(DataikuStorageAPI):
 

    def __init__(self, config, kwargs = None  ):
        '''
        example: 
            
 
           
           config = 
            {
            'managed_folder_name':'Data',
            
            'app_name':'WFDemo'
            
            'data_folder_name':'data', #(optional,if not given it is set to data. It is relative to the project path )
            'projects_folder_name':'projects', #(optional,if not given it is set to projects )
            'studies_folder_name':'studies', #(optional,if not given it is set to studies. It is relative to the project )


             'host': xxxxx,  project_api_key: xxxx   
            
            } 



        '''
        if kwargs is not None:
            super().__init__(  **kwargs )
        else:
            super().__init__(  )
        
        try: 
            self._folder_name = config.get('managed_folder_name','')  
            self._app_name    = config['app_name'] if 'app_name' in config else ''
            
            self._projects_folder_name = 'projects' if 'projects_folder_name' not in config else config['projects_folder_name'] 
            self._studies_folder_name  = 'studies'  if 'studies_folder_name'  not in config else config['studies_folder_name'] 
            self._data_folder_name     = 'data'     if 'data_folder_name'     not in config else config['data_folder_name'] 
            self._folder_id = None 
            self._client = None 
               
            self._data_folder_name=self._data_folder_name.strip()
            self._studies_folder_name=self._studies_folder_name.strip()
            self._projects_folder_name=self._projects_folder_name.strip()
          
        
            special=['/','\\']
            
            if self._studies_folder_name[0] in special:
                self._studies_folder_name = self._studies_folder_name[1:]
                
            if self._data_folder_name[0] in special:
                self._data_folder_name = self._data_folder_name[1:]
       
            if self._projects_folder_name[0] in special:
                self._projects_folder_name = self._projects_folder_name[1:]
                
            
            ##############
            self._client= None 
            self._host = config['host']
            self._project_api_key = config['project_api_key'] 
                
            self._client = dataikuapi.DSSClient(self._host, self._project_api_key)
            project_metadata = self._client.list_projects()[0]
            
            self._project_id = project_metadata['projectKey']
            p = self._client.get_project(   self._project_id    )

            
            known_folders = list( (item['name'],str(item['id'])) for item in p.list_managed_folders() )
            managed_folders = [(item[0],item[1]) for item in known_folders 
                                if self._folder_name.lower()==item[0].lower()]
            
            if any(managed_folders):
                self._folder_id = managed_folders[0][1]
      
                
            #else:
            #    raise ValueError('Cannot find the managed folder in the given project')
            
            



            
        except Exception as e:
            print('Invalid arguments. ', e)
            raise( e )
        

    def setManagedFolder( self, name ):
        
        p = self._get_client().get_project(  self._project_id    )
        known_folders = list( (item['name'],str(item['id'])) for item in p.list_managed_folders() )
        managed_folders = [(item[0],item[1]) for item in known_folders if name.lower()==item[0].lower()]
            
        if any(managed_folders):
            self._folder_id = managed_folders[0][1]
            self._folder_name = name 
            return True
        
        return False

    
    @staticmethod 
    def list_managed_folders(host, project_api_key, keys = None):
        '''
        This is a wrapper around Dataiku functionality inside the dataiku package that simply
        returns a list of string where each element corresponds to the name of one managed folder 
        found in the default dataiku project.

        keys (optional) is a list of strings. If passed as argument, the function returns 
        as before a list but this time a list of dictionaries, one per folder. The keys are the 
        properties of the folder correspnding to ksys. 
        '''
        client = dataikuapi.DSSClient(host, project_api_key)
        project_metadata = client.list_projects()[0]
        project_id = project_metadata['projectKey']
        p = client.get_project(   project_id   )
        d = p.list_managed_folders() 

      
        if keys is None:
            managed_folder_names = [ item['name'] for item in d ] 
            return managed_folder_names  

 
        #check if iterable 
        #then check all items in keys are strings
        return [ {key:item[key] for key in keys }  for item in d ]



    def _get_handle(self): 
        return self._get_client().get_project(self._project_id).get_managed_folder(self._folder_id)
      
    def _get_client( self ):
        if self._client is None:
            self._client = dataikuapi.DSSClient(self._host, self._project_api_key)

        return self._client
        

    @staticmethod       
    def read_dataset( host, project_api_key, managed_folder_name, path ):
  
        def read_csv(  path, handle, parse_dates=False, nrows = None ):

            target_path=path.replace('\\','/').replace('//','/')
            try:
                with handle.get_file( target_path ) as fd:

                    print( target_path )    

                    df = pd.read_csv(fd.raw, nrows = nrows )#, encoding='utf-8-sig' )
                    
                    if parse_dates:
                        date_cols = [col_name for col_name in df.columns if 'date' in col_name.lower()]
                        if len(date_cols)>0: 
                            col_name = date_cols[0]
                            dates = pd.to_datetime(df[col_name])
                            df.drop(col_name, inplace=True, errors='ignore', axis=1)
                            df.insert(0, col_name, dates)

                    return df 

            except Exception as e:
                print( e ) 
                raise 


        _client = dataikuapi.DSSClient(host, project_api_key)
        _project_metadata = _client.list_projects()[0]
        _project_id = _project_metadata['projectKey']
        p = _client.get_project(   _project_id   )
        known_folders = list( (item['name'],str(item['id'])) for item in p.list_managed_folders() )
        managed_folders = [(item[0],item[1]) for item in known_folders if managed_folder_name.lower()==item[0].lower()]
            
        if not any(managed_folders):
            return None 
    



        _folder_id = managed_folders[0][1]
        handle = _client. get_project(_project_id).get_managed_folder(_folder_id)

        preffix = path 
        if preffix[0] != '/': preffix = '/' + preffix  
        files = [file['path'] for file in  handle.list_contents()['items'] if preffix in file['path']  ]

        inj,prod,loc,events = None, None, None, None
        csv_files = [f for f in files if '.csv' in f] 
        parse_dates = True 
        for file_name in csv_files:
            if 'injectors' in file_name.lower(): inj    = read_csv( file_name, handle,parse_dates=parse_dates  )
            if 'producers' in file_name.lower(): prod   = read_csv( file_name, handle,parse_dates=parse_dates )
            if 'locations' in file_name.lower(): loc    = read_csv( file_name, handle,parse_dates=parse_dates )
            if 'events'    in file_name.lower(): events = read_csv( file_name, handle,parse_dates=parse_dates )


        data = CRMDataset.instance( inj,prod,loc,events)
        return data 
 