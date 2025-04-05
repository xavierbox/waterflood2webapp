

const resizeObserver = new ResizeObserver(entries => {
    for (let entry of entries) {
    //console.log('entry:', entry.target.id);
    //console.log('Size changed:', entry.contentRect);
    //console.log(`Width: ${entry.contentRect.width}px, Height: ${entry.contentRect.height}px`);
    
    relayout( entry.target );

    }
});

function relayout( container){

    //container.style.padding = '20px';
    let inner_offset = 5; 
    let pad = 45;

    let body = document.getElementsByTagName('body')[0];
    const styles = getComputedStyle(body);
    //let color = styles.getPropertyValue('--tint-color')

    const update = {
        //title: {text: 'some new title'}, // updates the title
        'width':   (parseInt( container.offsetWidth ) - pad).toString(),   // updates the xaxis range
        'height':  ( parseInt(container.offsetHeight ) - pad).toString(),   // updates the end of the yaxis range
        
        //'paper_bgcolor': color,
        'textposition':  'top center',
        //'plot_bgcolor':  'darkblue',

        //'x': inner_offset,
        'margin': {
        'l': inner_offset,
        'r': inner_offset,
        'b': 10*inner_offset,
        't': inner_offset,
        //'pad': 4  
        },
        'autosize': true,
        
        };
    Plotly.relayout(container, update);

}

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
    function rmu_selection_changed(evt){
            let subzone_selected =Id('reservoir-unit-selector').getValue();
            let data = JSON.parse( Id('reservoir-unit-selector').dataset.info );
            let reservoir = Object.keys(data['reservoirs'])[0];
            let sectors = data['reservoirs'][reservoir][subzone_selected];
            Id('sector-selector').set_data( sectors );
    }
    //pick the first reservoir regardless of how many there are.
    let reservoir = Object.keys(data['reservoirs'])[0];
    let subzone_names = Object.keys(data['reservoirs'][reservoir]);
    Id('reservoir-unit-selector').setData( subzone_names);
    Id('reservoir-unit-selector').dataset.info = JSON.stringify(data);

    Id('reservoir-unit-selector').removeEventListener('change', rmu_selection_changed );
    Id('reservoir-unit-selector').addEventListener('change', rmu_selection_changed );

    Id('end-date').value = new Date(data['dates'][1]).toISOString().slice(0, 10);
    Id('start-date').value = new Date(data['dates'][0]).toISOString().slice(0, 10);
    Id('study-selector').set_data(data['studies']);
    Id('workflow-selector').set_data(data['workflows']);     
    
    Id('project_name').innerHTML = data['project_name'];

}

function get_project_data_selection( ){

    let data = {}
    data['subzone'] = Id('reservoir-unit-selector').getValue();
    data['date']   = [Id('start-date').value, Id('end-date').value];
    data['sector'] = Id('sector-selector').getCheckedItems().map(str => parseInt(str));
    data['project_name'] = Id('project_name').innerHTML;
    

    if(selected_well_names != undefined)
        data['name']   = selected_well_names
    //else
    //    data['name']   = all_well_names_visible;
    
 
    return data;
    /*.setData( data['reservoir_management_units']);          
    Id('sector-selector').setItems('Sector ', data['sectors'] );
    Id('end-date').value = new Date(data['dates'][0]).toISOString().slice(0, 16);
    Id('start-date').value = new Date(data['dates'][1]).toISOString().slice(0, 16);
    Id('study-selector').set_data(data['studies']);
    Id('workflow-selector').set_data(data['workflows']);        */ 
}


