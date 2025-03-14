
from datetime import date, datetime
import pickle, numpy as np, pandas as pd
 
from wf_lib2.crm_helper import CRMHelper
from wf_lib2.crm_definitions import *
from wf_lib2.data.crm_data_utils import check_if_time_gaps#, get_time_intersection


#def integrated_error( yhat, ytrue, squared = False): 
#
#    sum1 = yhat.sum()
#    sum2 = ytrue.sum()
#    error = ((sum1-sum2)**2)**0.5 if squared == False else (sum1-sum2)**2
#    return  error 


class CRMProcess:
    
    '''
    The class defines a minimum interface that all the simulators must implement 
    in order to be called by the Simulation scheduller. 
    
    Processes: 
        Kovalc calculations, all the CRM models and other calculations done such as the Time-Lagged 
        estimations are subclasses of a CRMProcess. In essence a CRMProcess is a calculation that operates 
        on a dataset (called pattern) and produces a result: CRMProcessResult.

        When sharing the same interface, all the processes can be treated in the same way by a higher-level
        orchestration logic such as the SimulationScheduller.
    
    Outputs:  
    
        The outputs of the methods fit and quick_fit must always be of the type OptimizationResult. 
        The output of the method predict must be of the type SimulationResult. 
        The objec SimulationResult can be an input to other processes, thus allowing chanining processes  
        in serial within a pipeline. For instance, a CRMModel may the done first and the 
        results passed to a Kovalc calculation. In order for this logic to work and to prevent the need 
        of treating every case as an special case, the common interface is needed. 
        (Please see the notes on OptimizationResult and SimulationResult in the documentation.)
    
    Inputs:
    
        All the Processes operate on a  pattern (or SimulationResult) and some configuration parameters may 
        be provided (input_args). If none configuration parameters are provided, the models should 
        beave according to a default set of parameters as returned by get_default_parameters.
        For the case of the CRMModels the input is a pattern. For Kovalc, the input is either a pattern 
        or a SimumulationResult (both implement the same interface)
        The configuration arguments will depend on the process itself. In general these are dictionaries 
        or subclasses of the standard dictionary class. 
    
    Note on optimization processes
    
        The method fit_preprocess must be called before fit or quick_fit. All the configuration that 
        the process may need must be included in such fit_preprocess method. 

    
    '''
    
    def __init__(self, name = None, extra =0 ):
        self._name = name
        self.extra = extra 
        self.log = [] 
       
    def fit_preprocess(self, pattern, input_args=None, verbose=False):
        #method is empty because it is an abstract class
        return self 
                 
    def fit(self, verbose=False): 
        #method is empty because it is an abstract class
        pass
    
    def quick_fit(self,verbose=False):
        #method is empty because it is an abstract class
        pass
    
    def predict( self ):
        #method is empty because it is an abstract class
        pass
    
    def get_default_params(  self ):
        #method is empty because it is an abstract class
        pass

        
