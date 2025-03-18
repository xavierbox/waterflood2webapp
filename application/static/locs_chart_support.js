let selected_well_names = undefined;
let locs_chart_initialized = false; 

function set_selected_well_names( names ){
    selected_well_names = names != undefined ? Array.from(names) : undefined;   
    console.log('Selected well names', selected_well_names!=undefined);

    if( names!=undefined)
        Id('well-selection-indicator').classList.add('active');
    else 
    Id('well-selection-indicator').classList.remove('active');
    

}

function populate_locations_plot( data ){
    let app_layout = Id('main-layout');
    let where = 'middle-top';
    let locs_container = app_layout.get_pane(where);// Id('locs-chart');
    //locs_container.innerHTML = '';   
    key = 'locations';
    l = data[key]['layout'];
    l['height'] = locs_container.offsetHeight;
    l['autosize'] = true;

    if( locs_chart_initialized == true){
    let layout = locs_container.layout;
    console.log( '-------------------------',layout )
    }

    Plotly.react(locs_container, data[key]['data'], l, {responsive: true})
    .then((p)=>{
        locs_chart_initialized = true;
        relayout( locs_container );
        set_selected_well_names( undefined );

        p.on('plotly_selected', function(eventData) {
            if (eventData) {
                console.log("Selection type:", eventData.range ? "box" : "lasso");
                console.log("Selected data points:", eventData.points);

                let local_selected_well_names = [];
                for( let point of eventData.points){
                    let index = point.pointIndex;
                    let well_name = point.data.text[index];
                    local_selected_well_names.push(well_name);
                }

                set_selected_well_names( local_selected_well_names );
                //console.log('Selected well names:', selected_well_names);
            }
            else{
                console.log('No data selected');
                set_selected_well_names( undefined );
            }
        });

        resizeObserver.observe(locs_container);


    }); 

    // this works !!
    // Plotly chart initialization
    //app_layout.addEventListener('pane-resized', (evt)=>{
    //if( evt.detail.id.includes(where) )
    //{relayout( locs_container );}}) ;
    


}

