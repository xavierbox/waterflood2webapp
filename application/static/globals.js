
const chart_title_font_size = 24;
let highlighted_marker_opacity = 0.7;
let highlighted_marker_color = 'orange';
let highlighted_marker_size = 30; 

let locations_chart_pane = 'middle-top';


let selected_well_names_in_scatter_chart = undefined;  //user selected wells in a wells chart 
let selected_well_names = undefined;                   //user selected wells in a locations chart 
let locs_chart_initialized = false;                    //was the locs chart initialized 

function isEmptyOrWhitespace(str) {
    return str.trim() === "";
}

function isValidDate(date1) {
    const date = new Date(date1);
    return !isNaN(date.getTime()); // Checks if it's a valid date
}


/*called when the user selects some wells with the lasso in the locations chart
  the window also emits an event that other component can subscribe to
*/
function set_selected_well_names( names ){
    selected_well_names = names != undefined ? Array.from(names) : undefined;   
    console.log('Selected well names', selected_well_names!=undefined);

    if( names!=undefined)
        {Id('well-selection-indicator').classList.add('active');
        console.log('Selected well names', names);
        }
    
    else 
    Id('well-selection-indicator').classList.remove('active');


    window.dispatchEvent(new CustomEvent('wells-names-selected-in-locs-chart', {
        detail: { names: selected_well_names }
    }));
}

function set_selected_well_names_in_scatter_chart( names ){
    selected_well_names_in_scatter_chart = names != undefined ? Array.from(names) : undefined;   
    console.log('Selected well names in scatter chart ', selected_well_names_in_scatter_chart!=undefined);

    if( names!=undefined)
        {Id('well-selection-indicator').classList.add('active');
        console.log('Selected well names in scatter chart', names);
        }
    
    else 
    Id('well-selection-indicator').classList.remove('active');


    window.dispatchEvent(new CustomEvent('wells-names-selected-in-scatter-chart', {
        detail: { names: selected_well_names_in_scatter_chart }
    }));
}


