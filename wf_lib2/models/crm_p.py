from joblib import Parallel, delayed
from datetime import date, datetime, timedelta
import numpy as np, pandas as pd,multiprocessing as mp, pprint, pickle, json 
 
from sklearn.metrics import mean_squared_error,r2_score, root_mean_squared_error
from sklearn.linear_model import Ridge, LinearRegression
from scipy.optimize import minimize, Bounds,LinearConstraint

from   wf_lib2.crm_definitions import * 
from   wf_lib2.models.crm_model import CRMSingleModel, CRMModel#, integrated_error
from   wf_lib2.crm_helper      import CRMHelper 
from   wf_lib2.data.crm_pattern     import CRMPattern
from   wf_lib2.data.crm_data_utils  import * 

##test

class CRMPSingle( CRMSingleModel ):
    '''
    CRMP solver for single-producer patterns. This class shouldnt be instantiated in the general case.
    The CRMP class defined below should be used instead. The CRMPSingle exists only as support for the 
    CRMP class which accounts for multi-producer and multi-pattern scenarios. 
    '''
    
    ###########################################
    ###              public API         #######  
    ###  implements the CRMModel interface  ###
    ###########################################

    def __init__(self ):
        super().__init__('CRMPSingle')
        self._clear()
        
    def get_default_params(self): 
        
        '''
        Returns the default parameters to be used during optimization,
        All or some of these can be replaced all by the input_args passed to the 
        fit_preprocess method.
        
        Returns:
            
            args (dict): Dictionary with default parameters for the CRM-P model 
        
        Example of use 1:
        
            args_dict = CRMP().get_default_params()
            print(args_dict)
            
            >>{'parameters': {'tau':   {'bounds':(1,50), 'init_value': 5.0} ,
            >>                'taup':  {'bounds':(1,50), 'init_value': 5.0}
            >>               },
            >> 'dt': 1.0,
            >> 'max_running_time': 1000.0,
            >> 'optimizer': {'maxiter': 1000,'name': 'Nelder-Mead', 'tolerance': 1e-03},
            >> 'pre_optimizer': {'name': 'TNC'} 
            >>}
            
        Example of use 2 (change tau limits and pre-optimizer before running model):
        
            args_dict = CRMP().get_default_params()
            args_dict['parameters']['tau']['bounds'] = (20,25)
            args_dict['pre_optimizer']['name'] = 'powell'
       
            model = CRMP()
            optimization_result = model.pre_process( data, args_dict ).fit() 
            predictions = model.predict()

             (etc...)            
        '''
        
        args = {
            'dates': ['1950-09-23','2200-01-28'],
            'parameters': {
                'tau':   {'bounds': (0.1,50), 'init_value': 5.0} ,
                'taup':  {'bounds':(0.1,50), 'init_value': 5.0}
            },


            'dt': 1.0,
            'max_running_time': 1000.0,
            'optimizer': {'maxiter': 1000,'name': 'Nelder-Mead', 'tolerance': 1e-03},
            'pre_optimizer': {'name': 'Powell'},
            #'primary': True 
        }
        return args 
  
    def fit_preprocess_pattern(self, pattern, args):
        
        #args = {dates:['date1', 'date2']}
           
        #Checks that we have time series, dataframes and no time gaps. Raises a ValueError
        self._validate_input_pattern( pattern )  

        # Raises an exception is something wrong happens. 
        # Adjust training time-frame.
        # Modifies the input pattern to slice dates [date1, date3]
        # removes inactive wells
        # Training dates are [date1,date2], testing dates are [date1, date3 ]
        tdate1, tdate2, tdate3 = self.adjust_training_testing_dates( pattern, args )



        #note that prod pressure will be None most of the time (no bhp)
        dates = pd.to_datetime(pattern.water_injection.index).values 
        mask = dates >= tdate1
        inj, prod  = pattern.water_injection[mask], pattern.liquid_production[mask]
        qo,qo_date = prod.values[ 0 ], prod.index.values[ 0 ] 

        return pattern, tdate1, tdate2, tdate3, inj, prod, qo,qo_date 
    
    
    def fit_preprocess( self, pattern,input_args=None, verbose=False):
        ''' 
        This is the first function to be called before any simulation.
        Here, the input pattern is sliced in time according to the best 
        compromise between the available data and the user params for 
        dates. 

        The pattern once processed is stored and the model state 
        is saved. Such state contains a matrix representation of all the 
        data as it is used in the fitting and predicting processes later.

        Note that the state saves tdate1---tdate3. The first 2 are the 
        training timeframes whereas t1-t3 are the testing
        ''' 


        self._clear()

        names = ",".join (['I:']+list(pattern.injector_names) + ['P:']+list(pattern.producer_names) )
        self.log.append(  f'[fit_preprocess] for {names}' )

        args = self._process_args( input_args )

        #returns the same pattern object received (same memory id) but modified 
        #from args, it only uses {dates:['date1', 'date2']}
        #the resulting pattern is stored internally as _data 
        #pattern, tdate1, tdate2, tdate3, inj, prod, qo,qo_date = self.fit_preprocess_pattern( pattern, args )
        
        self._validate_input_pattern( pattern )  

        # Raises an exception is something wrong happens. 
        # Adjust training time-frame.
        # Modifies the input pattern to slice dates [date1, date3]
        # removes inactive wells
        # Training dates are [date1,date2], testing dates are [date1, date3 ]
        tdate1, tdate2, tdate3 = self.adjust_training_testing_dates( pattern, args )


        #note that prod pressure will be None most of the time (no bhp)
        dates = pd.to_datetime(pattern.water_injection.index).values 
        mask = dates >= tdate1
        inj, prod  = pattern.water_injection[mask], pattern.liquid_production[mask]
        qo,qo_date = prod.values[ 0 ], prod.index.values[ 0 ] 
        
        #if args['primary'] is False:
        #    qo = 0.0 
        
    

        self.log.append(  f'[fit_preprocess] updating internal state' )
        args['crm_model'] = self._name 
        args['tdate1']  = str(tdate1)
        args['tdate2']  = str(tdate2)
        args['tdate3']  = str(tdate3)  
        args['qo'], args['qo_date'] = qo, str((qo_date))[0:10] 
        args['injector_names'] = list(inj.columns)
        args['producer_names'] = list(prod.columns)

        self.producer_name = list(prod.columns)[0]
        self.injector_names = list(inj.columns)
            
        self._init_state( args )
        self._data = pattern 
        self.log.append(  '[fit_preprocess]  finished' )

        return self
 
    def _fit(self, quick = False, verbose=False):

        self.optimization_result = {} 
        data = self._data
        
        print( self._data )
        
        if data is None:
            raise ValueError('[fit] Cannot fit the data because fit_preprocess failed or was never called')
        
         

        tdate1, tdate2 = np.datetime64( self._state['tdate1']),np.datetime64( self._state['tdate2'])
        dates = pd.to_datetime(data.water_injection.index).values 
        
        mask = (dates >= tdate1) & (dates <= tdate2)
        inj, prod  = data.water_injection[mask], data.liquid_production[mask]
        prod_press = data.producer_pressure[mask] if data.producer_pressure is not None else None 
        invI, invP, invDP, invDates = self._get_matrices(  inj, prod, prod_press )    

        if invP.shape[0] < 1:
            error = "[fit] Error when assembling matrices. Production data is missing. Producer {self.producer_name}"
            raise ValueError( error )
                
        if invI.shape[0] < 1:
            error = "[fit] Error when assembling matrices. Production data is there but injection data is missing. Producer {self.producer_name}"
            raise ValueError( error )
        
        #this concatenation is only used in CRM-P. For CRMIP is not convenient 
        invI = np.concatenate( (invI,                               #gain injectors                                  
                                np.zeros( shape=(invI.shape[0],1)), #dp
                                np.zeros( shape=(invI.shape[0],1))),#qo  
                                axis=1) 
        
        self._state['bhp'] = self.has_bhp
        self._state['invI']= invI
        self._state['invP']=invP
        self._state['invDP']=invDP
        self._state['invDates']=invDates

        
        #optimization parameters 
        parameters = self._state['parameters']
        bounds = [parameters['tau']['bounds'],parameters['taup']['bounds'] ]
        init_tau, init_taup = parameters['tau']['init_value'], parameters['taup']['init_value']  
        
        #options 
        #num_injectors = self._state['invI'].shape[1]
        options = {'maxiter':max(self._state['optimizer']['maxiter'], 10*invI.shape[1]), 'disp':verbose}
        
        #initial conditions 
        params = [ init_tau, init_taup]
        result, lambdas, init_tau, init_taup  = self._pseudo_grid_search( params, bounds, options )
        self._update_from_optimization( )#result ) 


        #if only a quick-fit is done return what we have now.
        if quick: 
            if verbose: print('Pre-optimization finished. Results',init_tau,  init_taup )
            return self.optimization_result  
        
        #further optimize starting where the prev was left
        options = {'maxiter':max(self._state['optimizer']['maxiter'], 10*invI.shape[1]), 'disp':verbose}
        params = np.array( [init_tau,init_taup] )
        
  
        
        optimizer = self._state['optimizer']
        result = minimize( fun       = self._loss, 
                           x0        = params, 
                           method    = optimizer['name'],         
                           callback  = self._keep_working,
                           bounds    = bounds,
                           args      = self._state , 
                           options   = options,  
                           tol       = optimizer['tolerance'])
    
        self._state['message'] = result['message']
        self._update_from_optimization()#result)
        #################################################################################

        if verbose:
            print('allocation = {} Tau = {} Taup = {} '.format(self.allocation, self.tau, self.taup) )
            print('Finalized. Time(s) = {}'.format( self._state['elapsed_time']))

        return self.optimization_result                 

    def prediction_calculations(self, inj,prod ,prod_press ):
                

        invI, invP, invDP, invDates = self._get_matrices ( inj,prod,prod_press)


        #the matrix invI concatenates the production rates + tau * BHP + qo ( last column )
        invI = np.concatenate( (invI,                               #gain                                  
                                np.zeros( shape=(invI.shape[0],1)), #dp
                                np.zeros( shape=(invI.shape[0],1))),#qo  
                              axis=1) 
        

        
        qo, dt, lambdas, tau, taup = self._state['qo'], self._state['dt'], self._state['lambdas'].flatten(),self._state['tau'],self._state['taup']

        #the matrix invI concatenates the production rates + tau * BHP + qo ( last column )
        last_column = invI.shape[1]-1        
        invI[ :,  last_column - 1] = tau * invDP[:,0] 
        invI[ :,  last_column ] = 0.0

        #these are the individul contributions series -without the primary-. 
        pred_series = self._compute_pseudo_flow_matrix(invI, tau, dt) 

        #primary 
        time_steps = invI.shape[0]    
        inv_primary = np.array([ -dt*(1+n)/taup for n in range(time_steps)]) 
        inv_primary = qo * np.exp(inv_primary ).reshape( invP.shape )
        
        last_column = pred_series.shape[1]-1
        pred_series[ :,  last_column ] = inv_primary[:,0]

 
        #now the only thing to do is to multiply the prediction series times the lambdas
        Q = lambdas * pred_series


        return Q, invI, invP, invDP 
  
    def predict( self  ):

    
        data = self._data 
 

        if data is None: 
            raise ValueError('[predict] The fit_preprocess step was not done or it failed. Predictions arent possible') 

        if self.optimization_result is None:
            raise ValueError('[predict] The fit_preprocess and/or fit step was not done or it failed. Predictions arent possible') 
        
        if len(self.optimization_result) <1:
            raise ValueError('[predict] The fit_preprocess step was not done or it failed. Predictions arent possible') 
        
 
        tdate1, tdate2, tdate3 = np.datetime64( self._state['tdate1']), np.datetime64( self._state['tdate2']), np.datetime64( self._state['tdate3']) 
        dates = pd.to_datetime(data.water_injection.index).values 
        testing_mask = (dates >= tdate1) & (dates <= tdate3)
        

        inj, prod  = data.water_injection[testing_mask], data.liquid_production[testing_mask]
        prod_press = data.producer_pressure[testing_mask] if data.producer_pressure is not None else None 
        if prod_press is None: 
            prod_press= np.zeros ( shape= (inj.shape[0], 1) )
            self._state['last_prod_press'] = 0.0 
 
        else:
            self._state['last_prod_press'] = float(prod_press.values[ prod_press.shape[0]-1 ])
                 

        #check must equal tdate1 
        qo_date = self._state['qo_date'] 
        Q, invI, invP, invDP = self.prediction_calculations(inj, prod, prod_press )
        
    


        ##################################################################
        #prediction reselts. These are consumed by Koval and also exported
        ##################################################################
        lambdas, tau, taup = self._state['lambdas'].flatten(),self._state['tau'],self._state['taup']

        #primary support 
        primary_support = Q[:,-1:] #the last column is the primary contribution

        #for crmp, the last - 1 is the producer pressure, if none, then it is zero 

        
        #dates for the time series and slicing of some input data also reported 
        values_dates = pd.Series( inj.index ).values[1:] 
        
        #total water injected (only the lambdas part, dont include the J's as in the paper)
        water_injected  = np.sum(Q[:,0:len(lambdas)-2], axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 

        Q = np.sum( Q , axis = 1 ).reshape( invI.shape[0],1)
        df  = pd.DataFrame({
            LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX: Q.flatten(), 
            CUMMULATIVE_WATER_INJECTED_KEYS[0] + SIM_SUFFIX:water_injected.flatten(),     
            DATE_KEYS[0] :  values_dates,   
            LIQUID_PRODUCTION_KEYS[0]: invP.flatten(),
            PRIMARY_SUPPORT_KEYS[1]:primary_support.flatten()
            })
        
        if data.water_production is not None: 
            mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate3))
            w = data.water_production[1:]
            w = w[ pd.to_datetime(w.index) >= np.datetime64(tdate1) ]
            w = w[ pd.to_datetime(w.index) <= np.datetime64(tdate3)]
            df[ WATER_PRODUCTION_KEYS[0]] = w.values.flatten()
        
        df.set_index( DATE_KEYS[0], drop = True, inplace= True)
        df['NAME'] = self._state['producer_names'][0]     

        mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate2))
        df['TRAIN'] = mask
        df['ID'] = np.arange(0,df.shape[0],1)


        df1 = pd.DataFrame( {} )
        injector_names = self._state['injector_names']
        df1['INJECTOR'] =  injector_names
        df1['PRODUCER'] =  len(injector_names)*[ self._state['producer_names'][0] ]   
        df1[ALLOCATION_KEYS[0]]     =  list(lambdas)[0:len(lambdas)-2]
        df1['tau']   = len(injector_names)*[ tau ]   
        df1['taup']  = len(injector_names)*[ taup ] 
        df1[PRODUCTIVITY_KEYS[0]]  = len(injector_names)*[ self._state['Productivy'] ]     
        df1[PRIMARY_SUPPORT_KEYS[0] ]  = float( lambdas[-1:] ) 
        df1['MODEL']  = len(injector_names)*[ self.name ] 
        df1['ID'] = np.arange(0,df1.shape[0],1)

        d = {}
        d['crm'] = df1 
        d['rates'] = df 
        d['optimization'] = self.optimization_result 


        self.prediction_result = d

        return d 
 
    def forecast( self, water_injection_df, producer_pressure_df = None ):

     
        data = self._data 
        if data is None: 
            raise ValueError('[forecast] The fit_preprocess step was not done or it failed. Predictions arent possible') 

        if self.prediction_result is None: 
            raise ValueError('[forecast] The predict step was not done or it failed. Forecasts arent possible') 
        


        tdate1, tdate2 , tdate3 = np.datetime64( self._state['tdate1']),  np.datetime64( self._state['tdate2']),  np.datetime64( '2200-01-25' )
        dates = pd.to_datetime(water_injection_df.index).values 
        forecast_mask = dates >= tdate1

 
        inj  = water_injection_df[forecast_mask]
        prod = np.zeros ( shape= (inj.shape[0], 1) )
        prod_press = producer_pressure_df[forecast_mask] if producer_pressure_df is not None else None 
        
 
        #no bhp used in training 
        if self._state['bhp'] == False: 

            prod_press= np.zeros ( shape= (inj.shape[0], 1) )


        #bhp was used in training but if no bhp passed to forecast, will assume that the last known value is kept 
        #if bhp was used in training and it is passed to the forecast, then it will be used as expected. 
        else:
            if prod_press is None:  
                #print('bhp used in training but not passed to the forecast, so the last value known will be used.')
                prod_press= self._state['last_prod_press'] * np.ones ( shape= (inj.shape[0], 1) )

        #now the usual stuff: get the parameters, assembly the matrices, and predict 
        Q, invI, invP, invDP = self.prediction_calculations( inj,prod ,prod_press)

      
    
        ##################################################################
        #prediction results.  
        ##################################################################
        lambdas, tau, taup = self._state['lambdas'].flatten(),self._state['tau'],self._state['taup']
        values_dates = pd.Series( inj.index ).values[1:] 
        

        #total water injected (only the lambdas part, dont include the J's as in the paper)
        water_injected  = np.sum(Q[:,0:len(lambdas)-2], axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 

        Q = np.sum( Q , axis = 1 ).reshape( invI.shape[0],1)
        df  = pd.DataFrame({
            LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX: Q.flatten(), 
            CUMMULATIVE_WATER_INJECTED_KEYS[0] + SIM_SUFFIX:water_injected.flatten(),     
            DATE_KEYS[0] :  values_dates
            })
        


        df.set_index( DATE_KEYS[0], drop = True, inplace= True)
        df['NAME'] = self._state['producer_names'][0]     

        train_mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate2))
        df['TRAIN'] = train_mask
        df['ID'] = np.arange(0,df.shape[0],1)
        d = {}
        d['rates'] = df 

        self.forecast_result = d 
        return self.forecast_result 
     
    def set_parameters( self, lambdas, tau, taup ):

        self._state['lambdas'] = lambdas 
        self._state['tau'] = tau
        self._state['taup'] = taup
        
        n_params = len( lambdas )
        self._state['Primary support coeff'] = lambdas[n_params-1]
        self._state['Productivy'] = lambdas[n_params-2]
        self._state['Allocation'] = lambdas[0:-2]

        return self
        
    def evaluate_error( self, lambdas=None, tau=None , taup=None ):

        if lambdas is None:lambdas = self._state['lambdas']
        if tau  is None: tau  = self._state['tau'  ]
        if taup is None: taup = self._state['taup' ]
        
  
        invP = self._state['invP']
        pred_series = self._get_P_matrix( tau , taup )
        Q = lambdas * pred_series
        Q = np.sum( Q , axis = 1 ).reshape( invP.shape )

        error_metric =  root_mean_squared_error(invP, Q)#   
        #error_metric = mean_squared_error(invP, Q, squared=False) #if self._state['integrated']==False else integrated_error(invP, Q, squared=False)
        
        return  error_metric

    def set_internal_state_from_json( self, optimization_result ):
    
        '''
        Sets the internal state, except the matrices from json-saved optimization results.
        
        '''
        if isinstance(optimization_result, str ):
            s = dict( json.loads( optimization_result ) )
            
        else:
            s = optimization_result 
        
        #for CRMP
        if 'Allocation' in s:  s['Allocation'] = np.array(s['Allocation'])     
        if 'allocation' in s:  s['allocation'] = np.array(s['allocation'])     
        if 'lambdas'    in s:  s['lambdas'] = np.array(s['lambdas'])     
        if 'start_time' in s:  s['start_time'] = np.datetime64(s['start_time'])     
        if 'qo' in s: s['qo']  = np.array(s['qo'])

        
        self._state = {} 
        self._state.update( s )
        self.has_bhp = self._state['bhp'] #doesnt seem to be needed  
        self.optimization_result = optimization_result


        
        

    ###########################################
    ###              private API         ######  
    ###########################################
    
    def _compute_pseudo_flow_matrix(self, invI, tau, dt):
        
        time_steps = invI.shape[0]      
        window_size = 5 + int(5.0 * tau )
        E = np.flip(CRMHelper.get_row_vector_E(tau,dt, time_steps))
        pseudo_flow = np.zeros ( (time_steps,invI.shape[1]) )
        
        for tn in range( time_steps ):
            
            io = max(0, tn + 1 - window_size )
            Iview = invI[ io:tn+1,:]
            
            Eview = E[0,-Iview.shape[0]:]
            pseudo_flow[tn] = np.dot(Eview,Iview) 
          
        return pseudo_flow
        
    def _process_args(self, input_args = None ):
   
        def extract_date( s ):
            if s is None: return None 
        
            chars = ['-','/','\\',',']
            for char in chars: 
                if char in s: 
                    y,m,d= s.split(char)
                    return date( int(y),int(m),int(d))
            return None 

        if input_args is None: input_args = {}
        
        args = self.get_default_params()
        
        #the optimizer 
        if 'optimizer' in input_args: args['optimizer'].update( input_args['optimizer'] )
        args['optimizer']['name'] = optimizers_name_map[ args['optimizer']['name'].lower() ]   
        
        #pre-optimizer 
        if 'pre_optimizer' in input_args: args['pre_optimizer'].update( input_args['pre_optimizer'] )
        args['pre_optimizer']['name'] = optimizers_name_map[ args['pre_optimizer']['name'].lower() ]       
        
        #dates 
        if 'dates' in input_args:
 
            dates = input_args['dates']
            if len(dates) < 3: 
                dates.append('2200-11-20')

            args['dates'] = dates
            date1, date2,date3 = extract_date(args['dates'][0]), extract_date(args['dates'][1]), extract_date(args['dates'][2])

            if (date1 is None) and (date2 is None): args.pop( 'dates' )
                
            else:
                if (date1 is not None) and (date2 is not None): date1, date2 = sorted( [ date1, date2] ) 
                elif date1 is None: date1 = date.min
                elif date2 is None: date2 = date.max
                else: pass
                
                date1,date2 = sorted([date1,date2])
                args['dates'] = [ date1, date2,date3 ]
            

        #parameters tau and taup 
        if 'parameters' in input_args:
            if 'tau'  in input_args['parameters']: args['parameters']['tau']  = input_args['parameters']['tau']
            if 'taup' in input_args['parameters']: args['parameters']['taup'] = input_args['parameters']['taup']
                
        #time step
        if 'dt' in input_args: args['dt'] = input_args['dt']
        if 'max_running_time' in input_args: args['max_running_time']  = input_args['max_running_time']
        if 'maxiter' in input_args: args['maxiter']  = input_args['maxiter']
 
        #the error metric
        if 'integrated' in input_args: 
            args['integrated'] = input_args['integrated']
    
        #if 'primary' in input_args: 
        #    args['primary'] = input_args['primary']
    

        #other keys that may be related to multi-well 
        for key,value in input_args.items():
            if key in args:
                pass
            else:
                args[key] = value 
                
            

        return args
   
    def _get_P_matrix(self, tau , taup ):


        'The Q matrix, once multiplied by lambdas and summed along 1 is yhat'
        state = self._state 
        invI, invDP, invP,dt,qo = state['invI'],state['invDP'],state['invP'],state['dt'],state['qo']

        #the matrix invI concatenates the production rates + BHP + qo ( last column )
        #that Pressure column needs to be multiplied by +tau
        last_column = invI.shape[1]-1        
        invI[ :,  last_column - 1] = tau * invDP[:,0]  #pressure
        invI[ :,  last_column ] = 0.0                  #qo 
 
        pred_series = self._compute_pseudo_flow_matrix(invI, tau, dt) 

        #primary 
        time_steps = invI.shape[0]    
        inv_primary = np.array([ -dt*(1+n)/taup for n in range(time_steps)]) 
        inv_primary = qo * np.exp(inv_primary ).reshape( (time_steps,1) )
        pred_series[ :,  last_column ] = inv_primary[:,0]

        return pred_series
             
    def _loss(self, params, *args):
        
        #by convenction, tau and taup are the last two parameters. 
        tau,taup  = params[0], params[1]
        if tau < 0.001: tau = 0.001
        if taup < 0.001: taup = 0.001


        state = args[0]
        state['counter'] = state['counter']+1

        extra_loss = 1.0 
        pred_series = self._get_P_matrix( tau , taup)
        model = LinearRegression(positive=True,fit_intercept=False )
        invP = self._state['invP']
        reg = model.fit(pred_series, invP ) #fit coefficients for everythig   
        lambdas =  reg.coef_[0]#.flatten()  
        
        #print( lambdas.shape )
        #lambdas = lambdas.reshape( lambdas.shape[0],1)
        #large_lambdas =  np.array([ v if v > 1.0 else 0.0 for v in lambdas  ])
        #extra_loss =  1.0 + np.sum(large_lambdas**2)  
        #lambdas = np.array( [ v if v <= 1.0 else 1.0 for v in lambdas  ] )
        
        #primary support enforced to 1 
        #lambdas[ -1] = 1.0 
       
       

        yhat = (lambdas * pred_series).sum(axis=1).reshape( invP.shape )     
        error_metric =  root_mean_squared_error(invP, yhat)
        #error_metric = extra_loss * mean_squared_error(invP, yhat, squared=False)# if self._state['integrated']==False else integrated_error(invP, yhat, squared=False)
      
        state['rmse'] = error_metric
        state['r2'] = r2_score(invP, yhat)
        self.set_parameters( lambdas, tau, taup )
                  
        
        return error_metric 
       
    def _get_matrices( self,  inj, prod, prod_press = None ):
        
        num_time_steps = inj.shape[0]
        invI = CRMHelper._to_numpy(inj).reshape(num_time_steps,inj.shape[1])

        #can be zero when called as part of the forecast, where production is none
        if prod is None:
            invP = np.zeros ( shape= (invI.shape[0], 1) )
        else:
            invP = CRMHelper._to_numpy(prod).reshape(num_time_steps,prod.shape[1])
        
        invDates = CRMHelper._to_numpy( pd.Series(inj.index) ).reshape(num_time_steps,1)   
        
        #in many cases, there will be no BHP 
        if prod_press is None:
            invDP= np.zeros ( shape= (invI.shape[0], 1) )
            self.has_bhp = False
        else: 
            # P is really DP = [P1-Po, P2-P1, P3-P2,....] The Po value will be discarded. 
            prod_press  = CRMHelper._to_numpy( prod_press) #
            prod_press  = CRMHelper.shift_up(prod_press)-prod_press  
            invDP = -1.0*( prod_press.reshape( invI.shape[0],1))
            invDP[ invDP.shape[0] -1 ] = invDP[ invDP.shape[0] -2 ]
            self.has_bhp = True 
            
        #firs step is for the qo
        invI =  invI[1:invI.shape[0], :]  
        invP =  invP[1:invP.shape[0], : ]
        invDP =  invDP[1:invDP.shape[0], : ]
        invDates =  invDates[1:invDates.shape[0], :]     
            
        return invI, invP, invDP, invDates 

    def _pseudo_grid_search(self, params, bounds, options ):

        result = minimize(fun = self._loss, x0 = params, 
                          method= self._state['pre_optimizer']['name'],          
                          #callback=self._keep_working,
                          bounds = bounds ,
                          args=self._state , 
                          options = options, 
                          tol=self._state['optimizer']['tolerance'])

        self._state['message'] = result['message']
        lambdas = self._state['lambdas']
        tau     = self._state['tau']
        taup    = self._state['taup']
        return result, lambdas, tau, taup     
  
    def _format_prediction_results( self, water_production, Q, inj, invP, lambdas, tau, taup, tdate1, tdate3 ): 
  
        #primary support 
        primary_support = Q[:,-1:] #the last column is the primary contribution

        #for crmp, the last - 1 is the producer pressure, if none, then it is zero 
        prod_pressure = Q[:,-2:-1]
        
        #dates for the time series and slicing of some input data also reported 
        values_dates = pd.Series( inj.index ).values[1:] 
        
        #total water injected (only the lambdas part, dont include the J's as in the paper)
        water_injected  = np.sum(Q[:,0:len(lambdas)-2], axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 

        df  = pd.DataFrame({
            LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX: Q.flatten(), 
            CUMMULATIVE_WATER_INJECTED_KEYS[0] + SIM_SUFFIX:water_injected.flatten(),     
            DATE_KEYS[0] :  values_dates,   
            LIQUID_PRODUCTION_KEYS[0]: invP.flatten(),
            PRIMARY_SUPPORT_KEYS[0]:primary_support.flatten()
            })
        
        if water_production is not None: 
            mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate3))
            df[ WATER_PRODUCTION_KEYS[0]] = water_production[mask].values 
        
        df.set_index( DATE_KEYS[0], drop = True, inplace= True)
        df['NAME'] = self._state['producer_names'][0]     


        df['ID'] = np.arange(0,df.shape[0],1)


        df1 = pd.DataFrame( {} )
        injector_names = self._state['injector_names']
        df1['INJECTOR'] =  injector_names
        df1['PRODUCER'] =  len(injector_names)*[ self._state['producer_names'][0] ]   
        df1[ALLOCATION_KEYS[0]]     =  list(lambdas)[0:len(lambdas)-2]
        df1['tau']   = len(injector_names)*[ tau ]   
        df1['taup']  = len(injector_names)*[ taup ] 
        df1[PRODUCTIVITY_KEYS[0]]  = len(injector_names)*[ self._state['Productivy'] ]     
        df1[PRIMARY_SUPPORT_KEYS[0] ]  = float( lambdas[-1:] ) 
        df1['MODEL']  = len(injector_names)*[ self.name ] 
        df1['ID'] = np.arange(0,df1.shape[0],1)

        d = {}
        d['crm'] = df1 
        d['rates'] = df 
        d['optimization'] = self.optimization_result 
        
        
        return d 
 

    
