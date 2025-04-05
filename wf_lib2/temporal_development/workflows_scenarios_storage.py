
import pandas as pd, json, numpy as np, sys
import pathlib# import Path
import pprint,copy  
 
from wf_lib2.crm_definitions import *
from wf_lib2.data.crm_dataset import CRMDataset
from wf_lib2.data.crm_pattern import CRMPattern 
from wf_lib2.models.crm_factory import crm_factory
from wf_lib2.models.crm_model import  CRMSingleModel
from wf_lib2.models.crm_p import CRMPSingle, CRMP 
from wf_lib2.models.crm_ip import CRMIPSingle, CRMIP 
from pathlib import Path
import json


local_config = {
    'managed_folder_name': Path('C:/Work/2025/waterflood/webapp/azFolder'),
    'app_name':'WF',
    'data_folder_name':'data', #(optional,if not given it is set to data. It is relative to the project path )
    'projects_folder_name':'projects', #(optional,if not given it is set to projects )
    'studies_folder_name':'studies' #(optional,if not given it is set to studies. It is relative to the project )
}
 
 

class FilesystemStorage:
    
    def __init__(self, config ):
        self.config = config 
        
    def get_project_description(self, filters = None):
            
        project_name = filters.get('project_name', 'Demo1')
        
        #we fetch the project description from the dataset
        #zones, sectors...subzones, etc
        
        crm_dataset = FilesystemStorage( local_config ).get_project_dataset( project_name )
            
        reservoir_names = crm_dataset.locations_df[ZONE_KEYS[0]].unique().tolist()

        reservoirs = {} 
        for name in reservoir_names:
            reservoirs[name] = {}
            tmp = crm_dataset.filter_by(ZONE_KEYS[0], [name])
            subzones = crm_dataset.locations_df[SUBZONE_KEYS[0]].unique().tolist()
            print('----subzones', subzones)
            
            for subzone in subzones:
                tmp2 = tmp.filter_by(SUBZONE_KEYS[0], [subzone])
                sectors = sorted(tmp2.locations_df[SECTOR_KEYS[0]].unique().tolist())
                
                print( tmp2.locations_df )
                
                reservoirs[name][subzone] = [] 
                reservoirs[name][subzone]=[ int(s) for s in sectors ]  
                

        
        studies = ['Field scale', 'Demo 1', 'Lasso-sector ']
        dates   = [crm_dataset.producers_df['DATE'].min(),crm_dataset.producers_df['DATE'].max()]
       
                    
                
        backend_data  = {
                    #'workflows': wokflow_names,
                    'studies': studies,
                    #'reservoir_management_units': reservoir_management_units,
                    #'sectors': sectors,
                    'dates': dates,
                    'reservoirs': reservoirs
                }

        return backend_data
     
    def get_project_dataset( self, project_name, filters = None  ):
        
        path = self.projects_path / project_name / self.config['data_folder_name']
        if not path.exists():
            print('Project folder does not exist')
            return None
        
        inj  = pd.read_csv( path /'injectors.csv')
        prd  = pd.read_csv( path /'producers.csv')
        locs = pd.read_csv( path /'locations.csv')
                  
        time_format =  DATE_FORMAT # DATE_FORMAT  #21/07/2024
        crm_dataset = CRMDataset.instance( inj, prd, locs, time_format=time_format )
        
        
        if not filters is None:
                
            if 'name'in filters:
                names = filters['name']
                if not isinstance(names, list):
                    names = [names]
                crm_dataset = crm_dataset.filter_by(NAME_KEYS[0], names)
                
            if 'date' in filters:
                date1,date2 = filters['date'] 
                crm_dataset = crm_dataset.slice_dates_dataset(  date1, date2 )
            
            if 'zone' in filters:
                unit = filters['zone']
                if not isinstance(unit, list):
                    unit = [unit]
                    
                if len(unit)>0:
                    crm_dataset = crm_dataset.filter_by(ZONE_KEYS[0], unit)
            
            if 'subzone' in filters:
                unit = filters['subzone']
                if not isinstance(unit, list):
                    unit = [unit]
                    
                if len(unit)>0:
                    crm_dataset = crm_dataset.filter_by(SUBZONE_KEYS[0], unit)
            
            if 'sector' in filters:
                sector = filters['sector']
                if not isinstance(sector, list):
                    print('***filtering sectors', sector)
                    sector = [sector]
                if len(sector) > 0:
                    crm_dataset = crm_dataset.filter_by(SECTOR_KEYS[0], [int(i) for i in sector] )
            
     
        dataset_filters = copy.deepcopy( filters )
        
        
   
        return crm_dataset 
        
    def list_studies( self, project_name, filter = None ):
        studies_path = self.projects_path / project_name / self.config['studies_folder_name']
        l =  [ p.name for p in studies_path.iterdir() if p.is_dir()]
        return l 
    
    def create_study( self, project_name, study_name ):
        study_path = self.projects_path / project_name / self.config['studies_folder_name'] / study_name
        study_path.mkdir(parents=True, exist_ok=True)
        return study_path
    
                 
    def list_projects( self ):
        folders = [ p.name for p in self.projects_path.iterdir() if p.is_dir()]
        return folders
     
    @property
    def projects_path( self ):
        return self.config['managed_folder_name'] / f"{self.config['app_name']}/{self.config['projects_folder_name']}"
      
    def save_historical_df( self, df, path, index =False ):
    
        df.to_csv( path, index = index )
        
    def load_historical_df( self, path ):
        return pd.read_csv(path)
    
    
    def save_historical_lambdas_taus(  self, project_name, simulation_name, aggregated_lambdas_taus):
        study_path = self.projects_path / project_name / self.config['studies_folder_name'] / simulation_name
        file_name = 'historical_liquid_crm.csv'
        
        file_path = study_path / file_name
        self.save_historical_df( aggregated_lambdas_taus, file_path )
        
    def load_historical_lambdas_taus( self, project_name, simulation_name ):
        study_path = self.projects_path / project_name / self.config['studies_folder_name'] / simulation_name
        file_name = 'historical_liquid_crm.csv'
        return self.load_historical_df( study_path / file_name )

    def save_historical_liquid_rates( self, project_name, simulation_name, aggregated_rates):
        study_path = self.projects_path / project_name / self.config['studies_folder_name'] / simulation_name
        file_name = 'historical_liquid_rates.csv'
        file_path = study_path / file_name
        self.save_historical_df( aggregated_rates, file_path )
        
        
            
            