class CRMSingleModel(CRMProcess):
    
    def __init__(self, name = None ):
        super().__init__(name)
        self.producer_name = None 
        self.injector_names = None 
 
    def _clear( self ):
        self._state = {} 
        self.optimization_result = None 
        self.prediction_result = None 
        self.forecast_result = None 
        self.log = [] 
        self._data = None 
        self.has_bhp = None 

        
    def _init_state(self, args):
        
        args['counter'] = 0 
        
        now = np.datetime64('now')#datetime.now() 
        args['start_time'] = now #'datetime.strftime( now, format = "%Y-%m-%d" )
        args['elapsed_time'] = 0 

        
        self._state = { }
        self._state.update( args )
        
        return self._state 

    def save_file( self,file_name ):
        '''
        Trys to save a binary representation of the object in a file. 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (string):  the complete file path  
        '''
        
        with open( file_name, 'wb') as f: pickle.dump(self, f)
            
    @staticmethod 
    def load_file( file_name ):
        '''
        Trys to load a binary file (serialized object). 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (string):  the complete file path  
        '''
        with open(file_name, 'rb') as f:  return pickle.load(f)   
               
    def save_file_desriptor( self, fd ):  
        '''
        Trys to save a model into an open file (or download stream as in Dataikui) 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (stream):  the complete file path  
        '''
        pickle.dump(self, fd)
    
    def load_file_descriptor( self, fd ): 
        '''
        Trys to load a model from an open file (or download stream as in Dataikui) 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (stream):  the open file descriptor
        '''
        return pickle.load(fd)
     
    @property
    def name(self): return self._name
     
    def _validate_input_pattern( self, p ):
         
        names = ",".join (['I:']+list(p.injector_names) + ['P:']+list(p.producer_names) )
        self.log.append(  f'[_validate_input_pattern] for {names}' )
   

        dfs = [ p.water_injection, p.liquid_production  ]  

        DATE = DATE_KEYS[0].upper()
        for df in dfs:
            
            if not isinstance(df, pd.DataFrame):
                error = "[_validate_input_pattern] Error: processing inj,prod. These must be dataframes"
                self.log.append(  error )
                raise ValueError(error)
                
            if df.index.name is None  or DATE not in df.index.name.upper():
                error = '[_validate_input_pattern] Error: The index of the dataframes must be a date.'
                self.log.append(  error )
                raise ValueError( error )
                
            #if check_if_time_gaps(df) == True: 
            #    error = '[_validate_input_pattern] There is an error in the dataset. There are missing dates or repeated ones. Please fix your data'
            #    self.log.append(  error )
            #    raise ValueError(error)  
            


    def adjust_training_testing_dates( self, single_producer_pattern, args ):
        
 
        dates = args['dates']
        if len(dates)<3: dates.append('2200-11-20')
        date1, date2,date3 = dates[0], dates[1], dates[2]

        names = ",".join (['I:']+list(single_producer_pattern.injector_names) + ['P:']+list(single_producer_pattern.producer_names) )
        
        self.log.append(  f'[adjust_training_testing_dates] received {date1}, {date2}' )
        
        water_injection   = single_producer_pattern.water_injection 
        liquid_production = single_producer_pattern.liquid_production 
       
              
        #convert everything to timestamp
        date_format = '%Y-%m-%d'
        if isinstance( date1, str ): #assume both are str
            date1, date2 = datetime.strptime(date1, date_format).date(),datetime.strptime(date2, date_format).date()
            date3 =  datetime.strptime(date3, date_format).date()
            
            #date1,date2,date3 = np.datetime64( date1),np.datetime64( date2),np.datetime64( date3 )
        try:
            date1, date2 = pd.Timestamp(date1),pd.Timestamp(date2)
            date3 = pd.Timestamp(date3)


        except: 
            error= f'[slice_dates] date1{type(date1)} and date2{type(date2)} and date3{type(date3)} must be str or timestamps'
            self.log.append( error )
            raise ValueError(error) 


        #t1 must (start of training) must be > the firs uptick of the producer 
        #first slice the producer to the user dates >= date1 and check if it is active 

        producer_name = liquid_production.columns[0]
        vliquid = liquid_production[ pd.to_datetime(liquid_production.index).values >= date1] 
        uptick_prodution = vliquid[ vliquid[producer_name] > MIN_PRODUCTION_LEVEL ]
        if uptick_prodution.shape[0] < 1:
            raise ValueError(f'[adjust_training_testing_dates] The uptick time for producer {producer_name} is zero for the time-frame selected.')


        producer_days_active = uptick_prodution.shape[0]
        
        #this is the beginnning of the training 
        date1 = max( date1, pd.to_datetime(uptick_prodution.index).values.min() )
      
        # max allowed for training must be smaller than the max of producer 
        date2 = min( date2, pd.to_datetime(uptick_prodution.index).values.max() )
       
        #up to when is that we can do predictions ? 
        #in principle, up to when I have signal in the producer or a lesser time if there is one
        date3 = min(date3, pd.to_datetime(uptick_prodution.index).values.max() )
       
        
        #now look at the injectors, discard all that are not up more than MIN_UPTICK_INJECTOR of the training-testing time 
        uptick_water = water_injection[ ( pd.to_datetime(water_injection.index).values >= date1) &  ( pd.to_datetime(water_injection.index).values <=date2) ]
        inj_to_keep, inj_to_delete = [], [] 
        for c in uptick_water.columns: 
            values = uptick_water[c]


            up_percent = len(values[ values > MIN_INJECTION_LEVEL ])/(1+len(values))
            
            if up_percent < MIN_UPTICK_INJECTOR:
                inj_to_delete.append( c )
                error = f'[adjust_training_testing_dates] Injector {c} will be deleted because uptick percent is {up_percent}'
                self.log.append(error)
                
            else: inj_to_keep.append( c )

        single_producer_pattern.delete_wells( inj_to_delete )
        single_producer_pattern.slice_dates( date1, date3 )


 
        if single_producer_pattern.liquid_production.shape[0] < 5:

            error = f'[adjust_training_testing_dates] Error: The producer {single_producer_pattern.producer_names[0]} is active less than 5 time steps for the time-frame selected.'
            self.log.append(error)
            raise ValueError(error)

        if producer_days_active < 5:
            error = f'[adjust_training_testing_dates] Error: The producer {single_producer_pattern.producer_names[0]} is active less than 5 time steps for the time-frame selected.'
            self.log.append(error)
            raise ValueError(error)
        

        if len(inj_to_keep)<1:
            error =f'[adjust_training_testing_dates]  Error:  {names} No injectors active for the selected timeframe'
            self.log.append(error)
            raise ValueError(error)
            
        if len(inj_to_delete)>0:
            self.log.append("[{}] [adjust_training_testing_dates] Some injectors will be removed from the calculation: {}".format(names, ','.join(inj_to_delete) ))



        if single_producer_pattern.water_injection.shape[0] != single_producer_pattern.liquid_production.shape[0]:

            #the injectors may have started later than the producers, or simply stopped before.
            #what we can do is to try to get an interval inside the current one, where there is some injection
             
            self.log.append('[adjust_training_testing_dates] After all the manipulation, we still cant match the dates for injectors and producers.')

            water_injection = single_producer_pattern.water_injection
            liquid_production = single_producer_pattern.liquid_production
            t1 = pd.to_datetime(water_injection.index).values.min()
            t2 = pd.to_datetime(water_injection.index).values.max()
            t3 = pd.to_datetime(liquid_production.index).values.min()
            t4 = pd.to_datetime(liquid_production.index).values.max()
            
            t1 = max( t1, t3 )
            t3 = min( t2, t4 )

            date1= max( date1, t1 )
            date3= min( date3, t3 )
            date2= min( date2, t3 )
            single_producer_pattern.slice_dates( date1, date3 )

            if single_producer_pattern.water_injection.shape[0] != single_producer_pattern.liquid_production.shape[0]:
                error = f'{names} [adjust_training_testing_dates] Error: Missmatch in production/injection data. Time gaps, repeated dates,non-intersecting time window or inative producer in time t1'
                self.log.append(error)
                raise ValueError( error )
            
        self.log.append(f'[adjust_training_testing_dates]  Re-adjusted tdate1 to  {date1}  ' )
        self.log.append(f'[adjust_training_testing_dates]  Re-adjusted tdate2 to  {date2}  ' )
        self.log.append(f'[adjust_training_testing_dates]  Re-adjusted tdate3 to  {date3}  ' )

        return date1, date2, date3 
    

    def _keep_working(self, xk)->bool:
            
        delta  = np.datetime64('now') - self._state['start_time']
        seconds  = delta.astype('timedelta64[s]').astype('float')
        
        self._state['elapsed_time'] = seconds 
        if seconds  > self._state['max_running_time']: 
            return True 
        return False 
        
   
    
        #seconds = timedelta.astype('timedelta64[s]').astype(np.int32) - start_time
        # 
        #self._state['elapsed_time'] = CRMHelper.elapsed_seconds_since(self._state['start_time'])
        #if self._state['elapsed_time']  > self._state['max_running_time']: 
            #return True 
        #return False 

    def _update_from_optimization(self):

        '''
        This function is called at different times. Its only purpose is to copy to the optimization_result dictionary 
        some values stored in the model state ( while not copying big matrices )
        '''
        state = self._state 
        self.optimization_result = {}
        self.log.append('[update_from_optimization]')

        #new version. Just copy everything except matrices 
        for key, value in   self._state.items():

            if 'inv' in key:
                pass #we dont want the matrices 

            #ndarrays are not by default json-serializable and thats annoying later
            #so we make them a list 
            elif isinstance( value, np.ndarray): 
                self.optimization_result[key] = value.tolist()
                
                
            elif isinstance( value, datetime): 
                self.optimization_result[key] = str(value)
                
                #to datetime again datetime.fromisoformat('2024-08-05 14:01:46.794337')
                
            elif isinstance( value, np.datetime64):
                self.optimization_result[key] = str(value)
                #recover it as np.datetime64( string )
                
            elif isinstance( value, np.float32):
                self.optimization_result[key] = float(value)

                
            elif isinstance( value, np.float64):
                self.optimization_result[key] = float(value)
        
                
            else: self.optimization_result[key] = value


        self.log.append('[update_from_optimization] finished')
        num_injectors = len( state['injector_names'] )
        allocs = state['lambdas'].flatten().tolist()
        self.optimization_result['allocation']   = allocs[0:num_injectors] 
        

    def _fit(self, quick = False, verbose=False):
        raise ValueError(' _fit must be called from a derived class')
    
    def fit( self, verbose = False):
        return self._fit( False, verbose)
            
    def quick_fit( self, verbose = False):
        return self._fit( True , verbose)