class CRMP(CRMModel):
    
    '''
    CRMP solver for multi-pattern. Patterns can be multi-producer or single producer ones. 
    '''
   
    def __init__(self ):
 
        super().__init__('CRMP' )
        self._clear()
        
    def fit_preprocess( self, data, input_args = None ):
        '''
        After initialization, this is the first function that needs to be called in a CRM simulation.

        Here, the software stores the relevant information (matrices, tensors, names,etc) that are needed
        in the simulation. In this step, the arguments (optional) are also processed to determine, for instance,
        the trainning interval times and the testing interval

        Internally, the code splits the data in single-well patterns and calls SingleModel.fit_preprocess( ) for each.
        Single-well patterns for which the fit_preprocess doenst fail are stored for later simulation

        Errors are logged and appended to the model log.
        
        Note that the function returns -self- soi it can be chained wiith the fit method

        Example of use:

                from wf_lib.cdata.crm_pattern import CRMPattern 
                from wf_lib.models.crm_p import CRMP,CRMPSingle

                #generate some suynthetic data for testing
                pattern = CRMPattern().generate_default_multiwell_pattern()
                
                #create a model 
                model = CRMP()

                #train
                _= model.fit_preprocess( pattern )

                
        '''
        
        self.patterns,self.single_well_patterns, patterns   = None, None, None
        self.failed_models = [] 
        
        if isinstance(data, list ):         #option 1, a list of patterns 
            patterns = data 
            
        elif isinstance(data, CRMPattern ): #option 2, a single pattern
            patterns = [data]
                       
        else:
            raise ValueError( '[pre_process] Dont know what this data type is in fit_preprocess CRMP') 
            
        #for each pattern we have one set of parameters 
        args = None 
        if input_args is None: args =  len(patterns) * [self.get_default_params() ] 
        else:
            if not isinstance( input_args, list ):args = len(patterns) * [ input_args ]
            else: args = input_args
            if len(args) > len(patterns): args = args[0:len(patterns) ]
            elif len(args) < len(patterns): args = args.copy() + (len(patterns)  - len(args)) * [ self.get_default_params() ]      
        
      
        log = self.log 
        single_well_patterns = [] 
        success_count = 0 
        
        
        #one set of arguments per pattern which is copied to all its single-well sub-patterns
        for n,p in enumerate( patterns ):
            singles = p.multi_well_to_single()
            
            for id_, single in enumerate( singles ):     
                try:
                    model = self._get_submodel()
                    model._name = self._name 
                    
                    #args[n]['prod_id'] = id_
                    #args[n]['pattern_id'] = n 
                                    
                    model.fit_preprocess( single, args[n] )
                    
                    model.producer_name  = single.producer_names[0]
                    model.injector_names = single.injector_names  
                    single_well_patterns.append(single)
                    self.models.append( model )
                    success_count = 1 + success_count

                    #log.extend( model.log )

                except Exception as e:
                    self.failed_models.append( (single.producer_names[0],'preprocessing ' + str(e)) )
                    
                    s=' pattern ' + str(n) + ' id ' + str(id_)
                    print(str(e)+s)
                     
                    #log.extend( model.log )
                    log.append( str(e) + s )
                    
                    
        
        if success_count > 0:
            self.patterns = patterns
            self.single_well_patterns = single_well_patterns
        else:
            self.single_well_patterns = None 
            self.patterns = None 
            
        
        # print('leaving prefit with a nuber of models ', len(self.models) )
        self.optimization_result = []
         
        self.args = {} 
        if input_args is not None:  self.args.update( input_args )
        return self
    
    def fit( self ):#, serial = None,  balance = None  ):
        '''
        
        Once the model is initialized (fit_preprocess), this method carries-out the optimization.
        Note in the code below, that fit is chained (optionally) to fit_preprocess so the training 
        and data processing can be done in a single step. 
        
        Example of use:

                from wf_lib.cdata.crm_pattern import CRMPattern 
                from wf_lib.models.crm_p import CRMP,CRMPSingle

                #generate some suynthetic data for testing
                pattern = CRMPattern().generate_default_multiwell_pattern()
                
                #create a model 
                model = CRMP()

                #train
                optimization_result = model.fit_preprocess( pattern ).fit( )
                
                #print the results 
                optimization_result

            Result: 
                
                [{'message': 'Optimization terminated successfully.',
                'dates': [datetime.date(1950, 9, 23), datetime.date(2200, 1, 28)],
                'parameters': {'tau': {'bounds': (1, 50), 'init_value': 5.0},
                'taup': {'bounds': (1, 50), 'init_value': 5.0}},
                'max_running_time': 1000.0,
                'optimizer': {'maxiter': 1000, 'name': 'Nelder-Mead', 'tolerance': 0.001},
                'pre_optimizer': {'name': 'TNC'},
                'integrated': False,
                'crm_model': 'CRMP',
                'qo': [827.9422766501973],
                'injector_names': ['Inj0', 'Inj1', 'Inj2', 'Inj3'],
                'producer_names': ['Producer1'],
                'elapsed_time': 0.479247,
                'bhp': False,
                'rmse': 0.6273988592066048,
                'r2': 0.9998389519936466,
                'lambdas': [0.6023967254047103,
                0.4947917686337314,
                ...
                ],
                'tau': 16.600374237437986,
                'taup': 13.43
                
                ...},
                {'message': 'Optimization terminated successfully.',
                ...
                }
                {'message': 'Optimization terminated successfully.',
                ...
                }
                ]
                
        '''
        # print(  print('entering fit with a nuber of models, failed ', len(self.models), len(self.failed_models) ))
        
        self.prediction_result = {}
        balance = self.args.get( 'balance', {}).get('type', 'none')
        serial  = self.args.get( 'serial', True )
        
        def CRMPSingleSolver( n ):

            m,r = self.models[n], {} 
           
            try:
                r = m.fit()
                               
            except Exception as e: 
                #self.failed_models.append( (m.producer_name,'fit: ' + str(e)) )        
                
                r = {'message': 'Error ' + str(e)}

 
            return n,r,m
        
        
        if self.single_well_patterns is None:
            # print('Cannot fit the data, patterns not defined in a pre-process step')
            self.optimization_result = []
            return []
        
        self.optimization_result = []
        models_to_delete = [] 
        
        
        if serial == True: 
            
            self.log.append('serial fitting started')
            for i, m in enumerate ( self.models ):
                r = {}
                try:
                    
                    r = m.fit(  )

                except Exception as e:
                    s = f'fit: unexpected error. Producer {m.producer_name}. '+str(e)
                    r = {'message': s }

                    self.log.append( m.producer_name +  s )
                    self.failed_models.append( (m.producer_name, s ))
                    models_to_delete.append( m )
                    
            
                self.optimization_result.append( r )   
                self.log.append(f'fit model {i}, progress {100.0*(1+i)/len(self.models)}')
            

        else:
            self.log.append('parallel fitting started')
            num_producers = len( self.models )
            num_cpus =  max( mp.cpu_count(), min( num_producers, mp.cpu_count() ))
            
            models = self.models 
            results  = Parallel(n_jobs=num_cpus)(delayed(CRMPSingleSolver)
            ( n ) for n in range( len(models) ))   
            
     
            for i,item in enumerate( results ): 
            
                n,r,forked_model   = item

                self.models[n] = forked_model
                self.models[n].optimization_result = r
                
                
            self.optimization_result = [] 
            #####self.models_ids = { }
            for m in self.models: 
                r = m.optimization_result
                
                # when running in parallel we run a forked model, which makes hard to track failures in the 
                # same way that the serial case.
                # in the serial we get an exception and we handle it. Here we just get r as a dictionary and 
                # try to find the word 'error' under the message key 
                if 'error' in r['message'].lower(): #rtreat is as an exception
                    self.log.append( r['message'] )
                    self.failed_models.append( (m.producer_name,'fit: ' + r['message'] ) )
                    models_to_delete.append( m )
                 
                self.optimization_result.append( r )  
                
           
           
        for item in models_to_delete: 
            # print('deleting a model ', m.producer_name )
            self.models.remove( item )
            
        self.log.append('fitting finished')
        
        if balance is None:
            self.log.append('no-balancing done')
             
        elif isinstance(balance, str):
            # print('balancing string....')
            if balance.lower() == 'full':
                print('full balancing')
                self.log.append('doing a full balance')
                self.balance('full' )
                self.log.append('balancing done')
                
            elif balance.lower() == 'quick':
                self.log.append('doing a quick balance')
                self.balance('quick')
                self.log.append('balancing done')
        
            else:
                self.log.append('no-balancing done')
             
        else:
            self.log.append('no-balancing done')
             
        # print('leaving fit with a nuber of models ', len(self.models) )
          
        self.prediction_result['optimization']  = self.optimization_result
        return self.optimization_result
    
    def predict( self  ):
        
        self.prediction_result  ={}
        _predictions = [] 
        
        models_to_delete = [] 
        self.log.append('prediction started')
        for i,m in enumerate(self.models):
            
            try:
                
                #if i == 0: 
                #    raise  ValueError('Hard-coded failure for predict id == 0 ')
                
                p = m.predict( )  
                r = m.optimization_result               
                #p['rates']['id'] = r['id']
                #p['crm']['pattern_id'] = r['pattern_id']
                
                #p['rates']['prod_id'] = r['prod_id']
                #p['rates']['pattern_id'] = r['pattern_id']
                
                #p['crm']['pattern_id'] = r['pattern_id']
                #p['crm']['prod_id'] = r['prod_id']
                
                
                _predictions.append( p ) 
                self.log.append(f'prediction for model {i} finished, progress {100.0*(1+i)/len(self.models)}')
                
            except Exception as e:
                self.log.append( 'Prediction failed ' + str(e) )
                self.failed_models.append( (m.producer_name,'predict: ' + str(e)) )
                for item in models_to_delete:
                    self.models.remove( item )
                    
                print('failed predictions:',str(e)  )
      
        try:
            rates = [ p['rates'] for p in _predictions ]
            if len(rates)>0: rates = pd.concat( rates, axis = 0 )
            self.log.append('rates processed')

            crms = [ p['crm'] for p in _predictions ]
            if len(crms)>0: crms = pd.concat( crms, axis = 0 )
            self.log.append('crm results processed')

            crms['ID'] = np.arange(0,crms.shape[0],1)
            crms.set_index( 'ID', inplace = True, drop = False  )
            rates.sort_values('DATE')['ID'] = np.arange(0,rates.shape[0],1)


            self.prediction_result = { 'crm': crms, 'rates': rates , 'optimization':  self.optimization_result }
            self.log.append('prediction results processed')

        except Exception as e:
            self.log.append('processing prediction results failed')
            

        return self.prediction_result
         
    def balance(self, balance_type = 'quick'):

        def _get_successful_models():# self ):
            '''Go through the optimization results of the model and 
            returns the list of models and optimization results for which 
            the word success was found in the messsge. The rest are discarded.
            '''
            opts, success_models = [], [] 
            for m in self.models:
                if 'success' in m.optimization_result['message']:
                    opts.append(  m.optimization_result )
                    success_models.append( m )

            return opts, success_models
        
        def _get_off_balance_injectors():# self ):
            '''
            Returns a dictionaty with keys the injector names and as values the producers linked to those
            injectors and the total allocation, if the allocation sum is greater than 1. 
            '''
            opts, _= _get_successful_models( )#self ) 
            d = {}
            for opt in opts:
                producer    = opt['producer_names'][0]
                injectors   = opt['injector_names']
                allocations = opt['allocation']
                for i,injector in enumerate( injectors ):
                    if injector not in d.keys(): d[injector] = {'producers':[],'allocation':0.0 }
                    d[injector]['producers'].append( (producer, i, allocations[i] )  )
                    d[injector]['allocation'] = d[injector]['allocation'] + allocations[i]

            d = { item:value  for item,value in d.items() if value['allocation'] > 1.0 }
            
            return d
        
        def _balancer_loss( params, *args ):

            opts = args[0]
            sub_models = args[1]
            error = 0.0 
            x = None 

            for n,sub_model in enumerate(sub_models):

                #get the indices in the global list of the parameters for the model
                r = opts[ n ]
                model_parameters = r['parameter_index']

                #the current value of all of these 
                vals = params[ model_parameters ] 
                tau, taup = vals[-2:]
                lambdas   =  vals[0:-2]
                sub_model.set_parameters( lambdas, tau, taup )

                #now evaluate the model error 
                e = sub_model.evaluate_error()# lambdas, tau, taup )
                error = error + e 
                
                     
                sub_model._state['rmse'] = error
                sub_model._update_from_optimization()

                    
            #print('balancer loss ', error )
            return error 

        
        def _construct_balancing_matrices( optimization_results ):

            parameter_counter,injector_constraints, bounds, init_values = -1, {}, [], [] 

            #for each single=wel model = item 
            for item in  optimization_results :

                #each of its parameters will have an index in a global list 
                item['parameter_index'] = [] 
                injector_names = item['injector_names']
                num_injectors = len( injector_names )

                #all the coefficients allocs + J + qo 
                well_parameters = item['lambdas'] # CRMP[ [lambdas-injectors(ninj), productivity(1), qo(1)]]
                extras = 0    

                for n,value in enumerate(well_parameters):#for allocs [ value1, value2,...] + J [1] and qo [1] 

                    parameter_counter = parameter_counter + 1 
                    item['parameter_index'].append( parameter_counter )

                    if n < num_injectors:                   #allocations  

                        if injector_constraints.get( injector_names[n], None ) is None: 
                            injector_constraints[injector_names[n]] = [] 

                        injector_constraints[injector_names[n]].append( parameter_counter )
                        bounds.append( (0.0,1.0) )
                        init_values.append( value )

                    else: #productiviy and qo. Productivity is one value for CRM-P same for qo, tau and taup 

                        if extras == 0 :                    #productivity                         
                            init_values.append( value )
                            bounds.append( (0.0,value+0.01) )
                            extras = 1 

                        else:                               #qo 
                            bounds.append( (0.0,1.0) )
                            init_values.append( value )

                #now tau and taup 
                tau_bounds, taup_bounds = item['parameters']['tau']['bounds'], item['parameters']['taup']['bounds']
                bounds.extend( [( tau_bounds[0],tau_bounds[1]), ( taup_bounds[0],taup_bounds[1])]  )
                item['parameter_index'].extend( [parameter_counter+1,parameter_counter+2 ] )
                parameter_counter = parameter_counter+2
                init_values.extend( [ item['tau'],item['taup'] ] )

            return injector_constraints, bounds, init_values,parameter_counter


        ######################################################################################
        
        if self.optimization_result is None or len(self.optimization_result)<1:
            s = '[fit] Cannot balance the data, either a call to fit() failed or it was never called.' 
            print(s) 
            raise ValueError(s)
            
        
        off_balance = _get_off_balance_injectors( )#self ) 
        if( len( off_balance ) < 1):
            print('Nothing to balance')
            return { 'message': 'success: Nothing to balance'} 


        opts, success_models =  _get_successful_models()#self)
        
        sum_error = 0.0 
        if (balance_type == 'quick') or (balance_type == 'full'):
        
                                 
            for i, item in enumerate( off_balance.items() ):

                inj_name, producers, allocation = item[0], item[1]['producers'], item[1]['allocation']
                delta = (allocation-1.0)/len(producers)
                
                if delta > 0.01:

                    scaling_factor = 1.0 / allocation
                    producer_names = [ item[0] for item in producers]
                    for m in self.models: 
                        if m._state['producer_names'][0] in producer_names:
                            index = m._state['injector_names'].index( inj_name )
                            m._state['lambdas'][index]  = m._state['lambdas'][index] * scaling_factor
                            error = m.evaluate_error()
                            sum_error = sum_error + error  
                            m._state['rmse'] = error
                            m._update_from_optimization()
                            
                            
            self.optimization_result = [] 
            for m in self.models: 
                r = m.optimization_result
                self.optimization_result.append( r )    
                
            '''
            for i, item in enumerate( off_balance.items() ):

                inj_name, producers, allocation = item[0], item[1]['producers'], item[1]['allocation']
                delta = (allocation-1.0)/len(producers)

                if delta > 0.01:

                    producer_names = [ item[0] for item in producers]
                    for m in self.models: 
                        if m._state['producer_names'][0] in producer_names:
                            index = m._state['injector_names'].index( inj_name )
                            m._state['lambdas'][index]  = m._state['lambdas'][index] - delta  
                            error = m.evaluate_error()
                            sum_error = sum_error + error  
                            
                            
                            m._state['rmse'] = error
                            m._update_from_optimization()


            self.optimization_result = [] 
            for m in self.models: 
                r = m.optimization_result
                self.optimization_result.append( r ) 
            '''
        
            if balance_type == 'quick':
                return { 'message': 'success. Quick balancing done'} 
        
        if balance_type.lower() == 'full':
            
              
            print('------- Entering in the full balancing now P------')
            
            
            options = {'maxiter': self.args['balance'].get('maxiter',100)}
            tolerance = self.args['balance'].get('tolerance', 0.01)
            print('# We believe that the total error is of the order of ', sum_error,'  before balancing ' )
            print('# The setup optimizer parameters ', options, tolerance )
            
            
            
            inj_constraints, bounds, init_vals,param_count = _construct_balancing_matrices( opts )
            init_vals = np.array( init_vals )
            inj_constraints = np.array( list( inj_constraints.values())) 
            num_contraints = inj_constraints.shape[0]
            ub = np.array( (num_contraints) * [1.0] )
            lb = np.array( (num_contraints) * [0.0] )

            param_count = param_count + 1 #starts with zro 
            A = np.zeros( shape = (inj_constraints.shape[0],param_count) )
            for n in range( inj_constraints.shape[0] ): A[n,inj_constraints[n]] = 1.0


              
            
            
            state = (opts,success_models) 
            linear_constraint = LinearConstraint( A, lb, ub ) 
            result = minimize( fun       = _balancer_loss, 
                               x0        = init_vals, 
                               method    =  self.args['optimizer']['name'],
                               bounds    = bounds,
                               constraints = linear_constraint,
                               args      = state , 
                               options   = options,  
                               tol       = tolerance )


            self.optimization_result = [] 
            for m in self.models: 
                r = m.optimization_result
                self.optimization_result.append( r ) 

            return result 
  
    def set_internal_state_from_json( self, s ):
        '''
        Restores a model for prediction (or forecast)
        from its previous representation of prediction['optimization'] as 
        a json string. self.prediction_results['optimization'] should be available as soon as the model is fit. 
        '''
        pass 

    def _get_submodel( self ):
        return CRMPSingle()

    def forecast( self, water_injection_df, producer_pressure_df = None ):
        
        forecasts = [] 
        models = self.models
        self.log.append('forecast started')
        self.forecast_result = None 

        for n,m in  enumerate( models ):

            try:
                print('doing forecast for model',n )
                producer_name, injector_names = m._state['producer_names'][0], m._state['injector_names']   
                water    = water_injection_df[injector_names]
                if water.shape[1] < 1: 
                    raise ValueError(f'[forecast] Injector names not found in the water injection table for model {n}' )

                pressure = None if producer_pressure_df is None else producer_pressure_df[[producer_name]]

  
                ff = m.forecast( water, pressure )
                forecasts.append( ff )
                self.log.append( f'--Done forecast for producer {producer_name} [{n+1}] out of {len(models)}' )

            except Exception as e:
                s = f'[forecst] {str(e)}'
                print(s)
                self.log.append( s )

        self.forecast_result = {}
        self.forecast_result['rates'] = pd.concat( [single_forecast['rates'] for single_forecast in forecasts ], axis = 0 ) 
        self.log.append('forecast finished')      

        return self.forecast_result 

    def get_default_params( self ): 
        
        params_ = self._get_submodel().get_default_params()
        params_['serial'] = True 
        params_['balance'] = { 'type':'quick', 'maxiter':100, 'tolerance': 0.001 }
        return params_
 

