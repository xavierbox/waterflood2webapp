import numpy as np, pandas as pd, math, multiprocessing as mp
from datetime import date, datetime, timedelta
from joblib   import Parallel, delayed
from collections.abc import Iterable

from sklearn.metrics      import mean_squared_error,r2_score
from scipy.optimize       import minimize, Bounds
 
from   wf_lib2.crm_definitions   import * 
from   wf_lib2.models.crm_model  import CRMSingleModel, CRMModel
from   wf_lib2.crm_helper        import CRMHelper 
from   wf_lib2.data.crm_pattern  import CRMPattern
from   wf_lib2.data.crm_data_utils  import * 
from   wf_lib2.crm_definitions import *


def find_column_with_meaning( columns:Iterable, meaning:Iterable, search_sim_suffix = False  )->str:
        
    '''
    Takes a list of strings (columns of a dataframe, for instance) and search for the first column with a name
    that can be understood as having the meaning passed as argument, for instance, a meaning could be 
    WATER_PRODUCTION_KEYS or CUMMULATIVE_WATER_INJECTED_KEYS.

    When the last argument is true, it search for the names associated with a given meaning as well but the names 
    are appended the simulation suffix defined in the crm_definitions.py 
    As an example, the cummulative water injected should be searched as a simulation result since this is not 
    typically an input. The call would be:

    cum_water_injected   = find_column_with_meaning( rates.columns, CUMMULATIVE_WATER_INJECTED_KEYS, True )

    Meanings such as Liquid_Production can be an input/output  to/of the simulations. Depending on what is searched 
    for, one should add or not the preffix. 

    liquid_production     = find_column_with_meaning( rates.columns, LIQUID_PRODUCTION_KEYS, False )
    liquid_production_sim = find_column_with_meaning( rates.columns, LIQUID_PRODUCTION_KEYS, True )

    >>'LIQUID_PRODUCTION',
    >>'LIQUID_PRODUCTION_sim'
    '''
    
    
    if search_sim_suffix == True:
        sim_meaning =[ (m + SIM_SUFFIX).lower() for m in meaning]
        for col in columns:
            if col.lower() in sim_meaning: return col
         
        return None 

    meaning =[ m.lower() for m in meaning]
    for col in columns:
        if col.lower() in meaning: return col

    return None 
  

