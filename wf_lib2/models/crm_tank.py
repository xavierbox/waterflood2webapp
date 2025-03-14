
import numpy as np, pandas as pd, math, multiprocessing as mp
from datetime import date, datetime, timedelta
from joblib   import Parallel, delayed

from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression

from wf_lib2.models.crm_p import CRMPSingle, CRMP , integrated_error
from wf_lib2.models.crm_model import integrated_error
from wf_lib2.data.crm_pattern   import CRMPattern
from wf_lib2.crm_helper      import CRMHelper 
from wf_lib2.crm_definitions     import *

class CRMTankSingle( CRMPSingle ):

    '''
    Helper class that shouldnt be instantiated directly. It exists just to help the CRMTank class defined below.
    In its own, it should work fine to solve problems of only one pattern (either single or multiple-well patterns)
    '''
    
    ###########################################
    ###              public API         #######  
    ###  re-implements the CRMP interface  ###
    ###########################################
    def __init__(self, input_args = None ):

        super().__init__()
        self._name = 'CRMTankSingle'
        self.lumped_injector_names = None  #Shilpy suggestion 
        self.lumped_producer_names = None  #Shilpy suggestion 
        
     
    def _lump_pattern_for_tank( self, pattern ):

        copy_pattern = CRMPattern()# pattern.copy()
        producer_names = pattern.producer_names 

        #remove pressure, the tank shouldnt have pressure 


        for key in pattern.keys():

            column_meaning = name_to_meaning( key, RATE_KEYWORDS )
            is_pressure_column = name_to_meaning( key,  [PRODUCER_PRESSURE_KEYS])
            
            
            #it is a rate or a pressure 
            if column_meaning is not None: 
                
                #now we shouldnt forget to get rid of the pressure, if it is there. 
                if is_pressure_column is None: #column_meaning != PRODUCER_PRESSURE_KEYS[0]:
        
                    new_values = pattern[ key ].sum( axis = 1)
                    copy_pattern[ column_meaning ] = pd.DataFrame( new_values )  

                    name = 'TankProducer' if  pattern[key].columns[0] in( producer_names ) else 'TankInjector'
                    copy_pattern[ column_meaning ].columns = [name]

            else:
                if is_pressure_column is None:
                    copy_pattern[ key ] = pattern[key].copy()


        print( 'copy pattern')
        print( copy_pattern )


        return copy_pattern 

    def fit_preprocess( self, input_pattern,input_args=None, verbose=False):
        
        '''
        The idea is to convert the Tank into a CRM-P with one producer one injector and **no pressure**.
        If we do that here, then the rest of the code can be inherited from the CRMP 
        '''
        self.lumped_injector_names = list( input_pattern.water_injection.columns  )
        self.lumped_producer_names = list(input_pattern.liquid_production.columns ) 
        lumped_pattern = self._lump_pattern_for_tank( input_pattern )
         
        
            
        super().fit_preprocess( lumped_pattern, input_args, verbose)

        return self
    

    def fit( self, serial = False, balance=False):
        
        result = super().fit( )#serial = True )

        result['lumped_injector_names'] = self.lumped_injector_names
        result['lumped_producer_names'] = self.lumped_producer_names

        return result 

        #self.optimization_result[0]['lumped_injector_names'] = self.lumped_injector_names
        #self.optimization_result[0]['lumped_producer_names'] = self.lumped_producer_names

        #self.optimization_result   = result 
        #return self.optimization_result  
    
    
    ###########################################
    ###              private API         ######  
    ###########################################
    
    #all is inherited from the CRMP. Nothing to implement
    #if the CRM-P works, this one works 
    