class CRMPSingleConstrained( CRMPSingle ):
    '''
    CRMP solver for single-producer patterns. This class shouldnt be instantiated in the general case.
    The CRMP class defined below should be used instead. The CRMPSingle exists only as support for the 
    CRMP class which accounts for multi-producer and multi-pattern scenarios. 
    '''
    
    ###########################################
    ###              public API         #######  
    ###  implements the CRMModel interface  ###
    ###########################################

    def __init__(self ):
        super().__init__()#'CRMPSingleConstrained')
        self._clear()
        self._name = 'CRMPSingleConstrained'
        
        
    def _process_args(self, input_args = None ):
   
        def extract_date( s ):
            if s is None: return None 
        
            chars = ['-','/','\\',',']
            for char in chars: 
                if char in s: 
                    y,m,d= s.split(char)
                    return date( int(y),int(m),int(d))
            return None 

        if input_args is None: input_args = {}
        
        args = self.get_default_params()
        
        #the optimizer 
        if 'optimizer' in input_args: args['optimizer'].update( input_args['optimizer'] )
        args['optimizer']['name'] = optimizers_name_map[ args['optimizer']['name'].lower() ]   
        
        #pre-optimizer 
        if 'pre_optimizer' in input_args: args['pre_optimizer'].update( input_args['pre_optimizer'] )
        args['pre_optimizer']['name'] = optimizers_name_map[ args['pre_optimizer']['name'].lower() ]       
        
        #dates 
        if 'dates' in input_args:
 
            dates = input_args['dates']
            if len(dates) < 3: 
                dates.append('2200-11-20')

            args['dates'] = dates
            date1, date2,date3 = extract_date(args['dates'][0]), extract_date(args['dates'][1]), extract_date(args['dates'][2])

            if (date1 is None) and (date2 is None): args.pop( 'dates' )
                
            else:
                if (date1 is not None) and (date2 is not None): date1, date2 = sorted( [ date1, date2] ) 
                elif date1 is None: date1 = date.min
                elif date2 is None: date2 = date.max
                else: pass
                
                date1,date2 = sorted([date1,date2])
                args['dates'] = [ date1, date2,date3 ]
            

        #parameters tau and taup 
        if 'parameters' in input_args:
            if 'tau'  in input_args['parameters']: args['parameters']['tau']  = input_args['parameters']['tau']
            if 'taup' in input_args['parameters']: args['parameters']['taup'] = input_args['parameters']['taup']
            if 'lambda' in input_args['parameters']: args['parameters']['lambda'] = input_args['parameters']['lambda']
            if 'productivity_index' in input_args['parameters']: args['parameters']['productivity_index'] = input_args['parameters']['productivity_index']
            if 'qo_lambda' in input_args['parameters']: args['parameters']['qo_lambda'] = input_args['parameters']['qo_lambda']
            
            
                
        #other stuff that the user can override 
        if 'dt' in input_args: args['dt'] = input_args['dt']
        if 'regularization' in input_args: args['regularization'] = input_args['regularization']
        
        if 'max_running_time' in input_args: args['max_running_time']  = input_args['max_running_time']
        if 'maxiter' in input_args: args['maxiter']  = input_args['maxiter']
 
  
        if 'primary' in input_args: 
            args['primary'] = input_args['primary']
    

        #other keys that may be related to multi-well 
        for key,value in input_args.items():
            if key in args:
                pass
            else:
                args[key] = value 
                
            

        return args
   
 
    def get_default_params(self): 
        
        '''
        Returns the default parameters to be used during optimization,
        All or some of these can be replaced all by the input_args passed to the 
        fit_preprocess method.
        
        Returns:
            
            args (dict): Dictionary with default parameters for the CRM-P model 
        
        Example of use 1:
        
            args_dict = CRMP().get_default_params()
            print(args_dict)
            
            >>{'parameters': {'tau':   {'bounds':(1,50), 'init_value': 5.0} ,
            >>                'taup':  {'bounds':(1,50), 'init_value': 5.0}
            >>               },
            >> 'dt': 1.0,
            >> 'max_running_time': 1000.0,
            >> 'optimizer': {'maxiter': 1000,'name': 'Nelder-Mead', 'tolerance': 1e-03},
            >> 'pre_optimizer': {'name': 'TNC'} 
            >>}
            
        Example of use 2 (change tau limits and pre-optimizer before running model):
        
            args_dict = CRMP().get_default_params()
            args_dict['parameters']['tau']['bounds'] = (20,25)
            args_dict['pre_optimizer']['name'] = 'powell'
       
            model = CRMP()
            optimization_result = model.pre_process( data, args_dict ).fit() 
            predictions = model.predict()

             (etc...)            
        '''
        
        args = {
            'dates': ['1950-09-23','2200-01-28'],
                   
            'parameters': {
                'tau':   {'bounds': (0.1,50), 'init_value': 5.0} ,
                'taup':  {'bounds':(0.1,50), 'init_value': 5.0},
                'lambda':   {'bounds': (0.01,0.99), 'init_value': 0.4321},
                'productivity_index':   {'bounds': (0.0,0.5), 'init_value': 0.0},
                'qo_lambda':   {'bounds': (0.0,1.2), 'init_value': 1.0}
            },


            'dt': 1.0,
            'regularization': 0.001, 
            'max_running_time': 1000.0,
            'optimizer': {'maxiter': 1000,'name': 'SLSQP', 'tolerance': 1e-04},
            'pre_optimizer': {'name': 'Powell'},
            'primary': True 
        }
        
        return args 
  
       
    ###########################################
    ###              private API         ######  
    ###########################################
              
    def _loss(self, params, *args):
        
        #by convenction, tau and taup are the last two parameters. 
        tau,taup  = params[0], params[1]
        if tau < 0.001: tau = 0.001
        if taup < 0.001: taup = 0.001

        state = args[0]
        num_injectors = len( state['injector_names'] )
        state['counter'] = state['counter']+1

        lambdas = params[2 : ] #all lambdas, lambda_0 and lambda_J 
        

        extra_loss = 1.0 
        pred_series = self._get_P_matrix( tau , taup)
        
        invP = self._state['invP']
        yhat = (lambdas * pred_series).sum(axis=1).reshape( invP.shape )     
        error_metric = extra_loss * root_mean_squared_error(invP, yhat)# if self._state['integrated']==False else integrated_error(invP, yhat, squared=False)
       
        state['rmse'] = error_metric
        state['r2'] = r2_score(invP, yhat)
        self.set_parameters( lambdas, tau, taup )

        #print(error_metric, lambdas )
        #model = LinearRegression(positive=True,fit_intercept=False )
        #reg = model.fit(pred_series, invP ) #fit coefficients for everythig   
        #lambdas =  reg.coef_[0]#.flatten()  
        #yhat = (lambdas * pred_series).sum(axis=1).reshape( invP.shape )     
        #error_metric = extra_loss * mean_squared_error(invP, yhat, squared=False)# if self._state['integrated']==False else integrated_error(invP, yhat, squared=False)
        #state['rmse'] = error_metric
        #state['r2'] = r2_score(invP, yhat)
        #self.set_parameters( lambdas, tau, taup )
                  
        
        return error_metric 
       
    def _fit(self, quick = False, verbose=False):

        self.optimization_result = {} 
        data = self._data
        if data is None:
            raise ValueError('[fit] Cannot fit the data because fit_preprocess failed or was never called')
        
         

        tdate1, tdate2 = np.datetime64( self._state['tdate1']),np.datetime64( self._state['tdate2'])
        dates = pd.to_datetime(data.water_injection.index).values 
        
        mask = (dates >= tdate1) & (dates <= tdate2)
        inj, prod  = data.water_injection[mask], data.liquid_production[mask]
        
        
        
        
        prod_press = data.producer_pressure[mask] if data.producer_pressure is not None else None 
        invI, invP, invDP, invDates = self._get_matrices(  inj, prod, prod_press )    
        

        if invP.shape[0] < 1:
            error = "[fit] Error when assembling matrices. Production data is missing. Producer {self.producer_name}"
            raise ValueError( error )
                
        if invI.shape[0] < 1:
            error = "[fit] Error when assembling matrices. Production data is there but injection data is missing. Producer {self.producer_name}"
            raise ValueError( error )
          
     
        #this concatenation is only used in CRM-P. For CRMIP is not convenient 
        invI = np.concatenate( (invI,                               #gain injectors                                  
                                np.zeros( shape=(invI.shape[0],1)), #dp
                                np.zeros( shape=(invI.shape[0],1))),#qo  
                                axis=1) 
        
        self._state['bhp'] = self.has_bhp
        self._state['invI']= invI
        self._state['invP']=invP
        self._state['invDP']=invDP
        self._state['invDates']=invDates


        ##############################################
        # initial values and bounds for the parameters 
        # we will organize themn as [ tau, taup, lambdas, qo_lambda, productivity_index_lambda ] 
        
        parameters = self._state['parameters']
        
        # tau, taup bounds 
        tau_bounds = [parameters['tau']['bounds'],parameters['taup']['bounds'] ]
       
        # how many injectors do we have. We have 1 lambda bound for each  
        num_injectors = len( self._state['injector_names'] ) 
        min_lambda, max_lambda = parameters['lambda']['bounds'][0], parameters['lambda']['bounds'][1]
        lambda_bounds =  [  (min_lambda, max_lambda) for n in range(  num_injectors ) ] 


        # bounds for the productivity index 
        productivity_bounds = [parameters['productivity_index']['bounds'] ]# if self.has_bhp else (-0.01,0.01)]

        # bounds for the qo coefficient 
        qo_lambda_bounds = [ parameters['qo_lambda']['bounds'] ]
        
        
        all_bounds = tau_bounds + lambda_bounds + productivity_bounds + qo_lambda_bounds
   
        ############################################ 
        # now the initial values, in the same order 
        init_values = [ parameters['tau']['init_value'], parameters['taup']['init_value'] ] 
        init_values = init_values + [ parameters['lambda']['init_value'] for n in range( num_injectors) ] 
        init_values = init_values + [ parameters['productivity_index']['init_value'] if self.has_bhp else 0.0]   
        init_values = init_values + [ parameters['qo_lambda']['init_value'] ] 
        
        
        optimizer = self._state['optimizer']
        options = {'maxiter':max(self._state['optimizer']['maxiter'], 10*invI.shape[1]), 'disp':verbose}
        tolerance = optimizer['tolerance']
        result = minimize( fun       = self._loss, 
                      x0        = init_values ,
                      method    = optimizer['name'],         
                      bounds    = all_bounds,
                      args      = self._state, 
                      options   = options, 
                      tol       = tolerance
                      )
        
        self._state['message'] = result['message']
        self._update_from_optimization()#result)
        #################################################################################

        if verbose:
            print('allocation = {} Tau = {} Taup = {} '.format(self.allocation, self.tau, self.taup) )
            print('Finalized. Time(s) = {}'.format( self._state['elapsed_time']))

        return self.optimization_result      
        '''
        #optimization parameters 
        parameters = self._state['parameters']
        bounds = [parameters['tau']['bounds'],parameters['taup']['bounds'] ]
        init_tau, init_taup = parameters['tau']['init_value'], parameters['taup']['init_value']  
        
        #options 
        #num_injectors = self._state['invI'].shape[1]
        options = {'maxiter':max(self._state['optimizer']['maxiter'], 10*invI.shape[1]), 'disp':verbose}
        
        #initial conditions 
        params = [ init_tau, init_taup]
        result, lambdas, init_tau, init_taup  = self._pseudo_grid_search( params, bounds, options )
        self._update_from_optimization( )#result ) 


        #if only a quick-fit is done return what we have now.
        if quick: 
            if verbose: print('Pre-optimization finished. Results',init_tau,  init_taup )
            return self.optimization_result  
        
        #further optimize starting where the prev was left
        options = {'maxiter':max(self._state['optimizer']['maxiter'], 10*invI.shape[1]), 'disp':verbose}
        params = np.array( [init_tau,init_taup] )
        
  
        
        optimizer = self._state['optimizer']
        result = minimize( fun       = self._loss, 
                           x0        = params, 
                           method    = optimizer['name'],         
                           callback  = self._keep_working,
                           bounds    = bounds,
                           args      = self._state , 
                           options   = options,  
                           tol       = optimizer['tolerance'])
    
        self._state['message'] = result['message']
        self._update_from_optimization()#result)
        #################################################################################

        if verbose:
            print('allocation = {} Tau = {} Taup = {} '.format(self.allocation, self.tau, self.taup) )
            print('Finalized. Time(s) = {}'.format( self._state['elapsed_time']))

        return self.optimization_result                 
        ''' 

  
