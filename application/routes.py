from application import app_var as app 
import os, sys, pprint, pandas as pd, numpy as np
import sys,json
from pathlib import Path
sys.path.append('./')
sys.path.append('../')
sys.path.append('../..')

from wf_lib2.temporal_development.workflows_scenarios_storage import *


from flask import (redirect, render_template, request, jsonify,send_from_directory, url_for)
from flask import send_from_directory, make_response
from wf_lib2.crm_definitions import *
from wf_lib2.data.crm_dataset  import CRMDataset
from wf_lib2.data.crm_pattern  import CRMPattern

from typing import List
from wf_lib2.view_model.view_model import *
from flask_cors import CORS
 
crm_dataset = None 
dataset_filters = None 
    
    
# Alias
Storage = FilesystemStorage


     

@app.route('/static/<path:filename>')
def static_files(filename):
    response = make_response(send_from_directory('application/static', filename))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

    
   
@app.route('/get_list_of_projects',methods=['GET'])
def get_list_of_projects():
    data = {'projects': Storage( local_config ).list_projects()  }
    return {'data':data }, 200 
  
  
@app.route('/get_project_description',methods=['GET','POST'])
def get_project_description():

    data = request.get_json()

    storage = Storage( local_config )
    description = storage.get_project_description( data )
    
    wokflow_names=['Liquid history match', 
                    'Watercut history match', 
                    'Static pattern flow balancing',
                    'Lagged correlation analysis',
                    'Genetic optimization',
                    'GenAI-powered analytics ' 
                    ]
       
    description['workflows'] = wokflow_names
    description['project_name'] = data['project_name']
    description['studies'] =  storage.list_studies( data['project_name'] )
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
    #w = Storage(local_config).get_dataset( filters )
    w = Storage(local_config).get_project_dataset( filters['project_name'], filters )
        
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
    
    ui_sim_params = request.get_json()    
    project_name = ui_sim_params['project_name']
    study_name = ui_sim_params['simulation']['name']
    
    storage = Storage(local_config)
    study_path = storage.create_study(project_name, study_name ) / f'{study_name}.json'
    # Write to file
    with study_path.open("w", encoding="utf-8") as f:
        json.dump(ui_sim_params, f, indent=2)
        
    data = {'studies' : storage.list_studies(project_name) }  
            
    
    return jsonify( {'message':'Modelling data uploaded successfully','data': data}), 200   


@app.route('/run_history_match_simulation',methods=['POST'])
def run_history_match_simulation():
    
    try:
        sim_params = request.get_json()
        project_name = sim_params['project_name']
        study_name = sim_params['simulation']['name']
        (   aggregated_rates, 
            aggregated_lambdas_taus, 
            aggregated_optimization, 
            aggregated_failures, 
            aggregated_single_well_models
        ) = run_liquid_history_match_scenario( sim_params )
            
        print( aggregated_lambdas_taus )
        
            
        return jsonify( {'message':'Modelling data uploaded successfully'}), 200   

    except Exception as e:
        print('Error in run_history_match_simulation', e)
        return jsonify( {'message':'Unexpected error in simulation'}, 500 )



@app.route('/fetch_liquid_history_match_tau_lambda_results',methods=['POST'])
def fetch_liquid_history_match_tau_lambda_results():
     
    sim_params = request.get_json()
    print( sim_params)
    
    project_name = sim_params['project_name']
    study_name = sim_params['study_name'] 
    results = Storage(local_config).load_historical_lambdas_taus( project_name, study_name )
    results_flat = results.to_dict(orient='records')
    print( results_flat[0:5] )
    
    return jsonify( {'message':'Modelling data uploaded successfully', 'data':results_flat }), 200



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
    
    crm_dataset = Storage(local_config).get_project_dataset(filters['project_name'], filters)
    
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


