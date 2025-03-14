from typing import List
from wf_lib2.crm_definitions import *
from wf_lib2.data.crm_dataset  import CRMDataset
from wf_lib2.data.crm_pattern  import CRMPattern
import numpy as np  
from pyproj import Proj, Transformer
import copy
 
def utm_to_latlon(x, y, zone=38):
    """
    Convert UTM coordinates to latitude and longitude.
    
    Parameters:
        x (float, list, or np.ndarray): Easting (X coordinate in meters)
        y (float, list, or np.ndarray): Northing (Y coordinate in meters)
        zone (int, optional): UTM zone number (default: 38 for Kuwait)
    
    Returns:
        (lat, lon): Tuple of latitude and longitude (same type as input)
    """
    # Convert input to numpy array for vectorized operations
    x, y = np.asarray(x), np.asarray(y)

    # Determine hemisphere (North for y > 0, South otherwise)
    hemisphere = np.where(y > 0, 'north', 'south')

    # Define transformation
    utm_proj = Proj(proj='utm', zone=zone, hemisphere=hemisphere[0])
    latlon_proj = Proj(proj='latlong', datum='WGS84')
    transformer = Transformer.from_proj(utm_proj, latlon_proj)

    # Transform coordinates
    lon, lat = transformer.transform(x, y)

    # Convert back to original type (if input was a list, return a list)
    if isinstance(x, list):
        return list(lat), list(lon)
    elif isinstance(x, float) or np.isscalar(x):
        return float(lat), float(lon)
    
    return lat, lon  # Returns NumPy array by default
 
 
def apply_dataset_filters( input_dataset:CRMDataset, filters: dict = None ) -> CRMDataset:
    d = input_dataset 
    
    if filters is None: filters = {} 
    
    dates = filters.get(DATE_KEYS[0], None)
    producer_names = filters.get('producer_names', None)
    injector_names = filters.get('injector_names', None)
    sector    = filters.get(SECTOR_KEYS[0], None)
    zone      = filters.get(ZONE_KEYS[0], None)  
    subzone   = filters.get(SUBZONE_KEYS[0], None)   
    reservoir = filters.get(RESERVOIR_KEYS[0], None)   #WARA
        
    NAME_COL = find_column( d.producers_df.columns, NAME_KEYS )
    if dates is not None:
        d = d.slice_dates_dataset( dates[0], dates[1])
        
    if producer_names is not None:
        names = producer_names + d.injector_names
        d = d.filter_by( NAME_COL, names )
    if injector_names is not None:
        names = d.producer_names + injector_names
        d = d.filter_by(NAME_COL, names )
        
    if sector is not None:
        if not isinstance(sector, List):
            sector = list( sector)
        sector = [ int(x) for x in sector ]
        col_name   = find_column( d.locations_df.columns, SECTOR_KEYS )
        well_names = d.locations_df[d.locations_df[col_name].isin(sector)][NAME_COL].values
        d = d.filter_by(NAME_COL, well_names ) 
        
    
        
    return d 

#producer summaries, the producer names are the column names
def get_dataset_field_summary( input_dataset:CRMDataset, cummulative=False, filters: dict = None ):
    
    ''' 
    all optional 
    filters = { 'dates': [date1, date2],
                'producer_names': [name1, name2],
                'injector_names': [name1, name2],
                'SECTOR': [1,2,3],
                'ZONE': ['Lower','Upper'],
                'RESERVOIR': [name1]
              }  
    
    time series of aggregated values 
    return {'liquid_production':liquid_production_summary, 
            'water_production':water_production_summary, 
            'oil_production':oil_production_summary,
            'water_injection': water_injection
            }
            
    '''
        


    d= apply_dataset_filters( input_dataset, filters )
            

    p = d.get_pattern(fix_time_gaps=True, fill_nan=0.0)
    liquid_production_summary = p.liquid_production.sum(axis=1)
    water_production_summary = p.water_production.sum(axis=1)
    oil_production_summary = p.oil_production.sum(axis=1)
    water_injection = p.water_injection.sum(axis=1)
    
    active_producers = p.liquid_production.gt( MIN_PRODUCTION_LEVEL).sum(axis=1)
    active_injectors = p.water_injection.gt(MIN_UPTICK_INJECTOR).sum(axis=1)
    
    
    if cummulative:
        liquid_production_summary = liquid_production_summary.cumsum()
        water_production_summary = water_production_summary.cumsum()
        oil_production_summary = oil_production_summary.cumsum()
        water_injection = water_injection.cumsum()
    
        
    # pie-chart for the fractions at the last known date 
    last_date = p.liquid_production.index[-1]
    liquid = liquid_production_summary[last_date]
    water  = water_production_summary[last_date]  
    oil    = oil_production_summary[last_date]
        
    total = liquid + water + oil
    liquid = liquid/total
    water  = water/total    
    oil    = oil/total
    
    
         
    return  {'active_producers':active_producers, 'active_injectors':active_injectors},\
            {'liquid_production':liquid_production_summary, 'water_production':water_production_summary, 'oil_production':oil_production_summary},\
            {'water_injection': water_injection},\
            {'liquid_fraction':liquid, 'water_fraction':water, 'oil_fraction':oil}, \
            {'dataset':d},{'pattern':p}
            
