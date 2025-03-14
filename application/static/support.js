function get_server(iurl, imethod, idata, resolve, reject) {

    return new Promise((resolve, reject) => {
            $.ajax({
                type: imethod,
                url: iurl,
                xhr: function () { return new window.XMLHttpRequest(); },

                processData: false,
                contentType: 'application/json',
                data: idata,
                success: function (resp) {
                    
                let obj = resp;//JSON.parse( resp )
                console.log('success')
                if (resolve != undefined) resolve(obj);
                },
                error: function (jqXHR, status, errorThrown) {
                    console.log('error', jqXHR, 'status', status, 'thrown', errorThrown);
                    console.log('status', status);
                    console.log('errorThrown', errorThrown);
                    
                    let error_message = jqXHR.responseText
                    let message = 'Error in the backend.\nThe error was:\n'+ error_message + '\n\n'+ '\nThe status code was: '+jqXHR.status
                    console.log( message );

                    if (reject != undefined) reject(jqXHR,status, errorThrown );
                }
            });
        });//ajax promise
}
 
function populate_project_description( data ){

    console.log('Populating project description...');
    console.log(data);

    console.log(typeof(data),data['reservoir_management_units']);
    Id('reservoir-unit-selector').setData( data['reservoir_management_units']);          
    Id('sector-selector').setItems('Sector ', data['sectors'] );
    Id('end-date').value = new Date(data['dates'][1]).toISOString().slice(0, 10);
    Id('start-date').value = new Date(data['dates'][0]).toISOString().slice(0, 10);
    Id('study-selector').set_data(data['studies']);
    Id('workflow-selector').set_data(data['workflows']);         
}

function get_project_data_selection( ){

    let data = {}
    data['reservoir_management_units'] = Id('reservoir-unit-selector').getValue();
    
    data['dates'] = [Id('start-date').value, Id('end-date').value];
    data['sectors'] = Id('sector-selector').getCheckedItems();

    return data;
    /*.setData( data['reservoir_management_units']);          
    Id('sector-selector').setItems('Sector ', data['sectors'] );
    Id('end-date').value = new Date(data['dates'][0]).toISOString().slice(0, 16);
    Id('start-date').value = new Date(data['dates'][1]).toISOString().slice(0, 16);
    Id('study-selector').set_data(data['studies']);
    Id('workflow-selector').set_data(data['workflows']);        */ 
}

function populate_field_plots( data ){
    console.log('Populating field plots...');
    
    let field_plots = []; 
    
    let app_layout = Id('main-layout');

    let where = 'middle-top';
    let locs_container = app_layout.get_pane(where);// Id('locs-chart');
    locs_container.innerHTML = '';
    /*
    
    let locs_data = data['locations'];
    let locs_plot = document.createElement('div');
    locs_container.appendChild(locs_plot);
    locs_plot.id = 'locs-plot';
    */
    key = 'locations';
    l = data[key]['layout'];
    l['height'] = locs_container.offsetHeight;
    l['autosize'] = true;
    Plotly.newPlot(locs_container, data[key]['data'], l, {responsive: true});                 
    field_plots.push(locs_container);
    
    /**/
    function relayout( container){

        //container.style.padding = '20px';
        let inner_offset = 10; 
        let pad = 50;
        const update = {
            title: {text: 'some new title'}, // updates the title
            'width':   (parseInt( container.offsetWidth ) - pad).toString(),   // updates the xaxis range
            'height':  (parseInt(container.offsetHeight ) - pad/2).toString(),   // updates the end of the yaxis range
            
            //'paper_bgcolor': 'orange',
            'plot_bgcolor': 'lightgrey',

            //'x': inner_offset,
            'margin': {
            'l': 8,
            'r': 8,
            'b': 8,
            't': 8,
            //'pad': 4  
            },
            'autosize': true,
            
            };
            Plotly.relayout(container, update);

    }
   
    // Plotly chart initialization
    app_layout.addEventListener('pane-resized', (evt)=>{
    if( evt.detail.id.includes(where) )
    {relayout( locs_container );}}) ;relayout( locs_container );

    /**/


    let chart_keys = ['fractions','historical_production'];
    let container =   Id('field-charts-container');
    container.innerHTML = '';
    for( let key of chart_keys){

        let plot = document.createElement('div');
        container.appendChild(plot);
        plot.id = 'field-plot-'+key;
        Plotly.newPlot(plot, data[key]['data'], data[key]['layout'], {responsive: true});    
        container.appendChild(document.createElement('hr'));
        field_plots.push(plot);
    }

    let activity_container = Id('activity-charts-container');
    activity_container.innerHTML = '';
    let activity_data = data['activity'];
    let plot = document.createElement('div');
    activity_container.appendChild(plot);
    plot.id = 'activity-plot';
    Plotly.newPlot(plot, activity_data['data'], activity_data['layout'], {responsive: true});  
    field_plots.push(plot);

    let sector_container = Id('sector-charts-container');
    sector_container.innerHTML = '';
    plot = document.createElement('div');
    sector_container.appendChild(plot);
    plot.id = 'sector-plot-volumes';
    Plotly.newPlot(plot, data['sector_volumes']['data'], data['sector_volumes']['layout'], {responsive: true});


    let containers = document.querySelectorAll('.field-chart-container');

    

    }
    /*for( let svg_container of svg_containers){
        svg_container.style.height = '100%';
        //svg_container.style.width = '100%';
    }*/

    //console.log('Field plots populated');

//}


function get_project_description_mock_server(){

    let wokflow_names=['Liquid history match', 
         'Watercut history match', 
         'Static pattern flow balancing',
         'Lagged correlation analysis' 
         ]

    let backend_data  = {
        'workflows': wokflow_names,
        'studies':['Study 1', 'Study 2', 'Study 3'],
        'reservoir_management_units': ['RMU 1', 'RMU 2', 'RMU 3'],
        'sectors': ['Sector 1', 'Sector 2', 'Sector 3'],    
    }

    return backend_data;

}

function showCard(cardId, btn) {
    document.getElementById('data-selection-card').style.display = 'none';
    document.getElementById('studies-selector-card').style.display = 'none';
    document.getElementById('views-selector-card').style.display = 'none';
    //document.getElementById('workflows-selector-card').style.display = 'none';
    document.getElementById(cardId).style.display = 'block';

    //Id('data_studies_views_buttons').querySelectorAll('.btn-sm').forEach((btn)=>{
    //    btn.classList.remove('active');
    //});
    btn.classList.add('active');
}


 

