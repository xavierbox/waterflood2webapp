function prepare_crm_simulation_export( crm_control_setup, project_setup_details) {
                    

    console.log('Debugging setting a crm simulation parameters launch');

    //crm setup
    //let crm_control_setup = evt.detail['crm_setup'];
    console.log('crm_control_setup', crm_control_setup);
    console.log('balabce', crm_control_setup.simulation.balance);


    //project name, sectors, subzone, etc.... 
    //let project_setup_details = get_project_data_selection();
    let subzone = project_setup_details['subzone'];

    console.log( project_setup_details );


    let sim_params = {

        project_name: project_setup_details['project_name'],
        
        filters : {
            sector: project_setup_details['sector'],
            subzone: project_setup_details['subzone'],
            date: project_setup_details['date'],
        },


        managed_folder_name: 'azFolder', 
        app_name: 'WF', 
        data_folder_name: 'data', 
        projects_folder_name: 'projects', 
        studies_folder_name: 'studies',
        dt: 1, 
        max_running_time: 1000, 
       
        primary: true, 
        regularization: 0.0,  
    
        //from the control 
        //export_only : crm_control_setup.export_only,
        //distance : crm_control_setup.distance, 
        //explicit: { 'subzone' : { subzone:{} } }

        
    } 

    sim_params.export_only = crm_control_setup.export_only;
    sim_params.distance = crm_control_setup.distance; 

    sim_params['explicit'] = {
        subzone: {
            [subzone]: crm_control_setup.explicit
        }
    };


    //sim_params['explicit'] = { 'subzone': { `{subzone}`: crm_control_setup.explicit} };
    sim_params['simulation'] = crm_control_setup.simulation; 
    sim_params['simulation']['balance']= {'type': crm_control_setup.simulation.balance, 'max_iter': 100, 'tolerance': 0.01}
    sim_params['simulation']['optimizer']= {'maxiter': 1234, 'name': 'SLSQP', 'tolerance': 0.001} 

    return sim_params;
 

}

