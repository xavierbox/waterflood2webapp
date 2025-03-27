#from application import app_var as app 
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
 
class Storage:
    
    def __init__(self, config ):
        self.config = config 
        
    def get_dataset( self, filters = None ):
        
        if not filters is None:
            print('---received a request with filters', filters)

        
        locs = pd.read_csv( 'example_datasets/locations_example1.csv')
        locs['LAT'], locs['LONG'] = utm_to_latlon( locs['X'], locs['Y'] )
        inj =  pd.read_csv( 'example_datasets/injectors_example1.csv')
        prd =  pd.read_csv( 'example_datasets/producers_example1.csv')
        

        #locs = pd.read_csv( 'C:/Work/2025/waterflood/webapp/application/example_datasets/koc_DATASET_LocationsSynthetic.csv').fillna(111.0)
        #inj = pd.read_csv(  'C:/Work/2025/waterflood/webapp/application/example_datasets/koc_DATASET_InjectorsSynthetic.csv').fillna(110.0)
        #prd = pd.read_csv(  'C:/Work/2025/waterflood/webapp/application/example_datasets/koc_DATASET_ProducersSynthetic.csv').fillna(101.0)
        
        print('done')
        
        
     
        time_format =  "%d/%m/%Y" # DATE_FORMAT  #21/07/2024
        crm_dataset = CRMDataset.instance( inj, prd, locs, time_format=time_format ) 
        crm_dataset.check_dataset()
        
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
                    'Genetic optimization' 
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
            
 
def get_field_charts():

    filters = {'subzone':['LW'], 'sector':[1,4,7]}
    crm_dataset = Storage( None ).get_dataset( filters )

    d= apply_dataset_filters( crm_dataset, filters )
            
    p = d.get_pattern(fix_time_gaps=True, fill_nan=0.0)
    print(p.liquid_production)
     
    #return jsonify( {'message':'Data loaded', 'data' : field_charts }), 200   
    

    # field 
    # time cummulatives, current step aggregates and active wells in time 
    #producers_fig, fractions_fig, active_fig, locs  = mock_get_field_plots() 
    #field_charts = dict( fractions = fractions_fig, 
    #                    historical_production = producers_fig, 
    #                    activity = active_fig,
    #                    locations = locs
    #                    )
    #return jsonify( {'message':'Data loaded', 'data' : field_charts }), 200   
  
  
  
get_field_charts() 