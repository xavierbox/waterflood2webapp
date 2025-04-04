from application import app_var as app 
import os, sys, pprint, pandas as pd, numpy as np
import sys
from pathlib import Path
sys.path.append('./')
sys.path.append('../')
sys.path.append('../..')

from flask import (redirect, render_template, request, jsonify,send_from_directory, url_for)
from wf_lib2.crm_definitions import *
from wf_lib2.data.crm_dataset  import CRMDataset
from wf_lib2.data.crm_pattern  import CRMPattern

from typing import List
from wf_lib2.view_model.view_model import *
 
crm_dataset = None 
dataset_filters = None 
    
local_config = {
    'managed_folder_name': Path('C:/Work/2025/waterflood/webapp/azFolder'),
    'app_name':'WF',
    'data_folder_name':'data', #(optional,if not given it is set to data. It is relative to the project path )
    'projects_folder_name':'projects', #(optional,if not given it is set to projects )
    'studies_folder_name':'studies' #(optional,if not given it is set to studies. It is relative to the project )
}
 
 
class Storage:
    
    def __init__(self, config ):
        self.config = config 
        
    def get_dataset( self, filters = None ):
        
        global crm_dataset, dataset_filters
        
        raise ValueError('get_dataset is not implemented')
    
        
        if filters is None: filters = {} 
        
        project_name = filters.get('project_name', 'Synthetic 1')
        #if not crm_dataset is None:
        #    if dataset_filters == filters:
        #        print('dataset already loaded')
        #        return crm_dataset
            
        #name = 'Synthetic 1'
        
        if project_name == 'Synthetic 1':
            inj = pd.read_csv( 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here\\SyntheticV2_InjectorsSynthetic.csv' )
            prd = pd.read_csv( 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here\\SyntheticV2_ProducersSynthetic.csv' )
            locs = pd.read_csv( 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here\\SyntheticV2_LocationsSynthetic.csv')
            locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
                    
            time_format =  "%Y/%m/%d" # DATE_FORMAT  #21/07/2024
            crm_dataset = CRMDataset.instance( inj, prd, locs, time_format=time_format )
            crm_dataset= crm_dataset.slice_dates_dataset( '1845-01-01', '2021-11-27' )
             
                
                
        if project_name == 'Demo real data 2 Reservoirs':
            locs = pd.read_csv( 'C:\\Work\\2025\\waterflood\\repo\\example_datasets/locations_example1.csv')
            locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
            inj =  pd.read_csv( 'C:\\Work\\2025\\waterflood\\repo\\example_datasets/injectors_example1.csv')
            prd =  pd.read_csv( 'C:\\Work\\2025\\waterflood\\repo\\example_datasets/producers_example1.csv')
            time_format =  "%d/%m/%Y" # DATE_FORMAT  #21/07/2024
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
                   
    def get_datasetold( self, filters = None ):
        
        global crm_dataset, dataset_filters
        
        if not crm_dataset is None:
            if dataset_filters == filters:
                print('dataset already loaded')
                return crm_dataset
            
             
            
       
        dataset_filters = copy.deepcopy( filters )
        locs = pd.read_csv( 'C:\\Work\\2025\\waterflood\\repo\\example_datasets/locations_example1.csv')
        locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
        inj =  pd.read_csv( 'C:\\Work\\2025\\waterflood\\repo\\example_datasets/injectors_example1.csv')
        prd =  pd.read_csv( 'C:\\Work\\2025\\waterflood\\repo\\example_datasets/producers_example1.csv')
        time_format =  "%d/%m/%Y" # DATE_FORMAT  #21/07/2024
        crm_dataset = CRMDataset.instance( inj, prd, locs, time_format=time_format ) 
  
  

        file1 = 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here/koc_DATASET_InjectorsSynthetic.csv' 
        file3 = 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here/koc_DATASET_LocationsSynthetic.csv' 
        file2 = 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here/koc_DATASET_ProducersSynthetic.csv' 
        print( pathlib.Path(file1))
        inj =  pd.read_csv( file1 )
        prd =  pd.read_csv( file2 )
        locs = pd.read_csv( file3 )
        #locs['Y'] = locs['Y'] + 8000.00
        #locs['X'] = locs['X'] - 370000.0
        
        well_names_reservoir2 = ['BG-0299P', 'BG-0918P', 'BG-1236P', 'BG-1237P', 'BG-1240P', 'BG-1254P', 'BG-1259P', 'BG-1359P', 'BG-1362P', 'BG-1654P', 'BG-0772I', 'BG-0833I', 'BG-0834I', 'BG-1139I', 'BG-1143I', 'BG-1145I', 'BG-1219I', 'BG-1262I', 'BG-1263I', 'BG-1264I', 'BG-1280I', 'BG-1294I', 'BG-1354I', 'BG-1358I', 'BG-1360I', 'BG-1422I', 'BG-1423I', 'BG-1429I', 'BG-1432I']
        inj['SUBZONE'] = inj['NAME'].apply( lambda x: 'RW' if x in well_names_reservoir2 else 'LW' )
        prd['SUBZONE'] = prd['NAME'].apply( lambda x: 'RW' if x in well_names_reservoir2 else 'LW' )
        locs['SUBZONE'] = locs['NAME'].apply( lambda x: 'RW' if x in well_names_reservoir2 else 'LW' )
        
        
        
        #well_names_sector1 = ['BG-0234P', 'BG-0241P', 'BG-0757P', 'BG-1054P', 'BG-1723P', 'BG-1728P', 'BG-0604I', 'BG-0721I', 'BG-0722I', 'BG-0725I', 'BG-0739I', 'BG-0756I', 'BG-0758I', 'BG-0759I', 'BG-1204I', 'BG-1206I', 'BG-1430I', 'BG-1588I', 'BG-1692I', 'BG-1768I']
        #inj['SECTOR'] = inj['NAME'].apply( lambda x: 1 if x in well_names_sector1 else 0 )
        #prd['SECTOR'] = prd['NAME'].apply( lambda x: 1 if x in well_names_sector1 else 0 )
        #locs['SECTOR'] = locs['NAME'].apply( lambda x: 1 if x in well_names_sector1 else 0 )
        
        
        
        locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
        
        time_format =  "%Y/%m/%d" # DATE_FORMAT  #21/07/2024
        crm_dataset = CRMDataset.instance( inj, prd, locs, time_format=time_format ) 
        #crm_dataset= crm_dataset.slice_dates_dataset( '1845-01-01', '2021-11-27' )
        
        #inj.to_csv( 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here\\SyntheticV2_InjectorsSynthetic.csv',index=False )
        #prd.to_csv( 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here\\SyntheticV2_ProducersSynthetic.csv',index=False )
        #locs.to_csv( 'C:\\Work\\2025\\waterflood\\webapp\\example_datasets_here\\SyntheticV2_LocationsSynthetic.csv',index=False )
  
        '''x = crm_dataset.filter_by('SECTOR', [4] )
        x = x.filter_by('SUBZONE', ['LW'] )
        x = x.slice_dates_dataset( '21/01/2024', '21/09/2024' )        
        crm_dataset = x
        return crm_dataset'''
    
        
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
            
     
        return crm_dataset

    def get_project_description(self, filters = None):
            
        project_name = filters.get('project_name', 'Demo1')
        
        #we fetch the project description from the dataset
        #zones, sectors...subzones, etc
        
        crm_dataset = Storage( local_config ).get_project_dataset( project_name )
            
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
        locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
                    
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
        pass 
    
    def create_study( self, project_name, study_name ):
        pass    
    
    def get_study_connections( self, project_name, study_name ):
        pass
    
    def get_study_rates( self, project_name, study_name ):
        pass
    
        
        
    def list_projects( self ):
        folders = [ p.name for p in self.projects_path.iterdir() if p.is_dir()]
        return folders
     
    @property
    def projects_path( self ):
        return self.config['managed_folder_name'] / f"{self.config['app_name']}/{self.config['projects_folder_name']}"
      
    
     

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('application/static', filename)
         
   
@app.route('/get_list_of_projects',methods=['GET'])
def get_list_of_projects():
    data = {'projects': Storage( local_config ).list_projects()  }
    return {'data':data }, 200 
  
  
@app.route('/get_project_description',methods=['GET','POST'])
def get_project_description():

    data = request.get_json()
    print('Request get_project_description called with', data )
    description = Storage( local_config ).get_project_description( data )
    wokflow_names=['Liquid history match', 
                    'Watercut history match', 
                    'Static pattern flow balancing',
                    'Lagged correlation analysis',
                    'Genetic optimization',
                    'GenAI-powered analytics ' 
                    ]
       
    description['workflows'] = wokflow_names
    description['project_name'] = data['project_name']
    description['studies'] =  ['Field scale', 'Demo1', 'Lasso-sector ']
    return { 'data': description }, 200 
  
  
@app.route('/get_field_wells',methods=['GET','POST'])
def get_field_wells():
    
    filters = request.get_json()
 
    crm_dataset = Storage(local_config).get_project_dataset( filters['project_name'], filters )
    chart = get_field_wells_snapshot( crm_dataset )#, filters  )

    return jsonify( {'message':'Data loaded', 'data' : chart }), 200  

@app.route('/get_default_charts',methods=['GET','POST'])
def get_default_charts():
    filters = request.get_json()
    crm_dataset = Storage(local_config).get_project_dataset( filters['project_name'], filters )
    dataset_filters = filters
            
    # locations chart 
    locs_fig  = get_dataset_locations_plot( crm_dataset )#, filters  )
    #locs_charts = dict(locations = locs_fig)
    all_names = crm_dataset.injector_names + crm_dataset.producer_names
    #locs_charts['all_names'] = all_names


    # first tab of charts 
    producers_fig, fractions_fig, active_fig  =  get_dataset_field_summary_plots( crm_dataset )# , filters  )
    sector_volumes_fig = get_dataset_sector_summary_plots( crm_dataset )
    #field_charts = dict( fractions = fractions_fig, 
    #                    historical_production = producers_fig, 
    #                    activity = active_fig,
    #                    sector_volumes = sector_volumes_fig
    #                    )
    
    
    wells_chart = get_field_wells_snapshot( crm_dataset )#, filters  )
    
    charts = dict( 
                   #first tab of charts 
                   fractions = fractions_fig, 
                   historical_production = producers_fig, 
                   activity = active_fig,
                   
                   #second tab
                   sector_volumes = sector_volumes_fig, 
                   
                   #third tab
                   wells = wells_chart,
                     
                   #locations 
                   locations = locs_fig,
                   all_names = all_names)
    

    return jsonify( {'message':'Data loaded', 'data' : charts }), 200   



@app.route('/get_field_charts',methods=['GET','POST'])
def get_field_charts():

    global crm_dataset, dataset_filters

    filters = request.get_json()
    crm_dataset = Storage(local_config).get_project_dataset( filters['project_name'], filters )
    dataset_filters = filters
            
        
       
    producers_fig, fractions_fig, active_fig  =  get_dataset_field_summary_plots( crm_dataset )# , filters  )
    sector_volumes_fig = get_dataset_sector_summary_plots( crm_dataset )
    field_charts = dict( fractions = fractions_fig, 
                        historical_production = producers_fig, 
                        activity = active_fig,
                        sector_volumes = sector_volumes_fig
                        )
     
    return jsonify( {'message':'Data loaded', 'data' : field_charts }), 200   
    

    # field 
    # time cummulatives, current step aggregates and active wells in time 
    #producers_fig, fractions_fig, active_fig, locs  = mock_get_field_plots() 
    #field_charts = dict( fractions = fractions_fig, 
    #                    historical_production = producers_fig, 
    #                    activity = active_fig,
    #                    locations = locs
    #                    )
    #return jsonify( {'message':'Data loaded', 'data' : field_charts }), 200   
    
@app.route('/get_locations_chart',methods=['GET','POST'])
def get_locations_chart():

    
    filters = request.get_json()
    print('Request for ***********/get_locations_chart received', filters)

    crm_dataset = Storage(local_config).get_project_dataset( filters['project_name'], filters )
    locs_fig  = get_dataset_locations_plot( crm_dataset )#, filters  )
    
    locs_charts = dict(locations = locs_fig)
    all_names = crm_dataset.injector_names + crm_dataset.producer_names
    locs_charts['all_names'] = all_names
    return jsonify( {'message':'Data loaded', 'data' : locs_charts }), 200   
    

    # field 
    # time cummulatives, current step aggregates and active wells in time 
    #producers_fig, fractions_fig, active_fig, locs  = mock_get_field_plots() 
    #field_charts = dict( fractions = fractions_fig, 
    #                    historical_production = producers_fig, 
    #                    activity = active_fig,
    #                    locations = locs
    #                    )
    #return jsonify( {'message':'Data loaded', 'data' : field_charts }), 200   

    
@app.route('/get_wells_data',methods=['GET','POST'])
def get_wells_data(): 
    '''
    Returns data that the UI might use such as diatances between wells, well rates, etc.
    This method is called after some charts are produced in the UI and loads the data
    in the background
    '''    
    filters = request.get_json()
    print('Request for /get_field_charts received', filters)
    crm_dataset = Storage(None).get_dataset( filters )
    #producer_injector_distances = crm_dataset.get_producer_injectors_distances_flat()
    #all_well_distances  = crm_dataset.get_all_distances_flat()
    
    
    
    return jsonify( {'message':'Data loaded', 'all_well_distances' : all_well_distances }), 200   
    
    
@app.route('/tell_me_everything_about_this_well',methods=['GET','POST'])
def tell_me_everything_about_this_well():
    
    filters = request.get_json()
    well_name = filters['well_name']
    w = Storage(None).get_dataset( filters )
    
    #w = CRMDataset.generate_default_multiwell_dataset()
    #p = w.producers_df.copy()
    #p[ find_column(w.producers_df.columns, OIL_PRODUCTION_KEYS) ] = 123.456
    #p[ find_column(w.producers_df.columns, GAS_PRODUCTION_KEYS) ] = 223
    #p[ find_column(w.producers_df.columns, WATER_PRODUCTION_KEYS) ] = 323.456
    #p[ find_column(w.injectors_df.columns, LIQUID_PRODUCTION_KEYS) ] = 523.456
    #w.producers_df = p 
    #well_name = w.producer_names[0] # filters['well_name']
    
    data = get_everything_for_this_well( w, well_name, max_neighbours_distance = 2000, max_neighbours = 10 )

    return jsonify( {'message':'Well details: rates and neighbours fetched', 'data' : data }), 200   



 
@app.route('/start_liquid_history_match_simulation',methods=['POST'])
def start_liquid_history_match_simulation():
    return jsonify( {'message':'Modelling data received and processed successfully'}), 200   

    






def old_get_well_details():
    
    '''data = {
        
        'name':   'Well 1',
        'type':   'Injector',
        'neighbours':  [ {'Well':'Well 2', 'Type':'Injector', 'Distance': 453.23}, {} .... ]
        'rates:': {
            'dates': [....]
            'liquid': [....]
            'gas': [....]
            'oil': [...]
        }
    }'''
    
    filters = request.get_json()
    w = Storage(None).get_dataset( filters )
    w = CRMDataset.generate_default_multiwell_dataset()
    well_name = w.producer_names[0] # filters['well_name']
    
    if well_name in crm_dataset.injector_names:
        w.filter_by('NAME', [well_name], w.producer_names)
        
        W_COL = find_column(w.injectors_df.columns, WATER_INJECTION_KEYS)
        rates = w[ W_COL ].sort_index().fillna(0.0)
        
        if rates.index.name == 'DATE':
            dates = rates.index.values.astype('datetime64[D]').astype( str )[0:10].tolist() 
        else:
            dates = rates['DATE'].values.astype('datetime64[D]').astype( str )[0:10].tolist() 
        
        rates = { 'dates':dates, 'Water_injection': rates[W_COL].values.tolist() } 
    else:
        O_COL,G_COL,W_COL = find_column(w.producers_df.columns, OIL_PRODUCTION_KEYS), find_column(w.producers_df.columns, GAS_PRODUCTION_KEYS), find_column(w.producers_df.columns, WATER_PRODUCTION_KEYS)
        w.filter_by('NAME', [well_name], w.injector_names)
        oil = w[ O_COL].sort_index().fillna(0.0)
        gas = w[ G_COL].sort_index().fillna(0.0)
        water = w[ W_COL].sort_index().fillna(0.0)
 
        if water.index.name == 'DATE':
            dates = water.index.values.astype('datetime64[D]').astype( str )[0:10].tolist() 
        else:
            dates = water['DATE'].values.astype('datetime64[D]').astype( str )[0:10].tolist() 
        
        rates = { 'dates':dates, 'Oil_production': oil[O_COL].values.tolist(), 'Gas_production': gas[G_COL].values.tolist(), 'Water_production': water[W_COL].values.tolist()  }
        
        
        
    well_types = {} 
    for iname in w.injector_names:
        well_types[iname] = 'Injector'
    for pname in w.producer_names:
        well_types[pname] = 'Producer'
            

    producer_injector_distances = w.get_all_distances_flat()
    print( producer_injector_distances )
    closest = [
        entry for entry in producer_injector_distances
        if entry["well1"].lower() == well_name.lower()
    ]
    # Sort by distance
    closest.sort(key=lambda x: x["distance"])
    # Build flat structure with name, type, and distance
    result = []
    for entry in closest[:10]:
        other_well = entry["well2"]
        result.append({
            "name": other_well,
            "type": well_types.get(other_well, "Unknown"),
            "distance": entry["distance"]
        })
    
    data = { 
            'neighbours' : result,
            'well_name' : well_name,
            'well_type' : well_types[well_name],
            'rates': rates
    }
    print( data )
    
    
    
    return jsonify( {'message':'Well details fetched', 'data' : data }), 200   
   

@app.route('/layout')
def layout():
     #return render_template('layoutVersion1B.html')
     #return render_template('FixedColumnLeftSide.html')
     return render_template('layoutVersion0C.html')
     return render_template('layoutVersion0B.html')
      

@app.route('/layout2')
def layout2():
     #return render_template('layoutVersion1B.html')
     #return render_template('FixedColumnLeftSide.html')
     
     #return render_template('layoutVersion0B.html')
     return render_template('layoutVersion0C.html')



@app.route('/crm')
def crm():
     return render_template('crm_setup_page0.html')
 
@app.route('/well_detail_dialog')
def well_detail_dialog():
     return render_template('well_detail_dialog.html')
 
 
 
@app.route('/get_crm_input_data', methods=['GET','POST'])
def get_crm_input_data():
   
    def get_time_series( dates, df  ):
    
        rates = {'dates': dates,'data': {col: df[col].tolist() for col in df.columns} }
    
        return rates 
    
   
    
    filters = request.get_json()
    #filters['date'] = ['21-12-2022', '21-12-2024' ]
    #filters.update({'sector': [1,4,7],'subzone':'LW'})
    
    print('Request for /get_crm_data received', filters)
    
    crm_dataset = Storage(None).get_dataset(filters)
    
    #we need the distances to pass to the UI so wecan filter pairs 
    distances = crm_dataset.get_producer_injectors_distances_flat()
    
    #now we also need the rates to display and guide the user 
    pattern = crm_dataset.get_pattern( fix_time_gaps = True, fill_nan = 0.0 )
    #print( pattern.liquid_production.head(5) )
 
    
    df = pattern.liquid_production
    dates = df.index.strftime('%Y-%m-%d').tolist()
    #print( dates[0:10])
    
    df = pattern.liquid_production
    liquid_production = get_time_series( dates, df  )
 
    df = pattern.water_injection 
    water_injection = get_time_series( dates, df  )
    
    
    data = {
        'distances':distances,
        'dates':dates,
        'water_injection':water_injection,
        'liquid_production': liquid_production
    } 
    
    return jsonify( data ), 200   
  
      

@app.route('/users')
def users():
    print('Request for users page received')
    
    posts = [
        {
            'author': {'name': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'name': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    user = {'name':'xavier'}
    return render_template('users.html',user=user,title='users page', posts = posts)
     

@app.route('/')
def index():
   print('Request for index page received')
   return render_template('layoutVersion0C.html')

   #return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
   name = request.form.get('name')

   if name:
       print('Request for hello page received with name=%s' % name)
       return render_template('hello.html', name = name)
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))