class KovalSingle(CRMSingleModel):

    def __init__(self):
        super().__init__('Koval')
        self._clear()
     
        self.vp_scale = 1.00e5
        self.wo_scale = 1.0e4
           
    def get_default_params(self):     
        '''
        The function returns the default parameters used by the model.
        
        The function is called internally and the model parameters overwrite these defaults when 
        the client code (user) provides some or all of them. 
        
        As with every process in the CRM lib the update happens in the fit_preprocess method.
        
        Returns:  Default parameters for the solver
        
        '''
        args = {
            'dates': ['1950-09-23','2200-01-28'],
            'parameters': {
                'vp':  {'bounds': (1e5,25e6), 'init_value': 1.1e5},
                'kval':{'bounds':(1.05,37.0), 'init_value': 5.10},
                'water_zero_threshold': 0.05,
                'wo'  : {'bounds':(0.0,0.5e4), 'init_value': 0.0},
                'fo'  : {'bounds':(0.0,0.5), 'init_value': 0.0}
                   
            },
            'dt': 1.0,
            'max_running_time': 1000.0,
            'optimizer': {'maxiter': 2000,'name': 'Nelder-Mead', 'tolerance': 1e-03},
            'pre_optimizer': {'name': 'TNC'} 
        }
        return args 
       
    def process_args( self, input_args = None ):
        
        '''
        Parses the arguments for the simulation passed as parameters. These arguments overwrite any 
        default parameters of the model
        
        Returns: simulation parameters combining default ones and the ones passed as arguments 
        '''
        def extract_date( s ):
            if s is None: return None 
        
            chars = ['-','/','\\',',']
            for char in chars: 
                if char in s: 
                    y,m,d= s.split(char)
                    return date( int(y),int(m),int(d))
            return None 
        
        
        
        args =self.get_default_params()
        if input_args is None: input_args = {} 
        
        #the optimizer 
        #_optimizers_name_map = CRMModel()._optimizers_name_map
        
        if 'optimizer' in input_args:args['optimizer'].update( input_args['optimizer'] )
        args['optimizer']['name']=optimizers_name_map[ args['optimizer']['name'].lower() ]   
        
        if 'pre_optimizer' in input_args:args['pre_optimizer'].update( input_args['pre_optimizer'] )
        args['pre_optimizer']['name']=optimizers_name_map[ args['pre_optimizer']['name'].lower() ] 
        
        
        #dates 
        if 'dates' in input_args:
            args['tdates'] = input_args['dates']
            date1, date2 = extract_date(args['tdates'][0]), extract_date(args['tdates'][1])
            if (date1 is None) and (date2 is None): args.pop( 'tdates' )
            else:
                if (date1 is not None) and (date2 is not None): date1, date2 = sorted( [ date1, date2] ) 
                elif date1 is None: date1 = date.min
                elif date2 is None: date2 = date.max
             
                
                date1,date2 = sorted([date1,date2])
                args['tdates'] = [ date1, date2 ]
        
        
        #parameters vp, kval  
        if 'parameters' in input_args:
            
            
            if 'vp'  in input_args['parameters']: args['parameters']['vp']    = input_args['parameters']['vp']
            if 'kval' in input_args['parameters']: args['parameters']['kval'] = input_args['parameters']['kval']
            if 'water_zero_threshold' in input_args['parameters']: 
                args['parameters']['water_zero_threshold'] = 1.0*input_args['parameters']['water_zero_threshold']
            if 'wo' in input_args['parameters']: 
                args['parameters']['wo'] = input_args['parameters']['wo']
            if 'fo' in input_args['parameters']: 
                args['parameters']['fo'] = input_args['parameters']['fo']
                
            
                
                
        args['water_zero_threshold'] = args['parameters']['water_zero_threshold']
        
        
        return args 
        
    def _validate_input_data( self, df ):


        DATE = DATE_KEYS[0].upper()
        if not isinstance(df, pd.DataFrame):
            error = "Error processing rates_df. It must be a dataframe"
            raise ValueError(error)
            
        #we need a date, either it is an index or a column       
        if df.index.name is not None and DATE in df.index.name.upper(): 
            #ok, the index are dates
            pass 
        else:
            if find_column_with_meaning( df.columns, DATE_KEYS) is None: 
                error = 'The dataframe must provide a date either as index or as a column.'
                raise ValueError( error )
            
            
        #we need cumm_water_injected, liquid_produced, water_producer
        cols = df.columns
        if find_column_with_meaning( cols, CUMMULATIVE_WATER_INJECTED_KEYS, True) is None:
            raise ValueError( "Cummulated water injected not found" )
        
        if find_column_with_meaning( cols, WATER_PRODUCTION_KEYS) is None:
            raise ValueError( "Water production data not found" )
            
        
        if find_column_with_meaning( cols, LIQUID_PRODUCTION_KEYS, False) is None:
            raise ValueError( "Liquid production hard data not found" )

                
        #if check_if_time_gaps(df) == True: 
        #    error = 'There is an error in the dataset. There are missing dates or repeated ones.'
        #    print(error)
        #    #raise ValueError(error)  
            
                               
    def fit_preprocess(self, rates_df, input_args=None ):
        #the model requires cumm_water_injected, liquid_produced, water_produced, dates and optionally 
        #a name column for the producer. If not given, the "default name" wil be used
        #the dates may be an index column or a standard column 
             
        self._clear()
        self._validate_input_data( rates_df )
            
        args = self.process_args( input_args )
        self._init_state( args )
            
        cols  =  rates_df.columns
        cumm_water_col        = find_column_with_meaning( cols, CUMMULATIVE_WATER_INJECTED_KEYS,True)
        if cumm_water_col is None:
            cumm_water_col = find_column_with_meaning( cols, CUMMULATIVE_WATER_INJECTED_KEYS,False)
        
        water_produced_col    = find_column_with_meaning( cols, WATER_PRODUCTION_KEYS)
        #liquid_produced_col   = find_column_with_meaning( cols, LIQUID_PRODUCTION_KEYS,True)
        liquid_produced_data_col   = find_column_with_meaning( cols, LIQUID_PRODUCTION_KEYS,False)
        
       
        #producer name 
        name_col = find_column_with_meaning( cols, NAME_KEYS)
        if name_col is None: 
            self.producer_name = 'Default' 
        else: 
            self.producer_name = rates_df[name_col].unique()[0]
        
        
        #dates 
        dates = None 
        date_col = find_column_with_meaning( cols, DATE_KEYS)
        if date_col is not None: dates = rates_df[ date_col ].values 
        else: dates =  rates_df.index.values
            
        #rates as numpy arrays 
        cum_water, water_produced = rates_df[ cumm_water_col ], rates_df[ water_produced_col ]
        #liquid_produced = rates_df[ liquid_produced_col ]
        
        data_liquid_produced = rates_df[ liquid_produced_data_col ]

        
        #the 10.0 below is to avoid dividing by zero. 
        water_fraction = water_produced / (10.0 + data_liquid_produced )

        self._state['producer_names'] = [self.producer_name ]
        self._state[ DATE_KEYS[0] ] = dates 
        self._state[ WATER_PRODUCTION_KEYS[0]] = water_produced.values
        self._state[ WATER_PRODUCTION_FRACTION_KEYS[0] ] = water_fraction.values
        self._state[ CUMMULATIVE_WATER_INJECTED_KEYS[0] ] = cum_water.values
 
        
        
        
        optional = find_column_with_meaning( cols, LIQUID_PRODUCTION_KEYS,True) 
        if optional is not None:
            self._state[ LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX ] = rates_df[optional].values 
        
        self._state[ LIQUID_PRODUCTION_KEYS[0]   ] = data_liquid_produced.values  
        self._state['producer_names'] = self.producer_name
        
        
        #one last check, check that we actually have some water production above the zero threshold
        inj_cum, fw = self._state[CUMMULATIVE_WATER_INJECTED_KEYS[0]], self._state[WATER_PRODUCTION_FRACTION_KEYS[0]]
        threshold = self._state['water_zero_threshold']
        mask = (fw >= threshold) & (fw < 1 - threshold )
        view_inj_cum = inj_cum[mask]
         
        
        if view_inj_cum.size < 5:
            print('Not enough data of water production to train the model. ', self.producer_name)
            error = 'Not enough data of water production to train the model. P:'+self.producer_name
            self._clear()
            raise ValueError( error )
        
        
        self._data = rates_df
        return self 

    def _update_from_optimization(self, result):

            state = self._state 
            self.optimization_result = {}

            self.optimization_result['message'] = result['message']
            self.optimization_result['nitr']     = result['nit']
            self.optimization_result['success']  = result['success']
            self.optimization_result['rmse']     = state['rmse']
            self.optimization_result['elapsed_time']  = state['elapsed_time']  
            self.optimization_result['start_time']    = state['start_time']  
            self.optimization_result['producer_names'] = self._state['producer_names']
        
        
            #self.optimization_result['R2']       = state['R2']
            self.optimization_result['vp']       = state['vp']
            self.optimization_result['kval']       = state['kval']
            self.optimization_result['wo']       = state['wo']
                   
    def quick_fit(self,verbose=False):
        return self._fit( False )
        
    def _koval_fwOLD( self,cum_inj, vp, kval, wo    ):
 
        
        td = (1.0 + cum_inj +wo )/ vp 
 
        if kval < 1.01: kval  = 1.01
  
        fw = wo + (kval - (kval/td)**0.5 )/(kval-1.0)  
        mask0, mask1 = td < 1.0/kval, td > kval 
        fw[mask0]=0
        fw[mask1]=1
        return fw 
            
    def _koval_fw( self,cum_inj, vp, kval, wo, fo = 0.0    ):
 

        cum2 = cum_inj.copy()
        cum2 = cum_inj - wo #[ cum_inj < wo ] = 0.0 
        cum2[ cum2 < 0] = 1.0


        td = (1.0 + cum2 )/ vp 
 
        if kval < 1.01: kval  = 1.01


  
        fw = fo + (kval - (kval/td)**0.5 )/(kval-1.0)  
        
        fw[fw < fo ] = fo 
        #mask0, mask1 = td < 1.0/kval, td > kval 
        #fw[mask0] = 0
        #fw[mask1] = 1

        #mask3 = cum_inj < wo 
        #fw[mask3] = fo 
        #fw[~mask3] = fo + fw 
        fw[ fw>1 ]  = 1 

        
        

        return fw 
    
               
    def _loss(self, params, *args):
        
        vp, kval,wo, fo  = params[0]*self.vp_scale,   params[1],    params[2]*self.wo_scale,   params[3]
        #print('loss wo',wo, fo)

        #vp, kval= params[0]*self.vp_scale, params[1]
        state = args[0]
        
        inj_cum, fw = state[CUMMULATIVE_WATER_INJECTED_KEYS[0]], state[WATER_PRODUCTION_FRACTION_KEYS[0]]

        #are we training?
        training = state.get('training',False)
        if training and 'tdates' in state:
            dates = state[ DATE_KEYS[0] ]
            tdate1, tdate2 = np.datetime64( state['tdates'][0]),np.datetime64( state['tdates'][1])
            mask = (dates >= tdate1) & (dates <= tdate2)
            inj_cum, fw = state[CUMMULATIVE_WATER_INJECTED_KEYS[0]][mask], state[WATER_PRODUCTION_FRACTION_KEYS[0]][mask]
                

        threshold = self._state['water_zero_threshold']
        mask = (fw >= threshold) & (fw < 1.0 - threshold )
        
        view_inj_cum = inj_cum[mask]
        predicted_fw = self._koval_fw( view_inj_cum , vp, kval, wo,fo  ).flatten()
        error = mean_squared_error( fw[ mask ] , predicted_fw, squared = False )
        state['rmse'] = error 
        state['r2'] = r2_score(fw[ mask ] , predicted_fw) 
        
        return error 
                                                 
    def _pseudo_grid_search(self, params, bounds, options ):
        
        #brute force first 
        vp_range  = np.arange( bounds[0][0], bounds[0][1], (bounds[0][1]-bounds[0][0])/5 )
        k_range   = np.arange( bounds[1][0], bounds[1][1], (bounds[1][1]-bounds[1][0])/5 )
        wo_range  = np.arange( bounds[2][0], bounds[2][1], (bounds[2][1]-bounds[2][0])/5 )
        fo_range  = np.arange( bounds[3][0], bounds[3][1], (bounds[3][1]-bounds[3][0])/5 )

     

        best_pair = (vp_range[0], k_range[0], wo_range[0], fo_range[0])
        smallest_error = 1.0e12 
        for vp in vp_range:
            for kval in k_range:
                for w in wo_range:
                    for ff in fo_range:
                        error = self._loss( [vp,kval,w, ff], self._state )
                        if error < smallest_error:
                            smallest_error = error
                            best_pair = ( vp, kval, w, ff )                   