#def get_dataset_summary_plots(input_dataset:CRMDataset, cummulative=False, filters: dict = None ):
def get_dataset_summary_plots(active_wells, production_summary, injection_summary, fractions):
 
    #returns aggregated time series 
    #active_wells, production_summary, injection_summary, fractions, \
    #dataset, pattern = get_dataset_field_summary( input_dataset,cummulative=cummulative, filters = filters )

    layout={'title' : {'text':'Volume fractions',
                       'size':24,'color':'black',
                       'x':0.5,'xanchor':'center'
                      },
                     'legend':{'x':0,'y':1,'xanchor':'left','yanchor':'top'},
                     'margin': {
                                'l': 50,  #// left margin
                                'r': 50,  #// right margin
                                't': 80,  #// top margin
                                'b': 50   #// bottom margin
                            },
                                'autosize':True
                                } 


    colors = ['green','cyan','grey']
    data = [ {'fillcolor':'light'+colors[n], 'line': {'color':'dark'+colors[n]},
            'name':key.replace('_',' ').capitalize(), 
            'type':'scatter','mode':'lines','opacity': 0.99915,#'fill':  'tonexty', #'tonexty',
            'stackgroup':'Aggregated', 
            'x':value.index.astype(str).values.tolist(), 
            'y':value.values.tolist()  } for n, (key, value) in  enumerate(production_summary.items()) ]
    
    
    #historical aggregates 
    layout['title']['text'] = 'Historical volumes (stacked)'
    producers_fig = { 'data': data, #'layout': {'title':'Historical volumes (stacked)', 
                                    #'yaxis':{'title':'Volume'},
                                    #'xaxis':{'title':'Date'},
                                    #'legend':{'x':0,'y':1,
                                    #'xanchor':'left','yanchor':'top'} 
                                    #}, 
                     'layout': copy.deepcopy(layout)
                     }
    
    
    #add the water as a line 
    inj_data = {'name':'Water injection', 'type':'scatter','mode':'lines', 'line':{'color':'black','dash':'dot'}}
    inj_data['x'] = injection_summary['water_injection'].index.astype(str).values.tolist()
    inj_data['y'] = injection_summary['water_injection'].values.tolist()
    producers_fig['data'].append( inj_data )
    
    #pie chart with the fractions the last day (cummulative if selected)
    labels = [ x.replace('_',' ').capitalize() for x in list(fractions.keys()) ]
    fractions_data = [ {'values': list(fractions.values()), 'labels': labels, 'type':'pie'} ]
    
    layout['title']['text'] = 'Volume fractions'
    fractions_fig = {'data': fractions_data, 'layout': copy.deepcopy(layout)
                    }
    
    # a bar chart with the active wells
    active_data = [ { 'name': key.replace('_',' ').capitalize(), 
                     'type':'bar','mode':'bar', \
                      'x':value.index.astype(str).tolist(), 'y':value.values.tolist()}\
                      for key, value in active_wells.items() ] 
    
    layout['title']['text'] = 'Active wells'
    active_fig = {'data': active_data, 'layout': copy.deepcopy(layout)
                  #'layout': {'title' :'Active wells',
                  #                   'legend':{'x':0,'y':1,'xanchor':'left','yanchor':'top'}, 
                  #          } 
                }
    return producers_fig, fractions_fig, active_fig 
        
def get_dataset_locations_plot( crm_dataset, filters: dict = None ):
    
  
    d = apply_dataset_filters( crm_dataset, filters )
    
    f = d.locations_df[ d.locations_df['NAME'].isin( d.producer_names )]
    producers_data = {
        'name':'Producers','type':"scattermap", 'mode': 'markers+text',
        'text': f['NAME'].unique().tolist(),
        'lat': f['LAT'].values.tolist(),
        'lon': f['LONG'].values.tolist(),
        'marker': {
            'size': 10, 
            'color': 'red', 
            #'symbol': 'square'
        }}

   
    f = d.locations_df[ d.locations_df['NAME'].isin( d.injector_names )]
    injectors_data = {
        'name':'Injectors','type':"scattermap", 'mode': 'markers+text',
        'text': f['NAME'].unique().tolist(),
        'lat': f['LAT'].values.tolist(),
        'lon': f['LONG'].values.tolist(),
        'marker': {
            'size': 10,'color': 'blue', 
            #'symbol': 'triangle'
        }}  
    
    
    lat, lon = d.locations_df['LAT'], d.locations_df['LONG'] 
    min_lat,max_lat, min_lon, max_lon = lat.min(),lat.max(),lon.min(), lon.max()
    
    layout = {
        'fitbounds':"locations",  
        'legend':{'x':0,'y':1,'xanchor':'left','yanchor':'top'}, 
        'map': {'bounds': {'east':  max_lon+0.25,
                           'north': max_lat+0.35,
                           'south': min_lat-0.35,
                           'west':  min_lon-0.25
                           },
                           'center': {'lat': lat.mean(), 'lon': lon.mean()},
                           'domain': {'x': [0.0, 1.0], 'y': [0.0, 1.0]},
                           'style': 'open-street-map',
                           #'zoom': 2
                           },
        'margin': { 'r': 0, 't': 0, 'b': 0, 'l': 0 }
    }   

    print(max_lon,max_lat,min_lat,min_lon) 
   
   
    fig = {'data':[producers_data, injectors_data] , 'layout':layout}
    return fig
