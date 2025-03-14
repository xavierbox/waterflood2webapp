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
 
def DEAD_mock_get_field_plots():
    
    locs = pd.read_csv( 'example_datasets/locations_example1.csv')
    locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
    inj =  pd.read_csv( 'example_datasets/injectors_example1.csv')
    prd =  pd.read_csv( 'example_datasets/producers_example1.csv')

    time_format = '%d/%m/%Y' #01/07/2024
    crm_dataset = CRMDataset.instance( inj, prd, locs, time_format=time_format ) 

    #ignore the errors 
    #reduce the size 
    dataset = crm_dataset.filter_by('SECTOR', [1, 2, 3])

    
    #dataset = CRMDataset.generate_default_multiwell_dataset()
    #dataset.producers_df['OIL_VOLUME'] = 0.2*dataset.producers_df['WATER_VOLUME'] 
    #dataset.producers_df['WATER_VOLUME'] = 0.8*dataset.producers_df['WATER_VOLUME'] 
  
    (active_wells, 
    production_summary, 
    injection_summary, 
    fractions, 
    filtered_dataset, pattern) = get_dataset_field_summary( dataset,cummulative=True )
   
    (producers_fig, 
     fractions_fig, 
     active_fig
    ) = get_dataset_field_summary_plots(active_wells, production_summary, injection_summary, fractions) 
    
    locs = get_dataset_locations_plot( dataset )
    
    return producers_fig, fractions_fig, active_fig, locs 

 
def mock_get_project_description(project_name='Project 1'):
            
    wokflow_names=['Liquid history match', 
                   'Watercut history match', 
                   'Static pattern flow balancing',
                   'Lagged correlation analysis',
                   'Genetic optimization' 
                  ]
    studies = ['Field scale', 'Demo 1', 'Lasso-sector ']
    reservoir_management_units = ['RMU 1', 'RMU 2', 'RMU 3']
    sectors =  7  
    dates   = ['2016-01-01', '2020-01-01'] 
                
    backend_data  = {
                'workflows': wokflow_names,
                'studies': studies,
                'reservoir_management_units': reservoir_management_units,
                'sectors': sectors,
                'dates': dates   
            }

    return backend_data
        
def mock_get_dataset( ):
    
    locs = pd.read_csv( 'example_datasets/locations_example1.csv')
    locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
    inj =  pd.read_csv( 'example_datasets/injectors_example1.csv')
    prd =  pd.read_csv( 'example_datasets/producers_example1.csv')

    time_format = '%d/%m/%Y' #01/07/2024
    crm_dataset = CRMDataset.instance( inj, prd, locs, time_format=time_format ) 
    
    crm_dataset = crm_dataset.filter_by('SECTOR', [1,2,3,4,5])
    crm_dataset = crm_dataset.slice_dates_dataset(  '01/06/2019', '01/01/2021' )
 
    return crm_dataset

@app.route('/get_project_description',methods=['GET','POST'])
def get_project_description():

    print('Request get_project_description fullfilled')
    data = mock_get_project_description()
    print('Request get_project_description fullfilled')
    
    return {'data':data }, 200 
  
  
@app.route('/get_field_charts',methods=['GET','POST'])
def get_field_charts():

    crm_dataset = mock_get_dataset()
    print('Request for /get_field_charts received')
    locs_fig  = get_dataset_locations_plot( crm_dataset )#, filters  )
    producers_fig, fractions_fig, active_fig  =  get_dataset_field_summary_plots( crm_dataset )# , filters  )
    sector_volumes_fig = get_dataset_sector_summary_plots( crm_dataset )
     
    
    field_charts = dict( fractions = fractions_fig, 
                        historical_production = producers_fig, 
                        activity = active_fig,
                        locations = locs_fig,
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
    
    
@app.route('/layout')
def layout():
     #return render_template('layoutVersion1B.html')
     return render_template('FixedColumnLeftSide.html')
     
     #return render_template('layoutVersion0B.html')
 
 
 
@app.route('/layout1')
def layout1():
     return render_template('layoutVersion1.html')
 
 

       
            

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