# 
        params[0] = best_pair[0]
        params[1] = best_pair[1] 
        params[2] = best_pair[2] 
        params[3] = best_pair[3] 
 
        result = minimize(fun = self._loss, x0 = params, 
                          method= self._state['pre_optimizer']['name'],          
                          bounds = bounds ,
                          args=self._state , 
                          options = options, 
                          tol=self._state['optimizer']['tolerance'])

 
        return result.x
                   
    def _update_from_optimization(self, result):

            state = self._state 
            self.optimization_result = {}

            self.optimization_result['message'] = result['message']
            self.optimization_result['nitr']     = result['nit']
            self.optimization_result['success']  = result['success']
            self.optimization_result['rmse']     = state['rmse']
            self.optimization_result['r2']     = state['r2']
            
            self.optimization_result['elapsed_time']  = state['elapsed_time']  
            self.optimization_result['start_time']    = state['start_time']  
            self.optimization_result['producer_names'] = self._state['producer_names']
        
        
      
            self.optimization_result['vp']         = state['vp']
            self.optimization_result['kval']       = state['kval']
            self.optimization_result['wo']         = state['wo']
            self.optimization_result['fo']         = state['fo']
            
             
    def fit(self, verbose=False):
        
        #optimization parameters 
        parameters = self._state['parameters']
       
        init_values = [parameters['vp']['init_value'],parameters['kval']['init_value'], parameters['wo']['init_value'],parameters['fo']['init_value']]        
        bounds = [parameters['vp']['bounds'],parameters['kval']['bounds'],parameters['wo']['bounds'],parameters['fo']['bounds']]
        
        #wo and vp are many orders of magnitude above kval. These are rescaled here to a range around 1 
        bounds[0] = (bounds[0][0] /self.vp_scale,bounds[0][1] /self.vp_scale ) 
        bounds[2] = (bounds[2][0] /self.wo_scale,bounds[2][1] /self.wo_scale ) 
        init_values[0] = init_values[0]/self.vp_scale
        init_values[2] = init_values[2]/self.wo_scale
        
        maxiter = self._state['optimizer']['maxiter']
        options = {'maxfun': maxiter, 'disp':verbose}
        
        
        self._state['training'] = True 
        init_values = self._pseudo_grid_search(init_values, bounds, options )

        optimizer = self._state['optimizer']
        options = {'maxiter': maxiter,'disp':verbose}
        
        result = minimize( fun       = self._loss, 
                           x0        = init_values, 
                           method    = optimizer['name'],         
                           bounds    = bounds,
                           args      = self._state , 
                           options = options, 
                           tol       = optimizer['tolerance'])
        
        
        self._state.pop('training')
        
        vp, kval, wo,fo = result.x[0]*self.vp_scale, result.x[1], result.x[2]*self.wo_scale, result.x[3]
  
        state = self._state 
        state[ 'vp'  ] = vp
        state[ 'kval'] = kval 
        state[ 'wo'  ] = wo 
        state[ 'fo'  ] = fo

        self._update_from_optimization(result)
        return  self.optimization_result       
    

    def forecast( self, water_injection_table ):

        self.forecast_result  = None 
        cum_inj = water_injection_table[CUMMULATIVE_WATER_INJECTED_KEYS[0]+SIM_SUFFIX] 

        state = self._state
        vp,kval,wo = state['vp'],state['kval'],state['wo']
        fw = self._koval_fw( cum_inj, vp, kval, wo )

        dates = water_injection_table.index.values.flatten()#[ DATE_KEYS[0] ]
    
        d = pd.DataFrame(
            {
                DATE_KEYS[0]: dates,
                WATER_PRODUCTION_FRACTION_KEYS[0] + SIM_SUFFIX: fw,
                CUMMULATIVE_WATER_INJECTED_KEYS[0] + SIM_SUFFIX : cum_inj
            })
        
        d[ NAME_KEYS[0] ] = self._state['producer_names']
        d['ID'] = np.arange(0,d.shape[0],1)
        d.set_index(DATE_KEYS[0], inplace=True, drop=True)

        self.forecast_result = d

        return  self.forecast_result #d.copy()


    def predict( self ):
    
        cum_inj = self._state[CUMMULATIVE_WATER_INJECTED_KEYS[0]] 
        water_produced_data = self._state[ WATER_PRODUCTION_FRACTION_KEYS[0] ]
        dates = self._state[ DATE_KEYS[0] ]
        
        vp,kval, wo, fo  = self._state['vp'], self._state['kval'], self._state['wo'] ,self._state['fo']  
        water_produced_sim  = self._koval_fw( cum_inj, vp, kval, wo, fo )
        

        d = pd.DataFrame(
            {
                DATE_KEYS[0]: dates,
                WATER_PRODUCTION_FRACTION_KEYS[0]: water_produced_data,
                WATER_PRODUCTION_FRACTION_KEYS[0] + SIM_SUFFIX: water_produced_sim,
                
                WATER_PRODUCTION_KEYS[0]: self._state[ WATER_PRODUCTION_KEYS[0]],
                CUMMULATIVE_WATER_INJECTED_KEYS[0] + SIM_SUFFIX : self._state[CUMMULATIVE_WATER_INJECTED_KEYS[0]],
                #LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX  : self._state[ LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX ],
                LIQUID_PRODUCTION_KEYS[0]    : self._state[ LIQUID_PRODUCTION_KEYS[0]   ]  
            })
        d[ NAME_KEYS[0] ] = self._state['producer_names']
        
       
        state = self._state    
        if 'tdates' in state:
            dates = state[ DATE_KEYS[0] ]
            tdate1, tdate2 = np.datetime64( state['tdates'][0]),np.datetime64( state['tdates'][1])
            mask = (dates >= tdate1) & (dates <= tdate2)
            d['TRAIN'] = mask 
    
        
        if LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX in self._state:
            d[ LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX ] = self._state[ LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX ] 
        
        
                
        d.set_index( DATE_KEYS[0], inplace=True, drop = True )
        

        self.prediction_result = {}
        self.prediction_result['rates'] = d
        
        
         
 
        crm = {'vp': [state['vp']], 
               'kval': [state['kval']],
               'wo': [state['wo']],
               'fo':[state['fo']],
               NAME_KEYS[0]:[state['producer_names']], 
               'r2':[state['r2']], 
               'rmse':[state['rmse']]
              }

        self.prediction_result['crm'] = pd.DataFrame( crm )
        self.prediction_result['optimization'] = self.optimization_result 
        
        
        return self.prediction_result 
 

