from typing import List
from wf_lib2.crm_definitions import *
from wf_lib2.data.crm_dataset  import CRMDataset
from wf_lib2.data.crm_pattern  import CRMPattern
import numpy as np  
from pyproj import Proj, Transformer
import copy
from scipy.spatial import cKDTree


default_colors = ['green','cyan','lightgrey','salmon','blue','red','purple','yellow','brown','pink']
 

def default_plotly_layout_python():
    
    layout={'title' : {'text':' ',
                       #'font-size':24,
                       #'font-color':'black',
                       'x':0.5,'xanchor':'center',
                       'textposition':  'top center',
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
    well_names = filters.get('names', None)
    
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
        
    if well_names is not None:
        d = d.filter_by(NAME_COL, well_names )
        
        
        
    if sector is not None:
        if not isinstance(sector, List):
            sector = list( sector)
        sector = [ int(x) for x in sector ]
        col_name   = find_column( d.locations_df.columns, SECTOR_KEYS )
        well_names = d.locations_df[d.locations_df[col_name].isin(sector)][NAME_COL].values
        d = d.filter_by(NAME_COL, well_names ) 
        
    keys = [zone, subzone, reservoir]
    known_keys = [ZONE_KEYS, SUBZONE_KEYS, RESERVOIR_KEYS]
    for n, key in enumerate(keys):
        if key is not None:
            if not isinstance(key, List):
                key = [key]
            col_name   = find_column( d.locations_df.columns, known_keys[n] )
            well_names = d.locations_df[d.locations_df[col_name].isin(key)][NAME_COL].values
            d = d.filter_by(NAME_COL, well_names )
            
        
    return d 

#producer summaries, the producer names are the column names
def OOBSOLETE_get_dataset_field_summary( input_dataset:CRMDataset, cummulative=False, filters: dict = None ):
    
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
     
        
    total = gas + water + oil
    liquid = liquid/total
    water  = water/total    
    oil    = oil/total
    gas    = gas/total
    
    
    
         
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


    def fractions_plot( pattern, cummulative = False ):
        liquid_production_summary = pattern.liquid_production.sum(axis=1)
        water_production_summary  = pattern.water_production.sum(axis=1)
        oil_production_summary    = pattern.oil_production.sum(axis=1)
        gas_production_summary    = pattern.gas_production.sum(axis=1)
        liquid_production_summary
        
        fractions_dfs = [water_production_summary, oil_production_summary,gas_production_summary]
        fractions_labels = ['Water', 'Oil','Gas']
        fractions_data   = []
        sum_values = 1.0 
        last_date = water_production_summary.index.max() 

        for n, w in enumerate(fractions_dfs):
            if cummulative:
                w = w.cumsum(axis = 0 )  
                
            last_date_value = w.loc[ w.index.max() ]
            fractions_data.append(last_date_value)
            sum_values = sum_values + last_date_value 
            last_date = max( last_date, w.index.max() )
        for n in range( len(fractions_data )):
            fractions_data[n] = round( fractions_data[n] / sum_values, 2 ) 
        
        x = 'cummulative' if cummulative == True else '' 
        layout = copy.deepcopy( default_plotly_layout_python() )
        layout['title']['text'] = f'Volume fractions {x} present-day ({last_date.strftime("%d-%m-%Y")})'
        layout['legend']= {'orientation': 'h', 'yanchor': 'bottom', 'y': -0.2, 'xanchor': 'center', 'x': 0.5}
        fig_dict  = {'data' : [ {'values':fractions_data,'labels':fractions_labels, 'type':'pie','hole':0.4, 'name':'Fractions',
                                'marker': {'colors': ['blue', 'lightgrey', 'brown']}
                                }
                            ],
                    'layout': layout,
                    'config': default_plotly_config_python()}
        
        return fig_dict


    def stacked_historical_production_plot( pattern, cummulative = False ):
        p = pattern 
        liquid_production_summary = p.liquid_production.sum(axis=1)
        water_production_summary  = p.water_production.sum(axis=1)
        oil_production_summary    = p.oil_production.sum(axis=1)
        gas_production_summary    = p.gas_production.sum(axis=1)
        water_injection = p.water_injection.sum(axis=1)
        
        if cummulative:
            liquid_production_summary = liquid_production_summary.cumsum()
            water_production_summary  = water_production_summary.cumsum()
            oil_production_summary    = oil_production_summary.cumsum()
            gas_production_summary    = gas_production_summary.cumsum()
            water_injection           = water_injection.cumsum()
            
        production_summary = {'water_production':water_production_summary,   
            'oil_production':oil_production_summary,   
            'gas_production':gas_production_summary,
            'liquid_production':liquid_production_summary, 
            }
        injection_summary = {'water_injection': water_injection}
        
        #historical aggregates 
        colors = ['blue','grey','brown','green'] + default_colors
        producers_data = [ {'fillcolor': {'color':'light'+colors[n]}, 'line': {'color':colors[n]},
                'name':key.replace('_',' ').capitalize(), 
                'type':'scatter','mode':'lines','opacity': 0.99915,#'fill':  'tonexty', #'tonexty',
                'stackgroup':'Aggregated', 
                'x':value.index.astype(str).values.tolist(), 
                'y':value.values.tolist()} for n, (key, value) in  enumerate(production_summary.items()) ]
        
        inj_data = {'name':'Water injection', 'type':'scatter','mode':'lines', 'line':{'color':'black','dash':'dot'},
                    'x' : injection_summary['water_injection'].index.astype(str).values.tolist(),
                    'y' : [ round(i,2) for i in injection_summary['water_injection'].values.tolist()]
                    }
        
        producers_data.append( inj_data )
        
        #round 2 decimals the production history  
        layout['title']['text'] = 'Stacked historical volumes' + (' (cummulative)' if cummulative else '')   
        producers_fig = { 'data': producers_data,'layout': copy.deepcopy(layout),'config':default_plotly_config_python()}   
        for d in producers_fig['data']:d['y'] = [ round(i,2) for i in d['y']]
    
        return producers_fig
    
       
    d= apply_dataset_filters( input_dataset, filters )
    pattern = d.get_pattern(fix_time_gaps=True, fill_nan=0.0)
    
    #pie chart 
    fractions_fig = fractions_plot( pattern, cummulative )
   
    #activity in time chart 
    active_producers = pattern.liquid_production.gt( MIN_PRODUCTION_LEVEL).sum(axis=1)
    active_injectors = pattern.water_injection.gt(MIN_UPTICK_INJECTOR).sum(axis=1)
    active_wells = {'active_producers':active_producers, 'active_injectors':active_injectors}
    active_data = [ { 'name': key.replace('_',' ').capitalize(), 'x':value.index.astype(str).tolist(), 'y':value.values.tolist()} for key, value in active_wells.items() ] 
    layout = copy.deepcopy( default_plotly_layout_python())
    layout['title']['text'] = 'Historical completion activity'
    active_fig = {'data': active_data, 'layout': layout,'config':default_plotly_config_python() }
    
    #historical stacked 
    producers_fig = stacked_historical_production_plot( pattern, cummulative )
    
    return producers_fig, fractions_fig, active_fig 
       
       
       
def get_dataset_locations_plot( crm_dataset, filters: dict = None ):
    
  
    d = apply_dataset_filters( crm_dataset, filters )
    SECTOR_COL = find_column( d.locations_df.columns, SECTOR_KEYS )
    LAT_COL = find_column( d.locations_df.columns, LAT_KEYS )
    LONG_COL = find_column( d.locations_df.columns, LONG_KEYS )
    
    f = d.locations_df[ d.locations_df['NAME'].isin( d.producer_names )]
    
    custom_data = ['Sector:' + str(s) for s in f[SECTOR_COL].values.tolist()]
    
    producers_data = {
        'name':'Producers','type':"scattermap", 'mode': 'markers+text',
        'text': f['NAME'].unique().tolist(),
        'customdata': custom_data,
        'textposition':  'top center',
          
        'hovertemplate': 
            '%{text}<br>' + 
            '%{customdata}<extra></extra>',
            
        'sector': f[SECTOR_COL].values.tolist(),
        'marker': {
            'size': 10, 
            'color': 'red', 
            #'symbol': 'square'
        }}
    
    if LAT_COL in f:
        producers_data['lat'] = f[LAT_COL].values.tolist()
        producers_data['lon'] = f[LONG_COL].values.tolist()
    else:
        X_COL = find_column( d.locations_df.columns, X_KEYS )
        Y_COL = find_column( d.locations_df.columns, Y_KEYS )
        producers_data['x'] = f[ X_COL].values.tolist()
        producers_data['y'] = f[ Y_COL].values.tolist()
        
        
   
    f = d.locations_df[ d.locations_df['NAME'].isin( d.injector_names )]
    custom_data = ['Sector:' + str(s) for s in f[SECTOR_COL].values.tolist()]

    injectors_data = {
        'name':'Injectors','type':"scattermap", 'mode': 'markers+text',
        'text': f['NAME'].unique().tolist(),
          'customdata': custom_data,
        'lat': f['LAT'].values.tolist(),
        'lon': f['LONG'].values.tolist(),
        'textposition':  'top center',  
        'hovertemplate': 
            '%{text}<br>' + 
            '%{customdata}<extra></extra>',
            
        'marker': {
            'size': 10,'color': 'blue', 
            #'symbol': 'triangle'
        }}  
    if LAT_COL in f:
        injectors_data['lat'] = f[LAT_COL].values.tolist()
        injectors_data['lon'] = f[LONG_COL].values.tolist()
    else:
        X_COL = find_column( d.locations_df.columns, X_KEYS )
        Y_COL = find_column( d.locations_df.columns, Y_KEYS )
        injectors_data['x'] = f[ X_COL].values.tolist()
        injectors_data['y'] = f[ Y_COL].values.tolist()
        
        
  
    layout = {
            'hoverlabel': {
                'font': {
                    'size': 16,      
                    'color': 'grey'
                }},
                
            #'fitbounds':"locations",  
            'legend':{'x':0,'y':1,'xanchor':'left','yanchor':'top'}, 
            'autosize':True,
            'textposition':  'top center',
            #'title': {'text':'Field locations'},
            'margin': { 'r': 10, 't': 10, 'b': 10, 'l': 10 }
        }  
      
    if LAT_COL in f:
        lat, lon = d.locations_df['LAT'], d.locations_df['LONG'] 
        min_lat,max_lat, min_lon, max_lon = lat.min(),lat.max(),lon.min(), lon.max()
 

        layout['map'] = {'bounds': {'east':  max_lon+0.5,
                           'north': max_lat+0.5,
                           'south': min_lat-0.5,
                           'west':  min_lon-0.5
                           },
                           'center': {'lat': lat.mean(), 'lon': lon.mean()},
                           'domain': {'x': [0.0, 1.0], 'y': [0.0, 1.0]},
                           'style': 'open-street-map',
                           #'zoom': 2
                           }
    
     
   
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
    #water_injected = copy.deepcopy(total_water_injected)
    #water_produced = copy.deepcopy(total_water_produced)
    #oil_produced   = copy.deepcopy(total_oil_produced)
    #gas_produced   = copy.deepcopy(total_gas_produced)
    
    
    #normalize per sector 
    total_liquid = [] 
    for n in range(0, len(total_water_produced)):
        total = (total_water_produced[n] + total_oil_produced[n] + total_gas_produced[n]).astype(float)
        total_water_produced[n] = (total_water_produced[n]/total).astype(float) if total > 0.0001 else 0
        total_oil_produced[n] = (total_oil_produced[n]/total).astype(float) if total > 0.0001 else 0
        total_gas_produced[n] = (total_gas_produced[n]/total).astype(float) if total > 0.0001 else 0 
        total_liquid.append( total.astype(float) )
    
    
    total_liquid = [ round(x,2) for x in total_liquid]
    total_water_injected = [ round(x,2) for x in total_water_injected]
    
    charts = [ total_water_produced, total_oil_produced, total_gas_produced,total_water_injected,total_liquid]
    
    
    data = [] 
    names.append('Total liquid produced')
    colors =  ['blue','lightgrey','brown','cyan','green']  + default_colors# ['blue','grey','brown','cyan','green','red','purple','yellow','brown','pink']
    for n,chart in enumerate(charts):
        chart_name_ = names[n].replace("_"," ").capitalize()
         
        y,x = chart,sectors
        y= [round(float(xx),2) for xx in y]
        #print(sectors, type(sectors), type(sectors[0]))
        
        d = { #'sector':sectors[n], 
             'name' : chart_name_, 'x':x, 'y':y, 'type':'bar', 'marker':{'color':colors[n]} }
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


def get_field_wells_snapshot( crm_dataset,# date_cutoff = '2020-02-01', 
                             x_column = None,y_column= None, filters = None ):

    if x_column is None: 
        x_column = 'WATER_PRODUCTION' 
    if y_column is None: 
        y_column = 'OIL_PRODUCTION'
        

    filtered = apply_dataset_filters( crm_dataset , filters )

    sector_map = filtered.locations_df.set_index('NAME')['SECTOR'].to_dict()
    filtered.producers_df['SECTOR'] = filtered.producers_df['NAME'].map( sector_map )


    df = filtered.producers_df.sort_values( by=['DATE'], ascending=True)
    #df = df[ df['DATE'] == date_cutoff ].sort_values( by=['DATE'],ascending=True)
  

    data = [] 
    markers = ['circle', 'triangle-right','square', 'diamond', 'triangle-up', 'triangle-down', 'cross', 'star','cross', 
               'hexagon','square-cross','circle-x','hourglass', 'pentagon','square-cross']
    
    sectors_array = sorted(df['SECTOR'].unique())
    xmax = 0.0 
    for s in sectors_array:
        ddf = df[df['SECTOR'] == s]
        grouped = ddf.groupby('NAME').agg( {x_column:'sum', y_column:'sum'} )[[x_column,y_column]]
        x,y = grouped[x_column].values.tolist(), grouped[y_column].values.tolist() 
        well_names = grouped.index.tolist() 
        #well_names = ddf['NAME'].values.tolist()
        #water_production = ddf[ x_column].values.tolist()
        #oil_production = ddf[ y_column].values.tolist()
    
        
        
        #sector = ddf['SECTOR'].values.tolist()
        marker = {'symbol': np.random.choice(markers)  }#, 'size':10}
        series = { 'marker':marker, 'textposition':'top center',
                  'textfont':{'size': 8},
                  'name':'Sector '+str(s),'text':well_names, 
                'x':x, 'y':y, 'mode':'markers', 'type':'scatter'}
        data.append( series )
        xmax = max( xmax, np.max(x) )
        
    #finally, add a straing line y = x as a guide to the eye 
    #xmin,xmax = np.min(water_production), np.max(water_production)
    #ymin,ymax = np.min(water_production), np.max(water_production)
    line = { 'x':[0,xmax], 'y':[0.0001,xmax], 
                       'mode':'lines', 
                       'line':{'width':1, 'color':'lightgrey', 'dash':'dashdot', 'color':'black'},
                       'type':'scatter', 'name':'y=x'

            }
    
    data.append( line )
        
    
    title1 = x_column.replace('_',' ').capitalize()
    title2 = y_column.replace('_',' ').capitalize()
    
    
    layout = {'xaxis':{'title': title1}, 'yaxis':{'title':title2}}
    fig = {'data':data, 'layout':layout}
    return fig 
   
 
 
def get_field_wells_snapshot_singles( crm_dataset,# date_cutoff = '2020-02-01', 
                             x_column = None,y_column= None, filters = None ):

    if x_column is None: 
        x_column = 'WATER_PRODUCTION' 
    if y_column is None: 
        y_column = 'OIL_PRODUCTION'
        

    filtered = apply_dataset_filters( crm_dataset , filters )

    sector_map = filtered.locations_df.set_index('NAME')['SECTOR'].to_dict()
    filtered.producers_df['SECTOR'] = filtered.producers_df['NAME'].map( sector_map )


    df = filtered.producers_df.sort_values( by=['DATE'], ascending=True)
    #df = df[ df['DATE'] == date_cutoff ].sort_values( by=['DATE'],ascending=True)
  

    data = [] 
    markers = ['circle', 'triangle-right','square', 'diamond', 'triangle-up', 'triangle-down', 'cross', 'star','cross', 
               'hexagon','square-cross','circle-x','hourglass', 'pentagon','square-cross']
    
    sectors_array = sorted(df['SECTOR'].unique())
    xmax = 0.0 
    for s in sectors_array:
        ddf = df[df['SECTOR'] == s]
        grouped = ddf.groupby('NAME').agg( {x_column:'sum', y_column:'sum'} )[[x_column,y_column]]
        x,y = grouped[x_column].values.tolist(), grouped[y_column].values.tolist() 
        well_names = grouped.index.tolist() 
        #well_names = ddf['NAME'].values.tolist()
        #water_production = ddf[ x_column].values.tolist()
        #oil_production = ddf[ y_column].values.tolist()
    
        
        
        #sector = ddf['SECTOR'].values.tolist()
        marker = {'symbol': np.random.choice(markers)  }#, 'size':10}
        series = { 'marker':marker, 'textposition':'top center',
                  'textfont':{'size': 8},
                  'name':'Sector '+str(s),'text':well_names, 
                'x':x, 'y':y, 
                'mode':'markers', 'type':'scatter'}
        data.append( series )
        xmax = max( xmax, np.max(x) )
        
    #finally, add a straing line y = x as a guide to the eye 
    #xmin,xmax = np.min(water_production), np.max(water_production)
    #ymin,ymax = np.min(water_production), np.max(water_production)
    line = { 'x':[0,xmax], 'y':[0.0001,xmax], 
                       'mode':'lines', 
                       'line':{'width':1, 'color':'lightgrey', 'dash':'dashdot', 'color':'black'},
                       'type':'scatter', 'name':'y=x'

            }
    
    data.append( line )
        
    
    title1 = x_column.replace('_',' ').capitalize()
    title2 = y_column.replace('_',' ').capitalize()
    
    
    layout = {'xaxis':{'title': title1}, 'yaxis':{'title':title2}}
    fig = {'data':data, 'layout':layout}
    return fig 
   
    
 
def get_field_wells_snapshot_helper( index, crm_dataset,x_column = None,y_column= None, filters = None ):

    showlegend= False if index != 1 else True  

    if x_column is None: x_column = 'WATER_PRODUCTION' 
    if y_column is None: y_column = 'OIL_PRODUCTION'
            

    filtered = apply_dataset_filters( crm_dataset , filters )

    sector_map = filtered.locations_df.set_index('NAME')['SECTOR'].to_dict()
    filtered.producers_df['SECTOR'] = filtered.producers_df['NAME'].map( sector_map )


    df = filtered.producers_df.sort_values( by=['DATE'], ascending=True)
    #df = df[ df['DATE'] == date_cutoff ].sort_values( by=['DATE'],ascending=True)
  

    data = [] 
    markers = ['circle', 'triangle-right','square', 'diamond', 'triangle-up', 'triangle-down', 'cross', 'star','cross', 
               'hexagon','square-cross','circle-x','hourglass', 'pentagon','square-cross']
    
    sectors_array = sorted(df['SECTOR'].unique())
    xmax = 0.0 
    for s in sectors_array:
        
        ddf = df[df['SECTOR'] == s]
        grouped = ddf.groupby('NAME').agg( {x_column:'sum', y_column:'sum'} )[[x_column,y_column]]
        x,y = grouped[x_column].values.tolist(), grouped[y_column].values.tolist() 
        well_names = grouped.index.tolist() 
        #well_names = ddf['NAME'].values.tolist()
        #water_production = ddf[ x_column].values.tolist()
        #oil_production = ddf[ y_column].values.tolist()
    
        
        
        #sector = ddf['SECTOR'].values.tolist()
        marker = {'symbol': np.random.choice(markers)  }#, 'size':10}
        series = { 'marker':marker, 'textposition':'top center',
                  'textfont':{'size': 8},
                   
                   
                    'xaxis': 'x'+str(index),
                   
                    'yaxis': 'y'+str(index), #'xaxis': 'x' ,
                    
                    'showlegend': showlegend, 
        
                  'name':'Sector '+str(s),'text':well_names, 'legendgroup': 'group'+str(s),
                'x':x, 'y':y, 'mode':'markers', 'type':'scatter'}
        
        
        data.append( series )
        xmax = max( xmax, np.max(x) )
        

        
    return data, xmax 
        
    #finally, add a straing line y = x as a guide to the eye 
    #xmin,xmax = np.min(water_production), np.max(water_production)
    #ymin,ymax = np.min(water_production), np.max(water_production)
    line = { 'x':[0,xmax], 'y':[0.0001,xmax], 
                       'mode':'lines', 
                       'line':{'width':1, 'color':'lightgrey', 'dash':'dashdot', 'color':'black'},
                       'type':'scatter', 'name':'y=x'

            }
    
    data.append( line )
        
    
    title1 = x_column.replace('_',' ').capitalize()
    title2 = y_column.replace('_',' ').capitalize()
    
    
    layout = {'xaxis':{'title': title1}, 'yaxis':{'title':title2}}
    fig = {'data':data, 'layout':layout}
    return fig 
 
    
def get_field_wells_snapshot( crm_dataset, filters = None ):
    
    WATER_PROD = find_column( crm_dataset.producers_df.columns, WATER_PRODUCTION_KEYS )
    OIL_PROD = find_column( crm_dataset.producers_df.columns, OIL_PRODUCTION_KEYS )
    GAS_PROD = find_column( crm_dataset.producers_df.columns, GAS_PRODUCTION_KEYS )
    LIQUID_PROD = find_column( crm_dataset.producers_df.columns, LIQUID_PRODUCTION_KEYS )
    data1,x1  = get_field_wells_snapshot_helper(1, crm_dataset,  x_column=WATER_PROD, y_column= GAS_PROD, filters = filters )
    data2,x2  = get_field_wells_snapshot_helper(2, crm_dataset,  x_column=WATER_PROD, y_column= OIL_PROD, filters = filters ) 
    data3,x3  = get_field_wells_snapshot_helper(3,crm_dataset,  x_column=WATER_PROD, y_column= LIQUID_PROD, filters = filters ) 
    xmax =max( x1,x2,x3 )
  
    line1 = {'legendgroup': 'y=x','x':[0,xmax], 'y':[0.0001,xmax],   'xaxis': 'x1','showlegend': True,'yaxis': 'y1','mode':'lines', 'line':{'width':1, 'color':'lightgrey', 'dash':'dashdot', 'color':'black'},'type':'scatter', 'name':'y=x'}
    line2 = {'legendgroup': 'y=x','showlegend':False,'x':[0,xmax], 'y':[0.0001,xmax],   'xaxis': 'x2','yaxis': 'y2','mode':'lines', 'line':{'width':1, 'color':'lightgrey', 'dash':'dashdot', 'color':'black'},'type':'scatter', 'name':'y=x'}
    line3 = {'legendgroup': 'y=x','showlegend':False, 'x':[0,xmax], 'y':[0.0001,xmax],   'xaxis': 'x3','yaxis': 'y3','mode':'lines', 'line':{'width':1, 'color':'lightgrey', 'dash':'dashdot', 'color':'black'},'type':'scatter', 'name':'y=x'}
    
    data1.append( line1 )
    data2.append( line2 )
    data3.append( line3 )
    data = data1 + data2 + data3
   

    oldlayout = {
        'height': 400, #'width':700,
        #'title': {'text':'Plotly Subplots with Shared X-axis'},
        #'xaxis': { 'title':{'text': 'Water production'},'domain': [0, 1]},
        #'xaxis1': { 'title':{'text': 'Water production'}},
        #'xaxis2': { 'title':{'text': 'Water production'}},
        
        'grid': {'rows': 1, 'columns': 3, 'pattern': 'independent'},
        'xaxis1': {'domain': [0, 0.28], 'title': {'text':'Water production'}},
        'yaxis1': { 'title':{'text': 'Gas production'}},
        
        'xaxis2': {'domain': [0.37, 0.65], 'title': {'text':'Water production'}},
        'yaxis2': { 'title':{'text': 'Oil production'}},

        'xaxis3': {'domain': [0.72, 1], 'title': 'Water production'},
        'yaxis3': { 'title':{'text': 'Liquid production'}},

        'legend': {
            'orientation': "v",
            'x': -0.05,   # Move legend to the left
            'y': 1,      # Align legend to the top
            'xanchor': "right", 
            'yanchor': "top"
        },
        'margin': {'l': 50},  #// Increase left margin to accommodate the legend
    }
    
    
    layout = {
            'height': 800, 
            'grid': {'rows': 3, 'columns': 1, 'pattern': 'independent'},
            'autosize': True,
            'automargin': True,
            #'margin': {'l': 50, 'r': 10, 't': 10, 'b': 10},
            'xaxis':  {'matches': 'x'},
            'xaxis2': {'matches': 'x'},
            'xaxis3': {'matches': 'x'},
            'xaxis4': {'matches': 'x'},
            
            'yaxis1': {'title':{'text': 'Gas production'}},
            'yaxis2': {'title':{'text': 'Oil production'}},
            'yaxis3': {'title':{'text': 'Liquid production'}},
            'xaxis1': {'title':{'text': 'Water production'}},
            'xaxis2': {'title':{'text': 'Water production'}},
            'xaxis3': {'title':{'text': 'Water production'}},
            'legend': {
            'orientation': "v",
            'x': 1.25,   # Move legend to the left
            'y': 1,      # Align legend to the top
            'xanchor': "right", 
            'yanchor': "top"
        },
            
            
            
        }
            
    
    return {'data':data ,'layout':layout, 'config':{'responsive':True },
            'raise_events': ['selected_well_name'] 
           }
     
        
    '''annotations: [
            {
                text: "Subtitle 1",
                x: 0.1, y: 1.15,  // Position above first subplot
                xref: "paper", yref: "paper",
                showarrow: false,
                font: {size: 14, color: "gray"}
            },
            {
                text: "Subtitle 1",
                x: 0.5, y: 1.15,  // Position above first subplot
                xref: "paper", yref: "paper",
                showarrow: false,
                font: {size: 14, color: "gray"}
            },
            {
                text: "Subtitle 1",
                x: 0.9, y: 1.15,  // Position above first subplot
                xref: "paper", yref: "paper",
                showarrow: false,
                font: {size: 14, color: "gray"}
            }]'''



## The next three functions are to support the little well-details-dialog. 
## They will not work unless the dataset is previously filtered to one and only one RMU 
def get_closest_neighbors(well_pairs, well_name, N=5):
    neighbors = []

    for pair in well_pairs:
        if pair['name1'] == well_name:
            neighbors.append({
                'name': pair['name2'],
                'type': pair['type2'],
                'distance': round( pair['distance'],1 ) 
            })

    # Sort by distance and return top N
    neighbors.sort(key=lambda x: x['distance'])
    return neighbors[:N]

def get_all_distances_flat(acrm_dataset, max_distance:float = 2500.00 ) -> list:
        

    df=  acrm_dataset.locations_df 
    # Build coordinate array and name list
    coords = df[['X', 'Y']].to_numpy()
    names = df['NAME'].to_numpy()

    # types map for quick search later
    well_type_dict = {} 
    for name in acrm_dataset.injector_names: 
        well_type_dict[name] = 'Injector'
    for name in acrm_dataset.producer_names:
        well_type_dict[name] = 'Producer'


    # Create KDTree, very fast unique pairs. 
    tree = cKDTree(coords)
    pairs = tree.query_pairs(r=max_distance, output_type='set')

    # Build bidirectional list
    well_pairs = []
    for i, j in pairs:
        for a, b in [(i, j), (j, i)]:
            name1, name2 = names[a], names[b]
            type1, type2 = well_type_dict[name1], well_type_dict[name2]
            distance = np.linalg.norm(coords[a] - coords[b])

            well_pairs.append({
                    'name1': name1,
                    'type1': type1,
                    'name2': name2,
                    'type2': type2,
                    'distance': distance
                })
        
        
    return well_pairs 
    
    '''
        Returns an array of these items: 
        [{
        "well_1": "AG4353",
        "type_1": "Producer",
        "well_2": "I32-001",
        "type_2": "Injector",
        "distance": 1000.0
        }, {} ] 
    ''' 
        
def get_everything_for_this_well( crm_dataset, well_name, max_neighbours_distance = 2000, max_neighbours = 10 ):
    """
    dict_keys(['neighbours', 'rates', 'well_name', 'type'])
    [{'name': 'Producer2', 'type': 'Producer', 'distance': 707.1},
    {'name': 'Inj3', 'type': 'Injector', 'distance': 1000.0},
    {'name': 'Inj2', 'type': 'Injector', 'distance': 1000.0},
    {'name': 'Inj0', 'type': 'Injector', 'distance': 1000.0},
    {'name': 'Inj1', 'type': 'Injector', 'distance': 1000.0},
    {'name': 'Producer3', 'type': 'Producer', 'distance': 1414.2}]
    """

    if well_name in crm_dataset.injector_names:
        W_COL = find_column(crm_dataset.injectors_df.columns, WATER_INJECTION_KEYS)
        N_COL = find_column(crm_dataset.injectors_df.columns, NAME_KEYS)
        w = crm_dataset.filter_by(N_COL, [well_name] + crm_dataset.producer_names )
        p = w.injectors_df
        well_type = 'Injector'
        dates = p.index.values.astype('datetime64[D]').astype( str ).tolist()  if p.index.name == 'DATE' \
            else p['DATE'].values.astype('datetime64[D]').astype( str ).tolist() 
            
        water = p[W_COL].fillna(0.0).values.tolist() 
        rates = { 'dates':dates, 'Injection': water } 
        
    else:
        O_COL,G_COL,W_COL = find_column(crm_dataset.producers_df.columns, OIL_PRODUCTION_KEYS), find_column(crm_dataset.producers_df.columns, GAS_PRODUCTION_KEYS), find_column(crm_dataset.producers_df.columns, WATER_PRODUCTION_KEYS)
        L_COL= find_column(crm_dataset.producers_df.columns, LIQUID_PRODUCTION_KEYS)
        N_COL = find_column(crm_dataset.injectors_df.columns, NAME_KEYS)
        well_type   = 'Producer'
        w = crm_dataset.filter_by(N_COL, [well_name] + crm_dataset.injector_names)
        p = w.producers_df.sort_values( by =['DATE'], ascending=True)
        
        dates = p.index.values.astype('datetime64[D]').astype( str ).tolist()  if p.index.name == 'DATE' \
            else p['DATE'].values.astype('datetime64[D]').astype( str ).tolist() 

        oil    = p[O_COL].fillna(0.0).values.tolist()
        water  = p[W_COL].fillna(0.0).values.tolist()
        gas    = p[G_COL].fillna(0.0).values.tolist()
        liquid = p[L_COL].fillna(0.0).values.tolist()
        
        rates = { 'dates':dates, 'Oil': oil, 'Gas': gas, 'Water': water, 'Liquid': liquid }
        
        
    well_types = {} 
    for iname in w.injector_names:
        well_types[iname] = 'Injector'
    for pname in w.producer_names:
        well_types[pname] = 'Producer'
            
 
    flat_all_pairs_distances = get_all_distances_flat(crm_dataset, max_neighbours_distance) 
    result = get_closest_neighbors(flat_all_pairs_distances, well_name, max_neighbours)
        
    data = {'neighbours': result, 'rates':rates,
            'well_name': well_name,
            'type': well_type 
            
            }  
    
    return data 
    
    