class CRMPConstrained(CRMP):
    
    def __init__(self):
        super().__init__()
        self._name = 'CRMPConstrained'
            
        
    def _get_submodel( self ):
        return CRMPSingleConstrained()
  






class old_CRMPSingle( CRMSingleModel ):
    '''
    CRMP solver for single-producer patterns. This class shouldnt be instantiated in the general case.
    The CRMP class defined below should be used instead. The CRMPSingle exists only as support for the 
    CRMP class which accounts for multi-producer and multi-pattern scenarios. 
    '''
    
    ###########################################
    ###              public API         #######  
    ###  implements the CRMModel interface  ###
    ###########################################

    def __init__(self ):
        super().__init__('CRMPSingle')
        self._clear()
        
    def get_default_params(self): 
        
        '''
        Returns the default parameters to be used during optimization,
        All or some of these can be replaced all by the input_args passed to the 
        fit_preprocess method.
        
        Returns:
            
            args (dict): Dictionary with default parameters for the CRM-P model 
        
        Example of use 1:
        
            args_dict = CRMP().get_default_params()
            print(args_dict)
            
            >>{'parameters': {'tau':   {'bounds':(1,50), 'init_value': 5.0} ,
            >>                'taup':  {'bounds':(1,50), 'init_value': 5.0}
            >>               },
            >> 'dt': 1.0,
            >> 'max_running_time': 1000.0,
            >> 'optimizer': {'maxiter': 1000,'name': 'Nelder-Mead', 'tolerance': 1e-03},
            >> 'pre_optimizer': {'name': 'TNC'} 
            >>}
            
        Example of use 2 (change tau limits and pre-optimizer before running model):
        
            args_dict = CRMP().get_default_params()
            args_dict['parameters']['tau']['bounds'] = (20,25)
            args_dict['pre_optimizer']['name'] = 'powell'
       
            model = CRMP()
            optimization_result = model.pre_process( data, args_dict ).fit() 
            predictions = model.predict()

             (etc...)            
        '''
        
        args = {
            'dates': ['1950-09-23','2200-01-28'],
            'parameters': {
                'tau':   {'bounds': (0.1,50), 'init_value': 5.0} ,
                'taup':  {'bounds':(0.1,50), 'init_value': 5.0}
            },


            'dt': 1.0,
            'max_running_time': 1000.0,
            'optimizer': {'maxiter': 1000,'name': 'Nelder-Mead', 'tolerance': 1e-04},
            'pre_optimizer': {'name': 'Powell'},
            'integrated': False,
            'primary': True 
        }
        return args 
  
    def fit_preprocess_pattern(self, pattern, args):
        
        #args = {dates:['date1', 'date2']}
           
        #Checks that we have time series, dataframes and no time gaps. Raises a ValueError
        self._validate_input_pattern( pattern )  

        # Raises an exception is something wrong happens. 
        # Adjust training time-frame.
        # Modifies the input pattern to slice dates [date1, date3]
        # removes inactive wells
        # Training dates are [date1,date2], testing dates are [date1, date3 ]
        tdate1, tdate2, tdate3 = self.adjust_training_testing_dates( pattern, args )


        #note that prod pressure will be None most of the time (no bhp)
        dates = pd.to_datetime(pattern.water_injection.index).values 
        mask = dates >= tdate1
        inj, prod  = pattern.water_injection[mask], pattern.liquid_production[mask]
        qo,qo_date = prod.values[ 0 ], prod.index.values[ 0 ] 

        return pattern, tdate1, tdate2, tdate3, inj, prod, qo,qo_date 
    
    
    def fit_preprocess( self, pattern,input_args=None, verbose=False):
        ''' 
        This is the first function to be called before any simulation.
        Here, the input pattern is sliced in time according to the best 
        compromise between the available data and the user params for 
        dates. 

        The pattern once processed is stored and the model state 
        is saved. Such state contains a matrix representation of all the 
        data as it is used in the fitting and predicting processes later.

        Note that the state saves tdate1---tdate3. The first 2 are the 
        training timeframes whereas t1-t3 are the testing
        ''' 


        self._clear()

        names = ",".join (['I:']+list(pattern.injector_names) + ['P:']+list(pattern.producer_names) )
        self.log.append(  f'[fit_preprocess] for {names}' )

        args = self._process_args( input_args )

        #returns the same pattern object received (same memory id) but modified 
        #from args, it only uses {dates:['date1', 'date2']}
        #the resulting pattern is stored internally as _data 
        #pattern, tdate1, tdate2, tdate3, inj, prod, qo,qo_date = self.fit_preprocess_pattern( pattern, args )
        
        self._validate_input_pattern( pattern )  

        # Raises an exception is something wrong happens. 
        # Adjust training time-frame.
        # Modifies the input pattern to slice dates [date1, date3]
        # removes inactive wells
        # Training dates are [date1,date2], testing dates are [date1, date3 ]
        tdate1, tdate2, tdate3 = self.adjust_training_testing_dates( pattern, args )


        #note that prod pressure will be None most of the time (no bhp)
        dates = pd.to_datetime(pattern.water_injection.index).values 
        mask = dates >= tdate1
        inj, prod  = pattern.water_injection[mask], pattern.liquid_production[mask]
        qo,qo_date = prod.values[ 0 ], prod.index.values[ 0 ] 
        
        if args['primary'] is False:
            qo = 0.0 
        
    

        self.log.append(  f'[fit_preprocess] updating internal state' )
        args['crm_model'] = self._name 
        args['tdate1']  = str(tdate1)
        args['tdate2']  = str(tdate2)
        args['tdate3']  = str(tdate3)  
        args['qo'], args['qo_date'] = qo, str((qo_date))[0:10] 
        args['injector_names'] = list(inj.columns)
        args['producer_names'] = list(prod.columns)

        self.producer_name = list(prod.columns)[0]
        self.injector_names = list(inj.columns)
            
        self._init_state( args )
        self._data = pattern 
        self.log.append(  '[fit_preprocess]  finished' )

        return self
 
    def _fit(self, quick = False, verbose=False):

        self.optimization_result = {} 
        data = self._data
        if data is None:
            raise ValueError('[fit] Cannot fit the data becuase fit_preprocess failed or was never called')
        
         

        tdate1, tdate2 = np.datetime64( self._state['tdate1']),np.datetime64( self._state['tdate2'])
        dates = pd.to_datetime(data.water_injection.index).values 
        
        mask = (dates >= tdate1) & (dates <= tdate2)
        inj, prod  = data.water_injection[mask], data.liquid_production[mask]
        prod_press = data.producer_pressure[mask] if data.producer_pressure is not None else None 
        invI, invP, invDP, invDates = self._get_matrices(  inj, prod, prod_press )    
        
        #this concatenation is only used in CRM-P. For CRMIP is not convenient 
        invI = np.concatenate( (invI,                               #gain injectors                                  
                                np.zeros( shape=(invI.shape[0],1)), #dp
                                np.zeros( shape=(invI.shape[0],1))),#qo  
                                axis=1) 
        
        self._state['bhp'] = self.has_bhp
        self._state['invI']= invI
        self._state['invP']=invP
        self._state['invDP']=invDP
        self._state['invDates']=invDates

        
        #optimization parameters 
        parameters = self._state['parameters']
        bounds = [parameters['tau']['bounds'],parameters['taup']['bounds'] ]
        init_tau, init_taup = parameters['tau']['init_value'], parameters['taup']['init_value']  
        
        #options 
        #num_injectors = self._state['invI'].shape[1]
        options = {'maxiter':max(self._state['optimizer']['maxiter'], 10*invI.shape[1]), 'disp':verbose}
        
        #initial conditions 
        params = [ init_tau, init_taup]
        result, lambdas, init_tau, init_taup  = self._pseudo_grid_search( params, bounds, options )
        self._update_from_optimization( )#result ) 


        #if only a quick-fit is done return what we have now.
        if quick: 
            if verbose: print('Pre-optimization finished. Results',init_tau,  init_taup )
            return self.optimization_result  
        
        #further optimize starting where the prev was left
        options = {'maxiter':max(self._state['optimizer']['maxiter'], 10*invI.shape[1]), 'disp':verbose}
        params = np.array( [init_tau,init_taup] )
        
  
        
        optimizer = self._state['optimizer']
        result = minimize( fun       = self._loss, 
                           x0        = params, 
                           method    = optimizer['name'],         
                           callback  = self._keep_working,
                           bounds    = bounds,
                           args      = self._state , 
                           options   = options,  
                           tol       = optimizer['tolerance'])
    
        self._state['message'] = result['message']
        self._update_from_optimization()#result)
        #################################################################################

        if verbose:
            print('allocation = {} Tau = {} Taup = {} '.format(self.allocation, self.tau, self.taup) )
            print('Finalized. Time(s) = {}'.format( self._state['elapsed_time']))

        return self.optimization_result                 

    def prediction_calculations(self, inj,prod ,prod_press ):
                

        invI, invP, invDP, invDates = self._get_matrices ( inj,prod,prod_press)


        #the matrix invI concatenates the production rates + tau * BHP + qo ( last column )
        invI = np.concatenate( (invI,                               #gain                                  
                                np.zeros( shape=(invI.shape[0],1)), #dp
                                np.zeros( shape=(invI.shape[0],1))),#qo  
                              axis=1) 
        

        
        qo, dt, lambdas, tau, taup = self._state['qo'], self._state['dt'], self._state['lambdas'].flatten(),self._state['tau'],self._state['taup']

        #the matrix invI concatenates the production rates + tau * BHP + qo ( last column )
        last_column = invI.shape[1]-1        
        invI[ :,  last_column - 1] = tau * invDP[:,0] 
        invI[ :,  last_column ] = 0.0

        #these are the individul contributions series -without the primary-. 
        pred_series = self._compute_pseudo_flow_matrix(invI, tau, dt) 

        #primary 
        time_steps = invI.shape[0]    
        inv_primary = np.array([ -dt*(1+n)/taup for n in range(time_steps)]) 
        inv_primary = qo * np.exp(inv_primary ).reshape( invP.shape )
        
        last_column = pred_series.shape[1]-1
        pred_series[ :,  last_column ] = inv_primary[:,0]

 
        #now the only thing to do is to multiply the prediction series times the lambdas
        Q = lambdas * pred_series


        return Q, invI, invP, invDP 
  
    def predict( self  ):

    
        data = self._data 
 

        if data is None: 
            raise ValueError('[predict] The fit_preprocess step was not done or it failed. Predictions arent possible') 

        if self.optimization_result is None:
            raise ValueError('[predict] The fit_preprocess and/or fit step was not done or it failed. Predictions arent possible') 
        
        if len(self.optimization_result) <1:
            raise ValueError('[predict] The fit_preprocess step was not done or it failed. Predictions arent possible') 
        
 
        tdate1, tdate2, tdate3 = np.datetime64( self._state['tdate1']), np.datetime64( self._state['tdate2']), np.datetime64( self._state['tdate3']) 
        dates = pd.to_datetime(data.water_injection.index).values 
        testing_mask = (dates >= tdate1) & (dates <= tdate3)
        

        inj, prod  = data.water_injection[testing_mask], data.liquid_production[testing_mask]
        prod_press = data.producer_pressure[testing_mask] if data.producer_pressure is not None else None 
        if prod_press is None: 
            prod_press= np.zeros ( shape= (inj.shape[0], 1) )
            self._state['last_prod_press'] = 0.0 
 
        else:
            self._state['last_prod_press'] = float(prod_press.values[ prod_press.shape[0]-1 ])
                 

        #check must equal tdate1 
        qo_date = self._state['qo_date'] 
        Q, invI, invP, invDP = self.prediction_calculations(inj, prod, prod_press )
        
    


        ##################################################################
        #prediction reselts. These are consumed by Koval and also exported
        ##################################################################
        lambdas, tau, taup = self._state['lambdas'].flatten(),self._state['tau'],self._state['taup']

        #primary support 
        primary_support = Q[:,-1:] #the last column is the primary contribution

        #for crmp, the last - 1 is the producer pressure, if none, then it is zero 

        
        #dates for the time series and slicing of some input data also reported 
        values_dates = pd.Series( inj.index ).values[1:] 
        
        #total water injected (only the lambdas part, dont include the J's as in the paper)
        water_injected  = np.sum(Q[:,0:len(lambdas)-2], axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 

        Q = np.sum( Q , axis = 1 ).reshape( invI.shape[0],1)
        df  = pd.DataFrame({
            LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX: Q.flatten(), 
            CUMMULATIVE_WATER_INJECTED_KEYS[0] + SIM_SUFFIX:water_injected.flatten(),     
            DATE_KEYS[0] :  values_dates,   
            LIQUID_PRODUCTION_KEYS[0]: invP.flatten(),
            PRIMARY_SUPPORT_KEYS[0]:primary_support.flatten()
            })
        
        if data.water_production is not None: 
            mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate3))
            w = data.water_production[1:]
            w = w[ pd.to_datetime(w.index) >= np.datetime64(tdate1) ]
            w = w[ pd.to_datetime(w.index) <= np.datetime64(tdate3)]
            df[ WATER_PRODUCTION_KEYS[0]] = w.values.flatten()
        
        df.set_index( DATE_KEYS[0], drop = True, inplace= True)
        df['NAME'] = self._state['producer_names'][0]     

        mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate2))
        df['TRAIN'] = mask
        df['ID'] = np.arange(0,df.shape[0],1)


        df1 = pd.DataFrame( {} )
        injector_names = self._state['injector_names']
        df1['INJECTOR'] =  injector_names
        df1['PRODUCER'] =  len(injector_names)*[ self._state['producer_names'][0] ]   
        df1[ALLOCATION_KEYS[0]]     =  list(lambdas)[0:len(lambdas)-2]
        df1['tau']   = len(injector_names)*[ tau ]   
        df1['taup']  = len(injector_names)*[ taup ] 
        df1[PRODUCTIVITY_KEYS[0]]  = len(injector_names)*[ self._state['Productivy'] ]     
        df1[PRIMARY_SUPPORT_KEYS[0] ]  = float( lambdas[-1:] ) 
        df1['MODEL']  = len(injector_names)*[ self.name ] 
        df1['ID'] = np.arange(0,df1.shape[0],1)

        d = {}
        d['crm'] = df1 
        d['rates'] = df 
        d['optimization'] = self.optimization_result 


        self.prediction_result = d

        return d 
 
    def forecast( self, water_injection_df, producer_pressure_df = None ):

     
        data = self._data 
        if data is None: 
            raise ValueError('[fortecast] The fit_preprocess step was not done or it failed. Predictions arent possible') 

        if self.prediction_result is None: 
            raise ValueError('[fortecast] The predict step was not done or it failed. Forecasts arent possible') 
        


        tdate1, tdate2 , tdate3 = np.datetime64( self._state['tdate1']),  np.datetime64( self._state['tdate2']),  np.datetime64( '2200-01-25' )
        dates = pd.to_datetime(water_injection_df.index).values 
        forecast_mask = dates >= tdate1

 
        inj  = water_injection_df[forecast_mask]
        prod = np.zeros ( shape= (inj.shape[0], 1) )
        prod_press = producer_pressure_df[forecast_mask] if producer_pressure_df is not None else None 
        
 
        #no bhp used in training 
        if self._state['bhp'] == False: 

            prod_press= np.zeros ( shape= (inj.shape[0], 1) )


        #bhp was used in training but if no bhp passed to forecast, will assume that the last known value is kept 
        #if bhp was used in training and it is passed to the forecast, then it will be used as expected. 
        else:
            if prod_press is None:  
                #print('bhp used in training but not passed to the forecast, so the last value known will be used.')
                prod_press= self._state['last_prod_press'] * np.ones ( shape= (inj.shape[0], 1) )

        #now the usual stuff: get the parameters, assembly the matrices, and predict 
        Q, invI, invP, invDP = self.prediction_calculations( inj,prod ,prod_press)

      
    
        ##################################################################
        #prediction results.  
        ##################################################################
        lambdas, tau, taup = self._state['lambdas'].flatten(),self._state['tau'],self._state['taup']
        values_dates = pd.Series( inj.index ).values[1:] 
        

        #total water injected (only the lambdas part, dont include the J's as in the paper)
        water_injected  = np.sum(Q[:,0:len(lambdas)-2], axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 

        Q = np.sum( Q , axis = 1 ).reshape( invI.shape[0],1)
        df  = pd.DataFrame({
            LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX: Q.flatten(), 
            CUMMULATIVE_WATER_INJECTED_KEYS[0] + SIM_SUFFIX:water_injected.flatten(),     
            DATE_KEYS[0] :  values_dates
            })
        


        df.set_index( DATE_KEYS[0], drop = True, inplace= True)
        df['NAME'] = self._state['producer_names'][0]     

        train_mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate2))
        df['TRAIN'] = train_mask
        df['ID'] = np.arange(0,df.shape[0],1)
        d = {}
        d['rates'] = df 

        self.forecast_result = d 
        return self.forecast_result 
     
    def set_parameters( self, lambdas, tau, taup ):

        self._state['lambdas'] = lambdas 
        self._state['tau'] = tau
        self._state['taup'] = taup
        
        n_params = len( lambdas )
        self._state['Primary support coeff'] = lambdas[n_params-1]
        self._state['Productivy'] = lambdas[n_params-2]
        self._state['Allocation'] = lambdas[0:-2]

        return self
        
    def evaluate_error( self, lambdas=None, tau=None , taup=None ):

        if lambdas is None:lambdas = self._state['lambdas']
        if tau  is None: tau  = self._state['tau'  ]
        if taup is None: taup = self._state['taup' ]
        
  
        invP = self._state['invP']
        pred_series = self._get_P_matrix( tau , taup )
        Q = lambdas * pred_series
        Q = np.sum( Q , axis = 1 ).reshape( invP.shape )

        error_metric =  root_mean_squared_error(invP, Q)#   
        #error_metric = mean_squared_error(invP, Q, squared=False)# if self._state['integrated']==False else integrated_error(invP, Q, squared=False)
        
        return  error_metric

    def set_internal_state_from_json( self, optimization_result ):
    
        '''
        Sets the internal state, except the matrices from json-saved optimization results.
        
        '''
        if isinstance(optimization_result, str ):
            s = dict( json.loads( optimization_result ) )
            
        else:
            s = optimization_result 
        
        #for CRMP
        if 'Allocation' in s:  s['Allocation'] = np.array(s['Allocation'])     
        if 'allocation' in s:  s['allocation'] = np.array(s['allocation'])     
        if 'lambdas'    in s:  s['lambdas'] = np.array(s['lambdas'])     
        if 'start_time' in s:  s['start_time'] = np.datetime64(s['start_time'])     
        if 'qo' in s: s['qo']  = np.array(s['qo'])

        
        self._state = {} 
        self._state.update( s )
        self.has_bhp = self._state['bhp'] #doesnt seem to be needed  
        self.optimization_result = optimization_result


        
        

    ###########################################
    ###              private API         ######  
    ###########################################
    
    def _compute_pseudo_flow_matrix(self, invI, tau, dt):
        
        time_steps = invI.shape[0]      
        window_size = 5 + int(5.0 * tau )
        E = np.flip(CRMHelper.get_row_vector_E(tau,dt, time_steps))
        pseudo_flow = np.zeros ( (time_steps,invI.shape[1]) )
        
        for tn in range( time_steps ):
            
            io = max(0, tn + 1 - window_size )
            Iview = invI[ io:tn+1,:]
            
            Eview = E[0,-Iview.shape[0]:]
            pseudo_flow[tn] = np.dot(Eview,Iview) 
          
        return pseudo_flow
        
    def _process_args(self, input_args = None ):
   
        def extract_date( s ):
            if s is None: return None 
        
            chars = ['-','/','\\',',']
            for char in chars: 
                if char in s: 
                    y,m,d= s.split(char)
                    return date( int(y),int(m),int(d))
            return None 

        if input_args is None: input_args = {}
        
        args = self.get_default_params()
        
        #the optimizer 
        if 'optimizer' in input_args: args['optimizer'].update( input_args['optimizer'] )
        args['optimizer']['name'] = optimizers_name_map[ args['optimizer']['name'].lower() ]   
        
        #pre-optimizer 
        if 'pre_optimizer' in input_args: args['pre_optimizer'].update( input_args['pre_optimizer'] )
        args['pre_optimizer']['name'] = optimizers_name_map[ args['pre_optimizer']['name'].lower() ]       
        
        #dates 
        if 'dates' in input_args:
 
            dates = input_args['dates']
            if len(dates) < 3: 
                dates.append('2200-11-20')

            args['dates'] = dates
            date1, date2,date3 = extract_date(args['dates'][0]), extract_date(args['dates'][1]), extract_date(args['dates'][2])

            if (date1 is None) and (date2 is None): args.pop( 'dates' )
                
            else:
                if (date1 is not None) and (date2 is not None): date1, date2 = sorted( [ date1, date2] ) 
                elif date1 is None: date1 = date.min
                elif date2 is None: date2 = date.max
                else: pass
                
                date1,date2 = sorted([date1,date2])
                args['dates'] = [ date1, date2,date3 ]
            

        #parameters tau and taup 
        if 'parameters' in input_args:
            if 'tau'  in input_args['parameters']: args['parameters']['tau']  = input_args['parameters']['tau']
            if 'taup' in input_args['parameters']: args['parameters']['taup'] = input_args['parameters']['taup']
                
        #time step
        if 'dt' in input_args: args['dt'] = input_args['dt']
        if 'max_running_time' in input_args: args['max_running_time']  = input_args['max_running_time']
        if 'maxiter' in input_args: args['maxiter']  = input_args['maxiter']
 
        #the error metric
        if 'integrated' in input_args: 
            args['integrated'] = input_args['integrated']
    
        if 'primary' in input_args: 
            args['primary'] = input_args['primary']
    

        #other keys that may be related to multi-well 
        for key,value in input_args.items():
            if key in args:
                pass
            else:
                args[key] = value 
                
            

        return args
   
    def _get_P_matrix(self, tau , taup ):


        'The Q matrix, once multiplied by lambdas and summed along 1 is yhat'
        state = self._state 
        invI, invDP, invP,dt,qo = state['invI'],state['invDP'],state['invP'],state['dt'],state['qo']

        #the matrix invI concatenates the production rates + BHP + qo ( last column )
        #that Pressure column needs to be multiplied by +tau
        last_column = invI.shape[1]-1        
        invI[ :,  last_column - 1] = tau * invDP[:,0]  #pressure
        invI[ :,  last_column ] = 0.0                  #qo 
 
        pred_series = self._compute_pseudo_flow_matrix(invI, tau, dt) 

        #primary 
        time_steps = invI.shape[0]    
        inv_primary = np.array([ -dt*(1+n)/taup for n in range(time_steps)]) 
        inv_primary = qo * np.exp(inv_primary ).reshape( (time_steps,1) )
        pred_series[ :,  last_column ] = inv_primary[:,0]

        return pred_series
             
    def _loss(self, params, *args):
        
        #by convenction, tau and taup are the last two parameters. 
        tau,taup  = params[0], params[1]
        if tau < 0.001: tau = 0.001
        if taup < 0.001: taup = 0.001


        state = args[0]
        state['counter'] = state['counter']+1

        extra_loss = 1.0 
        pred_series = self._get_P_matrix( tau , taup)
        model = LinearRegression(positive=True,fit_intercept=False )
        invP = self._state['invP']
        reg = model.fit(pred_series, invP ) #fit coefficients for everythig   
        lambdas =  reg.coef_[0]#.flatten()  
        
        #print( lambdas.shape )
        #lambdas = lambdas.reshape( lambdas.shape[0],1)
        #large_lambdas =  np.array([ v if v > 1.0 else 0.0 for v in lambdas  ])
        #extra_loss =  1.0 + np.sum(large_lambdas**2)  
        #lambdas = np.array( [ v if v <= 1.0 else 1.0 for v in lambdas  ] )
        
        #primary support enforced to 1 
        #lambdas[ -1] = 1.0 
       
       

        yhat = (lambdas * pred_series).sum(axis=1).reshape( invP.shape )     
        error_metric =  root_mean_squared_error(invP, yhat)
        #error_metric = extra_loss * mean_squared_error(invP, yhat, squared=False)# if self._state['integrated']==False else integrated_error(invP, yhat, squared=False)
      
        state['rmse'] = error_metric
        state['r2'] = r2_score(invP, yhat)
        self.set_parameters( lambdas, tau, taup )
                  
        
        return error_metric 
       
    def _get_matrices( self,  inj, prod, prod_press = None ):
        
        num_time_steps = inj.shape[0]
        invI = CRMHelper._to_numpy(inj).reshape(num_time_steps,inj.shape[1])

        #can be zero when called as part of the forecast, where production is none
        if prod is None:
            invP = np.zeros ( shape= (invI.shape[0], 1) )
        else:
            invP = CRMHelper._to_numpy(prod).reshape(num_time_steps,prod.shape[1])
        
        invDates = CRMHelper._to_numpy( pd.Series(inj.index) ).reshape(num_time_steps,1)   
        
        #in many cases, there will be no BHP 
        if prod_press is None:
            invDP= np.zeros ( shape= (invI.shape[0], 1) )
            self.has_bhp = False
        else: 
            # P is really DP = [P1-Po, P2-P1, P3-P2,....] The Po value will be discarded. 
            prod_press  = CRMHelper._to_numpy( prod_press) #
            prod_press  = CRMHelper.shift_up(prod_press)-prod_press  
            invDP = -1.0*( prod_press.reshape( invI.shape[0],1))
            invDP[ invDP.shape[0] -1 ] = invDP[ invDP.shape[0] -2 ]
            self.has_bhp = True 
            
        #firs step is for the qo
        invI =  invI[1:invI.shape[0], :]  
        invP =  invP[1:invP.shape[0], : ]
        invDP =  invDP[1:invDP.shape[0], : ]
        invDates =  invDates[1:invDates.shape[0], :]     
            
        return invI, invP, invDP, invDates 

    def _pseudo_grid_search(self, params, bounds, options ):

        result = minimize(fun = self._loss, x0 = params, 
                          method= self._state['pre_optimizer']['name'],          
                          #callback=self._keep_working,
                          bounds = bounds ,
                          args=self._state , 
                          options = options, 
                          tol=self._state['optimizer']['tolerance'])

        self._state['message'] = result['message']
        lambdas = self._state['lambdas']
        tau     = self._state['tau']
        taup    = self._state['taup']
        return result, lambdas, tau, taup     
  
    def _format_prediction_results( self, water_production, Q, inj, invP, lambdas, tau, taup, tdate1, tdate3 ): 
  
        #primary support 
        primary_support = Q[:,-1:] #the last column is the primary contribution

        #for crmp, the last - 1 is the producer pressure, if none, then it is zero 
        prod_pressure = Q[:,-2:-1]
        
        #dates for the time series and slicing of some input data also reported 
        values_dates = pd.Series( inj.index ).values[1:] 
        
        #total water injected (only the lambdas part, dont include the J's as in the paper)
        water_injected  = np.sum(Q[:,0:len(lambdas)-2], axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 

        df  = pd.DataFrame({
            LIQUID_PRODUCTION_KEYS[0] + SIM_SUFFIX: Q.flatten(), 
            CUMMULATIVE_WATER_INJECTED_KEYS[0] + SIM_SUFFIX:water_injected.flatten(),     
            DATE_KEYS[0] :  values_dates,   
            LIQUID_PRODUCTION_KEYS[0]: invP.flatten(),
            PRIMARY_SUPPORT_KEYS[0]:primary_support.flatten()
            })
        
        if water_production is not None: 
            mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate3))
            df[ WATER_PRODUCTION_KEYS[0]] = water_production[mask].values 
        
        df.set_index( DATE_KEYS[0], drop = True, inplace= True)
        df['NAME'] = self._state['producer_names'][0]     


        df['ID'] = np.arange(0,df.shape[0],1)


        df1 = pd.DataFrame( {} )
        injector_names = self._state['injector_names']
        df1['INJECTOR'] =  injector_names
        df1['PRODUCER'] =  len(injector_names)*[ self._state['producer_names'][0] ]   
        df1[ALLOCATION_KEYS[0]]     =  list(lambdas)[0:len(lambdas)-2]
        df1['tau']   = len(injector_names)*[ tau ]   
        df1['taup']  = len(injector_names)*[ taup ] 
        df1[PRODUCTIVITY_KEYS[0]]  = len(injector_names)*[ self._state['Productivy'] ]     
        df1[PRIMARY_SUPPORT_KEYS[0] ]  = float( lambdas[-1:] ) 
        df1['MODEL']  = len(injector_names)*[ self.name ] 
        df1['ID'] = np.arange(0,df1.shape[0],1)

        d = {}
        d['crm'] = df1 
        d['rates'] = df 
        d['optimization'] = self.optimization_result 
        
        
        return d 
 