class Koval(CRMModel): 
    
    def __init__(self):
        super().__init__('Koval')
        self._clear()
         
        
    def _validate_input_data( self, rates_df ):
        
        name_column = find_column_with_meaning(rates_df.columns, NAME_KEYS)
        producer_names = rates_df[ name_column ].unique()
        
        for name in producer_names:
            df = rates_df[ rates_df[name_column] == name ]
            KovalSingle()._validate_input_data( df )
                 
    def fit_preprocess(self, rates_df, input_args=None, verbose=False):
        
        self._validate_input_data( rates_df )
        rates_df.fillna(0.0, inplace=True) 
        self._data = rates_df 
        
        num_producers = len( rates_df[ find_column_with_meaning(rates_df.columns, NAME_KEYS) ].unique() )
        
        
        args = None 
        if input_args is None: args =  num_producers* [self.get_default_params() ] 
        else:
            if not isinstance( input_args, list ):args = num_producers * [ input_args ]
            else: args = input_args
            if len(args) > num_producers: args = args[0:num_producers]
            elif len(args) < num_producers: args = args.copy() + (num_producers - len(args)) * [ self.get_default_params() ] 
                           
        self.args = args 

        return self
    
    def fit( self ):
        return self.fit_predict()['optimization']
    
    def predict( self ):
        
        if self.optimization_result is None:
            print('Preditions arent possible. Need to pre-process and fit the model first')
            return {}
        
        return self.prediction_result
      
    def fit_predict(self):
        
        self.optimization_result = None 
        self.prediction_result   = None 
        self.forecast_result     = None 
        self.log.append('starting fitting and prediction')

        rates_df = self._data 
        name_column = find_column_with_meaning(rates_df.columns, NAME_KEYS)
        producer_names = rates_df[ name_column ].unique()
        
        results = [] 
        predictions = [] 
        
        for i,name in enumerate( producer_names ):
            
 
            try:
                result = {}
                model_args = self.args[ i ]
                single_rate = rates_df[ rates_df[name_column] ==name ]
                
                model = KovalSingle()
                result = model.fit_preprocess( single_rate, model_args ).fit()
                
                if i== 0:
                    self.saved = (model,single_rate, model_args)
                ################
                #return (model,single_rate, model_args)

                
                
                result['id'] = i 
                results.append( result )
                
                prediction = model.predict()
                prediction['rates']['id'] = i 
                prediction['crm']['id'] = i 
                prediction['optimization']['id'] = i 
                predictions.append( prediction )

                self.models.append( model )
                self.log.append( f'--Done fitting for producer {name} [{i+1}] out of {len(producer_names)}' )
                
            except Exception as e:
                print( str(e) )
                self.log.append(f'Error while fittng the model {name}: {str(e)}')


        rates = [prediction['rates'] for prediction in predictions ]
        crm   = [prediction['crm'] for prediction in predictions ]
        optimization = [prediction['optimization'] for prediction in predictions ]

        crm = pd.concat(crm, axis= 0 ) 
        crm.reset_index( inplace = True, drop = True  )
        rates = pd.concat(rates, axis= 0 ) 

        d = {}
        d['optimization'] = optimization
        d['rates'] = rates 
        d['crm'] = crm 
        
        self.optimization_result = optimization
        self.prediction_result = d 
        return self.prediction_result
    
    def _get_submodel( self ):
        return KovalSingle() 
    
    
    def forecast( self, rates_df ):


        self.forecast_result = None   
        forecasts = [] 
        self.log.append( 'Koval forecasting started' )
        
        for n,model in enumerate( self.models ):

            try:
                opt = model.optimization_result
                producer_name = opt['producer_names']
                vp,kval,wo = opt['vp'],opt['kval'],opt['wo']
                #print( vp,kval,wo )
                
                #get the relevant data in the new passed rates.
                data = rates_df[ rates_df['NAME'] == producer_name ]
            
                fw = model.forecast( data )
                forecasts.append( fw )
                self.log.append( f'--Done forecast for producer {producer_name} [{n+1}] out of {len(self.models)}' )

                

            except Exception as e:
                s = f'Error in forecast model {n}: {str(e)}'
                self.log.append( s )


        
        self.forecast_result = pd.concat( forecasts, axis = 0 )
            
        return self.forecast_result      
        
 