function dummy( data ){

    console.log('Populating dummy plots...');

    // Sample data for the plots
    const x = [1, 2, 3, 4, 5];
    const y1 = [10, 15, 13, 17, 14];
    const y2 = [5, 10, 7, 12, 9];
    const y3 = [2, 4, 5, 8, 6];

    const y1b = [13, 12, 13, 11, 16];

    // Define the individual traces
    const trace1 = {
        x: x,
        y: y1,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Plot 1',
        xaxis: 'x1',
        yaxis: 'y1',
        name: 'Sector1',legendgroup: 'group1'
    };
    const trace1b = {
        x: x,
        y: y1b,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Plot 1',
        xaxis: 'x1',
        yaxis: 'y1',name: 'Sector2',legendgroup: 'group2' 
    };
    const trace2 = {
        x: x,
        y: y2,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Plot 2',
        xaxis: 'x2',
        yaxis: 'y2',name: 'Sector1',legendgroup: 'group1',showlegend: false  
    };
    const trace2b = {
        x: x,
        y: y1b,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Plot 2',
        xaxis: 'x2',
        yaxis: 'y2',name: 'Sector2',legendgroup: 'group2',showlegend: false  
    };
    const trace3 = {
        x: x,
        y: y3,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Plot 3',
        xaxis: 'x3',
        yaxis: 'y3',name: 'Sector1',legendgroup: 'group1' ,showlegend: false 
    };
    const trace3b = {
        x: x,
        y: y1b,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Plot 2',
        xaxis: 'x3',
        yaxis: 'y3',name: 'Sector2',legendgroup: 'group2',showlegend: false  
    };


    const layout = {
        title: {text:'Plotly Subplots with Shared X-axis'},
        grid: {rows: 1, columns: 3, pattern: 'independent'},
        xaxis1: {domain: [0, 0.28], title: {text:'X Axis'}},
        yaxis1: { title:{text: 'Y1'}},
        
        xaxis2: {domain: [0.37, 0.65], title: {text:'X Axis'}},
        yaxis2: { title:{text: 'Y2'}},

        xaxis3: {domain: [0.72, 1], title: 'X Axis'},
        yaxis3: { title:{text: 'Y3'}},

        legend: {
            orientation: "v",
            x: -0.1,   // Move legend to the left
            y: 1,      // Align legend to the top
            xanchor: "right", 
            yanchor: "top"
        },
        margin: {l: 50},  // Increase left margin to accommodate the legend

        annotations: [
            {
                text: "Subtitle 1",
                x: 0.1, y: 1.15,  // Position above first subplot
                xref: "paper", yref: "paper",
                showarrow: false,
                font: {size: 14, color: "gray"}
            },
            {
                text: "Subtitle 1",
                x: 0.5, y: 1.15,  // Position above first subplot
                xref: "paper", yref: "paper",
                showarrow: false,
                font: {size: 14, color: "gray"}
            },
            {
                text: "Subtitle 1",
                x: 0.9, y: 1.15,  // Position above first subplot
                xref: "paper", yref: "paper",
                showarrow: false,
                font: {size: 14, color: "gray"}
            }]

    };

    // Render the plot
    //Plotly.newPlot('plot', [trace1,trace1b, trace2,trace2b, trace3, trace3b ], layout);

    // Render the plot
    let app_layout = Id('main-layout');
    let where = 'middle-bottom';
    let container = app_layout.get_pane(where);
    container.innerHTML = '';
    console.log('Container:', container);
    console.log(container.id);

    Plotly.newPlot(container,[trace1,trace1b, trace2,trace2b, trace3, trace3b ],layout, {responsive:true})
    .then(function (gd) {
        // Listen for zoom events
        plots = gd ; 

        function f (eventData) {
            if (eventData['xaxis.range[0]'] && eventData['xaxis.range[1]']) {
                const update = {
                    'xaxis1.range': [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']],
                    'xaxis2.range': [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']],
                    'xaxis3.range': [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']]
                };
                Plotly.relayout(gd, update);
            }
            if (eventData['xaxis3.range[0]'] && eventData['xaxis3.range[1]']) {
                const update = {
                    'xaxis.range': [eventData['xaxis3.range[0]'], eventData['xaxis3.range[1]']],
                    'xaxis2.range': [eventData['xaxis3.range[0]'], eventData['xaxis3.range[1]']],
                    //'xaxis3.range': [eventData['xaxis3.range[0]'], eventData['xaxis3.range[1]']]
                };
                Plotly.relayout(gd, update);
            }

            if (eventData['xaxis2.range[0]'] && eventData['xaxis2.range[1]']) {
                const update = {
                    'xaxis.range': [eventData['xaxis2.range[0]'], eventData['xaxis2.range[1]']],
                    //'xaxis1.range': [eventData['xaxis2.range[0]'], eventData['xaxis2.range[1]']],
                    //'xaxis2.range': [eventData['xaxis2.range[0]'], eventData['xaxis2.range[1]']],
                    'xaxis3.range': [eventData['xaxis2.range[0]'], eventData['xaxis2.range[1]']]
                };
                Plotly.relayout(gd, update);
            }
            if (eventData['xaxis1.range[0]'] && eventData['xaxis1.range[1]']) {
                const update = {
                    'xaxis.range': [eventData['xaxis1.range[0]'], eventData['xaxis1.range[1]']],
                    //'xaxis2.range': [eventData['xaxis1.range[0]'], eventData['xaxis1.range[1]']],
                    //'xaxis3.range': [eventData['xaxis1.range[0]'], eventData['xaxis1.range[1]']]
                };
                Plotly.relayout(gd, update);
            }




        };

        //let events = ['plotly_autosize', 'plotly_deselect', 'plotly_doubleclick', 'plotly_redraw']          gd.on('plotly_relayout', (eventData) =>{ f(eventData) });
        //for( let e of events ){
        //console.log(e);   
        //    gd.on( e, (eventData) =>{ f(eventData,gd) });
        //}
        gd.on('plotly_relayout', (eventData) =>{ f(eventData) });
        gd.on('plotly_restyle', (eventData) =>{ f(eventData) });        
        gd.on('plotly_doubleclick', function() {
            Plotly.relayout(gd, {
                'xaxis2.autorange': true,
                'yaxis2.autorange': true,
                'xaxis3.autorange': true,
                'yaxis3.autorange': true,
                'xaxis.autorange': true,
                'yaxis.autorange': true
                
                
            });
        });
        

        //this works
        //app_layout.addEventListener('pane-resized', (evt)=>{
        //    if( evt.detail.id.includes(where) )
        //    {relayout( container );}}) ;



        resizeObserver.observe(container);






    /* Id('plot-container-app').onresize = function(){
            Plotly.Plots.resize(gd);
        };

        window.addEventListener('resize', () => {
        Plotly.Plots.resize('plot');
        });*/

    });

}
    