class old_CRMP(CRMModel):
    
    '''
    CRMP solver for multi-pattern. Patterns can be multi-producer or single producer ones. 
    '''
   
    def __init__(self ):
 
        super().__init__('CRMP' )
        self._clear()
        #self.failed_models = []
        
    def fit_preprocess( self, data, input_args = None ):
        '''
        After initialization, this is the first function that needs to be called in a CRM simulation.

        Here, the software stores the relevant information (matrices, tensors, names,etc) that are needed
        in the simulation. In this step, the arguments (optional) are also processed to determine, for instance,
        the trainning interval times and the testing interval

        Internally, the code splits the data in single-well patterns and calls SingleModel.fit_preprocess( ) for each.
        Single-well patterns for which the fit_preprocess doenst fail are stored for later simulation

        Errors are logged and appended to the model log.
        
        Note that the function returns -self- soi it can be chained wiith the fit method

        Example of use:

                from wf_lib.cdata.crm_pattern import CRMPattern 
                from wf_lib.models.crm_p import CRMP,CRMPSingle

                #generate some suynthetic data for testing
                pattern = CRMPattern().generate_default_multiwell_pattern()
                
                #create a model 
                model = CRMP()

                #train
                _= model.fit_preprocess( pattern )

                
        '''
        
        self.patterns,self.single_well_patterns, patterns   = None, None, None
        self.failed_models = [] 
        
        if isinstance(data, list ):         #option 1, a list of patterns 
            patterns = data 
            
        elif isinstance(data, CRMPattern ): #option 2, a single pattern
            patterns = [data]
                       
        else:
            raise ValueError( '[pre_process] Dont know what this data type is in fit_preprocess CRMP') 
            
        #for each pattern we have one set of parameters 
        args = None 
        if input_args is None: args =  len(patterns) * [self.get_default_params() ] 
        else:
            if not isinstance( input_args, list ):args = len(patterns) * [ input_args ]
            else: args = input_args
            if len(args) > len(patterns): args = args[0:len(patterns) ]
            elif len(args) < len(patterns): args = args.copy() + (len(patterns)  - len(args)) * [ self.get_default_params() ]      
        
      
        log = self.log 
        single_well_patterns = [] 
        success_count = 0 
        
        
        #one set of arguments per pattern which is copied to all its single-well sub-patterns
        for n,p in enumerate( patterns ):
            singles = p.multi_well_to_single()
            
            for id_, single in enumerate( singles ):     
                try:
                    model = self._get_submodel()#CRMPSingle()
                    model._name = self._name 
                    
                    args[n]['prod_id'] = id_
                    args[n]['pattern_id'] = n 
                    
                    #if id_==0:
                    #    raise ValueError('Hard code failure for model ==0 ')
                    
                    model.fit_preprocess( single, args[n] )
                    
                    model.producer_name  = single.producer_names[0]
                    model.injector_names = single.injector_names  
                    single_well_patterns.append(single)
                    self.models.append( model )
                    success_count = 1 + success_count

                    #log.extend( model.log )

                except Exception as e:
                    self.failed_models.append( (single.producer_names[0],'preprocessing ' + str(e)) )
                    
                    s=' pattern ' + str(n) + ' id ' + str(id_)
                    print(str(e)+s)
                    log.append('****error [fit_preprocess]' + s )
                    #log.extend( model.log )
                    log.append( str(e) + s )
                    
                    
        
        if success_count > 0:
            self.patterns = patterns
            self.single_well_patterns = single_well_patterns
        else:
            self.single_well_patterns = None 
            self.patterns = None 
            
        
        print('leaving prefit with a nuber of models ', len(self.models) )
        self.optimization_result = []
         
        
        return self
    
    def fit(self, serial = True,  balance = None  ):
        '''
        
        Once the model is initialized (fit_preprocess), this method carries-out the optimization.
        Note in the code below, that fit is chained (optionally) to fit_preprocess so the training 
        and data processing can be done in a single step. 
        
        Example of use:

                from wf_lib.cdata.crm_pattern import CRMPattern 
                from wf_lib.models.crm_p import CRMP,CRMPSingle

                #generate some suynthetic data for testing
                pattern = CRMPattern().generate_default_multiwell_pattern()
                
                #create a model 
                model = CRMP()

                #train
                optimization_result = model.fit_preprocess( pattern ).fit( )
                
                #print the results 
                optimization_result

            Result: 
                
                [{'message': 'Optimization terminated successfully.',
                'dates': [datetime.date(1950, 9, 23), datetime.date(2200, 1, 28)],
                'parameters': {'tau': {'bounds': (1, 50), 'init_value': 5.0},
                'taup': {'bounds': (1, 50), 'init_value': 5.0}},
                'max_running_time': 1000.0,
                'optimizer': {'maxiter': 1000, 'name': 'Nelder-Mead', 'tolerance': 0.001},
                'pre_optimizer': {'name': 'TNC'},
                'integrated': False,
                'crm_model': 'CRMP',
                'qo': [827.9422766501973],
                'injector_names': ['Inj0', 'Inj1', 'Inj2', 'Inj3'],
                'producer_names': ['Producer1'],
                'elapsed_time': 0.479247,
                'bhp': False,
                'rmse': 0.6273988592066048,
                'r2': 0.9998389519936466,
                'lambdas': [0.6023967254047103,
                0.4947917686337314,
                ...
                ],
                'tau': 16.600374237437986,
                'taup': 13.43
                
                ...},
                {'message': 'Optimization terminated successfully.',
                ...
                }
                {'message': 'Optimization terminated successfully.',
                ...
                }
                ]
                
        '''
        print(  print('entering fit with a nuber of models, failed ', len(self.models), len(self.failed_models) ))
        
        self.prediction_result = {}

        def CRMPSingleSolver( n ):

            m,r = self.models[n], {} 
           
            try:
                r = m.fit()
                               
            except Exception as e: 
                #self.failed_models.append( (m.producer_name,'fit: ' + str(e)) )        
                r = {'message': 'Error ' + str(e)}


  
            return n,r,m
        
        
        if self.single_well_patterns is None:
            print('Cannot fit the data, patterns not defined in a pre-process step')
            self.optimization_result = []
            return []
        
        self.optimization_result = []
        models_to_delete = [] 
        
        
        if serial == True: 
            
            self.log.append('serial fitting started')
            for i, m in enumerate ( self.models ):
                r = {}
                try:
                    
                    #if i == 0:
                    #    raise ValueError('Hard-coded failure for model in fit == 0 ')
                    
                    r = m.fit(  )

                except Exception as e:
                    r = {'message': str(e) }
                    self.log.append( str(e) )
                    self.failed_models.append( (m.producer_name,'fit: ' + str(e)) )
                    models_to_delete.append( m )
                    
            
                self.optimization_result.append( r )   
                self.log.append(f'fit model {i}, progress {100.0*(1+i)/len(self.models)}')
            

        else:
            self.log.append('parallel fitting started')
            num_producers = len( self.models )
            num_cpus =  max( mp.cpu_count(), min( num_producers, mp.cpu_count() ))
            
            models = self.models 
            results  = Parallel(n_jobs=num_cpus)(delayed(CRMPSingleSolver)
            ( n ) for n in range( len(models) ))   
            
     
            for i,item in enumerate( results ): 
            
                n,r,forked_model   = item

                self.models[n] = forked_model
                self.models[n].optimization_result = r
                
                
            self.optimization_result = [] 
            #####self.models_ids = { }
            for m in self.models: 
                r = m.optimization_result
                
                # when running in parallel we run a forked model, which makes hard to track failures in the 
                # same way that the serial case.
                # in the serial we get an exception and we handle it. Here we just get r as a dictionary and 
                # try to find the word 'error' under the message key 
                if 'error' in r['message']: #rtreat is as an exception
                    self.log.append( r['message'] )
                    self.failed_models.append( (m.producer_name,'fit: ' + r['message'] ) )
                    models_to_delete.append( m )
                 
                self.optimization_result.append( r )  
                
           
           
        for item in models_to_delete: 
            print('deleting a model ', m.producer_name )
            self.models.remove( item )
            
        self.log.append('fitting finished')
        
        if balance is None:
            self.log.append('no-balancing done')
             
        elif isinstance(balance, str):
            print('balancing string....')
            if balance.lower() == 'full':
                print('full balancing')
                self.log.append('doing a full balance')
                self.balance('full' )
                self.log.append('balancing done')
                
            elif balance.lower() == 'quick':
                self.log.append('doing a quick balance')
                self.balance('quick')
                self.log.append('balancing done')
        
            else:
                self.log.append('no-balancing done')
             
        else:
            self.log.append('no-balancing done')
             
        print('leaving fit with a nuber of models ', len(self.models) )
          
        self.prediction_result['optimization']  = self.optimization_result
        return self.optimization_result
    
    def predict( self  ):
        
        self.prediction_result  ={}
        _predictions = [] 
        
        models_to_delete = [] 
        self.log.append('prediction started')
        for i,m in enumerate(self.models):
            
            try:
                
                #if i == 0: 
                #    raise  ValueError('Hard-coded failure for predict id == 0 ')
                
                p = m.predict( )  
                r = m.optimization_result               
                #p['rates']['id'] = r['id']
                #p['crm']['pattern_id'] = r['pattern_id']
                
                p['rates']['prod_id'] = r['prod_id']
                p['rates']['pattern_id'] = r['pattern_id']
                
                p['crm']['pattern_id'] = r['pattern_id']
                p['crm']['prod_id'] = r['prod_id']
                
                
                _predictions.append( p ) 
                self.log.append(f'prediction for model {i} finished, progress {100.0*(1+i)/len(self.models)}')
                
            except Exception as e:
                self.log.append( 'Prediction failed ' + str(e) )
                self.failed_models.append( (m.producer_name,'predict: ' + str(e)) )
                for item in models_to_delete:
                    self.models.remove( item )
                    
                print('failed predictions:',str(e)  )
      
        try:
            rates = [ p['rates'] for p in _predictions ]
            if len(rates)>0: rates = pd.concat( rates, axis = 0 )
            self.log.append('rates processed')

            crms = [ p['crm'] for p in _predictions ]
            if len(crms)>0: crms = pd.concat( crms, axis = 0 )
            self.log.append('crm results processed')

            crms['ID'] = np.arange(0,crms.shape[0],1)
            crms.set_index( 'ID', inplace = True, drop = False  )
            rates.sort_values('DATE')['ID'] = np.arange(0,rates.shape[0],1)


            self.prediction_result = { 'crm': crms, 'rates': rates , 'optimization':  self.optimization_result }
            self.log.append('prediction results processed')

        except Exception as e:
            self.log.append('processing prediction results failed')
            

        return self.prediction_result
         
    def balance(self, balance_type = 'quick'):

        def _get_successful_models():# self ):
            '''Go through the optimization results of the model and 
            returns the list of models and optimization results for which 
            the word success was found in the messsge. The rest are discarded.
            '''
            opts, success_models = [], [] 
            for m in self.models:
                if 'success' in m.optimization_result['message']:
                    opts.append(  m.optimization_result )
                    success_models.append( m )

            return opts, success_models
        
        def _get_off_balance_injectors():# self ):
            '''
            Returns a dictionaty with keys the injector names and as values the producers linked to those
            injectors and the total allocation, if the allocation sum is greater than 1. 
            '''
            opts, _= _get_successful_models( )#self ) 
            d = {}
            for opt in opts:
                producer    = opt['producer_names'][0]
                injectors   = opt['injector_names']
                allocations = opt['allocation']
                for i,injector in enumerate( injectors ):
                    if injector not in d.keys(): d[injector] = {'producers':[],'allocation':0.0 }
                    d[injector]['producers'].append( (producer, i, allocations[i] )  )
                    d[injector]['allocation'] = d[injector]['allocation'] + allocations[i]

            d = { item:value  for item,value in d.items() if value['allocation'] > 1.0 }
            return d
        
        def _balancer_loss( params, *args ):

            opts = args[0]
            sub_models = args[1]
            error = 0.0 
            x = None 

            for n,sub_model in enumerate(sub_models):

                #get the indices in the global list of the parameters for the model
                r = opts[ n ]
                model_parameters = r['parameter_index']

                #the current value of all of these 
                vals = params[ model_parameters ] 
                tau, taup = vals[-2:]
                lambdas   =  vals[0:-2]
                sub_model.set_parameters( lambdas, tau, taup )

                #now evaluate the model error 
                e = sub_model.evaluate_error()# lambdas, tau, taup )
                error = error + e 
                
                     
                sub_model._state['rmse'] = error
                sub_model._update_from_optimization()

                    

            return error 

        
        def _construct_balancing_matrices( optimization_results ):

            parameter_counter,injector_constraints, bounds, init_values = -1, {}, [], [] 

            #for each single=wel model = item 
            for item in  optimization_results :

                #each of its parameters will have an index in a global list 
                item['parameter_index'] = [] 
                injector_names = item['injector_names']
                num_injectors = len( injector_names )

                #all the coefficients allocs + J + qo 
                well_parameters = item['lambdas'] # CRMP[ [lambdas-injectors(ninj), productivity(1), qo(1)]]
                extras = 0    

                for n,value in enumerate(well_parameters):#for allocs [ value1, value2,...] + J [1] and qo [1] 

                    parameter_counter = parameter_counter + 1 
                    item['parameter_index'].append( parameter_counter )

                    if n < num_injectors:                   #allocations  

                        if injector_constraints.get( injector_names[n], None ) is None: 
                            injector_constraints[injector_names[n]] = [] 

                        injector_constraints[injector_names[n]].append( parameter_counter )
                        bounds.append( (0.0,1.01) )
                        init_values.append( value )

                    else: #productiviy and qo. Productivity is one value for CRM-P same for qo, tau and taup 

                        if extras == 0 :                    #productivity                         
                            init_values.append( value )
                            bounds.append( (0.0,value*1.5+0.01) )
                            extras = 1 

                        else:                               #qo 
                            bounds.append( (0.0,1.05) )
                            init_values.append( value )

                #now tau and taup 
                tau_bounds, taup_bounds = item['parameters']['tau']['bounds'], item['parameters']['taup']['bounds']
                bounds.extend( [( tau_bounds[0],tau_bounds[1]), ( taup_bounds[0],taup_bounds[1])]  )
                item['parameter_index'].extend( [parameter_counter+1,parameter_counter+2 ] )
                parameter_counter = parameter_counter+2
                init_values.extend( [ item['tau'],item['taup'] ] )

            return injector_constraints, bounds, init_values,parameter_counter


        ######################################################################################
        
        if self.optimization_result is None or len(self.optimization_result)<1:
            s = '[balance] Cannot balance the data, either a call to fit() failed or it was never called.' 
            print(s) 
            raise ValueError(s)
            
        
        off_balance = _get_off_balance_injectors( )#self ) 
        if( len( off_balance ) < 1):
            print('Nothing to balance')
            return { 'message': 'success: Nothing to balance'} 


        opts, success_models =  _get_successful_models()#self)
        
        if (balance_type == 'quick') or (balance_type == 'full'):
        
                         
            for i, item in enumerate( off_balance.items() ):

                inj_name, producers, allocation = item[0], item[1]['producers'], item[1]['allocation']
                delta = (allocation-1.0)/len(producers)
                
                if delta > 0.01:

                    scaling_factor = 1.0 / allocation
                    producer_names = [ item[0] for item in producers]
                    for m in self.models: 
                        if m._state['producer_names'][0] in producer_names:
                            index = m._state['injector_names'].index( inj_name )
                            m._state['lambdas'][index]  = m._state['lambdas'][index] * scaling_factor
                            error = m.evaluate_error()
                            m._state['rmse'] = error
                            m._update_from_optimization()
                            
            self.optimization_result = [] 
            for m in self.models: 
                r = m.optimization_result
                self.optimization_result.append( r )       
                
            '''
            for i, item in enumerate( off_balance.items() ):

                inj_name, producers, allocation = item[0], item[1]['producers'], item[1]['allocation']
                delta = (allocation-1.0)/len(producers)

                if delta > 0.01:

                    producer_names = [ item[0] for item in producers]
                    for m in self.models: 
                        if m._state['producer_names'][0] in producer_names:
                            index = m._state['injector_names'].index( inj_name )
                            m._state['lambdas'][index]  = m._state['lambdas'][index] - delta  
                            error = m.evaluate_error()
                            m._state['rmse'] = error
                            m._update_from_optimization()


            self.optimization_result = [] 
            for m in self.models: 
                r = m.optimization_result
                self.optimization_result.append( r ) 
                
            '''         
            if balance_type == 'quick':
                return { 'message': 'success. Quick balancing done'} 
        
        if balance_type.lower() == 'full':
            
            inj_constraints, bounds, init_vals,param_count = _construct_balancing_matrices( opts )
            init_vals = np.array( init_vals )
            inj_constraints = np.array( list( inj_constraints.values())) 
            num_contraints = inj_constraints.shape[0]
            ub = np.array( (num_contraints) * [1.0] )
            lb = np.array( (num_contraints) * [0.0] )

            param_count = param_count + 1 #starts with zro 
            A = np.zeros( shape = (inj_constraints.shape[0],param_count) )
            for n in range( inj_constraints.shape[0] ): A[n,inj_constraints[n]] = 1.0

            #return  opts,success_models, A, ub,lb, inj_constraints, bounds, init_vals,param_count


            state = (opts,success_models) 
            options = {'maxiter': 1000 }
            linear_constraint = LinearConstraint( A, lb, ub ) 
            result = minimize( fun       = _balancer_loss, 
                               x0        = init_vals, 
                               method    =  'SLSQP', #"trust-constr",# 'COBYLA','SLSQP', #          
                               bounds    = bounds,
                               constraints=linear_constraint,
                               args      = state , 
                               options   = options,  
                               tol       = 0.01 )


            self.optimization_result = [] 
            for m in self.models: 
                r = m.optimization_result
                self.optimization_result.append( r ) 

            return result 
  
    def set_internal_state_from_json( self, s ):
        '''
        Restores a model for prediction (or forecast)
        from its previous representation of prediction['optimization'] as 
        a json string. self.prediction_results['optimization'] should be available as soon as the model is fit. 
        '''
        pass 

    def _get_submodel( self ):
        return CRMPSingle()

    def forecast( self, water_injection_df, producer_pressure_df = None ):
        
        forecasts = [] 
        models = self.models
        self.log.append('forecast started')
        self.forecast_result = None 

        for n,m in  enumerate( models ):

            try:
                print('doing forecast for model',n )
                producer_name, injector_names = m._state['producer_names'][0], m._state['injector_names']   
                water    = water_injection_df[injector_names]
                if water.shape[1] < 1: 
                    raise ValueError(f'[forecast] Injector names not found in the water injection table for model {n}' )

                pressure = None if producer_pressure_df is None else producer_pressure_df[[producer_name]]

  
                ff = m.forecast( water, pressure )
                forecasts.append( ff )
                self.log.append( f'--Done forecast for producer {producer_name} [{n+1}] out of {len(models)}' )

            except Exception as e:
                s = f'[forecast] Error in forecast model {n}: {str(e)}'
                print(s)
                self.log.append( s )

        self.forecast_result = {}
        self.forecast_result['rates'] = pd.concat( [single_forecast['rates'] for single_forecast in forecasts ], axis = 0 ) 
        self.log.append('forecast finished')      

        return self.forecast_result 


    
    