def run_history_match_workflow( crm_dataset, sim_params ):
    
    '''
  
    returns 
    aggregated_rates, aggregated_lambdas_taus, aggregated_optimization, aggregated_failures, aggregated_single_well_models
    
    '''
    def get_well_names_per_subzone( sim_params_ui ):
        
        well_names_per_subzone = {} 
        subzones = list(sim_params_ui['explicit']['subzone'].keys())
        
        for subzone in subzones:            
            well_names_per_subzone[ subzone ] = set()
            #for p,i in sim_params['explicit']['subzone'][subzone].items():
            #    all_well_names.update( [p] + i )
        for k,v in well_names_per_subzone.items(): well_names_per_subzone[k] = list( v )
        return subzones, well_names_per_subzone
    
    aggregated_rates        = []
    aggregated_lambdas_taus = [] 
    aggregated_failures     = [] 
    aggregated_optimization = {}
    aggregated_single_well_models = [] 
    

    simulation_name = sim_params['simulation'].get('name', 'Default')

    
    # lets get the list of subzones 
    if 'explicit' in sim_params:
        subzones, well_names_per_subzone = get_well_names_per_subzone( sim_params )
        print('we are explicit and subzones are ', subzones )
    
    else:
        subzones = list( crm_dataset.locations_df['SUBZONE'].unique() ) if 'SUBZONE' in crm_dataset.locations_df.columns else ['UNIQUE']
   
    
    # this loop is not needed
    for subzone in subzones:
        
        subzone_dataset = crm_dataset.filter_by('SUBZONE', [subzone] )
        
        # we gave two ways of modelling the patterns, one is distance. The other one is explicit. 
        # if explicit is provided, then the distance is ignored and single-well patterns are assemnblied in a list.
        
        # find the list of patterns to simulate 
        patterns = [] 
        if 'explicit' in sim_params:
            
            print('patterns (single-well) are explicitly listed per subzone')
            single_well_patterns_data = sim_params['explicit']['subzone'][subzone]
            #print( single_well_patterns_data )
            for producer, injectors in single_well_patterns_data.items():
                names = [producer]+injectors
                patterns.append( subzone_dataset.filter_by('NAME', names ).get_pattern(fix_time_gaps = False) )
               
        else:
            distance_threshold = sim_params.get('distance', 999999 ) #infinite if isnt provided 
            patterns = subzone_dataset.get_distance_patterns( distance_threshold, fix_time_gaps = False )
  
 

        # initialize a multi-well simulator and pass to it the list of single-well patterns
        # note that we could also pass a list of multi-well patterns
        model, model_type_name =   crm_factory( sim_params['simulation']['type'] ) 
        #print(id( model ), model_type_name, subzone  )
        
        print(sim_params['simulation'] )
        model.fit_preprocess( patterns , sim_params['simulation'] )
        
        
        model.fit()
        results = model.predict()
        print('prediction done for subzone ', subzone)
           
        failures  = [] 
        temp_failures = model.failed_models 
        for item in temp_failures:
            new_tuple = tuple( [ x for x in item ] + [subzone ] )            
            failures.append( new_tuple )
        
        
        aggregated_failures = aggregated_failures + failures 
        
        for sub_model in model.models:
        #    
            sub_model.optimization_result['subzone'] = subzone         
            sub_model.optimization_result['simulation_name'] = simulation_name        
            sub_model.prediction_result['crm']['R2'] = sub_model.optimization_result['r2']
            sub_model.prediction_result['crm']['SUBZONE'] = subzone    
            sub_model.prediction_result['crm']['SIMULATION'] = simulation_name    
                    
            sub_model.prediction_result['rates']['SUBZONE'] = subzone 
            sub_model.prediction_result['rates']['PRODUCER'] = sub_model.producer_name  
            sub_model.prediction_result['rates']['SIMULATION'] = simulation_name 
            
            aggregated_lambdas_taus.append( sub_model.prediction_result['crm'])
            aggregated_rates.append( sub_model.prediction_result['rates'])
            aggregated_optimization[ (simulation_name, sub_model.producer_name, subzone) ] = sub_model.optimization_result 
            aggregated_single_well_models.append( sub_model )
         
    #print('all models were run in the workflow. Putting results together')
    #print('aggregated_lambdas_taus', aggregated_lambdas_taus)
    if aggregated_lambdas_taus is None or len(aggregated_lambdas_taus)<1:
        
        aggregated_rates = None
        aggregated_lambdas_taus = None 
        aggregated_optimization = None 
        aggregated_single_well_models = None 
        return (aggregated_rates, 
                aggregated_lambdas_taus, 
                aggregated_optimization, 
                aggregated_failures, 
                aggregated_single_well_models)
    
    aggregated_lambdas_taus = pd.concat( aggregated_lambdas_taus, axis = 0 )
    aggregated_rates = pd.concat( aggregated_rates, axis = 0 )
    aggregated_lambdas_taus.rename( columns = {'allocation':'ALLOCATION','tau':'TAU', 'taup':'TAUP', 'productivity':'PRODUCTIVITY'},inplace=True )
    #aggregated_rates.drop( ['ID','prod_id','pattern_id'], axis = 1, inplace=True)
    #aggregated_lambdas_taus.drop( ['ID','prod_id','pattern_id'], axis = 1, inplace=True)
 
    #remove the DATE as index, it is a pain
    aggregated_rates.reset_index( inplace=True, drop=False)
    
    
    # all the aggregated rates contain only the time intersection used during the fitting and columns like the OIL_VOLUME and 
    # GAS_VOLUME and SECTOR if preset, are not produced. Thats how the original solution worked. Since we cant modify it because 
    # it is being used in other projects, we need to implement workarounds here if needed
    # if that functionality is needed we should apply the required merges and joins here 

    print('done, returning here ')
    return (aggregated_rates, 
            aggregated_lambdas_taus, 
            aggregated_optimization, 
            aggregated_failures, 
            aggregated_single_well_models)


