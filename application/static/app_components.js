
class AAAppMainLayout extends HTMLElement {
    constructor() {
        super();
    }

    getTemplate(){
        // Create the inner HTML structure
        return `
                        <div id="main-layout" class="container-fluid mt-1">
                            <div  class="row">
                                <div class="columns-container">
                                    <!-- Left Pane -->
                                    <div id="left-pane" class="col-2 column" style="position: relative;">
                                        <div id = 'left-top' class="pane flex-grow-2" style="overflow-y: auto;max-height: 170%; flex-basis: 65%;"></div>
                                        <div id = 'left-bottom' class="pane flex-grow-1" style="overflow-y: auto;max-height: 70%; flex-basis: 25%;"></div>
                                    </div>

                                    <!-- Middle Pane -->
                                    <div id="middle-pane" class="col-5 column gx-5" style="position: relative;">
                                        <div id="left-separator" class="separator" style="left: 0;"></div>
                                        <div id = 'middle-top'  class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 50%;"></div>
                                        <div class="handler" style="flex-basis: 2%;"></div>
                                        <div id = 'middle-bottom' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 50%;"></div>
                                    </div>

                                    <!-- Right Pane -->
                                    <div id="right-pane" class="col-5 column" style="position: relative;">
                                        <div  id = 'right-top' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 30%;"></div>
                                        <div class="handler"></div>
                                        <div  id = 'right-bottom' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 70%;">
                                        </div>
                                        <div id="right-separator" class="separator" style="left: 0;"></div>
                                    </div>
                                </div>
                            </div>
                               
                    
                        </div>

                    `;

                    /*<!--div class="row">
                    <!-- Draggable Separator Above Messages -->
                   <div id="messages-separator" class="xxseparator" style="cursor: ns-resize; height: 5px; background: gray;"></div>

                  <div style='padding:20px;overflow-y: scroll;' class="message-container acolumns-container mt-1" id="messages"></div>
               
               
                  </div-->*/

                

    }

    getStyle(){
        return  `

        .message-container{
        background-color: red;    height: 10vh;            
        }

        body {
                background-color: #f5f5f5; /* Smoke white */
            }

            .pane {
                background-color: white;
                border: 1px solid #ddd;
                padding-left: 10px;
                padding-right: 10px;
                padding-top: 10px;
                xxpadding-bottom: 10px;
                
            }

            #left-pane .pane:nth-child(1) {
                background-color: #ffcccc; /* Random light color */
            }

            #left-pane .pane:nth-child(2) {
                background-color: #ccffcc; /* Random light color */
            }

            #left-pane .pane:nth-child(3) {
                background-color: #ccccff; /* Random light color */
            }

            #middle-pane .pane:nth-child(1) {
                background-color: #ffffcc; /* Random light color */
            }

            #middle-pane .pane:nth-child(2) {
                background-color: #ccffff; /* Random light color */
            }

            #right-pane .pane:nth-child(1) {
                background-color: #ffccff; /* Random light color */
            }

            #right-pane .pane:nth-child(2) {
                background-color: #cce5ff; /* Random light color */
            }

            .columns-container {
                display: flex;
                height: 80vh;
                gap: 0;
            }

            .column {
                display: flex;
                flex-direction: column;
                gap: 10px; /* Small gap between rows */
                position: relative;
                height: 100%;
            }

            .separator {
                width: 8px;
                background-color: red;
                cursor: ew-resize;
                position: absolute;
                top: 0;
                bottom: 0;
                z-index: 1;
            }

            .separator:hover {
                background-color: darkred;
            }

            .handler:hover {
                background-color: darkred;
            }

            .handler {
                height: 10px;
                background-color: red;
            }
        `;

    }

    initResizableMessages(){
        return;
        const separator = this.querySelector("#messages-separator");
        const messages = this.querySelector("#messages");
        let xxisResizing = false;
        let xxstartY, xxstartHeight;


        function xxonMouseMove(e) {
            if (!xxisResizing) return;

            //console.log('moving!!!')

            let delta = (e.clientY - xxstartY)
            const newHeight = xxstartHeight - delta;
            messages.style.height = `${newHeight}px`;

            let leftSeparator = this.querySelector('#xxx');

            let h = leftSeparator.offsetHeight + 0.025*delta ;
            console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() +'px';

        }
    
        function xxonMouseUp() {
            xxisResizing = false;

            console.log('up!!!')
            document.removeEventListener("mousemove", xxonMouseMove);
            document.removeEventListener("mouseup", xxonMouseUp);
        }    
        
        separator.addEventListener("mousedown", (e) => {
            xxisResizing = true;
            xxstartY = e.clientY;
            xxstartHeight = messages.offsetHeight;
            document.addEventListener("mousemove",  xxonMouseMove);
            document.addEventListener("mouseup", xxonMouseUp);
            console.log('down!!!')
        });
    


    }


    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.initResizableColumns();
        this.initResizableRows();

        this.initResizableMessages();

        //const style = document.createElement('style');
        //style.textContent = this.getStyle();
        //document.head.appendChild(style);


    }

    initResizableColumns() {
        const leftSeparator = this.querySelector('#left-separator');
        const rightSeparator = this.querySelector('#right-separator');
        const leftPane = this.querySelector('#left-pane');
        const middlePane = this.querySelector('#middle-pane');
        const rightPane = this.querySelector('#right-pane');


        let isResizingLeft = false;
let lastDownXLeft = 0;

leftSeparator.addEventListener('mousedown', (e) => {
    isResizingLeft = true;
    lastDownXLeft = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingLeft) return;

    let offset = e.clientX - lastDownXLeft;
    let newLeftWidth = leftPane.offsetWidth + offset;
    let newMiddleWidth = middlePane.offsetWidth - offset;

    if (newLeftWidth > 50 && newMiddleWidth > 50) {
        leftPane.style.width = `${newLeftWidth}px`;
        middlePane.style.width = `${newMiddleWidth}px`;

    
        //rightPane.style.margin= "5%";
        //rightPane.style.width = "100%";
    

    }

    lastDownXLeft = e.clientX;
});

document.addEventListener('mouseup', () => {
    if (isResizingLeft) {
            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: leftPane.id,
                    offsetWidth: leftPane.offsetWidth,
                    offsetHeight: leftPane.offsetHeight
                }
            }));

            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: middlePane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));
        }
       