def generate_analytical_koval( args ):
    
    def koval_water_fraction_analytical( cumm_water_injected, vp, kval ):
        '''
        Analytical calculation of kval fractiona water.
        The function takes the cummulated wated injected, the pore volume and the kval constant.

        Note that the former (cummulated wated injected) needs to be computed somewhere and passed 
        here as a numpy array or a pandas series. It will depend on the injection rate of the 
        contributing wells, their allocation factor, etc.  

        Note kval needs to be strictly greater than one

        Returns: a sequence of the fractional water values for a given cummulative injection, pore 
        volume (vp) and kval constant.
        '''

        td = cumm_water_injected / vp            #adim time 
        fw = (kval - (kval/td)**0.5 )/(kval-1.0) #water fraction [0,1]
        mask0, mask1 = td < 1.0/kval, td > kval  
        fw[mask0]=0
        fw[mask1]=1

        return fw

    dates, internal_length, min_rate, max_rate = CRMHelper.get_day_range(args['days']),args['internal_length'],args['min_rate'],args['max_rate']
    days = len(dates)
   
    I = CRMHelper.generate_sample_injector_rates(days, internal_length,min_rate, max_rate )    
    DATE, CUMM_RATE = DATE_KEYS[0], CUMMULATIVE_WATER_INJECTED_KEYS[0]
    inj_df = pd.DataFrame( { DATE:dates, WATER_INJECTION_KEYS[0]: I.flatten() 
                           } )
    
    inj_df.reset_index( inplace=True, drop = True  )
    inj_df[ CUMM_RATE ] = inj_df[WATER_INJECTION_KEYS[0]].cumsum( axis = 0 )

    dates = CRMHelper.get_dates( inj_df.shape[0] )
    inj_df[DATE_KEYS[0]] = dates 
    inj_df.set_index( DATE_KEYS[0], inplace=True )

    vp   = args['vp']
    kval = args['kval']
    fw = koval_water_fraction_analytical(  inj_df[ CUMM_RATE ].values, vp, kval )
    inj_df[ WATER_PRODUCTION_FRACTION_KEYS[0] ] = fw 
    
    inj_df['NAME'] = 'Producer1'
    
    return inj_df


