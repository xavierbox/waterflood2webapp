
const chart_title_font_size = 24;
let highlighted_marker_opacity = 0.7;
let highlighted_marker_color = 'orange';
let highlighted_marker_size = 30; 

let locations_chart_pane = 'middle-top';


let selected_well_names_in_scatter_chart = undefined;  //user selected wells in a wells chart 
let selected_well_names = undefined;                   //user selected wells in a locations chart 
let all_well_names_visible = undefined;                //all well names in the locations chart selected or not 
let locs_chart_initialized = false;                    //was the locs chart initialized 

function isEmptyOrWhitespace(str) {
    return str.trim() === "";
}

function isValidDate(date1) {
    const date = new Date(date1);
    return !isNaN(date.getTime()); // Checks if it's a valid date
}

function addMonthsToDate(dateStr, step) {
    let [year, month, day] = dateStr.split('-').map(Number);
    month -= 1; // Convert to 0-based month

    // Add step months manually
    step = Number(step);
    let totalMonths = month + step;
    let newYear = year + Math.floor(totalMonths / 12);
    let newMonth = totalMonths % 12;
    if (newMonth < 0) {
        newMonth += 12;
        newYear -= 1;
    }

    // Get last day of the new month
    let lastDay = new Date(newYear, newMonth + 1, 0).getDate();
    let newDay = Math.min(day, lastDay);

    let resultDate = new Date(newYear, newMonth, newDay);
    return resultDate.toISOString().split('T')[0];
}

function moveDates(direction = 1){
    let [date1,date2,step] = [ Id('start-date').value,Id('end-date').value, Id('range-value').value];

    step = Number(step) * direction;
    date1 = addMonthsToDate(date1, step)
    date2 = addMonthsToDate(date2, step)
    console.log( date1,date2,step )

    Id('start-date').value  = date1;
    Id('end-date').value    = date2;

}

function validateProjectDataSelection(read_data) {
    message = ""

    if(read_data['subzone']==undefined) return "\nInvalid RMU selection\n";
    if(read_data['subzone']=='Select option') return "\nInvalid RMU selection\n";

    
    if(!isValidDate( read_data['date'][0])) message = "\nInvalid start date\n";
    if(!isValidDate( read_data['date'][1])) message += "\nInvalid end date\n";

    return message;
}


/*called when the user selects some wells with the lasso in the locations chart
  the window also emits an event that other component can subscribe to
*/
function set_selected_well_names( names ){
    selected_well_names = names != undefined ? Array.from(names) : undefined;   
    console.log('Selected well names in locs chart', selected_well_names!=undefined);

    if( names!=undefined)
        {Id('well-selection-indicator').classList.add('active');
         //console.log('Selected well names', names);
        }
    
    else 
    Id('well-selection-indicator').classList.remove('active');

    console.log('dispatching wells-names-selected-in-locs-chart');

    window.dispatchEvent(new CustomEvent('wells-names-selected-in-locs-chart', {
        detail: { names: selected_well_names }
    }));
}

function set_selected_well_names_in_scatter_chart( names ){
    selected_well_names_in_scatter_chart = names != undefined ? Array.from(names) : undefined;   
    console.log('Selected well names in scatter chart ', selected_well_names_in_scatter_chart!=undefined);

    window.dispatchEvent(new CustomEvent('wells-names-selected-in-scatter-chart', {
        detail: { names: selected_well_names_in_scatter_chart }
    }));
}