isResizingLeft = false;
    document.body.style.cursor = 'default';
});

// For the middle-right separator between middle-pane and right-pane

let isResizingRight = false;
let lastDownXRight = 0;

rightSeparator.addEventListener('mousedown', (e) => {
    isResizingRight = true;
    lastDownXRight = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingRight) return;

    let offset = e.clientX - lastDownXRight;
    let newRightWidth = rightPane.offsetWidth - offset;  // Decrease right-pane width on drag left
    let newMiddleWidth = middlePane.offsetWidth + offset;  // Increase middle-pane width on drag left

    if (newRightWidth > 50 && newMiddleWidth > 50) {
        middlePane.style.width = `${newMiddleWidth}px`;
        //rightPane.style.width = "96%";//`${newRightWidth}px`;
        let x = window.innerWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);

        rightPane.style.width = `${x}px`;//"20%";//`${newRightWidth}px`;
        //rightPane.style.flex_basis = parseInt(100.0*newRightWidth/(newMiddleWidth + newRightWidth ));

    }

    lastDownXRight = e.clientX;
});

document.addEventListener('mouseup', () => {

    if (isResizingRight) {
            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: rightPane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));

            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: middlePane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));
        }

   
    isResizingRight = false;
    document.body.style.cursor = 'default';
});
    }

    initResizableRows() {
        this.querySelectorAll('.handler').forEach(handler => {
            let isDragging = false;

            const onDrag = (e) => {
             
                if (!isDragging) return;

                const parent = handler.parentNode;
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;
                const parentRect = parent.getBoundingClientRect();

                const prevHeight = e.clientY - parentRect.top - prevRow.offsetTop;
                const nextHeight = parentRect.height - prevHeight - handler.offsetHeight;

                const minHeight = 30; // Minimum height in pixels
                if (prevHeight > minHeight && nextHeight > minHeight) {
                    prevRow.style.flexBasis = `${prevHeight}px`;
                    nextRow.style.flexBasis = `${nextHeight}px`;
                }
            };

            const stopDrag = () => {

                if (isDragging) {
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: prevRow.id,
                        newWidth: prevRow.offsetWidth,
                        newHeight: prevRow.offsetHeight
                    }
                }));

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: nextRow.id,
                        newWidth: nextRow.offsetWidth,
                        newHeight: nextRow.offsetHeight
                    }
                }));

            }


                isDragging = false;
                document.body.style.cursor = 'default';
                document.removeEventListener('mousemove', onDrag);
                document.removeEventListener('mouseup', stopDrag);
            };

            handler.addEventListener('mousedown', () => {
                isDragging = true;
                document.body.style.cursor = 'row-resize';
                document.addEventListener('mousemove', onDrag);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }


//api 
addMessage(text) {
    const messagesContainer = this.querySelector("#messages");

    const message = document.createElement("p");
    message.textContent = text;
    messagesContainer.appendChild(message);
    }
setMessage(text) {
    const messagesContainer = this.querySelector("#messages");
    messagesContainer.innerHTML = ""; 
    const message = document.createElement("p");
    message.textContent = text;
    messagesContainer.appendChild(message);
    }
clearMessage(text) {
    const messagesContainer = this.querySelector("#messages");
    messagesContainer.innerHTML = ""; 
    }

// Set content in the specified pane
set(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        if (typeof content === 'string') {
            pane.innerHTML = content;  // Set content as innerHTML if it's a string
        } else if (content instanceof HTMLElement) {
            pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a string or an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
clear(where) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        pane.innerHTML = ''; // Clear existing content
    }
    
    
}
append(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        //if (typeof content === 'string') {
        //    pane.innerHTML = content;  // Set content as innerHTML if it's a string

        if (content instanceof HTMLElement) {
            //pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
get_pane( id ){
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(id)) {
        const pane = this.querySelector(`#${id}`);
        return pane; 
    }

}

}


//works fine but too many divisions
class AppMainLayout1 extends HTMLElement {
    constructor() {
        super();
    }

    getTemplate(){
        // Create the inner HTML structure
        return `
                        <div id="main-layout" class="container-fluid mt-1">
                            <div  class="row">
                                <div id='xxx' class="columns-container">
                                    <!-- Left Pane -->
                                    <div id="left-pane" class="col-2 column" style="position: relative;">
                                        <div id = 'left-top' class="pane flex-grow-1" style="overflow-y: scroll;max-height: 40%; flex-basis: 25%;"></div>
                                        <div id = 'left-middle' class="pane flex-grow-1" style="overflow-y: scroll;max-height: 30%; flex-basis: 50%;"></div>
                                        <div id = 'left-bottom' class="pane flex-grow-1" style="overflow-y: scroll;max-height: 30%; flex-basis: 25%;"></div>
                                    </div>

                                    <!-- Middle Pane -->
                                    <div id="middle-pane" class="col-5 column gx-5" style="position: relative;">
                                        <div id="left-separator" class="separator" style="left: 0;"></div>
                                        <div id = 'middle-top'  class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 150%;"></div>
                                        <div class="handler" style="flex-basis: 2%;"></div>
                                        <div id = 'middle-bottom' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 150%;"></div>
                                    </div>

                                    <!-- Right Pane -->
                                    <div id="right-pane" class="col-5 column" style="position: relative;">
                                        <div  id = 'right-top' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 30%;"></div>
                                        <div class="handler"></div>
                                        <div  id = 'right-bottom' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 70%;">
                                  
                                        </div>
                                        <div id="right-separator" class="separator" style="left: 0;"></div>
                                    </div>
                                </div>
                            </div>
                               
                             <div class="row">
                                 <!-- Draggable Separator Above Messages -->
                                <div id="messages-separator" class="xxseparator" style="cursor: ns-resize; height: 5px; background: gray;"></div>

                               <div style='padding:20px;overflow-y: scroll;' class="message-container acolumns-container mt-1" id="messages"></div>
                            
                            
                               </div>
                        </div>

                    `;
                

    }

    getStyle(){
        return  `

        .message-container{
        background-color: red;    height: 10vh;            
        }

  

            .pane {
                background-color: white;
                border: 1px solid #ddd;
                padding-left: 10px;
                padding-right:10px;
                padding-top: 10px;
                xxpadding-bottom: 10px;
                
            }

            #left-pane .pane:nth-child(1) {
                background-color: #ffcccc; /* Random light color */
            }

            #left-pane .pane:nth-child(2) {
                background-color: #ccffcc; /* Random light color */
            }

            #left-pane .pane:nth-child(3) {
                background-color: #ccccff; /* Random light color */
            }

            #middle-pane .pane:nth-child(1) {
                background-color: #ffffcc; /* Random light color */
            }

            #middle-pane .pane:nth-child(2) {
                background-color: #ccffff; /* Random light color */
            }

            #right-pane .pane:nth-child(1) {
                background-color: #ffccff; /* Random light color */
            }

            #right-pane .pane:nth-child(2) {
                background-color: #cce5ff; /* Random light color */
            }

            .columns-container {
                display: flex;
                height: 75vh;
                gap: 0;
            }

            .column {
                display: flex;
                flex-direction: column;
                gap: 5px; /* Small gap between rows */
                position: relative;
                height: 100%;
            }

            .separator {
                width: 8px;
                background-color: grey;
                cursor: ew-resize;
                position: absolute;
                top: 0;
                bottom: 0;
                z-index: 1;
            }

            .separator:hover {
                background-color: black;
            }

            .handler:hover {
                background-color: black;
                height: 10px;
            }

            .handler {
                height: 10px;
                background-color: grey;
            }
        `;

    }

    initResizableMessages(){
        return;
        const separator = this.querySelector("#messages-separator");
        const messages = this.querySelector("#messages");
        let xxisResizing = false;
        let xxstartY, xxstartHeight;


        function xxonMouseMove(e) {
            if (!xxisResizing) return;

            //console.log('moving!!!')

            let delta = (e.clientY - xxstartY)
            const newHeight = xxstartHeight - delta;
            messages.style.height = `${newHeight}px`;

            let leftSeparator = this.querySelector('#xxx');

            let h = leftSeparator.offsetHeight + 0.025*delta ;
            //console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() +'px';

        }
    
        function xxonMouseUp() {
            xxisResizing = false;

            //console.log('up!!!')
            document.removeEventListener("mousemove", xxonMouseMove);
            document.removeEventListener("mouseup", xxonMouseUp);
        }    
        
        separator.addEventListener("mousedown", (e) => {
            xxisResizing = true;
            xxstartY = e.clientY;
            xxstartHeight = messages.offsetHeight;
            document.addEventListener("mousemove",  xxonMouseMove);
            document.addEventListener("mouseup", xxonMouseUp);
            console.log('down!!!')
        });
    


    }


    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.initResizableColumns();
        this.initResizableRows();

        this.initResizableMessages();

        const style = document.createElement('style');
        style.textContent = this.getStyle();
        document.head.appendChild(style);


    }

    initResizableColumns() {
        const leftSeparator = this.querySelector('#left-separator');
        const rightSeparator = this.querySelector('#right-separator');
        const leftPane = this.querySelector('#left-pane');
        const middlePane = this.querySelector('#middle-pane');
        const rightPane = this.querySelector('#right-pane');


        let isResizingLeft = false;
        let lastDownXLeft = 0;

leftSeparator.addEventListener('mousedown', (e) => {
    isResizingLeft = true;
    lastDownXLeft = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingLeft) return;

    let offset = e.clientX - lastDownXLeft;
    let newLeftWidth = leftPane.offsetWidth + offset;
    let newMiddleWidth = middlePane.offsetWidth - offset;

    //if (newLeftWidth > 50 && newMiddleWidth > 50) {
        leftPane.style.width = `${newLeftWidth}px`;
        middlePane.style.width = `${newMiddleWidth}px`;

    
        //rightPane.style.margin= "5%";
        //rightPane.style.width = "100%";
    

   // }

    lastDownXLeft = e.clientX;
});

document.addEventListener('mouseup', () => {
    if (isResizingLeft) {
            //console.log('resizing ', leftPane.id );
            //console.log('resizing ', middlePane.id );

            let subpanes = Array.from(leftPane.querySelectorAll('.pane')).concat( Array.from(middlePane.querySelectorAll('.pane')));
            subpanes.push(leftPane);
            subpanes.push(middlePane);
            //console.log('subpanes ', subpanes);
            for( let pane of subpanes ){
                //console.log('dipathing ', pane.id);
                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: pane.id,
                        offsetWidth: pane.offsetWidth,
                        offsetHeight: pane.offsetHeight
                    }
                }));
            } 

       
            /*this.dispatchEvent(new CustomEvent('pane-resized', {

                
                detail: {
                    id: leftPane.id,
                    offsetWidth: leftPane.offsetWidth,
                    offsetHeight: leftPane.offsetHeight
                }
            }));

            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: middlePane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));*/
        }
       

