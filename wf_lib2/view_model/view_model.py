from typing import List
from wf_lib2.crm_definitions import *
from wf_lib2.data.crm_dataset  import CRMDataset
from wf_lib2.data.crm_pattern  import CRMPattern
import numpy as np  
from pyproj import Proj, Transformer
import copy

default_colors = ['green','cyan','grey','orange','blue','red','purple','yellow','brown','pink']

def default_plotly_layout_python():
    
    layout={'title' : {'text':' ',
                       #'font-size':24,
                       #'font-color':'black',
                       'x':0.5,'xanchor':'center'
                      },
                     'legend':{'x':0.015,'y':0.985,'xanchor':'left','yanchor':'top'},
                     'margin': {
                                'l': 50,  #// left margin
                                'r': 50,  #// right margin
                                't': 80,  #// top margin
                                'b': 50   #// bottom margin
                            },
                                'autosize':True
                                } 
    
    return layout  
    
def default_plotly_config_python():
    return {
      'responsive': True,
      'displaylogo': False,
      'displayModeBar': True,
      'modeBarButtonsToAdd': ['zoom', 'pan', 'select', 'zoomIn', 'zoomOut', 'autoScale', 'resetScale','lasso2d']
    } 
    
 
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
            

    p = d.get_pattern(fix_time_gaps=False, fill_nan=0.0)
    liquid_production_summary = p.liquid_production.sum(axis=1)
    water_production_summary = p.water_production.sum(axis=1)
    oil_production_summary = p.oil_production.sum(axis=1)
    gas_production_summary = p.gas_production.sum(axis=1)
    
    water_injection = p.water_injection.sum(axis=1)
    
    active_producers = p.liquid_production.gt( MIN_PRODUCTION_LEVEL).sum(axis=1)
    active_injectors = p.water_injection.gt(MIN_UPTICK_INJECTOR).sum(axis=1)
    
    #cummulative = False
    if cummulative:
        liquid_production_summary = liquid_production_summary.cumsum()
        water_production_summary = water_production_summary.cumsum()
        oil_production_summary = oil_production_summary.cumsum()
        gas_production_summary = gas_production_summary.cumsum()
        water_injection = water_injection.cumsum()
        
    
        
    # pie-chart for the fractions at the last known date 
    last_date = p.liquid_production.index[-1]
    liquid = liquid_production_summary[last_date]
    water  = water_production_summary[last_date]  
    oil    = oil_production_summary[last_date]
    gas    = gas_production_summary[last_date]    
    
    print('------liquid', liquid, 'water', water, 'oil', oil, 'gas', gas, 'total', water+oil+gas)
        
    total = gas + water + oil
    liquid = liquid/total
    water  = water/total    
    oil    = oil/total
    gas    = gas/total
    
    #charts = [ total_water_produced, total_oil_produced, total_gas_produced,total_liquid,total_water_injected]
         
    return  {'active_producers':active_producers, 'active_injectors':active_injectors},\
        {'water_production':water_production_summary,   
        'oil_production':oil_production_summary,   
        'gas_production':gas_production_summary,
        'liquid_production':liquid_production_summary, 
        },\
        {'water_injection': water_injection},\
        {'water_fraction':water, 'oil_fraction':oil,'gas_fraction':gas}, \
        {'dataset':d},{'pattern':p}
            
            
            
