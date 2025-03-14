
import numpy as np, pandas as pd
import math, random 
from datetime import datetime, timedelta 
from sklearn.preprocessing import MinMaxScaler

from wf_lib2.crm_definitions import RANDOM_SEED
random.seed(RANDOM_SEED)



class CRMHelper:

    @staticmethod
    def get_row_vector_E(tau,dt,time_steps):
        dt_div_tau = dt/tau 
        E = -dt_div_tau * np.array([ n for n in range(time_steps)] ).reshape(1,time_steps)

        #this line is to prevent what appears to cause an overflow (exp(-300) for instance )
        #E [ E < -30 ] = -30 

        
        E = np.exp( E )
        E = (1.0 - math.exp(-dt_div_tau)) * E
        return E
    
 


    @staticmethod
    def primary_production_row( qo, tau, dt, nsteps, start = 0):
        return qo*np.exp( np.array( [ -dt*(start + n)/tau for n in range(nsteps)])).reshape(1,nsteps)
    

    @staticmethod
    def get_matrix_E( taus, dt, steps ):
        '''
        returns the matrix
        
       |   .   .  .      |
       |   .   .  .      | 
       |  T1  T2  T3 ....|
       |   .   .  .      |
       |   .   .  .      |
        
        nrows is nsteps.
        ncols is the number of producers, one per tau 
        
        Several of these matrices can be used in multi-well CRM-IP 
        
        '''
        

        ncolumns = taus.shape[0]
        E_matrix = np.zeros( shape=(steps,ncolumns) )
        
        for column in range( ncolumns ):
            tau = taus[column]
            E_matrix[:,column]= CRMHelper.get_row_vector_E( tau,dt,steps).flatten()
        
        return E_matrix 
        
  
    @staticmethod
    def elapsed_seconds_since(start_time): return (datetime.now()-start_time).microseconds/1.0E6
     
    
    @staticmethod 
    def _to_numpy( data ):

        #the most recent time-step is at the top 
        #if it was a dataframe
        if isinstance(data, pd.DataFrame):
            return data.to_numpy()
        
        elif isinstance(data, pd.Series):
            return data.to_numpy()
        
        elif isinstance(data, pd.core.indexes.base.Index):
            return data.to_numpy()

        #it was a numpy before
        elif isinstance(data, np.ndarray):  
            return data
        
        else: return None
    
    
    @staticmethod 
    def _to_numpy_and_flip( data ):

        '''expects a column vector
           [[1]
            [2]
            [3]
            ...
            ]

            and returns 

            [[fill]
            [1]
            [2]
            [3]
            ...
            ]
        '''

        #the most recent time-step is at the top 
        #if it was a dataframe
        if isinstance(data, pd.DataFrame):
            return np.flip( data.to_numpy(), axis = 0 )

        if isinstance(data, pd.Series):
            return np.flip( data.to_numpy(), axis = 0 )

        if isinstance(data, pd.core.indexes.base.Index):
            return np.flip( data.to_numpy(), axis = 0 )


        #it was a numpy before
        if isinstance(data, np.ndarray):  
            return np.flip( data, axis = 0 )

        return None


    
    
    @staticmethod
    def shift_down( e, fill_value =0 ):
        e = np.roll(e,1)
        e[0] = fill_value
        return e

    '''
    expects a row vector [1,2,....10]
    and returns          [fill, 1,2....]
    '''
    @staticmethod
    def shift_right( e, fill_value =0 ):
        e = np.roll(e,1).flatten()
        e[0]=fill_value
        return e.reshape( 1,len(e))
        #return e.reshape( len(e),1)

    @staticmethod
    def shift_up( e, fill_value = 0.0 ):
        '''
        Takes a series or a column vector and moves all the elements one step up.
        The last element, will be filled with the fill_value provided or zero if none 
        '''
        e = np.roll(e, -1, axis=0)
        e[ len(e)-1] = fill_value 
        return e 

    @staticmethod
    def get_dates( num_days,  year_month_day_date = None ):
        date_str = '2022/06/23' if year_month_day_date is None else year_month_day_date 
        
        base = datetime.strptime(date_str, '%Y/%M/%d').date()
        date_list = [base + timedelta(days=n) for n in range(num_days)]
        return date_list

    @staticmethod
    def construct_row_vector_e( days_minus_one=None, tau_fix=None, dt_fix=None):

        '''
        returns the transpose of this vector:
        [
        [(1-exp(-DT/tau)) exp( 0 )]
        [(1-exp(-DT/tau)) exp( -Dt/tau )]
        [(1-exp(-DT/tau)) exp( -2Dt/tau)]
        [(1-exp(-DT/tau)) exp( -3Dt/tau)]
        ]
        of shape ( Nt x 1 )
        
        note that the [ I1(tn) I1(tn-1) I1(tn-2)...] x e  equals to the entire contribution of I1 to time step tn 
        '''
        dt_div_tau = dt_fix/tau_fix 
        
        e = -dt_div_tau * CRMHelper.get_day_range(days_minus_one )
        e = np.exp( e )
        e = (1.0 - math.exp(-dt_div_tau)) * e
        return  e.reshape( 1,e.shape[0])
      

    @staticmethod
    def get_day_range( days ): return np.linspace(0,days,days+1)
    
    @staticmethod
    def generate_sample_injector_rates( days, internal_length,min_rate, max_rate):

        #E = np.array([(1-exp(-dt/tau))*math.exp(-n*dt/tau) for n in range(Nt) ]).reshape(1,Nt)
        #days = len( get_day_range(Nt) )
        I = [ (int(n%internal_length) == 0)*random.randrange(100*int(min_rate), 100*int(max_rate+1))  for n in range(days)]
        for n in range( len(I) ): 
            if I[n]==0: I[n] = I [n-1]
                
        scaled = MinMaxScaler(feature_range=(1.0*min_rate,1.0*max_rate)).fit_transform(np.array(I,dtype='float').reshape(-1, 1) ).flatten()
        return 1.0*scaled.reshape(days,1)

    @staticmethod
    def generate_production_crmp( injection_rates, tau, dt, alloc =1.0):
        days = injection_rates.shape[0]
        #print('days',  days )
        
        E = CRMHelper.construct_row_vector_e( days-1, tau, dt)
        
        II = np.flip(injection_rates*alloc)
        values = np.zeros( (days,1) )
        for tn in range(0, days ):
            value = np.dot( E, II)
            values[tn]=value 
            E = CRMHelper.shift_right(E)

        values = np.flip( values )
        return values 

    @staticmethod
    def generate_crmp_example_data( config, seed  = None ):
        
        if not seed:
            rng = np.random.default_rng(seed=RANDOM_SEED)
            random.seed( RANDOM_SEED )
        else:
            random.seed( seed )
            rng = np.random.default_rng(seed=seed)
           
        
        days = len( CRMHelper.get_day_range(config['days']))
        tau = config['tau'] 
        dt  = 1.0 * config['dt']        
        allocations = config['allocation']
        injectors_data = config['injectors']
        
        #injectors injection rate per day 
        inj_df = pd.DataFrame({})
        for index, inj in enumerate(injectors_data ):
            min_rate,max_rate,internal_length = inj['min_rate'], inj['max_rate'], inj['internal_length']
            I = CRMHelper.generate_sample_injector_rates(days, internal_length,min_rate, max_rate )
            inj_df.insert(index, 'Inj'+str(index), I.flatten() )
            
        #producer 
        prod_df = pd.DataFrame({})
        P1 = np.zeros( (days,1) )
        
        if isinstance( tau, float ):
            for inj_index in range( len(injectors_data) ): 
                I = inj_df.iloc[:,inj_index].to_numpy().reshape( days,1 )
                alloc = 1.0*allocations[inj_index]
                P1 = P1+ CRMHelper.generate_production_crmp( I, tau, dt, alloc )
 
        if isinstance( tau, list ):
            #print('tau is not the same for all injectors')
            for inj_index in range( len(injectors_data) ): 
                I = inj_df.iloc[:,inj_index].to_numpy().reshape( days,1 )
                alloc = 1.0*allocations[inj_index]
                P1 = P1+ CRMHelper.generate_production_crmp( I, tau[inj_index], dt, alloc )

        prod_df['Producer'] = P1.flatten() 
            
        #add the noise over an otherwise very clean series 
        if 'inj_noise_level' in config:
            noise_level = config['inj_noise_level']
            for col in inj_df.columns:
                noise = noise_level * rng.normal(0,1,inj_df.shape[0])
                inj_df[col] = inj_df[col] * (1.0 + noise) 

        if 'prod_noise_level' in config:
            noise_level = config['prod_noise_level']
            for col in prod_df.columns:
                noise = noise_level * rng.normal(0,1,inj_df.shape[0])
                prod_df[col] = prod_df[col] * (1.0 + noise) 
     
        if 'prod_outlier_freq' in config:
            freq_level = config['prod_outlier_freq']
            for col in prod_df.columns:
                values = prod_df[col]
                mean = np.mean(values)
                x = rng.uniform(low=0, high=1, size=prod_df.shape[0])
                rows_to_modify = np.array(x >= (1-freq_level)).flatten()
                prod_df.loc[rows_to_modify,col]= prod_df.loc[rows_to_modify,col] + 0.5*(-1 + 2.0*np.random.rand())*mean

   
        if 'primary_production' in config: 
            qo = config['primary_production']['qo']
            taup = config['primary_production']['taup']
            start = 0 
            nsteps = prod_df.shape[0]
            dt = config['dt']
            values = qo*np.exp( np.array( [ -dt*(start + n)/taup for n in range(nsteps)])).reshape(1,nsteps).flatten()
           
            
            for col in prod_df.columns:
                prod_df[col] = prod_df[col] + values
                
                
        #locations 
        locs_df = pd.DataFrame( {}, columns = ['NAME', 'X', 'Y'] )
        injectors_data = config['injectors']
        names = inj_df.columns 

        default_locations = [ (1000,0), (0, 1000), (-1000,0), (0,-1000) ] 
        for index, injector in enumerate(injectors_data):
            if 'location' in injector: 
                x,y = injector['location']
            else: x,y = default_locations[index]
            
            locs_df.loc[index] = [ 'Inj'+str(index), x, y ]
       
        #the single producer 
        if 'producer_location' in config:
            x,y = config['producer_location'] 
        else:
            x,y = 0,0 
            
        locs_df.loc[ locs_df.shape[0]] = ['Producer', x,y] 
         
                
        return inj_df ,prod_df, locs_df 
     