def run_history_match_special_case_tank_workflow( crm_dataset, sim_params ):
    '''
    returns 
    aggregated_rates, aggregated_lambdas_taus, aggregated_optimization, aggregated_failures, aggregated_single_well_models
    
    '''
    print('running special case tank workflow ')
    def get_well_names_per_subzone( sim_params_ui ):
        
        well_names_per_subzone = {} 
        subzones = list(sim_params_ui['explicit']['subzone'].keys())
        
        for subzone in subzones:            
            well_names_per_subzone[ subzone ] = set()
            #for p,i in sim_params['explicit']['subzone'][subzone].items():
            #    all_well_names.update( [p] + i )
        for k,v in well_names_per_subzone.items(): well_names_per_subzone[k] = list( v )
        return subzones, well_names_per_subzone
    
    aggregated_rates        = []
    aggregated_lambdas_taus = [] 
    aggregated_failures     = [] 
    aggregated_optimization = {}
    aggregated_single_well_models = [] 
     
    
    simulation_name = sim_params['simulation'].get('name', 'Default')

    
    # lets get the list of subzones 
    if 'explicit' in sim_params:
        subzones, well_names_per_subzone = get_well_names_per_subzone( sim_params )
        print('we are explicit and subzones are ', subzones )
    
    else:
        subzones = list( crm_dataset.locations_df['SUBZONE'].unique() ) if 'SUBZONE' in crm_dataset.locations_df.columns else ['UNIQUE']
   
    
    # this loop is not needed
    for subzone in subzones:
        
        subzone_dataset = crm_dataset.filter_by('SUBZONE', [subzone] )
        
        # we gave two ways of modelling the patterns, one is distance. The other one is explicit. 
        # if explicit is provided, then the distance is ignored and single-well patterns are assemnblied in a list.
        
        if 'explicit' in sim_params:
            all_well_names = [] 
            single_well_patterns_data = sim_params['explicit']['subzone'][subzone]
            for producer, injectors in single_well_patterns_data.items():
                all_well_names.extend( [producer]+injectors ) 
            subzone_dataset = subzone_dataset.filter_by('NAME', all_well_names )#.get_pattern(fix_time_gaps = False) )
   
        all_well_names = list( set(all_well_names) )
        print('all well names is ', all_well_names )
        tank_pattern = subzone_dataset.get_pattern(fix_time_gaps = False, fill_nan = 0.0 )

        # initialize a multi-well simulator and pass to it the list of single-well patterns
        # note that we could also pass a list of multi-well patterns
        model, model_type_name =   crm_factory( sim_params['simulation']['type'] ) 
        
        failed = False
        try:
            model.fit_preprocess( tank_pattern , sim_params['simulation'] )
            model.fit()
            results = model.predict()
            print('prediction done for subzone ', subzone)
            
            sub_model  = model
            sub_model.optimization_result['subzone'] = subzone         
            sub_model.optimization_result['simulation_name'] = simulation_name        
            sub_model.prediction_result['crm']['R2'] = sub_model.optimization_result['r2']
            sub_model.prediction_result['crm']['SUBZONE'] = subzone    
            sub_model.prediction_result['crm']['SIMULATION'] = simulation_name    

            sub_model.prediction_result['rates']['SUBZONE'] = subzone 
            sub_model.prediction_result['rates']['PRODUCER'] = sub_model.producer_name  
            sub_model.prediction_result['rates']['SIMULATION'] = simulation_name 

            aggregated_lambdas_taus.append( sub_model.prediction_result['crm'])
            aggregated_rates.append( sub_model.prediction_result['rates'])
            aggregated_optimization[ (simulation_name, sub_model.producer_name, subzone) ] = sub_model.optimization_result 
            aggregated_single_well_models.append( sub_model )

        
        except Exception as e:
            failed = True
            print('tank model for subzone ', subzone, ' failed ')
            aggregated_failures.append( ( 'Tank_'+subzone,str(e), subzone ))
            
                     
        
    print('all models ran (one per subzone) in the workflow. Putting results together')
    if aggregated_lambdas_taus is None or len(aggregated_lambdas_taus)<1:
        
        aggregated_rates = None
        aggregated_lambdas_taus = None 
        aggregated_optimization = None 
        aggregated_single_well_models = None 
        return (aggregated_rates, 
                aggregated_lambdas_taus, 
                aggregated_optimization, 
                aggregated_failures, 
                aggregated_single_well_models)
    
    aggregated_lambdas_taus = pd.concat( aggregated_lambdas_taus, axis = 0 )
    aggregated_rates = pd.concat( aggregated_rates, axis = 0 )
    aggregated_lambdas_taus.rename( columns = {'allocation':'ALLOCATION','tau':'TAU', 'taup':'TAUP', 'productivity':'PRODUCTIVITY'},inplace=True )
    
    #remove the DATE as index, it is a pain
    aggregated_rates.reset_index( inplace=True, drop=False)
    
    
    # all the aggregated rates contain only the time intersection used during the fitting and columns like the OIL_VOLUME and 
    # GAS_VOLUME and SECTOR if preset, are not produced. Thats how the original solution worked. Since we cant modify it because 
    # it is being used in other projects, we need to implement workarounds here if needed
    # if that functionality is needed we should apply the required merges and joins here 

    print('done, returning here ')
    return (aggregated_rates, 
            aggregated_lambdas_taus, 
            aggregated_optimization, 
            aggregated_failures, 
            aggregated_single_well_models)


def run_liquid_history_match_scenario( sim_params, storage = None ):
    
    if storage is None:
        storage = FilesystemStorage( local_config )
        
    try:
        project_name = sim_params['project_name'] #e.g. 'Demo1'
        
    except Exception as e:
        print('No project name provided')
        raise
        
    try:
        crm_dataset = storage.get_project_dataset( project_name, filters = sim_params.get('filters',None) )
        
    except Exception as e:
        print('No dataset provided or could not be fetched')
        raise
    
    try:
        (aggregated_rates, 
        aggregated_lambdas_taus, 
        aggregated_optimization, 
        aggregated_failures, 
        aggregated_single_well_models) = run_history_match_workflow( crm_dataset, sim_params ) 
        
        simulation_name = sim_params['simulation']['name']
        storage.save_historical_lambdas_taus(  project_name, simulation_name, aggregated_lambdas_taus  )
        storage.save_historical_liquid_rates( project_name, simulation_name, aggregated_rates  )    


        return (aggregated_rates, 
        aggregated_lambdas_taus, 
        aggregated_optimization, 
        aggregated_failures, 
        aggregated_single_well_models
        )
        
    except Exception as e:
        print('Error running history match workflow')
        raise
   
   
   