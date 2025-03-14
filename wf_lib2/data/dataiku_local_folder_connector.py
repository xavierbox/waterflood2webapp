
import pandas as pd, pickle 
import  dataiku
from wf_lib2.crm_definitions import * 
from wf_lib2.data.crm_dataset import CRMDataset 
from wf_lib2.data.crm_data_utils import find_columns, dataframe_to_json,aggregate_column
from wf_lib2.data.dataiku_storage_api import DataikuStorageAPI 



import warnings
warnings.filterwarnings(action='ignore', category=UserWarning) 
 
    
    
    
class DataikuLocalFolderConnector(DataikuStorageAPI):
 

    '''
    To be used outside dataiku in a client program  (a notebook a webapp, etc) to access the data 
    in a managed folder inside a remote dataiku project. We need the host and the api keys of the project
    '''

    def __init__(self, config, kwargs = None  ):
        '''

        The class assumes a set structure for the managed folder. At the top is the application name
        Inside it, one can have a sub-folder for projects and inside each of these, there is a folder
        for data and one for studies. 

        This info is passed to the class constructor in a dictionary. Below is an example

        Example of the configuration passed to the class: 
            
            config = 
            {
            'managed_folder_name':'Data',
            
            'app_name':'WWW-WFDemo'
            
            'data_folder_name':'XXdata', #(optional,if not given it is set to data. It is relative to the project path )
            
            'projects_folder_name':'YYprojects', #(optional,if not given it is set to projects )
            
            'studies_folder_name':'ZZstudies', #(optional,if not given it is set to studies. It is relative to the project )
            
            } 
            
            Example of the managed folder structure:
            
            ManagedFolder 
                    
                    App1 
                    
                    App2
                    
                    WWW-WFDemo              app_name (the application) 
                        YYprojects          the name of  the sub-folder for projects 
                            Project1        whatever project name 
                            Project2        ...
                            Project3        ... 
                                XXdata          data folder inside each project 
                                    dataset1
                                    dataset2
                                    dataset3
                                ZZstudies       studies folder inside each project 
                                    study1
                                    study2
                                    ...
            
            
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
                
            
            client = self._get_client()
        
            
            known_folders  = [ f['id'] for f in client.get_default_project().list_managed_folders() if f['name'] == self._folder_name ]
            
            if any(known_folders):
                
                self._folder_id = known_folders[0]
                self.set_managed_folder( self._folder_name )
            
        
            
        except Exception as e:
            print('Invalid arguments. ', str(e))
            raise( e )
          

    def _get_handle( self ):
        return self._get_client().get_default_project().get_managed_folder( self._folder_id )

      
    def _get_client( self ):
        if self._client is None: 
            self._client=dataiku.api_client()
        return self._client
        

    def set_managed_folder( self, name ):
        
        p = self._get_client().get_default_project()
        known_folders = list( (item['name'],str(item['id'])) for item in p.list_managed_folders() )
        managed_folders = [(item[0],item[1]) for item in known_folders if name.lower()==item[0].lower()]
            
        if any(managed_folders):
            self._folder_id = managed_folders[0][1]
            self._folder_name = name 
            return True
        
        return False
  

class KOCDataikuLocalStorageConnector(DataikuLocalFolderConnector):

    '''
    This object was created to support the KOC project.
    It inherits most of its functionality from wf_lib2 but adds bits and pieces to support the UI and the multi-RMU data. 
    
    
    Will work assuming only one zone (ONE reservoir) per project although there  might be one or more subzones (RMU)
    
    It is assumed one dataset per project.
    In other words, the dataset contains only one zone 
    
    '''

    def __init__(self, config, kwargs = None  ):
        super().__init__( config, kwargs )
        
        
        for arg, value in config.items(): 
            self.args[arg] = value 
                        
    def _filter_by( self, df, keywords, in_values ):
        
        values = in_values 
        if not isinstance(in_values,list):
            values=[in_values]
        
        column_name = find_columns(df.columns, keywords)[0]
        df = df[df[column_name].isin( values )].copy()

        return df 
    
    def _get_default_dataset_name( self ):
        '''
        returns the first one listed. In koc there is only one per project allowed so...thats the one
        '''
        
        project_name = self.args['project_name'] 
        datasets = self.list_project_datasets( project_name )
        print('datasets in project ', datasets )
        if datasets is None or len(datasets) < 1: 
            error = 'Cant find a dataset associated with propject '+ project_name 
            raise ValueError( error )
            
        return datasets[0]
            
        
        
    #old: get_well_locations and locations_df property   
    def fetch_locations_dataiku_table( self, zones = None   ):
        
        locs = self.fetch_dataiku_dataset_by_name( self.args['locations_dataiku_table'])
    
        if zones is not None: 
            if isinstance( zones, str ): 
                zones = [zones]
                
                
            locs = locs[ locs['ZONE'].isin( zones ) ]
        
        
        
        zone_names = list(locs["ZONE"].unique())
        subzones = {zone: list(locs[locs["ZONE"] == zone]["SUBZONE"].unique()) for zone in zone_names}
        ui_locs = { zone_name:{} for zone_name in zone_names }

        dfs = [] 
        for zone_name in zone_names:
            zone_df = locs[ locs['ZONE'] == zone_name ] 
            
            for subzone_name in subzones[ zone_name ]:
                sub_zone_df = zone_df[ zone_df['SUBZONE'] == subzone_name ] 
                g = sub_zone_df.groupby( by =['NAME'], as_index = False)['X','Y','WELL_TYPE','SECTOR','ZONE','SUBZONE'].agg (
                    {
                        'X': pd.Series.mean,
                        'Y': pd.Series.mean,
                        'WELL_TYPE': pd.Series.mode,
                        'SECTOR': pd.Series.mode,
                        #'ZONE': pd.Series.mode,
                        #'SUBZONE': pd.Series.mode, 
                    }
                )       
                
                g['ZONE'] = zone_name 
                g['SUBZONE'] = subzone_name 
                
                
                dfs.append ( g )
                
        if len(dfs) == 0 :return pd.DataFrame({})
        
        df = pd.concat( dfs, axis = 0 )
        return df 
 

    def list_zones_in_dataset( self ):
        
        project_name = self.args['project_name'] 
        dataset_name = self._get_default_dataset_name()
        
        dataset = self.get_dataset( project_name, dataset_name )
        locations_df = dataset.locations_df
        
        col = find_columns( locations_df, ZONE_KEYS )
        if not col:
            error = f'Cant find one column for the ZONE/RESERVOIR. The known columns are { ",".join(ZONE_KEYS) } in the locations table '
            raise ValueError( error )
        
        zones  = list(locations_df[col[0]].unique())
        return zones 
        
        
    def list_csv_files_in_dataset( self ):
        
        project_name = self.args['project_name'] 
        dataset_name = self._get_default_dataset_name()
            
        path = self.dataset_folder_path( project_name, dataset_name )
        files = [name.replace('/','') for name in self.list_files_in( path ) if 'csv' in name] 
        return files 
        
        
        
    def get_well_locations( self ):#, zones = None ):
        '''
        Assumes only one reservoir per dataset and one dataset per project. Multiple subzones (RMUs) allowed
        '''
        
        
        project_name = self.args['project_name'] 
        dataset_name = self._get_default_dataset_name()
        
        dataset = self.get_dataset( project_name, dataset_name )
        locs = dataset.locations_df
        

        #if zones is not None: 
        #    if isinstance( zones, str ): 
        #        zones = [zones]
        #    
        #    locs = locs[ locs['ZONE'].isin( zones ) ]
        
        
        
        zone_names = list(locs["ZONE"].unique())
        subzones = {zone: list(locs[locs["ZONE"] == zone]["SUBZONE"].unique()) for zone in zone_names}
        ui_locs = { zone_name:{} for zone_name in zone_names }

        dfs = [] 
        for zone_name in zone_names:
            zone_df = locs[ locs['ZONE'] == zone_name ] 
            
            for subzone_name in subzones[ zone_name ]:
                sub_zone_df = zone_df[ zone_df['SUBZONE'] == subzone_name ] 
                g = sub_zone_df.groupby( by =['NAME'], as_index = False)['X','Y','WELL_TYPE','SECTOR','ZONE','SUBZONE'].agg (
                    {
                        'X': pd.Series.mean,
                        'Y': pd.Series.mean,
                        'WELL_TYPE': pd.Series.mode,
                        'SECTOR': pd.Series.mode,
                        'ZONE': pd.Series.mode,
                        'SUBZONE': pd.Series.mode, 
                    }
                )       
                
                dfs.append ( g )
                
                
        df = pd.concat( dfs, axis = 0 )
        return df 
        

    def well_rates( self, well_names:list = None, subzones:list = None, sectors:list = None ):
 
        def filter_by( df, keywords, values ):
            column_name = find_columns(df.columns, keywords)[0]
            df = df[df[column_name].isin( values )]
            return df 
        
     
        
        project_name = self.args['project_name'] 
        dataset_name = self._get_default_dataset_name()
        
        dataset = self.get_dataset( project_name, dataset_name )
        locations = dataset.locations_df
        
    
        if well_names is not None:
            if isinstance(well_names, str): well_names = [well_names]
            locations  = filter_by( locations, NAME_KEYS, well_names )
            
        #if zones is not None:
        #    if isinstance(zones, str): zones = [zones]
        #    locations  = filter_by( locations, ZONE_KEYS, zones )
            
        if subzones is not None:
            if isinstance(subzones, str): subzones = [subzones]
            locations  = filter_by( locations, SUBZONE_KEYS, subzones )
             
        if sectors is not None:
            if isinstance(sectors, int): sectors = [sectors]
            locations  = filter_by( locations, SECTOR_KEYS, sectors )
            
        NAME_COL = find_columns(locations.columns, NAME_KEYS)[0]
        filtered_well_names = locations[NAME_COL].unique()
        
        injectors_df = dataset.injectors_df
        producers_df = dataset.producers_df

        NAME_COL = find_columns(injectors_df.columns, NAME_KEYS)[0]
        inj  = injectors_df[ injectors_df[NAME_COL].isin( filtered_well_names )]
        NAME_COL = find_columns(producers_df.columns, NAME_KEYS)[0]
        prod = producers_df[ producers_df[NAME_COL].isin( filtered_well_names )]
        
        ##print("[Fixme]: hard-coded column names for INJECTION_VOLUME and WATER_VOLUME")
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
            water_production,
        )
            
         
    def get_injector_producer_locations_filtered( self, filters = None ):
        
        ''' 
        receives filters =  
        {
        'subzone': ['WARA-BOTTOM'], 
        'sector': ['1', '2', '8', '5', '4']
        'name':[name1, name2,...] (optional)
        }
        
        fetches the locations, injectors and producers and returns the slice copy of them that 
        satifies the filters. 
        ''' 
        
        if filters is None:
            filters = {} 
        
        project_name = self.args['project_name'] 
        dataset_name = self._get_default_dataset_name()
        dataset = self.get_dataset( project_name, dataset_name )
        locs_filtered = dataset.locations_df
        
        keys = list(filters.keys())
        
        for key in keys:
            
            cols  =  find_columns( [key], NAME_KEYS )
            if len(cols) > 0:
                name_key = cols[0] 
                if filters[ name_key ] is None: continue 
                
                locs_filtered = self._filter_by( locs_filtered, NAME_KEYS, filters[name_key] )
                df=locs_filtered
               
            cols  =  find_columns( [key], SUBZONE_KEYS )
            if len(cols) > 0:
                subzone_key = cols[0] 
                if filters[ subzone_key ] is None: continue 
                
                locs_filtered = self._filter_by( locs_filtered, SUBZONE_KEYS, filters[subzone_key] )
                df=locs_filtered
                
            cols  =  find_columns( [key], SECTOR_KEYS )
            if len(cols) > 0:
                sector_key = cols[0] 
                if filters[ sector_key ] is None: continue 
                
                sectors = [int(s) for s in  filters[sector_key] ]
                locs_filtered = self._filter_by( locs_filtered, SECTOR_KEYS, sectors )
                df=locs_filtered
 
        name_col= find_columns( locs_filtered.columns, NAME_KEYS )[0]
        names = list( locs_filtered[name_col].unique() )
        
        name_col= find_columns( dataset.injectors_df.columns, NAME_KEYS )[0]
        inj = dataset.injectors_df[ dataset.injectors_df[name_col].isin(names) ]
        
        name_col= find_columns( dataset.producers_df.columns, NAME_KEYS )[0]
        prod = dataset.producers_df[ dataset.producers_df[name_col].isin(names) ]

        
        return inj, prod, locs_filtered

        
    def _aux_get_injector_producer_pairs_filtered(  self,  inj, prod,locs, th_dist=None, return_distances=False ):

        '''
        receives the inj, prod, loc
        and return pairs as { prod_name:[ inj1, inj2...] } that are within the distance threshold per subzone 
        
        if return_distances = True 
        
        returns pairs as { prod_name: [ (inj1,dist),(inj2,dist2)...] } that are within the distance threshold
        
        '''

        if th_dist is None: th_dist = 50.0e3 #(50km)

        name, x, y = find_columns( locs.columns, NAME_KEYS )[0],find_columns( locs.columns, X_KEYS )[0],find_columns( locs.columns, Y_KEYS)[0] 
        name, x, y = locs[name].values, locs[x].values, locs[y].values 

        d = {} 
        for i in range(0,len(name)): d[name[i]] = [ x[i], y[i] ] 


        inj_names = inj[ find_columns(inj.columns, NAME_KEYS)[0] ].unique()
        prd_names = prod[ find_columns(prod.columns, NAME_KEYS)[0] ].unique()

        producer_injector_pairs = {} 
        
        injector_names= []
        producer_names= []
        for prd_name in prd_names:
            x1,y1  = d[prd_name ]
            
            for inj_name in inj_names:
                x2,y2  = d[inj_name ]
                
                d2 = ((x1-x2)**2) + ((y1-y2)**2) 
                if d2 < th_dist * th_dist:
                    
                    neighbours =  producer_injector_pairs.get( prd_name, [] )
                    injector_names.append( inj_name )
                    producer_names.append( prd_name )
                    
                    if return_distances:
                        neighbours.append( (inj_name, math.sqrt( d2 )) )
                    else:
                        neighbours.append( inj_name )
                        
                    producer_injector_pairs[ prd_name ] = neighbours

        for name, value in producer_injector_pairs.items():
            producer_injector_pairs[name] = {'injectors': value} 

        injector_names = list(set( injector_names ))
        producer_names = list(set( producer_names ))
        return  producer_injector_pairs, injector_names, producer_names

    
    def get_injector_producer_pairs_filtered( self, filters = None, distance = 999999, return_distances=False  ):
        ''' 
        receives filters =  
        {'not anymore zone': 'WARA', 
        'subzone': ['WARA-BOTTOM'], 
        'sector': ['1', '2', '8', '5', '4'] (optional)
        'name':[name1, name2,...] (optional)
        }
        
        fetches the locations, injectors and producers and returns the slice copy of them that 
        satifies the filters. 
        ''' 
        if filters is None: 
            filters = {} 
 
        inj, prod, locs =self.get_injector_producer_locations_filtered( filters )
        
        producer_injector_pairs, injector_names, producer_names = self._aux_get_injector_producer_pairs_filtered(inj, prod, locs, distance,return_distances )

        return producer_injector_pairs, injector_names, producer_names
 
 

    ################################################# 
    #           persistency of historical           #
    #################################################
    def save_models(self,models, simulation_name ):
        

        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        
        for model in models:
            optimization_result = model.optimization_result
            file_name = base_address +'/' + f"{optimization_result['name']}_{optimization_result['producer_names'][0]}_{optimization_result['subzone']}.model"

            handle = self._get_handle()     
            handle.put_file(file_name, pickle.dumps(model) )
            
    def list_models( self, simulation_name  ):
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        
        files = [f.replace('/','') for f in self.list_files_in( base_address ) if '.model' in f ]

         
        return files   
    
    def load_model(self, simulation_name, model_name ):
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        path = base_address + '/' + model_name 
        
       
        model = None 
        try:
            
            model = self.restore_simulation_model_from_path( path )
            return model  
        
        except Exception as e:
            print(f'Error fetching model {path}. Error {str(e)}')
            return None 
    
    '''
    def restore_simulation_model_from_path( self, target_path ):
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
    '''
    
    def list_project_studies_with_koval( self, project_name ):
        
        '''
        returns a list of tuples [ (study_name, subzone, []producer1, producer2, ....) ]
        '''
        names = self.list_project_studies( project_name )
        
        # now we need to find those for which we also have a koval simulation
        sims_with_koval = [] 
        for name in names:
            historical_koval_crm = self.load_historical_koval_crm( name )

            if historical_koval_crm.shape[0] > 1:
                subzone = historical_koval_crm['SUBZONE'].unique()[0]
                producers = list(historical_koval_crm['PRODUCER'].unique())
                sims_with_koval.append( (name,subzone, producers) )
        
        return sims_with_koval 
    
    
        
    def save_historical_optimization_results( self, historical_optimization_results,simulation_name )  :

        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +'/historical_optimization_results.bin' 
        
        handle = self._get_handle()     
        handle.put_file(file_name, pickle.dumps( historical_optimization_results) )
  
    def load_historical_optimization_results( self,simulation_name )  :
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +'/historical_optimization_results.bin' 
        
        handle = self._get_handle() 
        restored = None  
        
        try:
            with handle.get_file( file_name ) as fd:
                restored = pickle.loads(fd.content)
        except:
            return {}
        
        return restored 
     
    def save_historical_df( self, df, path, index =False ):
    
        handle = self._get_handle()     
        handle.put_file(path, df.to_csv(index = index ))
    
    def load_historical_df( self, path ):
        
        handle = self._get_handle()
        try:
            with handle.get_file( path ) as fd:
                df = pd.read_csv(fd.raw, )#, encoding='utf-8-sig' )
        except:
            df = pd.DataFrame( {} ) 
        
        return df 
    
    def save_historical_lambdas_taus( self, df, simulation_name ) :
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +'/historical_liquid_crm.csv'
        
        return self.save_historical_df( df, file_name, False )  

        
   
    def load_historical_lambdas_taus( self, simulation_name ):
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +'/historical_liquid_crm.csv'

        return self.load_historical_df( file_name )
     
    def load_historical_liquid_rates( self,simulation_name )  :
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +   '/historical_liquid_rates.csv'  
         
        df  = self.load_historical_df( file_name )
        return df 
    
    def save_historical_liquid_rates( self, df,simulation_name )  :
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +   '/historical_liquid_rates.csv' 
        
        return self.save_historical_df( df, file_name, False ) #False=DATE is a col not index 
      
    
    def update_historical_optimization_results(self, new_history_simulations, old_history_simulations):
            
        for new_result_key, new_result_value in new_history_simulations.items():
            old_history_simulations[ new_result_key ] =  new_result_value 
            
        return old_history_simulations 
    
    
    def update_historical_table(self, new_df, old_df):                
        updated = None 
        if old_df.empty == True:
            updated = new_df
        else:
            

                
            #new_df['code'] = new_df['PRODUCER']+new_df['SUBZONE']+new_df['SIMULATION']
            new_df['code'] = new_df['PRODUCER'].astype(str) + new_df['SUBZONE'].astype(str) + new_df['SIMULATION'].astype(str)
       
    
            #old_df['code'] = old_df['PRODUCER']+old_df['SUBZONE']+old_df['SIMULATION']
            old_df['code'] = old_df['PRODUCER'].astype(str) + old_df['SUBZONE'].astype(str) + old_df['SIMULATION'].astype(str)
       
    
            to_replace = list( new_df['code'].unique() )
            old_df = old_df[ ~old_df['code'].isin(to_replace ) ].copy()
            new_df.drop('code', axis = 1, inplace=True)
            old_df.drop('code', axis = 1, inplace=True)
            updated = pd.concat( [old_df, new_df], axis = 0 ) 

        return updated

              
    def update_lambdas_taus(self, new_lambdas_taus, historical_lambdas_taus):
        return self.update_historical_table( new_lambdas_taus, historical_lambdas_taus)

    
    def update_liquid_rates(self, new_liquid_rates, historical_liquid_rates):
        return self.update_historical_table( new_liquid_rates, historical_liquid_rates)

 
    def save_historical_liquid_crm( self, df )  :
        self.save_historical_lambdas_taus( df )
           
    def save_historical_koval_rates( self, df, simulation_name ):
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +   '/historical_koval_rates.csv' 
        
        self.save_historical_df( df, file_name, False ) #False=DATE is a col not index 
    
    def load_historical_koval_rates( self, simulation_name ):
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        
        file_name  = base_address +   '/historical_koval_rates.csv' 
        df  = self.load_historical_df( file_name )
        return df 
    
     
    def save_historical_koval_crm( self, df, simulation_name ):
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +   '/historical_koval_crm.csv' 
        
        self.save_historical_df( df, file_name, False ) #False=DATE is a col not index 
    
    def load_historical_koval_crm( self, simulation_name ):
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        
        file_name  = base_address +   '/historical_koval_crm.csv' 
        df  = self.load_historical_df( file_name )
        return df 
    

    def save_historymatch_failures( self, df, simulation_name ) :
        
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +'/failures_historical_liquid_crm.csv'
        
        return self.save_historical_df( df, file_name, False )  
    
    def load_historymatch_failures( self, simulation_name ):
        project_name = self.args['project_name']
        base_address = self.study_folder_path(project_name,simulation_name)
        file_name  = base_address +'/failures_historical_liquid_crm.csv'

        return self.load_historical_df( file_name )
     
        
    def get_project_dataset( self ): 
        
        project_name = self.args['project_name']
        dataset_name =  self._get_default_dataset_name() 
        return super().get_dataset( project_name = project_name, dataset_name = dataset_name )
     
    
    def fetch_study_required_data_for_pfm( self, simulation_name, subzone_name  ):
       
        historical_koval_crm    = self.load_historical_koval_crm( simulation_name )
        historical_koval_rates  = self.load_historical_koval_rates( simulation_name )
        historical_koval_rates['DATE'] = pd.to_datetime( historical_koval_rates['DATE'] )
        

        
        #subzone 
        historical_koval_rates = historical_koval_rates[ historical_koval_rates['SUBZONE'] == subzone_name ]
        historical_koval_crm   = historical_koval_crm[ historical_koval_crm['SUBZONE'] == subzone_name ]
        
        
   
        historical_liquid_crm   = self.load_historical_lambdas_taus( simulation_name )
        historical_liquid_rates = self.load_historical_liquid_rates( simulation_name )
        historical_liquid_rates['DATE'] = pd.to_datetime( historical_liquid_rates['DATE'] )

        
        historical_liquid_crm   = historical_liquid_crm[ historical_liquid_crm['SUBZONE'] == subzone_name ]
        historical_liquid_rates   = historical_liquid_rates[ historical_liquid_rates['SUBZONE'] == subzone_name ]
                
        #injectors and producer filters 
        producer_names = list(historical_koval_crm['PRODUCER'].unique())
        injector_names = list(historical_liquid_crm[historical_liquid_crm['PRODUCER'].isin(producer_names)]['INJECTOR'].unique())
        
        historical_liquid_crm = historical_liquid_crm[historical_liquid_crm['PRODUCER'].isin(producer_names)]
        historical_liquid_rates = historical_liquid_rates[historical_liquid_rates['PRODUCER'].isin(producer_names)]
        historical_koval_rates = historical_koval_rates[historical_koval_rates['PRODUCER'].isin(producer_names)]
        

    
        crm_dataset =  self.get_project_dataset( ).filter_by( 'SUBZONE', [subzone_name] ).filter_by( 'NAME', producer_names + injector_names )
        injectors_liquid_rates = crm_dataset.injectors_df
        producers_liquid_rates = crm_dataset.producers_df
        locations  = crm_dataset.locations_df
        
        injectors_liquid_rates['DATE'] = pd.to_datetime( injectors_liquid_rates['DATE'] )
        producers_liquid_rates['DATE'] = pd.to_datetime( producers_liquid_rates['DATE'] )
        
  



        return  (historical_koval_crm, 
                 historical_koval_rates, 
                 historical_liquid_crm, 
                 historical_liquid_rates, 
                 injectors_liquid_rates,
                 producers_liquid_rates,
                 locations) 

    
class oldDataikuLocalFolderConnector(DataikuStorageAPI):
 

    '''
    To be used outside dataiku in a client program  (a notebook a webapp, etc) to access the data 
    in a managed folder inside a remote dataiku project. We need the host and the api keys of the project
    '''

    def __init__(self, config, kwargs = None  ):
        '''

        The class assumes a set structure for the managed folder. At the top is the application name
        Inside it, one can have a sub-folder for projects and inside each of these, there is a folder
        for data and one for studies. 

        This info is passed to the class constructor in a dictionary. Below is an example

        Example of the configuration passed to the class: 
            
            config = 
            {
            'managed_folder_name':'Data',
            
            'app_name':'WWW-WFDemo'
            
            'data_folder_name':'XXdata', #(optional,if not given it is set to data. It is relative to the project path )
            
            'projects_folder_name':'YYprojects', #(optional,if not given it is set to projects )
            
            'studies_folder_name':'ZZstudies', #(optional,if not given it is set to studies. It is relative to the project )
            
            } 
            
            Example of the managed folder structure:
            
            ManagedFolder 
                    
                    App1 
                    
                    App2
                    
                    WWW-WFDemo              app_name (the application) 
                        YYprojects          the name of  the sub-folder for projects 
                            Project1        whatever project name 
                            Project2        ...
                            Project3        ... 
                                XXdata          data folder inside each project 
                                    dataset1
                                    dataset2
                                    dataset3
                                ZZstudies       studies folder inside each project 
                                    study1
                                    study2
                                    ...
            
            
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
                
            
            client = self._get_client()
        
            
            known_folders  = [ f['id'] for f in client.get_default_project().list_managed_folders() if f['name'] == self._folder_name ]
            
            if any(known_folders):
                self._folder_id = known_folders[0]
        
            
        except Exception as e:
            print('Invalid arguments. ')
            raise( e )
            
    def list_managed_folders(self, keys = None):
        '''
        This is a wrapper around Dataiku functionality inside the dataiku package that simply
        returns a list of string where each element corresponds to the name of one managed folder 
        found in the default dataiku project.

        keys (optional) is a list of strings. If passed as argument, the function returns 
        as before a list but this time a list of dictionaries, one per folder. The keys are the 
        properties of the folder correspnding to ksys. 
        '''
        d = self._get_client().get_default_project().list_managed_folders()
        if keys is None:
            managed_folder_names = [ item['name'] for item in d ] 
            return managed_folder_names  

 
        #check if iterable 
        #then check all items are strings
        #if all( isinstance( key, str ) for key in keys 
        return [ {key:item[key] for key in keys }  for item in d ]


                
    @staticmethod       
    def read_dataset( managed_folder_name, path ):
  
        def read_csv(  path, handle, parse_dates=False, nrows = None ):

            target_path=path.replace('\\','/').replace('//','/')
            try:
                with handle.get_file( target_path ) as fd:

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


        known_folders  = [ f['id'] for f in dataiku.api_client().get_default_project().list_managed_folders() if f['name'] == managed_folder_name ]
        handle = dataiku.api_client().get_default_project().get_managed_folder( known_folders[0] )

        preffix = path 
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



    def _get_handle( self ):
        return self._get_client().get_default_project().get_managed_folder( self._folder_id )

      
    def _get_client( self ):
        if self._client is None: 
            self._client=dataiku.api_client()
        return self._client
        


    def set_managed_folder( self, name ):
        
        p = self._get_client().get_default_project()
        known_folders = list( (item['name'],str(item['id'])) for item in p.list_managed_folders() )
        managed_folders = [(item[0],item[1]) for item in known_folders if name.lower()==item[0].lower()]
            
        if any(managed_folders):
            self._folder_id = managed_folders[0][1]
            self._folder_name = name 
            return True
        
        return False