def get_dataset_field_summary_plots(input_dataset:CRMDataset, cummulative = False, filters: dict = None ):
#def get_dataset_summary_plots(active_wells, production_summary, injection_summary, fractions):
 
 
    active_wells, production_summary, injection_summary, fractions, dataset, pattern = get_dataset_field_summary( input_dataset, cummulative=cummulative,  filters = filters )
    
    #returns aggregated time series 
    #active_wells, production_summary, injection_summary, fractions, \
    #dataset, pattern = get_dataset_field_summary( input_dataset,cummulative=cummulative, filters = filters )

    layout = default_plotly_layout_python()


    colors = ['blue','grey','brown','green'] + default_colors #['green','cyan','grey','orange','blue','red','purple','yellow','brown','pink']
    xx =  [ {'fillcolor':'light'+colors[n],
            'name':key.replace('_',' ').capitalize()} for n, (key, value) in  enumerate(production_summary.items())]
 
    #print(xx)
     
    
    data = [ {'fillcolor': {'color':'light'+colors[n]}, 'line': {'color':colors[n]},
            'name':key.replace('_',' ').capitalize(), 
            'type':'scatter','mode':'lines','opacity': 0.99915,#'fill':  'tonexty', #'tonexty',
            'stackgroup':'Aggregated', 
            'x':value.index.astype(str).values.tolist(), 
            'y':value.values.tolist()  } for n, (key, value) in  enumerate(production_summary.items()) ]
    
    
    #historical aggregates 
    layout['title']['text'] = 'Stacked historical volumes' + (' (cummulative)' if cummulative else '')   
    producers_fig = { 'data': data,'layout': copy.deepcopy(layout),'config':default_plotly_config_python()
                     }
    
    
    #add the water as a line 
    inj_data = {'name':'Water injection', 'type':'scatter','mode':'lines', 'line':{'color':'black','dash':'dot'}}
    inj_data['x'] = injection_summary['water_injection'].index.astype(str).values.tolist()
    inj_data['y'] = injection_summary['water_injection'].values.tolist()
    producers_fig['data'].append( inj_data )
    
    
    
    #pie chart with the fractions the last day (cummulative if selected)
    #water-oil-gas and liquid fractions
    labels = [ x.replace('_',' ').capitalize() for x in list(fractions.keys()) ]
    print(labels)
    fractions_data = [ {'values': list(fractions.values()), 'labels': labels, 'type':'pie',
                        'marker':{'colors':['blue','grey','brown','green']}, 'hole':0.4, 'name':'Fractions'
                        } ]
    
    layout['title']['text'] = 'Volume fractions at present-day' + "" if not cummulative else " (cummulative)"
    layout['legend'] =dict(
        orientation='h',   # Set legend to horizontal
        yanchor='bottom',
        y=-0.2,            # Position below the plot
        xanchor='center',
        x=0.5              # Center the legend
    )
    fractions_fig = {'data': fractions_data, 'layout': copy.deepcopy(layout),
                     'config':default_plotly_config_python()
                    }
    
    # a bar chart with the active wells
    active_data = [ { 'name': key.replace('_',' ').capitalize(), 
                     #'type':'bar',
                     #'mode':'bar', \
                      'x':value.index.astype(str).tolist(), 'y':value.values.tolist()}\
                      for key, value in active_wells.items() ] 
    layout=default_plotly_layout_python()
    layout['title']['text'] = 'Active wells'

        
    active_fig = {'data': active_data, 'layout': copy.deepcopy(layout),'config':default_plotly_config_python() }
    return producers_fig, fractions_fig, active_fig 
       
       
def get_dataset_locations_plot( crm_dataset, filters: dict = None ):
    
  
    d = apply_dataset_filters( crm_dataset, filters )
    SECTOR_COL = find_column( d.locations_df.columns, SECTOR_KEYS )
    LAT_COL = find_column( d.locations_df.columns, LAT_KEYS )
    LONG_COL = find_column( d.locations_df.columns, LONG_KEYS )
    
    f = d.locations_df[ d.locations_df['NAME'].isin( d.producer_names )]
    producers_data = {
        'name':'Producers','type':"scattermap", 'mode': 'markers+text',
        'text': f['NAME'].unique().tolist(),
        'lat': f[LAT_COL].values.tolist(),
        'lon': f[LONG_COL].values.tolist(),
        'sector': f[SECTOR_COL].values.tolist(),
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
        #'fitbounds':"locations",  
        'legend':{'x':0,'y':1,'xanchor':'left','yanchor':'top'}, 
        'map': {'bounds': {'east':  max_lon+0.5,
                           'north': max_lat+0.5,
                           'south': min_lat-0.5,
                           'west':  min_lon-0.5
                           },
                           'center': {'lat': lat.mean(), 'lon': lon.mean()},
                           'domain': {'x': [0.0, 1.0], 'y': [0.0, 1.0]},
                           'style': 'open-street-map',
                           #'zoom': 2
                           },
        'margin': { 'r': 0, 't': 0, 'b': 0, 'l': 0 }
    }   

    layout2 = copy.deepcopy(layout).update(layout)
   
   
    fig = {'data':[producers_data, injectors_data] , 'layout':layout } #, 'config':default_plotly_config_python() }
    return fig