'''
#balancing example 
config = {
            'days': 350,
            'allocation': [0.80,0.70, 0.6,0.4], #num injectors, each element is a producer-injector pair   
            'tau': 16.43 , #one producer 
            'dt': 1.0, 
            'inj_noise_level': 0.0000050, 
            'injectors': [ {'max_rate': 0.40e3, 'min_rate': 0.25e3, 'internal_length':4, 'location':  (1000,0) }
                           ,{'max_rate': 0.3e3, 'min_rate': 0.15e3, 'internal_length':8, 'location' :  (0,1000)},
                          {'max_rate': 0.4e3, 'min_rate': 0.1e3, 'internal_length':8, 'location' :  (-1000,0)},
                          {'max_rate': 0.23e3, 'min_rate': 0.15e3, 'internal_length':12, 'location':  (0,-1000)}
                          
                         ],
            'prod_noise_level': 0.000008, 
            'prod_outlier_freq': 0.000008 ,
            'producer_location' : (0,0),
            'primary_production': {'qo': 0.8e3, 'taup':13.5}
        }

p = CRMPattern().generate_default_multiwell_pattern(config)
 
model =  CRMP()
sim_params = model.get_default_params()
sim_params['balance'] = 'full'
sim_params
_= model.fit_preprocess( p )
result = model.fit( balance='full') 


r = model.prediction_result['crm']
r[r['INJECTOR'] == 'Inj0' ]

	INJECTOR	PRODUCER	allocation	tau	taup	productivity	Lo	MODEL	ID	pattern_id	prod_id
ID											
0	Inj0	Producer1	0.621510	1.459647	50.000000	0.0	0.261972	CRMP	0	0	0
4	Inj0	Producer2	0.303676	2.011688	50.000000	0.0	0.337921	CRMP	4	0	1
8	Inj0	Producer3	0.074814	34.462742	27.238201	0.0	0.936737	CRMP	8	0	2


model.prediction_result['crm'].groupby( by =['INJECTOR'] )['allocation'].sum()

INJECTOR
Inj0    1.0
Inj1    1.0
Inj2    1.0
Inj3    1.0
'''
 