class CRMTank:
    
    '''
    CRMTank solver for multi and single pattern. 
    Patterns may be single wel or multiple-well.
    '''
    
    def __init__(self):
 
        self.patterns = None 
        self.optimization_result = []
        self.prediction_result  = {}
        
        self.log = [] 
        self.models = [] 

    
    def get_default_params( self ): 
        params_ = CRMTankSingle().get_default_params()
        return params_
        
     
    def fit_preprocess( self, data, input_args = None ):
        '''
        Splits the data in single-well patterns and calls SingleModel.fit_preprocess( ) for each.
        Single-well patterns for which the fit_preprocess doenst fail are stored for later simulation
        Errors are logged and appended to the model log.
        '''
        
        self.patterns, patterns   = None, None
        
        if isinstance(data, list ):         #option 1, a list of patterns 
            patterns = data 
            
        elif isinstance(data, CRMPattern ): #option 2, a single pattern
            patterns = [data]
                       
        else:
            raise ValueError( 'Dont know what this data type is in fit_preprocess CRMTank') 
            
        #for each pattern we have one set of parameters 
        args = None 
        if input_args is None: args =  len(patterns) * [self.get_default_params() ] 
        else:
            if not isinstance( input_args, list ):args = len(patterns) * [ input_args ]
            else: args = input_args
            if len(args) > len(patterns): args = args[0:len(patterns) ]
            elif len(args) < len(patterns): args = args.copy() + (len(patterns)  - len(args)) * [ self.get_default_params() ]      
        
      
        log = [] 
        success_count = 0 
        
        
        #one set of arguments per pattern which is copied to all its single-well sub-patterns
        for n,p in enumerate( patterns ):
  
            try:
                model = CRMTankSingle()
                    
                args[n]['prod_id'] = 0
                args[n]['pattern_id'] = n 
                model.fit_preprocess( p, args[n] )
                self.models.append( model )
                success_count = 1 + success_count
                    
            except Exception as e:
                print(str(e))
                log.append( str(e) )
                    
        
        if success_count > 0:
            self.patterns = patterns
        else:
            self.patterns = None 
            
        
        self.optimization_result = []
         
        
        return self
    
    
    def fit(self, serial = True,  balance = None  ):
        
        
        if self.patterns is None:
            print('Cannot fit the data, patterns not defined in a pre-process step')
            self.optimization_results = []
            return []
        
        self.optimization_result = []
  
        self.log.append('serial fitting started')
        for i, m in enumerate ( self.models ):
            r = {}
            try:
                r = m.fit(  )
                 
            except Exception as e:
                r = {'message': str(e) }
                self.log.append( str(e) )
                print( str(e) )

            self.optimization_result.append( r )   
            self.log.append(f'fit model {i}, progress {100.0*(1+i)/len(self.models)}')


        self.log.append('fitting finished')
        self.log.append('no-balancing available for CRMTank')
 
        merged = []
        for result in self.optimization_result: merged.append( result )
        self.optimization_result = merged  

        
        return self.optimization_result
    
    
    def predict( self ):
        
        self.prediction_result  ={}
        _predictions = [] 
        
        self.log.append('prediction started')
        for i,m in enumerate(self.models):
            
            try:
                p = m.predict()  
                r = m.optimization_result 
                #p['rates']['id'] = r['id']
                #p['rates']['pattern_id'] = r['pattern_id']
                #p['crm']['pattern_id'] = r['pattern_id']
                #p['crm']['id'] = r['id']

         

                p['rates']['prod_id'] = r['prod_id']
                p['rates']['pattern_id'] = r['pattern_id']
                p['crm']['pattern_id'] = r['pattern_id']
                p['crm']['prod_id'] = r['prod_id']


                s1 = ",".join(m.lumped_producer_names)
                s2 = ",".join(m.lumped_injector_names)
                p['crm']['producers'] = s1 
                p['crm']['injectors'] = s2 
                p['rates']['producers'] = s1 
                p['rates']['injectors'] = s2 
                
                 
                
                _predictions.append( p ) 
                self.log.append(f'prediction for model {i} finished, progress {100.0*(1+i)/len(self.models)}')
                
            except Exception as e:
                print(str(e))
                self.log.append( 'Prediction failed ' + str(e) )
    
    
      
        try: 
            rates = [ p['rates'] for p in _predictions ]
            if len(rates)>0: rates = pd.concat( rates, axis = 0 )
            self.log.append('rates processed')

            crms = [ p['crm'] for p in _predictions ]
            if len(crms)>0: crms = pd.concat( crms, axis = 0 )
            self.log.append('waterflood results processed')

            self.prediction_result = { 'crm': crms, 'rates': rates , 'optimization':  self.optimization_result }
            self.log.append('prediction results processed')

        except Exception as e:
            self.log.append('processing prediction results failed')
          

        return self.prediction_result


    
