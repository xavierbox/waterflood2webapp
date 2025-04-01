from application import app_var as app 
import os, sys, pprint, pandas as pd, numpy as np
import sys
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
    
    
class Storage:
    
    def __init__(self, config ):
        self.config = config 
        
    def get_dataset( self, filters = None ):
        
        global crm_dataset, dataset_filters
        
        if not crm_dataset is None:
            if dataset_filters == filters:
                print('dataset already loaded')
                return crm_dataset
       
        dataset_filters = copy.deepcopy( filters )
        locs = pd.read_csv( 'example_datasets/locations_example1.csv')
        locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
        inj =  pd.read_csv( 'example_datasets/injectors_example1.csv')
        prd =  pd.read_csv( 'example_datasets/producers_example1.csv')
        

     
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
            
     
        return crm_dataset

    def get_project_description(self, project_name='Project 1'):
            
        crm_dataset = self.get_dataset()
        reservoir_names = crm_dataset.locations_df[ZONE_KEYS[0]].unique().tolist()
        print('----reservoir_names', reservoir_names)
        reservoirs = {} 
        for name in reservoir_names:
            reservoirs[name] = {}
            tmp = crm_dataset.filter_by(ZONE_KEYS[0], [name])
            subzones = crm_dataset.locations_df[SUBZONE_KEYS[0]].unique().tolist()
            print('----subzones', subzones)
            
            for subzone in subzones:
                tmp2 = tmp.filter_by(SUBZONE_KEYS[0], [subzone])
                sectors = sorted(tmp2.locations_df[SECTOR_KEYS[0]].unique().tolist())
                reservoirs[name][subzone] = [ int(s) for s in sectors ]  
                

        
        wokflow_names=['Liquid history match', 
                    'Watercut history match', 
                    'Static pattern flow balancing',
                    'Lagged correlation analysis',
                    'Genetic optimization',
                    'GenAI-powered analytics ' 
                    ]
        studies = ['Field scale', 'Demo 1', 'Lasso-sector ']
        reservoir_management_units = ['RMU 1', 'RMU 2', 'RMU 3']
        sectors =  7  
        dates   = [crm_dataset.producers_df['DATE'].min(),crm_dataset.producers_df['DATE'].max()]
        print(dates)
                    
                
        backend_data  = {
                    'workflows': wokflow_names,
                    'studies': studies,
                    #'reservoir_management_units': reservoir_management_units,
                    #'sectors': sectors,
                    'dates': dates   ,
                    'reservoirs': reservoirs
                }

        return backend_data
     
     

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('application/static', filename)
         
   
@app.route('/get_list_of_projects',methods=['GET'])
def get_list_of_projects():

    data = {'projects': ['Demo real data 2 Reservoirs', 'Synthetic 1', 'Soyapour'] }
    return {'data':data }, 200 
  
  
@app.route('/get_project_description',methods=['GET','POST'])
def get_project_description():

    print('Request get_project_description fullfilled')
    data = Storage( None ).get_project_description()
    
    return {'data':data }, 200 
  
  
@app.route('/get_field_wells',methods=['GET','POST'])
def get_field_wells():
    
    filters = request.get_json()
    print('Request for /**************************get_field_wells_snapshot received', filters)

    crm_dataset = Storage( None ).get_dataset( filters )
    chart = get_field_wells_snapshot( crm_dataset )#, filters  )

    return jsonify( {'message':'Data loaded', 'data' : chart }), 200  


@app.route('/get_field_charts',methods=['GET','POST'])
def get_field_charts():

    global crm_dataset, dataset_filters

    filters = request.get_json()
    crm_dataset = Storage( None ).get_dataset( filters )
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

    crm_dataset = Storage(None).get_dataset( filters )
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


@app.route('/get_well_charts',methods=['GET','POST'])
def get_well_charts():

    return "all good", 200 

    filters = request.get_json()
    print('Request for /get_well_charts received', filters)

    crm_dataset = mock_get_dataset( filters )
       
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
     
     return render_template('layoutVersion0B.html')
 
       
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
   return render_template('index.html')

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