class CRMModel:
                   
    def __init__(self, name ):

        self._name = name
        self.failed_models = []
        self._clear()

    def _clear( self ):
     
        self.patterns = None 
        self.single_well_patterns = None 
        self.optimization_result = []
        self.prediction_result  = {}
        self.forecast_result = None 
        self.log = [] 
        self.models = [] 
        self.now_not_private_member = [] 
        self.public_member = [] 


    def _get_submodel( self ):
        raise ValueError('Calling get_submodel, which must be overwritten in a derived class')

    def get_default_params( self ): 
        
        params_ = self._get_submodel().get_default_params()
        return params_
    
    def save_file( self,file_name ):
        '''
        Trys to save a binary representation of the object in a file. 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (string):  the complete file path  
        '''
        
        with open( file_name, 'wb') as f: pickle.dump(self, f)
            
    @property 
    def name( self ): return self._name 

    @staticmethod 
    def load_file( file_name ):
        '''
        Trys to load a binary file (serialized object). 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (string):  the complete file path  
        '''
        with open(file_name, 'rb') as f:  return pickle.load(f)   
               
    def save_file_desriptor( self, fd ):  
        '''
        Trys to save a model into an open file (or download stream as in Dataikui) 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (stream):  the complete file path  
        '''
        pickle.dump(self, fd)
    
    @staticmethod 
    def load_file_descriptor( fd ): 
        '''
        Trys to load a model from an open file (or download stream as in Dataikui) 
        If an exception is raised it will not be handled, it will be passed to the client code 

            Parameters: 

                filename (stream):  the open file descriptor
        '''
        return pickle.load(fd)
     