def get_dataset_sector_summary_plots(input_dataset:CRMDataset, filters: dict = None ):
    
    crm_dataset = apply_dataset_filters( input_dataset, filters )
    
    #1. a bar-chart for each sector showing a snapshot of the the aggregated volumes
    #at the last time of the dataset (or filter if it includes dates)
    
    WATER_INJ_COL = find_column( crm_dataset.injectors_df.columns, WATER_INJECTION_KEYS )
    WATER_PROD    = find_column( crm_dataset.producers_df.columns, WATER_PRODUCTION_KEYS )   
    OIL_PROD      = find_column( crm_dataset.producers_df.columns, OIL_PRODUCTION_KEYS )
    GAS_PROD      = find_column( crm_dataset.producers_df.columns, GAS_PRODUCTION_KEYS )

    total_water_injected=[]
    total_water_produced=[]
    total_oil_produced=[]
    total_gas_produced=[]

    SECTOR_COL = find_column( crm_dataset.locations_df.columns, SECTOR_KEYS ) 
    sectors =  sorted(crm_dataset.locations_df[SECTOR_COL].unique().tolist())
    names  =['total_water_produced', 'total_oil_produced', 'total_gas_produced','total_water_injected', ]
    for sector in sorted(sectors):
        tmp = crm_dataset.filter_by('SECTOR', [sector] )
        
        
        total_water_produced.append( tmp.producers_df[ [WATER_PROD] ].sum(axis=0)[0])
        total_oil_produced.append(   tmp.producers_df[ [OIL_PROD] ].sum(axis=0)[0])
        total_gas_produced.append(   tmp.producers_df[ [GAS_PROD] ].sum(axis=0)[0] )
        total_water_injected.append( tmp.injectors_df[ [WATER_INJ_COL] ].sum(axis=0)[0])
    
    #this can be an inset: absolute values 
    water_injected = copy.deepcopy(total_water_injected)
    water_produced = copy.deepcopy(total_water_produced)
    oil_produced   = copy.deepcopy(total_oil_produced)
    gas_produced   = copy.deepcopy(total_gas_produced)
    
    
    
    
    
    
    
    #normalize per sector 
    total_liquid = [] 
    for n in range(0, len(total_water_produced)):
        total = (total_water_produced[n] + total_oil_produced[n] + total_gas_produced[n]).astype(float)
        total_water_produced[n] = (total_water_produced[n]/total).astype(float) if total > 0.0001 else 0
        total_oil_produced[n] = (total_oil_produced[n]/total).astype(float) if total > 0.0001 else 0
        total_gas_produced[n] = (total_gas_produced[n]/total).astype(float) if total > 0.0001 else 0 
        total_liquid.append( total.astype(float) )
    
    
    charts = [ total_water_produced, total_oil_produced, total_gas_produced,total_water_injected,total_liquid]
    
    
    data = [] 
    names.append('Total liquid produced')
    colors =  ['blue','grey','brown','cyan','green']  + default_colors# ['blue','grey','brown','cyan','green','red','purple','yellow','brown','pink']
    for n,chart in enumerate(charts):
        chart_name_ = names[n].replace("_"," ").capitalize()
        
        print( colors[n], chart_name_)
        
        y,x = chart,sectors
        y= [float(x) for x in y]
        #print(sectors, type(sectors), type(sectors[0]))
        
        d = { 'sector':sectors[n], 'name' : chart_name_, 'x':x, 'y':y, 'type':'bar', 'marker':{'color':colors[n]} }
        if chart == total_water_injected or chart == total_liquid:
            d['yaxis'] = 'y2'
            d['marker']['size'] = 16
            d['marker']['opacity'] = 0.5
            d['type']= 'scatter'
            d['mode'] = 'markers'
        
        data.append( d )
        
        #spline = copy.deepcopy( d )
        #spline['mode'] = 'lines'
        #spline['type'] = 'scatter'
        #spline['name'] = 'Spline ' + str(n)
        #spline["line"] ={"shape": "spline", "color": colors[n], "width": 3}
        #if chart == total_water_injected:    
        #    spline['yaxis'] = 'y2'
        #data.append( spline )        
        
        
    layout = default_plotly_layout_python()
    layout['title']['text'] = 'Cummulated volumes per sector'
    layout["yaxis"]= {
            "title": "Ratios",'zeroline':False 
        }
    layout["yaxis2"]= {
            "title": "Total volume", 
            "overlaying": "y",'zeroline':False,
            "side": "right"
        }
     
    layout['legend'] =dict(
        orientation='h',   # Set legend to horizontal
        yanchor='bottom',
        y=-0.2,            # Position below the plot
        xanchor='center',
        x=0.5              # Center the legend
    )
    
    sector_fig = {'data':data, 'layout':layout, 'config':default_plotly_config_python() }
    return sector_fig