import numpy as np, pandas as pd, math, multiprocessing as mp
from datetime import date, datetime, timedelta
from joblib   import Parallel, delayed

from sklearn.metrics      import r2_score,root_mean_squared_error


from sklearn.linear_model import Ridge, Lasso, LinearRegression
from scipy.optimize       import minimize, Bounds,LinearConstraint


from   wf_lib2.crm_definitions   import * 
from   wf_lib2.data.crm_dataset import CRMDataset
from   wf_lib2.models.crm_model  import CRMSingleModel, CRMModel
#from   wf_lib2.models.crm_model import integrated_error
from   wf_lib2.crm_helper        import CRMHelper 
from   wf_lib2.data.crm_pattern  import CRMPattern
from   wf_lib2.data.crm_data_utils  import * 




class CRMIPSingle(CRMSingleModel):
    
    '''
    CRMIP solver for single-producer patterns. This class shouldnt be instantiated in the general case.
    The CRMIP class defined below should be used instead. The CRMIPSingle exists only as support for the 
    CRMIP class. 
    '''
    
    def __init__(self, input_args = None ):
        super().__init__( 'CRMIPSingle')
        self._clear()
                
    def get_default_params( self ): 
        args = {
            'dates': ['1950-09-23','2200-01-28'],
            'parameters': {
                'tau': [ {'bounds': (0.1,50), 'init_value': 5.0} ],
                'taup':  {'bounds':(0.1,50), 'init_value': 5.0}
            },


            'dt': 1.0,
            'max_running_time': 2000.0,
            'optimizer': {'maxiter': 2000,'name': 'Nelder-Mead', 'tolerance': 1e-04},
            #'optimizer': {'maxiter': 2000,'name': 'SLSQP', 'tolerance': 1e-04},
            
            'pre_optimizer': {'name': 'TNC'},
            
            'distance': 2000.00
            #'integrated': False,
            #'primary':True 
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
    

    def fit_preprocess(self, pattern, input_args=None, verbose=False):
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
        self.log.append(  f'fit_preprocess for {names}' )

        args = self._process_args( pattern, input_args )

        #returns the same pattern object received (same memory id) but modified 
        #from args, it only uses {dates:['date1', 'date2']}
        #the resulting pattern is stored internally as _data 
        pattern, tdate1, tdate2, tdate3, inj, prod, qo,qo_date = self.fit_preprocess_pattern( pattern, args )
    
    
        #if args['primary'] is False:
        #    qo = 0.0 
            
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
        self.log.append(  'fit_preprocess finished' )
        
  
  
        return self 
   

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
        
        
        self._state['bhp']      = self.has_bhp
        self._state['invI']     = invI
        self._state['invP']     = invP
        self._state['invDP']    = invDP
        self._state['invDates'] = invDates

       
        #optimization parameters and bounds 
        parameters = self._state['parameters']
        taus = parameters['tau']
        init_tau  = [ item['init_value'] for item in taus ]
        init_taup = parameters['taup']['init_value'] 
        init_values = list(init_tau) + [init_taup ]
        
        tau_bounds  = [ item['bounds'] for item in taus ]
        taup_bounds = parameters['taup']['bounds'] 
        bounds = tau_bounds + [ taup_bounds ]
        
        max_iter = self._state['optimizer']['maxiter']
        options = {'maxiter':max(max_iter, 10*invI.shape[1]), 'disp':verbose}
        
       
        
        result, lambdas, tau, taup  = self._pseudo_grid_search( init_values, bounds, options )
        self._update_from_optimization( )#result ) 
        
        #quick fit, dont do the second optimization
        if quick:

            if verbose:
                print('allocation = {} tau = {} taup = {}'.format(lambdas, tau, taup) )
                
            return self.optimization_result 
        
        if verbose: 
            print('Optimization started after pre-conditioning. Initial conditions for tau',tau, taup )
             
              
        #args = self.args  
        params = list( tau )
        params.append( taup )
        options = {'maxiter':max(max_iter, 10*invI.shape[1]), 'disp':verbose}
        result = minimize(fun = self._loss, x0 = params, 
                           method= self._state['optimizer']['name'],         
                           callback=self._keep_working,
                           options = options, 
                           bounds = bounds,
                           args=self._state , 
                           tol=self._state['optimizer']['tolerance'])

        #print( self._state['Allocation'])
        
        self._state['message'] = result['message']        
        self._update_from_optimization()#result)
        #################################################################################

        if verbose:
            print('allocation = {} Tau = {} Taup = {} '.format(self.allocation, self.tau, self.taup) )
            print('Finalized. Time(s) = {}'.format( self._state['elapsed_time']))

        return self.optimization_result   
    
    def prediction_calculations(self, inj,prod ,prod_press ):

        dt,lambdas,tau, taup = self._state['dt'],self._state['lambdas'].flatten(),self._state['tau'], self._state['taup'] 
        invI, invP, invDP, invDates = self._get_matrices ( inj,prod,prod_press)
        pred_series = self._compute_pseudo_flow_matrix( invI, invDP, tau, dt)
        Q = lambdas[0:inj.shape[1]] * pred_series[:,0:inj.shape[1]] 

        return Q, invI, invP, invDP,pred_series 

    def predict( self  ):

        data = self._data 
        error_message = '[predict] The fit_preprocess step was not done or it failed. Predictions arent possible'

        if data is None: 
            raise ValueError(error_message) 

        if self.optimization_result is None:
            raise ValueError(error_message) 
        
        if len(self.optimization_result) <1:
            raise ValueError(error_message) 
        

        tdate1, tdate2, tdate3 = np.datetime64( self._state['tdate1']),np.datetime64( self._state['tdate2']), np.datetime64( self._state['tdate3']) 
        dates = pd.to_datetime(data.water_injection.index).values 
        testing_mask = (dates >= tdate1) & (dates <= tdate3)
        
        inj, prod  = data.water_injection[testing_mask], data.liquid_production[testing_mask]
        prod_press = data.producer_pressure[testing_mask] if data.producer_pressure is not None else None 

        self._state['last_prod_press'] = 0.0  if prod_press is None else float( prod_press.values[ prod_press.shape[0]-1] )
        

       
        #check must equal tdate1  qo_date =   self._state['qo_date'] 
        Q, invI, invP, invDP,pred_series = self.prediction_calculations(inj,prod ,prod_press )

        
        ##################################################################
        #prediction reselts. These are consumed by Koval and also exported
        ##################################################################
        qo,dt,lambdas,tau, taup = self._state['qo'],self._state['dt'],self._state['lambdas'].flatten(),self._state['tau'], self._state['taup'] 


        #primary 
        num_injectors = len(self._state['injector_names'] ) # invI.shape[1]        
        inv_primary = np.array([ -dt*(1+n)/taup for n in range(invI.shape[0])]) 
        inv_primary = lambdas[ len(lambdas)-1]*qo * np.exp(inv_primary ).reshape( invP.shape )
        
        #dates for the time series and slicing of some input data also reported 
        values_dates  = pd.Series( inj.index).values[1:] 
  
        #total water injected (only the lambdas part, dont include the J's as in the paper)
        water_injected  = np.sum(Q, axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 
         

        #liquid production prediction 
        pred_series = np.concatenate( [pred_series, inv_primary], axis = 1) 
        yhat = (self._state['lambdas'] * pred_series).sum(axis=1).reshape( invP.shape )
        

        df  = pd.DataFrame({
             LIQUID_PRODUCTION_KEYS[0]+SIM_SUFFIX: yhat.flatten(), 
             CUMMULATIVE_WATER_INJECTED_KEYS[0]+SIM_SUFFIX:water_injected.flatten(),
             DATE_KEYS[0] : values_dates,  
             LIQUID_PRODUCTION_KEYS[0]: invP.flatten(),
             PRIMARY_SUPPORT_KEYS[0]:inv_primary.flatten()
             })
        

        
        if data.water_production is not None: 
            
            #ignore the 1st step because it is qo (inj above was removed the 1st step )
            # this is old code: mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate3))
            w = data.water_production[1:]
            w = w[ pd.to_datetime(w.index) >= np.datetime64(tdate1) ]
            w = w[ pd.to_datetime(w.index) <= np.datetime64(tdate3)]
            df[ WATER_PRODUCTION_KEYS[0]] = w.values.flatten()
            
        
            #mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate3))
            #df[ WATER_PRODUCTION_KEYS[0]] = data.water_production[mask].values 

            
        df.set_index( DATE_KEYS[0], drop = True, inplace= True)
        df['NAME'] = self._state['producer_names'][0]     

        mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate2))
        df['TRAIN'] = mask
        df['ID'] = np.arange(0,df.shape[0],1)
          
        df1 = pd.DataFrame( {} )
        if self.has_bhp: productivity = lambdas[num_injectors:2*num_injectors]
        else: productivity = 0.0
        
        injector_names = self._state['injector_names']
        df1['INJECTOR'] =  injector_names
        df1['PRODUCER'] =  len(injector_names)*[ self._state['producer_names'][0] ]   
        df1[ALLOCATION_KEYS[0]]     =  list(lambdas[0:num_injectors])
        df1['tau']   =  tau    
        df1['taup']  = len(injector_names)*[ taup ] 
        df1[PRODUCTIVITY_KEYS[0]]  = productivity  
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
            prod_press= None


        #bhp was used in training but if no bhp passed to forecast, will assume that the last known value is kept 
        #if bhp was used in training and it is passed to the forecast, then it will be used as expected. 
        else:
            if prod_press is None:  
                prod_press= self._state['last_prod_press'] * np.ones ( shape= (inj.shape[0], 1) )


        #check must equal tdate1 qo_date =   self._state['qo_date'] 
        
        Q, invI, invP, invDP,pred_series = self.prediction_calculations(inj,prod ,prod_press )


        ##################################################################
        #prediction reselts. These are consumed by Koval and also exported
        ##################################################################
        qo,dt,lambdas,tau, taup = self._state['qo'],self._state['dt'],self._state['lambdas'].flatten(),self._state['tau'], self._state['taup'] 



        #primary num_injectors = len(self._state['injector_names'] ) # invI.shape[1]        
        inv_primary = np.array([ -dt*(1+n)/taup for n in range(invI.shape[0])]) 
        inv_primary = lambdas[ len(lambdas)-1]*qo * np.exp(inv_primary ).reshape( invP.shape )
        
        #dates for the time series and slicing of some input data also reported 
        values_dates  = pd.Series( inj.index).values[1:] 
  
        #total water injected (only the lambdas part, dont include the J's as in the paper)
        water_injected  = np.sum(Q, axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 
         

        #liquid production prediction 
        pred_series = np.concatenate( [pred_series, inv_primary], axis = 1) 
        yhat = (self._state['lambdas'] * pred_series).sum(axis=1).reshape( invP.shape )
        

        df  = pd.DataFrame({
             LIQUID_PRODUCTION_KEYS[0]+SIM_SUFFIX: yhat.flatten(), 
             CUMMULATIVE_WATER_INJECTED_KEYS[0]+SIM_SUFFIX:water_injected.flatten(),
             DATE_KEYS[0] : values_dates,  
             })
        
           
        df.set_index( DATE_KEYS[0], drop = True, inplace= True)
        df['NAME'] = self._state['producer_names'][0]     

        mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate2))
        df['TRAIN'] = mask
        df['ID'] = np.arange(0,df.shape[0],1)
                 

        self.forecast_result = {}
        self.forecast_result['rates'] = df 

        return self.forecast_result 

    def _process_args(self, pattern, input_args = None ):
   
        def extract_date( s ):
            if s is None: return None 
        
            chars = ['-','/','\\',',']
            for char in chars: 
                if char in s: 
                    y,m,d= s.split(char)
                    return date( int(y),int(m),int(d))
            return None 

        args = self.get_default_params()
        
         
        if input_args is None: input_args = {}
    
        
        #the optimizer 
        if 'optimizer' in input_args:args['optimizer'].update( input_args['optimizer'] )
        args['optimizer']['name']=optimizers_name_map[ args['optimizer']['name'].lower() ]   
        
        if 'pre_optimizer' in input_args:args['pre_optimizer'].update( input_args['pre_optimizer'] )
        args['pre_optimizer']['name']=optimizers_name_map[ args['pre_optimizer']['name'].lower() ]   
        
        
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
                else: 
                    #not sure if there is another condition 
                    pass
                
                date1,date2 = sorted([date1,date2])
                args['dates'] = [ date1, date2, date3 ]
            

        #parameters tau and taup 
        if 'parameters' in input_args:
            if 'tau'  in input_args['parameters']: args['parameters']['tau']  = input_args['parameters']['tau']
            if 'taup' in input_args['parameters']: args['parameters']['taup'] = input_args['parameters']['taup']
                
                
        #other 
        if 'dt' in input_args: args['dt']  = input_args['dt']
        if 'max_running_time' in input_args: args['max_running_time']  = input_args['max_running_time']
        if 'maxiter' in input_args: args['maxiter']  = input_args['maxiter']
        
        #the error metric
        if 'integrated' in input_args: 
            args['integrated'] = input_args['integrated']          
            
        #if 'primary' in input_args: 
        #    args['primary'] = input_args['primary']          
          
            
            
                

        parameters = args['parameters']
        num_injectors = pattern.num_injectors 
         
        tau_args = parameters['tau']
        if not isinstance( tau_args, list ): tau_args = [ tau_args ]
        if len( tau_args ) > num_injectors: tau_args = tau_args[0:num_injectors]
        if len( tau_args ) < num_injectors:
            to_add = (num_injectors - len(tau_args))*[ tau_args[-1:][0] ]
            tau_args.extend( to_add )
            
        
        args['parameters']['tau'] = tau_args 


        #other keys that may be related to multi-well 
        for key,value in input_args.items():
            if key in args:
                pass
            else:
                args[key] = value 


        return args
     
    def _get_P_matrix(self, tau , taup ):

        state = self._state 
        invI = state['invI']  #injection matrix
        invP = state['invP']  #production matrix 
        invDP = state['invDP']#productor's pressure column          
        dt = state['dt']
        qo = state['qo']
            
        
        pred_series = self._compute_pseudo_flow_matrix( invI, invDP, tau, dt)
        
        #primary 
        time_steps = invI.shape[0]   
        inv_primary = np.array([ -dt*(1+n)/taup for n in range(time_steps)]) 
        inv_primary = qo * np.exp(inv_primary ).reshape( invP.shape )
        
        pred_series = np.concatenate( [pred_series, inv_primary], axis = 1) 
        return pred_series

    def _get_matrices(self,water_injection, liquid_production, producer_pressure):
        #shorter names 
        inj, prod, prod_press,dates = water_injection, liquid_production, producer_pressure, pd.Series( water_injection.index) 
      
         
        num_time_steps = inj.shape[0]
        num_injectors = inj.shape[1]        
        invI =   CRMHelper._to_numpy(inj).reshape(num_time_steps,inj.shape[1])
        invP =   CRMHelper._to_numpy(prod).reshape(num_time_steps,prod.shape[1])
        invDates = CRMHelper._to_numpy(dates).reshape(num_time_steps,1)
                
        invI =  invI[1:invI.shape[0], :]  
        invP =  invP[1:invP.shape[0], : ]
        invDates =  invDates[1:invDates.shape[0], :] 
    
        #in many cases, there will be no BHP 
        if prod_press is None:
            invDP = None# np.zeros ( shape= (invI.shape[0], num_injectors) )
            self.has_bhp = False 
        else: 
            # P is really DP = [P1-Po, P2-P1, P3-P2,....] The Po value will be discarded. 
            self.has_bhp = True 
            prod_press  = CRMHelper._to_numpy( prod_press) #
            prod_press  = CRMHelper.shift_up(prod_press)-prod_press  
            temp_invDP = -1.0*( prod_press[1:] ).reshape( invI.shape[0],1) #take out the first one

            #since this is P(t2) - P(t1) the last value is undetermined. We set it equal to the previous one 
            temp_invDP[ temp_invDP.shape[0] -1 ] = temp_invDP[ temp_invDP.shape[0] -2 ]
            #this pressure matrix needs to be repeated horizontally since every injector has its own J
            invDP = np.zeros( shape=(temp_invDP.shape[0], num_injectors))
            
            for n in range( num_injectors):
                invDP[:,n]=temp_invDP[:,0]
    
    
    
        #print('returning matrices I, P, DP, Date', invI.shape, invP.shape, invDP.shape, invDates.shape )
        return invI, invP, invDP, invDates 
    
    def _pseudo_grid_search(self, params, bounds, options ):

        result = minimize(fun = self._loss, x0 = params, 
                              method =  self._state['pre_optimizer']['name'], #   'TNC', # 'powell',#'L-BFGS-B', # 'powell',         
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

    def set_parameters( self, lambdas, tau , taup ):
        self._state['lambdas'] = lambdas
        self._state['tau'] = tau
        self._state['taup'] = taup
        

        n_params = len(  lambdas )
        num_injectors= self._state['invI'].shape[1]  
        self._state['Primary support coeff'] = lambdas[n_params-1]
        
        if self.has_bhp: self._state['Productivy'] = lambdas[num_injectors:2*num_injectors]
        else: self._state['Productivy']  = 0.0 
            
        self._state['Allocation'] = lambdas[0:num_injectors]
        return self
    
    def evaluate_error( self, lambdas=None, tau=None , taup=None ):

        if lambdas is None: 
            lambdas = self._state['lambdas']
            n_params = len(  lambdas )
            num_injectors= self._state['invI'].shape[1]  
            self._state['Primary support coeff'] = lambdas[n_params-1]
            
            if self.has_bhp: self._state['Productivy'] = lambdas[num_injectors:2*num_injectors]
            else: self._state['Productivy']  = 0.0  
            self._state['Allocation'] = lambdas[0:num_injectors]


        if tau  is None: tau  = self._state['tau'  ]
        if taup is None: taup = self._state['taup' ]


        invP = self._state['invP']
        pred_series = self._get_P_matrix( tau , taup )
        Q = lambdas * pred_series
        Q = np.sum( Q , axis = 1 ).reshape( invP.shape )
        #squared_error = mean_squared_error(invP, Q, squared=False)
        #return  squared_error

        #error_metric = mean_squared_error(invP, Q, squared=False)# if self._state['integrated']==False else integrated_error(invP, Q, squared=False)
        error_metric =  root_mean_squared_error(invP, Q)# 

        return  error_metric

    def _loss(self, params, *args):

        state = args[0]
        state['counter'] = state['counter']+1

        invI = state['invI']  #inverted injection matrix
        tau = params[0:invI.shape[1]]
        taup = params[ len(params) - 1 ]
        tau[ tau < 0.001] = 0.01
        if taup < 0.001: taup = 0.01
        

        pred_series = self._get_P_matrix( tau , taup)
        
        model = LinearRegression(positive=True,copy_X=False,fit_intercept=False )
        invP = state['invP']  #production matrix 
        reg = model.fit(pred_series, invP ) #fit coefficients for everythig except primary       
        lambdas = reg.coef_[0]
        #lambdas.reshape( lambdas.shape[0],1) 
        #num_injectors = len(state['injector_names']) 
        #extra_loss = 1.0 
        #for n in range( num_injectors ):
        #    if lambdas[n]>1.0:
        #        extra_loss= lambdas[n]*lambdas[n]
        #        lambdas[n]=1.0
                
        
        #large_lambdas =  np.array([ v if v >= 1.0 else 0.0 for v in lambdas  ])
        #extra_loss =  1.0 + np.sum(large_lambdas**2)  
        #lambdas = np.array( [ v if v < 1.0 else 1.0 for v in lambdas  ] )
        
        #enforce primary support to 1.
        #lambdas[ -1] = 1.0 
        
        #model = Ridge(alpha = 1.0, max_iter=15000, tol=0.01, positive=True,copy_X=False,fit_intercept=False )
        #invP = state['invP']  #production matrix 
        #reg = model.fit(pred_series, invP ) #fit coefficients for everythig except primary       
        #lambdas = reg.coef_[0]
        #extra_loss =  1.0 
        
        
    
          
        
        Q = (lambdas * pred_series)
        Q = np.sum( Q , axis = 1 ).reshape( invP.shape )
        
        #squared_error = mean_squared_error(invP, Q, squared=False) 
        #error_metric =  mean_squared_error(invP, Q, squared=False)# if self._state['integrated']==False else integrated_error(invP, Q, squared=False)
        error_metric =  root_mean_squared_error(invP, Q)#
    

            
        state['rmse'] = error_metric
        state['r2'] = r2_score(invP, Q)
        self.set_parameters( lambdas, tau, taup )
        

        return error_metric
    
    def _compute_pseudo_flow_matrix(self, invI, invDP, taus, dt):
        '''
        This method returns the matrix that needs to be passed to the regression.
        The matrix contains all the time-steps considering the exponential weights in the 
        equations. The production will be this matrix times the lambdas (tensor product). 
        The lambdas are the ones obtained in the regression.
        '''
        time_steps = invI.shape[0]
        
   
        taus  = np.array( taus )
        E = np.flip(CRMHelper.get_matrix_E( taus, dt, time_steps), axis = 0  )
        
        
        max_tau = np.max(taus)
        window_size = 1 + int(5.0 * max_tau )

        #no pressure
        if self.has_bhp == False: 
            pseudo_flow = np.zeros ( shape = (invI.shape[0], invI.shape[1])  )
            for tn in range ( time_steps ) :
                Eview = E[-min( 1+tn, window_size ):]
                i = max(0, tn+1-window_size) 
                pseudo_flow[tn,:] =  np.sum( Eview * invI[i:tn+1] , axis = 0 ) 
            return pseudo_flow 
    
        #pressure 
        else:
            pseudo_flow = np.zeros ( shape = (invI.shape[0], 2*invI.shape[1])  )
            for tn in range ( time_steps ) :
                Eview = E[-min( 1+tn, window_size ):]
                i = max(0, tn+1-window_size) 
                G = Eview * [invI[i:tn+1], taus *  invDP[i:tn+1]] 
                pseudo_flow[tn,:] =  np.sum( np.concatenate( (G[0],G[1]), axis=1), axis = 0 ) 
            return pseudo_flow 
      

class CRMIP(CRMModel):
    
    '''
    CRMIP solver for multi-pattern and multi-well. Patterns can be multi-producer or single producer ones. 
    '''
    def __init__(self ):
 
        super().__init__('CRMIP' )
        self._clear()
    
    def _get_submodel( self ): 
        return CRMIPSingle()
    
    def fit_preprocess( self, data, input_args = None ):
        '''
        Splits the data in single-well patterns and calls SingleModel.fit_preprocess( ) for each.
        Single-well patterns for which the fit_preprocess doenst fail are stored for later simulation
        Errors are logged and appended to the model log.
        '''
        
        self.patterns,self.single_well_patterns, patterns   = None, None, None
        self.failed_models = [] 
        models_to_delete   = []
        
        if isinstance(data, list ):         #option 1, a list of patterns 
            patterns = data 
            
        elif isinstance(data, CRMPattern ): #option 2, a single pattern
            patterns = [data]
        
        elif isinstance(data, CRMDataset ) and ( 'distance' in input_args) : #option 3, a dataset and input_args contains a distance
            patterns = data.get_distance_patterns( input_args['distance'], fix_time_gaps = True, fill_nan=0.0)
              
                      
        else:
            raise ValueError( '[fit_preprocess] Dont know what this data type is in fit_preprocess CRMIP') 
            
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
                    single_well_patterns.append(single)
                    self.models.append( model )
                    success_count = 1 + success_count
                    #self.log.extend( model.log )

                except Exception as e:
                    
            
                    self.failed_models.append( (single.producer_names[0],'preprocessing ' + str(e)) )
                    print(single.producer_names[0] + '  ' + str(e))
                    self.log.extend( model.log )
                    log.append( single.producer_names[0] + '  ' + str(e))
        
        if success_count > 0:
            self.patterns = patterns
            self.single_well_patterns = single_well_patterns
        else:
            self.single_well_patterns = None 
            self.patterns = None 
            
        
        self.optimization_result = []
         
        self.args = {} 
        if input_args is not None:  self.args.update( input_args )
        return self
       
    def fit(self):#, serial = True, balance = None  ):
        
        self.prediction_result  = {}
        balance = self.args.get( 'balance', {}).get('type', 'none')
        serial  = self.args.get( 'serial', True )
    
    
        def CRMIPSingleSolver( n ):

            m,r = self.models[n], {} 
           
            try:
                r = m.fit()
                               
            except Exception as e: 
                r = {'message': str(e) }
  
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
    
                    r = m.fit(  )
                 
                except Exception as e:
                    self.failed_models.append( (m.producer_name,'fit: ' + str(e)) )
                    models_to_delete.append( m )
                    r = {'message': str(e) }
                    self.log.append( str(e) )
                    print( str(e) )

                self.optimization_result.append( r )   
                self.log.append(f'fit model {i}, progress {100.0*(1+i)/len(self.models)}')

        else:
            self.log.append('parallel fitting started')
            num_producers = len( self.models )
            num_cpus =  max( mp.cpu_count(), min( num_producers, mp.cpu_count() ))
            
            models = self.models 
            results  = Parallel(n_jobs=num_cpus)(delayed(CRMIPSingleSolver)
            ( n ) for n in range( len(models) ))   
            
     
            for i,item in enumerate( results ): 
            
                n,r,forked_model   = item
      
                self.models[n] = forked_model
                self.models[n].optimization_result = r
                
                
            self.optimization_result = [] 
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
            
            
        if balance.lower() == 'quick':
            self.log.append('doing a quick balance')
            self.balance('quick')
            self.log.append('balancing done')
        
        elif balance.lower() == 'full':
            print('full balancing')
            self.log.append('doing a full balance')
            self.balance('full' )
            self.log.append('balancing done')
        
        self.log.append('fitting finished')
        self.prediction_result['optimization']  = self.optimization_result
        return self.optimization_result    
            
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
        
        if (balance_type == 'quick'):
        
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
  
         
    def predict( self ):
        
        self.prediction_result  ={}
        _predictions = [] 
        
        self.log.append('prediction started')
        for i,m in enumerate(self.models):
            
            try:
                p = m.predict()  
                r = m.optimization_result               
       
                _predictions.append( p ) 
                self.log.append(f'prediction for model {i} finished, progress {100.0*(1+i)/len(self.models)}')
                
            except Exception as e:
                self.log.append( 'Prediction failed ' + str(e) )
    
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
                s = f'Error in forecast model {n}: {str(e)}'
                print(s)
                self.log.append( s )

        self.forecast_result = {}
        self.forecast_result['rates'] = pd.concat( [single_forecast['rates'] for single_forecast in forecasts ], axis = 0 ) 
        self.log.append('forecast finished')      

        return self.forecast_result 

    def get_default_params( self ): 
        
        params_ = self._get_submodel().get_default_params()
        params_['serial'] = True 
        params_['balance'] = { 'type':'none' }
        return params_
    

 
class CRMIDSingleConstrained(CRMIPSingle):
    
    '''
    CRMIP solver for single-producer patterns. This class shouldnt be instantiated in the general case.
    The CRMIP class defined below should be used instead. The CRMIPSingle exists only as support for the 
    CRMIP class. 
    '''
    
    def __init__(self, input_args = None ):
        super().__init__( )
        self._clear()
        self._name = 'CRMIDSingleConstrained'
       
                
    def get_default_params( self ): 
        
        args = {
            'dates': ['1950-09-23','2200-01-28'],
                   
            'parameters': {
                'tau':   {'bounds': (0.1,50), 'init_value': 5.0} ,
                'taup':  {'bounds':(0.1,50), 'init_value': 5.0},
                'lambda':   {'bounds': (0.01,0.99), 'init_value': 0.5},
                'productivity_index':   {'bounds': (0.0,1.25), 'init_value': 0.0},
                'qo_lambda':   {'bounds': (0.0,1.2), 'init_value': 1.0}
            },

            'regularization': 0.000001, 
            'dt': 1.0,
            'max_running_time': 2000.0,
            'optimizer': {'maxiter': 2000,'name': 'SLSQP', 'tolerance': 1e-03},
            #'optimizer': {'maxiter': 2000,'name': 'Nelder-Mead', 'tolerance': 1e-04},
             
            'pre_optimizer': {'name': 'Powell'},

        }
        
        return args 

    def _process_args(self, pattern, input_args = None ):
   
        def extract_date( s ):
            if s is None: return None 
        
            chars = ['-','/','\\',',']
            for char in chars: 
                if char in s: 
                    y,m,d= s.split(char)
                    return date( int(y),int(m),int(d))
            return None 

        args = self.get_default_params()
        
         
        if input_args is None: input_args = {}
    
        
        #the optimizer 
        if 'optimizer' in input_args:args['optimizer'].update( input_args['optimizer'] )
        args['optimizer']['name']=optimizers_name_map[ args['optimizer']['name'].lower() ]   
        
        if 'pre_optimizer' in input_args:args['pre_optimizer'].update( input_args['pre_optimizer'] )
        args['pre_optimizer']['name']=optimizers_name_map[ args['pre_optimizer']['name'].lower() ]   
        
        
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
                else: 
                    #not sure if there is another condition 
                    pass
                
                date1,date2 = sorted([date1,date2])
                args['dates'] = [ date1, date2, date3 ]
            

        #parameters tau and taup 
        if 'parameters' in input_args:
            if 'tau'  in input_args['parameters']: args['parameters']['tau']  = input_args['parameters']['tau']
            if 'taup' in input_args['parameters']: args['parameters']['taup'] = input_args['parameters']['taup']
            if 'lambda' in input_args['parameters']: args['parameters']['lambda'] = input_args['parameters']['lambda']
            if 'productivity_index' in input_args['parameters']: args['parameters']['productivity_index'] = input_args['parameters']['productivity_index']
            if 'qo_lambda' in input_args['parameters']: args['parameters']['qo_lambda'] = input_args['parameters']['qo_lambda']
             
                
        #other that the user caN OVERRIDE 
        if 'dt' in input_args: args['dt']  = input_args['dt']
        if 'max_running_time' in input_args: args['max_running_time']  = input_args['max_running_time']
        if 'maxiter' in input_args: args['maxiter']  = input_args['maxiter']
        if 'primary' in input_args: args['primary'] = input_args['primary']          
        if 'regularization' in input_args: args['regularization'] = input_args['regularization']          
               

        parameters = args['parameters']
        num_injectors = pattern.num_injectors 
         
        #tau_args = parameters['tau']
        #if not isinstance( tau_args, list ): tau_args = [ tau_args ]
        #if len( tau_args ) > num_injectors: tau_args = tau_args[0:num_injectors]
        #if len( tau_args ) < num_injectors:
        #    to_add = (num_injectors - len(tau_args))*[ tau_args[-1:][0] ]
        #    tau_args.extend( to_add )
            
        
        #args['parameters']['tau'] = tau_args 


        #other keys that may be related to multi-well 
        for key,value in input_args.items():
            if key in args:
                pass
            else:
                args[key] = value 


        return args
     
    ################


    def predict( self  ):

        ''' 
        predict is like fit but we use the entire dataset as opposed to a training date [date1, date2] 
        So we basically take the stored data and call the same functions called to produce yhat in the loss 
        function but now the I,P, dP matrices include all the dataset times 
        '''

        data = self._data 
        error_message = '[predict] The fit_preprocess step was not done or it failed. Predictions arent possible'

        if data is None: 
            raise ValueError(error_message) 

        if self.optimization_result is None:
            raise ValueError(error_message) 
        
        if len(self.optimization_result) <1:
            raise ValueError(error_message) 
        

        tdate1, tdate2, tdate3 = np.datetime64( self._state['tdate1']),np.datetime64( self._state['tdate2']), np.datetime64( self._state['tdate3']) 
       
        dates = pd.to_datetime(data.water_injection.index).values 
        testing_mask = (dates >= tdate1) & (dates <= tdate3)
        
        inj, prod  = data.water_injection[testing_mask], data.liquid_production[testing_mask]
        prod_press = data.producer_pressure[testing_mask] if data.producer_pressure is not None else None 
        
        # non concatenated matrices 
        invI, invP, invDP, invDates  = self._get_matrices( inj, prod, prod_press)

        # 
        invI = np.concatenate( (invI,                               #gain injectors                                  
                                np.zeros( shape=(invI.shape[0],1)), #dp
                                np.zeros( shape=(invI.shape[0],1))),#qo  
                                axis=1) 
        
                
        lambdas = self._state['lambdas'] 
        tau = self._state['tau']
        taup = self._state['taup']
        
        Q = lambdas * self._get_P_matrix( invI, invP, invDP, tau , taup)
        # The matrix first n_injectors columns are the total water injected per time step (day/month whatever )
        # The next column is the J (productivity index)
        # The last column is the primary production 
         
        # water injected integrated (cummulated) 
        num_injectors = len( self._state['injector_names'])
        water_injected  = np.sum(Q[:,0:num_injectors], axis = 1 ) 
        water_injected  = np.cumsum( water_injected, axis = 0 ) 
       
        # liquid production predicted 
        yhat = Q.sum( axis = 1 ).reshape( invP.shape )
        
        #primary 
        inv_primary = Q[:,-1:].reshape( invP.shape )

        # dates 
        values_dates  = invDates.flatten()
        
 
        df  = pd.DataFrame({
             LIQUID_PRODUCTION_KEYS[0]+SIM_SUFFIX: yhat.flatten(), 
             CUMMULATIVE_WATER_INJECTED_KEYS[0]+SIM_SUFFIX:water_injected.flatten(),
             DATE_KEYS[0] : values_dates,  
             LIQUID_PRODUCTION_KEYS[0]: invP.flatten(),
             PRIMARY_SUPPORT_KEYS[1]:inv_primary.flatten()
             })
        
        if data.water_production is not None: 
            
            #ignore the 1st step because it is qo (inj above was removed the 1st step )
            # this is old code: mask = (pd.to_datetime( values_dates ).values >= np.datetime64(tdate1)) & (pd.to_datetime( values_dates ).values<= np.datetime64(tdate3))
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
        if self.has_bhp: productivity = lambdas[num_injectors:2*num_injectors]
        else: productivity = 0.0
        
        injector_names = self._state['injector_names']
        df1['INJECTOR'] =  injector_names
        df1['PRODUCER'] =  len(injector_names)*[ self._state['producer_names'][0] ]   
        df1[ALLOCATION_KEYS[0]]     =  list(lambdas[0:num_injectors])
        df1['tau']   =  tau    
        df1['taup']  = len(injector_names)*[ taup ] 
        df1[PRODUCTIVITY_KEYS[0]]  = productivity  
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
        raise ValueError('CRMID forecast is not implemented yet')
         
    def _get_P_matrix(self, invI, invP, invDP, tau , taup ):

        ''''
        Returns the P matrix, i.e. a matrix where the first n_injectors columns are the gain.
        Then next column is the J and the last one is the qo. 
        All of these need to be multiplied by lamdas and summed along axis = 1 to get the predicted 
        fluid production. 
          
        '''

        state = self._state 
        #invI = state['invI']  #injection matrix
        #invP = state['invP']  #production matrix 
        #invDP = state['invDP']#productor's pressure column          
        dt = state['dt']
        qo = state['qo']


        # pred_series up to here is just the gain matrix, weighted by the taus 
        # the last two columns are full of zeros. One is fopr the J's thwe other one for the qo     
        pred_series = self._compute_pseudo_flow_matrix( invI, invDP, tau, dt)
        

        # the J, and qo will be filled here 
        # it is the same as in CRMPSingle but we use Taup for the J's 
        window_size = 1 + int(5.0 * taup )
        num_injectors = len( self._state['injector_names'] )
        time_steps = invI.shape[0] 
        
        E = np.flip(CRMHelper.get_row_vector_E(taup,dt, time_steps))
        for tn in range( time_steps ):
            
            io = max(0, tn + 1 - window_size )
            Iview = invI[ io:tn+1,num_injectors]
            
            Eview = E[0,-Iview.shape[0]:]
            pred_series[tn,num_injectors] = taup * np.dot(Eview,Iview.T) 
            
          
            
        #primary        
        inv_primary = np.array([ -dt*(1+n)/taup for n in range(time_steps)]) 
        inv_primary = qo * np.exp(inv_primary ).reshape( invP.shape )
        
        last_column = invI.shape[1] - 1 
        pred_series[:, last_column: ] =  inv_primary
        return pred_series

    def _get_matrices(self,water_injection, liquid_production, producer_pressure):
        #shorter names 
        inj, prod, prod_press,dates = water_injection, liquid_production, producer_pressure, pd.Series( water_injection.index) 
      
         
        num_time_steps = inj.shape[0]
        num_injectors = inj.shape[1]        
        invI =   CRMHelper._to_numpy(inj).reshape(num_time_steps,inj.shape[1])
        invP =   CRMHelper._to_numpy(prod).reshape(num_time_steps,prod.shape[1])
        invDates = CRMHelper._to_numpy(dates).reshape(num_time_steps,1)
                
        invI =  invI[1:invI.shape[0], :]  
        invP =  invP[1:invP.shape[0], : ]
        invDates =  invDates[1:invDates.shape[0], :] 
    
        #in many cases, there will be no BHP 
        if prod_press is None:
            invDP= np.zeros ( shape= (invI.shape[0], 1) )
            self.has_bhp = False
        else: 
            # P is really DP = [P1-Po, P2-P1, P3-P2,....] The Po value will be discarded. 
            self.has_bhp = True 
            prod_press  = CRMHelper._to_numpy( prod_press) #
            prod_press  = CRMHelper.shift_up(prod_press)-prod_press  
            temp_invDP = -1.0*( prod_press[1:] ).reshape( invI.shape[0],1) #take out the first one

            #since this is P(t2) - P(t1) the last value is undetermined. We set it equal to the previous one 
            temp_invDP[ temp_invDP.shape[0] -1 ] = temp_invDP[ temp_invDP.shape[0] -2 ]
            #this pressure matrix needs to be repeated horizontally since every injector has its own J
            invDP = np.zeros( shape=(temp_invDP.shape[0], num_injectors))
            
            for n in range( num_injectors):
                invDP[:,n]=temp_invDP[:,0]
    
    
    
        #print('returning matrices I, P, DP, Date', invI.shape, invP.shape, invDP.shape, invDates.shape )
        return invI, invP, invDP, invDates 
    
    def set_parameters( self, lambdas, tau , taup ):
        self._state['lambdas'] = lambdas
        self._state['tau'] = tau
        self._state['taup'] = taup
        
        num_injectors = len( self._state['injector_names'] )  
        self._state['Primary support coeff'] = lambdas[-1]
        
        if self.has_bhp: self._state['Productivy'] = lambdas[-2]
        else: self._state['Productivy']  = 0.0 
            
        self._state['Allocation'] = lambdas[0:num_injectors]
        #allocs = self._state['lambdas'].flatten().tolist()
        #self.optimization_result['allocation']   = allocs[0:num_injectors]
        
        return self
      
    def evaluate_error( self, lambdas=None, tau=None , taup=None ):

        if lambdas is None: 
            
            lambdas = self._state['lambdas']
            num_injectors= len( self._state['injector_names'] )  
            self._state['Primary support coeff'] = lambdas[-1]
            
            if self.has_bhp: self._state['Productivy'] = lambdas[-2]
            else: self._state['Productivy']  = 0.0  
            self._state['Allocation'] = lambdas[0:num_injectors]


        if tau  is None: tau  = self._state['tau'  ]
        if taup is None: taup = self._state['taup' ]


        invP  = self._state['invP']
        invI  = self._state['invI']
        invDP = self._state['invDP']
        
        pred_series = self._get_P_matrix( invI, invP, invDP, tau , taup )
        Q = lambdas * pred_series
        Q = np.sum( Q , axis = 1 ).reshape( invP.shape )

        #error_metric = mean_squared_error(invP, Q, squared=False) #+  self._state['regularization'] * (np.abs(lambdas[0:num_injectors]).sum())
        error_metric = root_mean_squared_error(invP, Q )#, squared=False) #+  self._state['regularization'] * (np.abs(lambdas[0:num_injectors]).sum())

        r2 = r2_score(invP, Q)


        return  error_metric, r2 

    def _compute_pseudo_flow_matrix(self, invI, invDP, taus, dt):
        
        # CRMIPSingleConstrained
        
        time_steps = invI.shape[0]
        num_injectors = len( self._state['injector_names'] )
        taus  = np.array( taus )
        E = np.flip(CRMHelper.get_matrix_E( taus, dt, time_steps), axis = 0  )
        max_tau = np.max(taus)
        window_size = 1 + int(5.0 * max_tau )

        # invI already has the J and qo  
        pseudo_flow = np.zeros ( (time_steps,invI.shape[1]) )

         
        for tn in range ( time_steps ) :
                Eview = E[-min( 1+tn, window_size ):]
                i = max(0, tn+1-window_size) 
                
                #element-wise product 
                pseudo_flow[tn, 0 : num_injectors ] =  np.sum( Eview * invI[i:tn+1, 0 : num_injectors] , axis = 0 ) 
                

        # at this point we filled the ninjecors first colummns (the gain matrix) and we have two other 
        # columns full of zeros, which correspond to the J and the qo.

         
        return pseudo_flow
       
    def _loss(self, params, *args):

        state = args[0]
        state['counter'] = state['counter']+1

        invI = state['invI']    # injection matrix + column for the J(1) plus column for primary
        invP = state['invP']    # production rate matrix
        invDP = state['invDP']  # productor's pressure column    
                
        num_injectors = len( self._state['injector_names'])
        tau = params[0:num_injectors]
        taup = params[ num_injectors ]
        tau[ tau < 0.001] = 0.001
        if taup < 0.001: taup = 0.001
        
        # assume 2 injectors 
        # lambdas [ tau1, tau2, taup, lambdas = [l1, l1, J1, qo ]]
        
        lambdas = params[ num_injectors+1:]
        pred_series = lambdas * self._get_P_matrix( invI, invP, invDP, tau , taup)
        yhat = pred_series.sum( axis = 1 ).reshape( invP.shape )
        
        #scaled_lambdas = [x*100.0 for x in lambdas ]
        #error_metric =  mean_squared_error(invP, yhat, squared=False) *( 1.0 + state['regularization'] * (np.abs(scaled_lambdas[0:num_injectors]).sum()) )#dot( lambdas, lambdas ) 
        error_metric =  root_mean_squared_error(invP, yhat)#*( 1.0 + state['regularization'] * (np.abs(scaled_lambdas[0:num_injectors]).sum()) )# , squared=False) *( 1.0 + state['regularization'] * (np.abs(scaled_lambdas[0:num_injectors]).sum()) )#dot( lambdas, lambdas ) 
        
        state['rmse'] = error_metric
        state['r2'] = r2_score(invP, yhat)
        
        
        self.set_parameters( lambdas, tau, taup )
        # eva = self.evaluate_error()
        # print( self._name, error_metric, eva )
        
        return error_metric
    
    def _fit(self, quick = False, verbose=False):
        
        self.optimization_result = {} 
        data = self._data
        if data is None:
            raise ValueError('Cannot fit the data because fit_preprocess failed or was never called')
        
         
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
        
        
        #this concatenation is only used in CRM-P and CRMIP-reduced (constrained).  
        invI = np.concatenate( (invI,                               #gain injectors                                  
                                np.zeros( shape=(invI.shape[0],1)), #dp
                                np.zeros( shape=(invI.shape[0],1))),#qo  
                                axis=1) 
        
        
        self._state['bhp'] = self.has_bhp
        self._state['invI']= invI
        self._state['invP']=invP
        self._state['invDP']=invDP
        self._state['invDates']=invDates
        

        # init values and bounds 
        parameters = self._state['parameters']
        
        # tau bounds 
        num_injectors = len( self._state['injector_names'] ) 
        min_tau, max_tau = parameters['tau']['bounds'][0], parameters['tau']['bounds'][1]
        tau_bounds =  [  (min_tau, max_tau) for i in range( num_injectors) ] + [parameters['taup']['bounds']]

        # lambda bounds 
        min_lambda, max_lambda = parameters['lambda']['bounds'][0], parameters['lambda']['bounds'][1]
        lambda_bounds =  [  (min_lambda, max_lambda) for n in range(  num_injectors ) ] 

        # bounds for the productivity index, in this version of CRMIP there is only one productivitty index  
        productivity_bounds = [parameters['productivity_index']['bounds'] ]# if self.has_bhp else (-0.01,0.01)]

        # bounds for the qo coefficient 
        qo_lambda_bounds = [ parameters['qo_lambda']['bounds'] ]
        
        all_bounds = tau_bounds + lambda_bounds + productivity_bounds + qo_lambda_bounds
  
        # now the initial values, in the same order  
        init_values  = [ parameters['tau']['init_value'] for i in range( num_injectors) ] + [parameters['taup']['init_value'] ]
        init_values = init_values + [ parameters['lambda']['init_value'] for n in range( num_injectors) ] 
        init_values = init_values + [ parameters['productivity_index']['init_value'] if self.has_bhp else 0.0]   
        init_values = init_values + [ parameters['qo_lambda']['init_value'] ] 
        
    
        optimizer = self._state['optimizer']
        options = {'maxiter':max(self._state['optimizer']['maxiter'], 10*invI.shape[1]), 'disp':verbose}    
        result = minimize( fun       = self._loss, 
                      x0        = init_values ,
                      method    = optimizer['name'],         
                      bounds    = all_bounds,
                      args      = self._state, 
                      options   = options, 
                      tol       = optimizer['tolerance']
                      )
        
        self._state['message'] = result['message']
        self._update_from_optimization()#result)
        #################################################################################

        if verbose:
            print('allocation = {} Tau = {} Taup = {} '.format(self.allocation, self.tau, self.taup) )
            print('Finalized. Time(s) = {}'.format( self._state['elapsed_time']))

        return self.optimization_result  
       
 

class CRMIDConstrained(CRMIP):
    
    def __init__(self ):
 
        super().__init__()
        self._name = 'CRMID'
    
    def _get_submodel( self ): 
        return CRMIDSingleConstrained()
   
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
                num_injectors = len( r['injector_names'] )
                model_parameters = r['parameter_index']

                #the current value of all of these 
                #lambdas + productivity + qo + taus + taup
                vals = params[ model_parameters ] 
                lambdas   =  vals[0:num_injectors+2]
                tau, taup = vals[num_injectors+2:2*num_injectors+2], vals[-1]
                tau[ tau < 0.01] = 0.01
                if taup < 0.01: taup = 0.01
        
                sub_model.set_parameters( lambdas, tau, taup )

                #now evaluate the model error 
                rmse, r2  = sub_model.evaluate_error()# lambdas, tau, taup )
                error = error + rmse 
                
                     
                sub_model._state['rmse'] = rmse 
                sub_model._state['r2'] = r2 
                
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
               
                lambda_bounds = item['parameters']['lambda']['bounds']
                productivity_bounds = item['parameters']['productivity_index']['bounds']
                qo_bounds = item['parameters']['qo_lambda']['bounds']
                tau_bounds = item['parameters']['tau']['bounds'] 
                taup_bounds = item['parameters']['taup']['bounds']
                lambdas=  item['lambdas'] 
               
               
                num_injectors = len( injector_names ) 
                
                for n in range(num_injectors):#for allocs [ value1, value2,...] + J [1] and qo [1] 

                    parameter_counter = parameter_counter + 1 
                    item['parameter_index'].append( parameter_counter )

                 
                    if injector_constraints.get( injector_names[n], None ) is None: 
                        injector_constraints[injector_names[n]] = [] 

                    injector_constraints[injector_names[n]].append( parameter_counter )
                    bounds.append( lambda_bounds ) # (0.0,1.0) )
                    init_values.append( lambdas[n] )

                 
                # the J, only 1  bounded but not constrained 
                parameter_counter = parameter_counter + 1
                init_values.append( lambdas[-2] )
                bounds.append( productivity_bounds )
                item['parameter_index'].append( parameter_counter )
                
                #  qo, only 1 bounded but not constrained
                parameter_counter = parameter_counter + 1 
                bounds.append( qo_bounds  )
                init_values.append( lambdas[-1] )
                item['parameter_index'].append( parameter_counter )
                
                #now tau and taup. tau is repeated num_injectors and taup only once 
                for value in item['tau']:
                    parameter_counter = parameter_counter + 1 
                    bounds.append( tau_bounds )
                    init_values.append( value ) 
                    item['parameter_index'].append( parameter_counter )
                
                parameter_counter = parameter_counter + 1 
                bounds.append( ( taup_bounds) )
                init_values.append( item['taup'] )
                item['parameter_index'].append( parameter_counter )
                 

            return injector_constraints, bounds, init_values,parameter_counter


        
        print(' CRMIDConstrained, balance=*', balance_type,'*', len(balance_type)  )
       
        
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
        
        sum_error = 0.0 
        if (balance_type == 'quick') or (balance_type.lower() == 'full') :
        
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
                            rmse,r2  = m.evaluate_error()
                            sum_error = sum_error + rmse  
                            #print('estimated error ip constrained ', rmse )
                            
                            
                            m._state['rmse'] = rmse
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
                            rmse,r2  = m.evaluate_error()
                            sum_error = sum_error + rmse  
                            #print('estimated error ip constrained ', rmse )
                            
                            
                            m._state['rmse'] = rmse
                            m._update_from_optimization()


            self.optimization_result = [] 
            for m in self.models: 
                r = m.optimization_result
                self.optimization_result.append( r ) 
        
            '''
            
            
            if (balance_type == 'quick'): 
                return { 'message': 'success. Quick balancing done'} 
        
        
        
        
        if balance_type.lower() == 'full':
            
            print('------- Entering in the full balancing now IP------')
            for m in self.models: 
                rmse,r2  = m.evaluate_error()
                sum_error = sum_error + rmse  
                            
            
            options = {'maxiter': self.args['balance'].get('maxiter',100)}
            if 'eps' in self.args['balance']:
                options['eps'] = self.args['balance']['eps']
            if 'ftol' in self.args['balance']:
                options['ftol'] = self.args['balance']['ftol']
                
            tolerance = self.args['balance'].get('tolerance', 0.01 * sum_error ) #* sum_error
            print('# We believe that the total error is of the order of ', sum_error,'  before balancing ' )
            print('# The setup optimizer parameters ', options, tolerance )
            #print('# atomatic tolerance experiment ')
            #tolerance = sum_error *  0.001 
            
        
            
            
            inj_constraints, bounds, init_vals,param_count = _construct_balancing_matrices( opts )
            init_vals = np.array( init_vals )
            inj_constraints = np.array( list( inj_constraints.values())) 
            num_contraints = inj_constraints.shape[0]
            ub = np.array( (num_contraints) * [1.0] )
            lb = np.array( (num_contraints) * [0.0] )

            param_count = param_count + 1 #starts with zro 
            A = np.zeros( shape = (inj_constraints.shape[0],param_count) )
            for n in range( inj_constraints.shape[0] ): A[n,inj_constraints[n]] = 1.0


              
            #options = {'maxiter': self.args['balance'].get('maxiter',1000)}
            #tolerance = self.args['balance'].get('tolerance', 0.01)
            
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

            print( result )

            self.optimization_result = [] 
            for m in self.models: 
                r = m.optimization_result
                self.optimization_result.append( r ) 

            return result 
  
      