isResizingLeft = false;
    document.body.style.cursor = 'default';
});

// For the middle-right separator between middle-pane and right-pane

let isResizingRight = false;
let lastDownXRight = 0;

rightSeparator.addEventListener('mousedown', (e) => {
    isResizingRight = true;
    lastDownXRight = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingRight) return;

    let offset = e.clientX - lastDownXRight;
    let newRightWidth = rightPane.offsetWidth - offset;  // Decrease right-pane width on drag left
    let newMiddleWidth = middlePane.offsetWidth + offset;  // Increase middle-pane width on drag left

    //rightPane.style.width = `${newRightWidth}px`;
    //middlePane.style.width = `${newMiddleWidth}px`;

    //old 
    middlePane.style.width = `${newMiddleWidth}px`;
    
    //let x = window.innerWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);
    //console.log(this.parentNode.offsetWidth)
    let x = this.parentNode.offsetWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);
    rightPane.style.width = `${x}px`;
    lastDownXRight = e.clientX;



});

document.addEventListener('mouseup', () => {

    if (isResizingRight) {

        let subpanes = Array.from(rightPane.querySelectorAll('.pane')).concat( Array.from(middlePane.querySelectorAll('.pane')));
        subpanes.push(rightPane);
        subpanes.push(middlePane);
        for( let pane of subpanes ){

            console.log('here dispatching event ', pane.id);
            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: pane.id,
                    offsetWidth: pane.offsetWidth,
                    offsetHeight: pane.offsetHeight
                }
            }));
        } 
    }

   
    isResizingRight = false;
    document.body.style.cursor = 'default';
});
    }

    initResizableRows() {
        this.querySelectorAll('.handler').forEach(handler => {
            let isDragging = false;

            const onDrag = (e) => {
             
                if (!isDragging) return;

                const parent = handler.parentNode;
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;
                const parentRect = parent.getBoundingClientRect();

                const prevHeight = e.clientY - parentRect.top - prevRow.offsetTop;
                const nextHeight = parentRect.height - prevHeight - handler.offsetHeight;

                //const minHeight = 0; // Minimum height in pixels
                //if (prevHeight > minHeight && nextHeight > minHeight) 
                    {
                    handler.style.flexBasis = `${handler.offsetHeight}px`;
                    prevRow.style.flexBasis = `${prevHeight}px`;
                    nextRow.style.flexBasis = `${nextHeight}px`;
                }
            };

            const stopDrag = () => {

                if (isDragging) {
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: prevRow.id,
                        newWidth: prevRow.offsetWidth,
                        newHeight: prevRow.offsetHeight
                    }
                }));

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: nextRow.id,
                        newWidth: nextRow.offsetWidth,
                        newHeight: nextRow.offsetHeight
                    }
                }));

            }


                isDragging = false;
                document.body.style.cursor = 'default';
                document.removeEventListener('mousemove', onDrag);
                document.removeEventListener('mouseup', stopDrag);
            };

            handler.addEventListener('mousedown', () => {
                isDragging = true;
                document.body.style.cursor = 'row-resize';
                document.addEventListener('mousemove', onDrag);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }


    //api 
    addDynamicPlotlyChart(where, data, layout,config) {

        function relayout( container){

            //container.style.padding = '20px';
            let inner_offset = 10; 
            let pad = 50;
            const update = {
                //title: {text: 'some new title'}, // updates the title
                'width':   (parseInt( container.offsetWidth ) - pad).toString(),   // updates the xaxis range
                'height':  (parseInt(container.offsetHeight ) - pad/2).toString(),   // updates the end of the yaxis range
                
                //'paper_bgcolor': 'orange',
                'plot_bgcolor': 'lightgrey',

                //'x': inner_offset,
                'margin': {
                'l': 78,
                'r': 78,
                'b': 48,
                't': 48,
                //'pad': 4  
                },
                'autosize': true,
                
            };
            Plotly.relayout(container, update);

        }
        let container =   this.get_pane(where)

        // Plotly chart initialization
        Plotly.newPlot(container, data, layout, config);    
        this.addEventListener('pane-resized', (evt)=>{
            if( evt.detail.id.includes(where) )  {
                relayout( container );
            }
        }) ;  
        relayout( container );
    }



addMessage(text) {
    const messagesContainer = this.querySelector("#messages");

    const message = document.createElement("p");
    message.textContent = text;
    messagesContainer.appendChild(message);
    }
setMessage(text) {
    const messagesContainer = this.querySelector("#messages");
    messagesContainer.innerHTML = ""; 
    const message = document.createElement("p");
    message.textContent = text;
    messagesContainer.appendChild(message);
    }
clearMessage(text) {
    const messagesContainer = this.querySelector("#messages");
    messagesContainer.innerHTML = ""; 
    }

// Set content in the specified pane
set(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        if (typeof content === 'string') {
            pane.innerHTML = content;  // Set content as innerHTML if it's a string
        } else if (content instanceof HTMLElement) {
            pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a string or an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
clear(where) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        pane.innerHTML = ''; // Clear existing content
    }
    
    
}
append(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        //if (typeof content === 'string') {
        //    pane.innerHTML = content;  // Set content as innerHTML if it's a string

        if (content instanceof HTMLElement) {
            //pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
get_pane( id ){
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(id)) {
        const pane = this.querySelector(`#${id}`);
        return pane; 
    }

}

}
customElements.define('app-layout-component1', AppMainLayout1);


//works fine but too many divisions
class AppMainLayout2 extends HTMLElement {
    constructor() {
        super();
    }

    getTemplate(){
        // Create the inner HTML structure
        return `
                        <div id="main-layout" class="container-fluid mt-1">
                            <div  class="row">
                                <div id='xxx' class="columns-container">
                                    <!-- Left Pane -->
                                 

                                    <div id="left-pane" class="col-2 column" style="position: relative;">
                                        <div id = 'left-top' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 150%;"></div>
                                        <div class="handler flex-grow-0" style="flex-basis: 2%;"></div>
                                        <div id = 'left-bottom' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 150%;"></div>
                                    </div>

                                    <!-- Middle Pane -->
                                    <div id="middle-pane" class="col-5 column gx-5" style="position: relative;">
                                        <div id="left-separator" class="separator" style="left: 0;"></div>
                                        <div id = 'middle-top'  class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 150%;"></div>
                                        <div class="handler" style="flex-basis: 2%;"></div>
                                        <div id = 'middle-bottom' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 150%;"></div>
                                    </div>

                                    <!-- Right Pane -->
                                    <div id="right-pane" class="col-5 column" style="position: relative;">
                                        <div  id = 'right-top' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 30%;"></div>
                                        <div class="handler"></div>
                                        <div  id = 'right-bottom' class="pane flex-grow-1" style="overflow-y: scroll;flex-basis: 70%;">
                                  
                                        </div>
                                        <div id="right-separator" class="separator" style="left: 0;"></div>
                                    </div>
                                </div>
                            </div>
                                
                        </div>

                    `;
                

    }

    getStyle(){
        return  `

        .message-container{
        background-color: red;    height: 10vh;            
        }

  

            .pane {
                background-color: white;
                border: 1px solid #ddd;
                padding-left: 10px;
                padding-right:10px;
                padding-top: 10px;
                xxpadding-bottom: 10px;
                
            }

            #left-pane .pane:nth-child(1) {
                background-color: #ffcccc; /* Random light color */
            }

            #left-pane .pane:nth-child(2) {
                background-color: #ccffcc; /* Random light color */
            }

            #left-pane .pane:nth-child(3) {
                background-color: #ccccff; /* Random light color */
            }

            #middle-pane .pane:nth-child(1) {
                background-color: #ffffcc; /* Random light color */
            }

            #middle-pane .pane:nth-child(2) {
                background-color: #ccffff; /* Random light color */
            }

            #right-pane .pane:nth-child(1) {
                background-color: #ffccff; /* Random light color */
            }

            #right-pane .pane:nth-child(2) {
                background-color: #cce5ff; /* Random light color */
            }

            .columns-container {
                display: flex;
                height: 75vh;
                gap: 0;
            }

            .column {
                display: flex;
                flex-direction: column;
                gap: 5px; /* Small gap between rows */
                position: relative;
                height: 100%;
            }

            .separator {
                width: 8px;
                background-color: grey;
                cursor: ew-resize;
                position: absolute;
                top: 0;
                bottom: 0;
                z-index: 1;
            }

            .separator:hover {
                background-color: black;
            }

            .handler:hover {
                background-color: black;
                height: 10px;
            }

            .handler {
                height: 10px;
                background-color: grey;
            }
        `;

    }

    initResizableMessages(){
        return;
        const separator = this.querySelector("#messages-separator");
        const messages = this.querySelector("#messages");
        let xxisResizing = false;
        let xxstartY, xxstartHeight;


        function xxonMouseMove(e) {
            if (!xxisResizing) return;

            //console.log('moving!!!')

            let delta = (e.clientY - xxstartY)
            const newHeight = xxstartHeight - delta;
            messages.style.height = `${newHeight}px`;

            let leftSeparator = this.querySelector('#xxx');

            let h = leftSeparator.offsetHeight + 0.025*delta ;
            //console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() +'px';

        }
    
        function xxonMouseUp() {
            xxisResizing = false;

            //console.log('up!!!')
            document.removeEventListener("mousemove", xxonMouseMove);
            document.removeEventListener("mouseup", xxonMouseUp);
        }    
        
        separator.addEventListener("mousedown", (e) => {
            xxisResizing = true;
            xxstartY = e.clientY;
            xxstartHeight = messages.offsetHeight;
            document.addEventListener("mousemove",  xxonMouseMove);
            document.addEventListener("mouseup", xxonMouseUp);
            console.log('down!!!')
        });
    


    }


    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.initResizableColumns();
        this.initResizableRows();

        this.initResizableMessages();

        const style = document.createElement('style');
        style.textContent = this.getStyle();
        document.head.appendChild(style);


    }

    initResizableColumns() {
        const leftSeparator = this.querySelector('#left-separator');
        const rightSeparator = this.querySelector('#right-separator');
        const leftPane = this.querySelector('#left-pane');
        const middlePane = this.querySelector('#middle-pane');
        const rightPane = this.querySelector('#right-pane');


        let isResizingLeft = false;
        let lastDownXLeft = 0;

leftSeparator.addEventListener('mousedown', (e) => {
    isResizingLeft = true;
    lastDownXLeft = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingLeft) return;

    let offset = e.clientX - lastDownXLeft;
    let newLeftWidth = leftPane.offsetWidth + offset;
    let newMiddleWidth = middlePane.offsetWidth - offset;

    //if (newLeftWidth > 50 && newMiddleWidth > 50) {
        leftPane.style.width = `${newLeftWidth}px`;
        middlePane.style.width = `${newMiddleWidth}px`;

    
        //rightPane.style.margin= "5%";
        //rightPane.style.width = "100%";
    

   // }

    lastDownXLeft = e.clientX;
});

document.addEventListener('mouseup', () => {
    if (isResizingLeft) {
            //console.log('resizing ', leftPane.id );
            //console.log('resizing ', middlePane.id );

            let subpanes = Array.from(leftPane.querySelectorAll('.pane')).concat( Array.from(middlePane.querySelectorAll('.pane')));
            subpanes.push(leftPane);
            subpanes.push(middlePane);
            //console.log('subpanes ', subpanes);
            for( let pane of subpanes ){
                //console.log('dipathing ', pane.id);
                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: pane.id,
                        offsetWidth: pane.offsetWidth,
                        offsetHeight: pane.offsetHeight
                    }
                }));
            } 

       
            /*this.dispatchEvent(new CustomEvent('pane-resized', {

                
                detail: {
                    id: leftPane.id,
                    offsetWidth: leftPane.offsetWidth,
                    offsetHeight: leftPane.offsetHeight
                }
            }));

            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: middlePane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));*/
        }
       