function populate_field_plots( data ){

    let field_plots = [];
    let chart_keys = ['fractions','historical_production'];
    let container =   Id('field-charts-container');
    container.innerHTML = '';

    let div1  = document.createElement('div');div1.classList.add('plots-tab-1');
    let div2  = document.createElement('div');div2.classList.add('plots-tab-2');
    div1.style.height = '100%';
    div1.style.width  = '100%';
    div2.style.height = '100%';
    div2.style.width  = '100%';
    div1.style.display = 'flex';
    div1.style.flexDirection = 'column';
    div1.style.flexWrap = 'wrap';
    div2.style.display = 'flex';
    div2.style.flexDirection = 'column';
    div2.style.flexWrap = 'wrap';
    
    container.appendChild(div1);
    container.appendChild(div2);
    //




    for( let key of chart_keys){

        //xdata.push(data[key]['data']);
        /*let plot = document.createElement('div');
        plot.classList.add('plots-tab-1');
        plot.id = 'field-plot-'+key;
        plot.style.height =   '33%';
        plot.style.minHeight = '33%';
        plot.style.maxHeight = '33%';
        plot.style.width     = '100%';
        container.appendChild(plot);
        console.log('appendsing oine')*/

        /*let plot = document.createElement('div');
        plot.style.height    =   '33%';
        plot.style.minHeight = '33%';
        plot.style.maxHeight = '33%';
        plot.style.width     = '100%';
        plot.style.display = 'flex';
        plot.style.flexDirection = 'row';*/

        //div1.appendChild(plot);
        Plotly.newPlot(div1, data[key]['data'], data[key]['layout'], {responsive: true}).then ((p)=>{});    
        
   
        
    }
    //const layout = { autosize:true, grid: { rows: 2, columns: 1, pattern: 'independent' }};
    //Plotly.newPlot(container, xdata, layout, {responsive: true}).then((p)=>{  
    //relayout( container );
    //});
    //resizeObserver.observe( xplot );

   
    let activity_container = container;

    let activity_data = data['activity'];

   /*
    let plot = document.createElement('div');
    activity_container.appendChild(plot);
    plot.id = 'activity-plot';
    plot.classList.add('plots-tab-1');
    plot.style.height =   '33%';
    plot.style.minHeight = '33%';
    plot.style.width     = '100%';*/


    Plotly.newPlot(div1, activity_data['data'], activity_data['layout'], {responsive: true})
    .then ((p)=>{

        setTimeout(() => {
            document.querySelectorAll('.js-plotly-plot').forEach(xplot => {Plotly.Plots.resize(xplot);});
            Id('main-layout').addEventListener('pane-resized', (evt) =>{
                document.querySelectorAll('.js-plotly-plot').forEach(xplot => {Plotly.Plots.resize(xplot);});
            });

        
        }, 500);

    });
 



    //.then ((p)=>{
    //    resizeObserver.observe( plot );
    //});
    //field_plots.push(plot);
     
    /******
    let sector_container = Id('sector-charts-container');
    sector_container.innerHTML = '';
    */
    /*plot = document.createElement('div');
    container.appendChild(plot);
    plot.id = 'sector-plot-volumes';
    plot.classList.add('plots-tab-2');
    plot.style.height    = '50%';
    plot.style.minHeight = '50%';
    plot.style.width     = '100%';*/
    Plotly.newPlot(div2, data['sector_volumes']['data'], data['sector_volumes']['layout'], {responsive: true})
 


    //.then ((p)=>{
    //    //resizeObserver.observe( plot );
    //    relayout( plot );
    //    }); 


    //field_plots.push(plot);

    /*for( let observed in field_plots ){
        resizeObserver.observe( observed );
    }*/

    //let containers = document.querySelectorAll('.field-chart-container');

    

}

function populate_field_wells_snapshot( data ){

    let div3  = document.createElement('div');div3.classList.add('plots-tab-3');
    div3.style.height = '100%';
    div3.style.width  = '100%';
    let container =   Id('field-charts-container');
    container.appendChild(div3);

    //let container = Id('wells-charts-container');
    //let container =   Id('field-charts-container');


    /*let plot = document.createElement('div');
    plot.classList.add('plots-tab-3');
    plot.style.height =   '100%';
    plot.style.minHeight = '100%';
    plot.style.maxHeight = '100%';
    plot.style.width     = '100%';
    container.appendChild(plot);
    plot.id = 'sector-plot-wells';*/
    const layout = {
        grid: {rows: 3, columns: 1, pattern: 'independent'},
        title: { text:' Cummulated volumes vs water produced'},
        autosize: true,
        automargin: true,
        //margin: {l: 70, r: 40, t: 40, b: 30},
        xaxis1:  {matches: 'x'},
        xaxis2: {matches: 'x'},
        xaxis3: {matches: 'x'},
        xaxis4: {matches: 'x'},
        yaxis1: { title:{text: 'Gas production'}},
        yaxis2: { title:{text: 'Oil production'}},
        yaxis3: { title:{text: 'Liquid production'}},

        //xaxis1: { title:{text:  'Water production'}},
        //xaxis2: { title:{text:  'Water production'}},
        //xaxis3: { title:{text:  'Water production'}},
        
        /*
        xaxis2: { title:{text: 'Water production'}},
        xaxis3: { title:{text: 'Water production'}},*/
        //height: 1000,//  width: 1000,
        
    };

    let p = Plotly.newPlot(div3, data['data'], layout, {responsive: true})
    p.then ((p)=>{
        p.on('plotly_selected', function(eventData) {
            if (eventData) {
                //console.log("---------Selection type:", eventData.range ? "box" : "lasso");
                //console.log("Selected data points:", eventData.points);

                let local_selected_well_names = [];
                for( let point of eventData.points){
                    let index = point.pointIndex;
                    let well_name = point.data.text[index];
                    local_selected_well_names.push(well_name);
                }

                set_selected_well_names_in_scatter_chart( local_selected_well_names );
                //console.log('Selected well names:', selected_well_names);
            }
            else{
                console.log('No data selected');
                set_selected_well_names_in_scatter_chart( undefined );
            }
        });
    }); 

 
    // /resizeObserver.observe( plot );



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


 

