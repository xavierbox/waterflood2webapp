
from   wf_lib2.models.crm_p  import CRMPSingle, CRMP,CRMPConstrained,CRMPSingleConstrained
from   wf_lib2.models.crm_ip import CRMIPSingle, CRMIP, CRMIDConstrained, CRMIDSingleConstrained
from   wf_lib2.models.crm_tank import *


def crm_factory( name ):
    name= name.lower().strip()
    
    if 'constrained' in name.lower():
        
        for item in ['crmp', 'crm_p','crm-p']: 
            if item in name: 
                return CRMPConstrained(), 'crmp_constrained'
        
        for item in ['crmid', 'crm_id','crm-id']: 
            if item in name:
                return CRMIDConstrained(), 'crmid_constrained'
        
        raise ValueError('The model needs to be set to either crmp_constrained, or crmid_constrained') 

    
    if name in ['crmp', 'crm_p','crm-p']: return CRMP(), 'crm_p'
    if name in ['crmip', 'crm_ip','crm-ip']: return CRMIP(), 'crm_ip'
    #if name in ['crmtank', 'crm_tank','crm-tank']: return CRMTank(), 'crm_tank'
    if name in ['crmtank', 'crm_tank','crm-tank']: return CRMTankSingle(), 'crm_tank_single'
    
    
    
    
    
    raise ValueError('The model needs to be set to either crm_tank, crm_p, or crm_ip') 
 
  
def crm_single_factory( name ):
    name= name.lower().strip()

    if 'constrained' in name.lower():
        
        for item in ['crmp', 'crm_p','crm-p']: 
            if item in name: 
                return CRMPSingleConstrained(), 'crmp_constrained'
        
        for item in ['crmid', 'crm_id','crm-id']: 
            if item in name:
                return CRMIDSingleConstrained(), 'crmid_constrained'
        
        raise ValueError('The model needs to be set to either crmp_constrained, or crmid_constrained') 

     
    if name in ['crmp', 'crm_p','crm-p']: return CRMPSingle(), 'crm_p_single'
    if name in ['crmip', 'crm_ip','crm-ip']: return CRMIPSingle(), 'crm_ip_single'
    if name in ['crmtank', 'crm_tank','crm-tank']: return CRMTank(), 'crm_tank'
    
    
    raise ValueError('The model needs to be set to either crm_tank, crm_p, or crm_ip') 
 