isResizingLeft = false;
    document.body.style.cursor = 'default';
});

// For the middle-right separator between middle-pane and right-pane

let isResizingRight = false;
let lastDownXRight = 0;

rightSeparator.addEventListener('mousedown', (e) => {
    isResizingRight = true;
    lastDownXRight = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingRight) return;

    let offset = e.clientX - lastDownXRight;
    let newRightWidth = rightPane.offsetWidth - offset;  // Decrease right-pane width on drag left
    let newMiddleWidth = middlePane.offsetWidth + offset;  // Increase middle-pane width on drag left

    //rightPane.style.width = `${newRightWidth}px`;
    //middlePane.style.width = `${newMiddleWidth}px`;

    //old 
    middlePane.style.width = `${newMiddleWidth}px`;
    
    //let x = window.innerWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);
    //console.log(this.parentNode.offsetWidth)
    let x = this.parentNode.offsetWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);
    rightPane.style.width = `${x}px`;
    lastDownXRight = e.clientX;



});

document.addEventListener('mouseup', () => {

    if (isResizingRight) {

        let subpanes = Array.from(rightPane.querySelectorAll('.pane')).concat( Array.from(middlePane.querySelectorAll('.pane')));
        subpanes.push(rightPane);
        subpanes.push(middlePane);
        for( let pane of subpanes ){

            console.log('here dispatching event ', pane.id);
            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: pane.id,
                    offsetWidth: pane.offsetWidth,
                    offsetHeight: pane.offsetHeight
                }
            }));
        } 
    }

   
    isResizingRight = false;
    document.body.style.cursor = 'default';
});
    }

    initResizableRows() {
        this.querySelectorAll('.handler').forEach(handler => {
            let isDragging = false;

            const onDrag = (e) => {
             
                if (!isDragging) return;

                const parent = handler.parentNode;
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;
                const parentRect = parent.getBoundingClientRect();

                const prevHeight = e.clientY - parentRect.top - prevRow.offsetTop;
                const nextHeight = parentRect.height - prevHeight - handler.offsetHeight;

                //const minHeight = 0; // Minimum height in pixels
                //if (prevHeight > minHeight && nextHeight > minHeight) 
                    {
                    handler.style.flexBasis = `${handler.offsetHeight}px`;
                    prevRow.style.flexBasis = `${prevHeight}px`;
                    nextRow.style.flexBasis = `${nextHeight}px`;
                }
            };

            const stopDrag = () => {

                if (isDragging) {
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: prevRow.id,
                        newWidth: prevRow.offsetWidth,
                        newHeight: prevRow.offsetHeight
                    }
                }));

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: nextRow.id,
                        newWidth: nextRow.offsetWidth,
                        newHeight: nextRow.offsetHeight
                    }
                }));

            }


                isDragging = false;
                document.body.style.cursor = 'default';
                document.removeEventListener('mousemove', onDrag);
                document.removeEventListener('mouseup', stopDrag);
            };

            handler.addEventListener('mousedown', () => {
                isDragging = true;
                document.body.style.cursor = 'row-resize';
                document.addEventListener('mousemove', onDrag);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }


    //api 
    addDynamicPlotlyChart(where, data, layout,config) {

        function relayout( container){

            //container.style.padding = '20px';
            let inner_offset = 10; 
            let pad = 50;
            const update = {
                //title: {text: 'some new title'}, // updates the title
                'width':   (parseInt( container.offsetWidth ) - pad).toString(),   // updates the xaxis range
                'height':  (parseInt(container.offsetHeight ) - pad/2).toString(),   // updates the end of the yaxis range
                
                //'paper_bgcolor': 'orange',
                'plot_bgcolor': 'lightgrey',

                //'x': inner_offset,
                'margin': {
                'l': 78,
                'r': 78,
                'b': 48,
                't': 48,
                //'pad': 4  
                },
                'autosize': true,
                
            };
            Plotly.relayout(container, update);

        }
        let container =   this.get_pane(where)

        // Plotly chart initialization
        Plotly.newPlot(container, data, layout, config);    
        this.addEventListener('pane-resized', (evt)=>{
            if( evt.detail.id.includes(where) )  {
                relayout( container );
            }
        }) ;  
        relayout( container );
    }



addMessage(text) {
    const messagesContainer = this.querySelector("#messages");

    const message = document.createElement("p");
    message.textContent = text;
    messagesContainer.appendChild(message);
    }
setMessage(text) {
    const messagesContainer = this.querySelector("#messages");
    messagesContainer.innerHTML = ""; 
    const message = document.createElement("p");
    message.textContent = text;
    messagesContainer.appendChild(message);
    }
clearMessage(text) {
    const messagesContainer = this.querySelector("#messages");
    messagesContainer.innerHTML = ""; 
    }

// Set content in the specified pane
set(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        if (typeof content === 'string') {
            pane.innerHTML = content;  // Set content as innerHTML if it's a string
        } else if (content instanceof HTMLElement) {
            pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a string or an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
clear(where) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        pane.innerHTML = ''; // Clear existing content
    }
    
    
}
append(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        //if (typeof content === 'string') {
        //    pane.innerHTML = content;  // Set content as innerHTML if it's a string

        if (content instanceof HTMLElement) {
            //pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
get_pane( id ){
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(id)) {
        const pane = this.querySelector(`#${id}`);
        return pane; 
    }

}

}
customElements.define('app-layout-component', AppMainLayout2);


//works fine but too many divisions
class AppSideLayout1 extends HTMLElement {
    constructor() {
        super();
    }

    getTemplate(){
        // Create the inner HTML structure
        return `
                    
                            <div  id="side-layout">
                                <div id='side-pane-container'>
                                    <!-- Left Pane -->
                                    <div id="side-pane" class="xx-column" style="aaposition: relative;">
                                        <div id = 'side-top' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 100%;"></div>
                                        <div class="handler flex-grow-0" style="flex-basis: 2%;"></div>
                                        <div id = 'side-bottom' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 100%;"></div>
                                    </div>
                                </div> 
                            </div>  
                    
                    `;
                

    }

    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.initResizableRows();
    }


    initResizableRows() {
        this.querySelectorAll('.handler').forEach(handler => {
            let isDragging = false;

            const onDrag = (e) => {
             
                if (!isDragging) return;

                const parent = handler.parentNode;
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;
                const parentRect = parent.getBoundingClientRect();

                const prevHeight = e.clientY - parentRect.top - prevRow.offsetTop;
                const nextHeight = parentRect.height - prevHeight - handler.offsetHeight;

                //const minHeight = 0; // Minimum height in pixels
                //if (prevHeight > minHeight && nextHeight > minHeight) 
                    {
                    handler.style.flexBasis = `${handler.offsetHeight}px`;
                    prevRow.style.flexBasis = `${prevHeight}px`;
                    nextRow.style.flexBasis = `${nextHeight}px`;
                }
            };

            const stopDrag = () => {

                if (isDragging) {
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: prevRow.id,
                        newWidth: prevRow.offsetWidth,
                        newHeight: prevRow.offsetHeight
                    }
                }));

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: nextRow.id,
                        newWidth: nextRow.offsetWidth,
                        newHeight: nextRow.offsetHeight
                    }
                }));

            }


                isDragging = false;
                document.body.style.cursor = 'default';
                document.removeEventListener('mousemove', onDrag);
                document.removeEventListener('mouseup', stopDrag);
            };

            handler.addEventListener('mousedown', () => {
                isDragging = true;
                document.body.style.cursor = 'row-resize';
                document.addEventListener('mousemove', onDrag);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }
  




// Set content in the specified pane
set(where, content) {
    const validPanes = ['side-top',  'side-bottom'];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        if (typeof content === 'string') {
            pane.innerHTML = content;  // Set content as innerHTML if it's a string
        } else if (content instanceof HTMLElement) {
            pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a string or an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
clear(where) {
    const validPanes = ['side-top',  'side-bottom'];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        pane.innerHTML = ''; // Clear existing content
    }
    
    
}
append(where, content) {
    const validPanes = ['side-top',  'side-bottom'];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        //if (typeof content === 'string') {
        //    pane.innerHTML = content;  // Set content as innerHTML if it's a string

        if (content instanceof HTMLElement) {
            //pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
get_pane( id ){
    const validPanes = ['side-top',  'side-bottom'];
    
    // Check if 'where' is valid
    if (validPanes.includes(id)) {
        const pane = this.querySelector(`#${id}`);
        return pane; 
    }

}

}
customElements.define('app-side-layout-component', AppSideLayout1);


class QuickJS_ThreeColumnMainLayout extends HTMLElement {
    constructor() {
        super();
    }

    getTemplate(){
        // Create the inner HTML structure
        return `
                        <div id="main-layout" class="caaontainer-fluid">
                            <div  class="arow">
                                <div id='columns-container' class="columns-container">
                                    <!-- Left Pane -->
                                    <div id="left-pane" class="col-2 column" style="position: relative;">
                                        <div id = 'left-top' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 60%;"></div>
                                        <div class="handler" style="flex-basis: 1%;"></div>
                                        <div id = 'left-bottom' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 55%;"></div>
                                    </div>

                                    <!-- Middle Pane -->
                                    <div id="middle-pane" class="col-5 column gx-2" style="position: relative;">
                                        <div id="left-separator" class="separator"  ></div>
                                        <div id = 'middle-top'  class="pane flex-grow-1" style="overflow-y: auto;flex-basis: 100%;"></div>
                                        <div class="handler flex-grow-0 lex-basis: 2%;"></div>
                                        <div id = 'middle-bottom' class="pane flex-grow-1" style="overflow-y: auto;flex-basis: 100%;"></div>
                                    </div>

                                    <!-- Right Pane -->
                                    <div id="right-pane" class="col-5 column" style="position: relative;">
                                        <div  id = 'right-top' class="pane flex-grow-1" style="overflow-y: auto;flex-basis: 100%;"></div>
                                        <div class="handler flex-grow-0 lex-basis: 2%;"></div>
                                        <div  id = 'right-bottom' class="pane flex-grow-1" style="overflow-y: auto;flex-basis: 100%;">
                                  
                                        </div>
                                        <div id="right-separator" class="separator"></div>
                                    </div>
                                </div>
                            </div>
                               
                             
                        </div>

                    `;
                

    }

    getStyle(){
        return "";
        return  `

 
            .pane {
                background-color: transparent;
                border: 1px solid #ddd;
                padding: 10px;
         
            }

            #left-pane .pane:nth-child(1) {
                background-color: transparent; //#ffcccc; /* Random light color */
            }

            #left-pane .pane:nth-child(2) {
                background-color: transparent; //#ccffcc; /* Random light color */
            }

            #left-pane .pane:nth-child(3) {
                background-color: transparent; //#ccccff; /* Random light color */
            }

            #middle-pane .pane:nth-child(1) {
                background-color: transparent; //#ffffcc; /* Random light color */
            }

            #middle-pane .pane:nth-child(2) {
                background-color: transparent; //#ccffff; /* Random light color */
            }

            #right-pane .pane:nth-child(1) {
                background-color: transparent; //#ffccff; /* Random light color */
            }

            #right-pane .pane:nth-child(2) {
                background-color: transparent; //#cce5ff; /* Random light color */
            }

            .columns-container {
                display: flex;
                height: 100vh;
                gap: 0;
            }

            .column {
                display: flex;
                flex-direction: column;
                gap: 5px; /* Small gap between rows */
                xxposition: relative;
                height: calc(100vh - 62px)
                margin-top:10px;
            }

            .separator {
                width: 8px;
                background-color: grey;
                cursor: ew-resize;
                position: absolute;
                top: 0;
                bottom: 0;
                z-index: 1;
            }

            .separator:hover {
                background-color: black;
            }

            .handler:hover {
                background-color: black;
                height: 10px;
            }

            .handler {
                height: 10px;
                background-color: grey;
            }
        `;

    }

    initResizableMessages(){
        return;
        const separator = this.querySelector("#messages-separator");
        const messages = this.querySelector("#messages");
        let xxisResizing = false;
        let xxstartY, xxstartHeight;


        function xxonMouseMove(e) {
            if (!xxisResizing) return;

            //console.log('moving!!!')

            let delta = (e.clientY - xxstartY)
            const newHeight = xxstartHeight - delta;
            messages.style.height = `${newHeight}px`;

            let leftSeparator = this.querySelector('#xxx');

            let h = leftSeparator.offsetHeight + 0.025*delta ;
            //console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() +'px';

        }
    
        function xxonMouseUp() {
            xxisResizing = false;

            //console.log('up!!!')
            document.removeEventListener("mousemove", xxonMouseMove);
            document.removeEventListener("mouseup", xxonMouseUp);
        }    
        
        separator.addEventListener("mousedown", (e) => {
            xxisResizing = true;
            xxstartY = e.clientY;
            xxstartHeight = messages.offsetHeight;
            document.addEventListener("mousemove",  xxonMouseMove);
            document.addEventListener("mouseup", xxonMouseUp);
            console.log('down!!!')
        });
    


    }


    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.initResizableColumns();
        this.initResizableRows();
        //const style = document.createElement('style');
        //style.textContent = this.getStyle();
        //document.head.appendChild(style);


    }

    initResizableColumns() {
        const leftSeparator = this.querySelector('#left-separator');
        const rightSeparator = this.querySelector('#right-separator');
        const leftPane = this.querySelector('#left-pane');
        const middlePane = this.querySelector('#middle-pane');
        const rightPane = this.querySelector('#right-pane');


        let isResizingLeft = false;
        let lastDownXLeft = 0;

    leftSeparator.addEventListener('mousedown', (e) => {
    isResizingLeft = true;
    lastDownXLeft = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingLeft) return;

    let offset = e.clientX - lastDownXLeft;
    let newLeftWidth = leftPane.offsetWidth + offset;
    let newMiddleWidth = middlePane.offsetWidth - offset;

    //if (newLeftWidth > 50 && newMiddleWidth > 50) {
        leftPane.style.width = `${newLeftWidth}px`;
        middlePane.style.width = `${newMiddleWidth}px`;

    
        //rightPane.style.margin= "5%";
        //rightPane.style.width = "100%";
    

   // }

    lastDownXLeft = e.clientX;
});

document.addEventListener('mouseup', () => {
    if (isResizingLeft) {
            //console.log('resizing ', leftPane.id );
            //console.log('resizing ', middlePane.id );

            let subpanes = Array.from(leftPane.querySelectorAll('.pane')).concat( Array.from(middlePane.querySelectorAll('.pane')));
            subpanes.push(leftPane);
            subpanes.push(middlePane);
            //console.log('subpanes ', subpanes);
            for( let pane of subpanes ){
                //console.log('dipathing ', pane.id);
                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: pane.id,
                        offsetWidth: pane.offsetWidth,
                        offsetHeight: pane.offsetHeight
                    }
                }));
            } 

       
            /*this.dispatchEvent(new CustomEvent('pane-resized', {

                
                detail: {
                    id: leftPane.id,
                    offsetWidth: leftPane.offsetWidth,
                    offsetHeight: leftPane.offsetHeight
                }
            }));

            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: middlePane.id,
                    offsetWidth: middlePane.offsetWidth,
                    offsetHeight: middlePane.offsetHeight
                }
            }));*/
        }
       

isResizingLeft = false;
    document.body.style.cursor = 'default';
});