def koval_water_fraction_analytical( cumm_water_injected, vp, kval ):
    '''
    Analytical calculation of kval fractiona water.
    The function takes the cummulated wated injected, the pore volume and the kval constant.
    
    Note that the former (cummulated wated injected) needs to be computed somewhere and passed 
    here as a numpy array or a pandas series. It will depend on the injection rate of the 
    contributing wells, their allocation factor, etc.  

    Note kval needs to be strictly greater than one
    
    Returns: a sequence of the fractional water values for a given cummulative injection, pore 
    volume (vp) and kval constant.
    '''
    
    td = cumm_water_injected / vp            #adim time 
    fw = (kval - (kval/td)**0.5 )/(kval-1.0) #water fraction [0,1]
    mask0, mask1 = td < 1.0/kval, td > kval  
    fw[mask0]=0
    fw[mask1]=1

    return fw 
## analytical koval example
#args = {
#    'vp':  1.1e5,
#    'kval': 1.5,
#    'days': 800, 'internal_length': 10, 'min_rate': 0.1e3, 'max_rate': 0.5e3, 'allocation': 0.6 
#}
#df = generate_analytical_koval(args)
#df.rename( {'CUM_WATER_INJECTED':'CUM_WATER_INJECTED_sim'}, inplace=True, axis = 1 )
#df['LIQUID_PRODUCTION'] = 0.6*df['WATER_INJECTION']# * df['WATER_FRACTION']
#df['WATER_PRODUCTION']  = df['LIQUID_PRODUCTION'] * df['WATER_FRACTION']
#display(df.head(15))
#f,ax = plt.subplots( nrows=3, ncols=1, figsize=(20,5))
#sns.lineplot( data = df[['WATER_FRACTION']], ax = ax[0])
#sns.lineplot( data = df[['CUM_WATER_INJECTED_sim']], ax=ax[1])
#sns.lineplot( data = df[['WATER_PRODUCTION']], ax=ax[2])
#plt.show()


        
        


     
    
    