// For the middle-right separator between middle-pane and right-pane

let isResizingRight = false;
let lastDownXRight = 0;

rightSeparator.addEventListener('mousedown', (e) => {
    isResizingRight = true;
    lastDownXRight = e.clientX;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizingRight) return;

    let offset = e.clientX - lastDownXRight;
    let newRightWidth = rightPane.offsetWidth - offset;  // Decrease right-pane width on drag left
    let newMiddleWidth = middlePane.offsetWidth + offset;  // Increase middle-pane width on drag left

    //rightPane.style.width = `${newRightWidth}px`;
    //middlePane.style.width = `${newMiddleWidth}px`;

    //old 
    middlePane.style.width = `${newMiddleWidth}px`;
    
    //let x = window.innerWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);
    //console.log(this.parentNode.offsetWidth)
    let x = this.parentNode.offsetWidth -20 - (leftPane.offsetWidth + offset + newMiddleWidth);
    rightPane.style.width = `${x}px`;
    lastDownXRight = e.clientX;



});

document.addEventListener('mouseup', () => {

    if (isResizingRight) {

        let subpanes = Array.from(rightPane.querySelectorAll('.pane')).concat( Array.from(middlePane.querySelectorAll('.pane')));
        subpanes.push(rightPane);
        subpanes.push(middlePane);
        for( let pane of subpanes ){

            console.log('here dispatching event ', pane.id);
            this.dispatchEvent(new CustomEvent('pane-resized', {
                detail: {
                    id: pane.id,
                    offsetWidth: pane.offsetWidth,
                    offsetHeight: pane.offsetHeight
                }
            }));
        } 
    }

   
    isResizingRight = false;
    document.body.style.cursor = 'default';
});
    }

    initResizableRows() {
        this.querySelectorAll('.handler').forEach(handler => {
            let isDragging = false;

            const onDrag = (e) => {
             
                if (!isDragging) return;

                const parent = handler.parentNode;
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;
                const parentRect = parent.getBoundingClientRect();

                const prevHeight = e.clientY - parentRect.top - prevRow.offsetTop;
                const nextHeight = parentRect.height - prevHeight - handler.offsetHeight;

                //const minHeight = 0; // Minimum height in pixels
                //if (prevHeight > minHeight && nextHeight > minHeight) 
                    {
                    handler.style.flexBasis = `${handler.offsetHeight}px`;
                    prevRow.style.flexBasis = `${prevHeight}px`;
                    nextRow.style.flexBasis = `${nextHeight}px`;
                }
            };

            const stopDrag = () => {

                if (isDragging) {
                const prevRow = handler.previousElementSibling;
                const nextRow = handler.nextElementSibling;

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: prevRow.id,
                        newWidth: prevRow.offsetWidth,
                        newHeight: prevRow.offsetHeight
                    }
                }));

                this.dispatchEvent(new CustomEvent('pane-resized', {
                    detail: {
                        id: nextRow.id,
                        newWidth: nextRow.offsetWidth,
                        newHeight: nextRow.offsetHeight
                    }
                }));

            }


                isDragging = false;
                document.body.style.cursor = 'default';
                document.removeEventListener('mousemove', onDrag);
                document.removeEventListener('mouseup', stopDrag);
            };

            handler.addEventListener('mousedown', () => {
                isDragging = true;
                document.body.style.cursor = 'row-resize';
                document.addEventListener('mousemove', onDrag);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }


    //api 
    addDynamicPlotlyChart(where, data, layout,config) {

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
            'l': 78,
            'r': 78,
            'b': 48,
            't': 48,
            //'pad': 4  
            },
            'autosize': true,
            
            };
            Plotly.relayout(container, update);

    }
    let container =   this.get_pane(where)

    // Plotly chart initialization
    Plotly.newPlot(container, data, layout, config);    
    this.addEventListener('pane-resized', (evt)=>{
        if( evt.detail.id.includes(where) )  {
            relayout( container );
        }
        }) ;  
    relayout( container );
    }

// Set content in the specified pane
set(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        if (typeof content === 'string') {
            pane.innerHTML = content;  // Set content as innerHTML if it's a string
        } else if (content instanceof HTMLElement) {
            pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a string or an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
clear(where) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        pane.innerHTML = ''; // Clear existing content
    }
    
    
}
append(where, content) {
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(where)) {
        const pane = this.querySelector(`#${where}`);
        
        //if (typeof content === 'string') {
        //    pane.innerHTML = content;  // Set content as innerHTML if it's a string

        if (content instanceof HTMLElement) {
            //pane.innerHTML = ''; // Clear existing content
            pane.appendChild(content);  // Append the HTML element
        } else {
            console.error('Content must be a an HTML element');
        }
    } else {
        console.error('Invalid pane ID');
    }
    
    
}
get_pane( id ){
    const validPanes = ['left-top', 'left-middle', 'left-bottom',
        'middle-top', 'middle-bottom', 'right-top', 'right-middle', 'right-bottom'
    ];
    
    // Check if 'where' is valid
    if (validPanes.includes(id)) {
        const pane = this.querySelector(`#${id}`);
        return pane; 
    }

}

}
customElements.define('three-column-main-layout', QuickJS_ThreeColumnMainLayout);
