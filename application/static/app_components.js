 
class AAAppMainLayout extends HTMLElement {
    constructor() {
        super();
    }

    getTemplate() {
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

    getStyle() {
        return `

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

    initResizableMessages() {
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

            let h = leftSeparator.offsetHeight + 0.025 * delta;
            console.log('h', h, delta)

            leftSeparator.style.height = h.toString() + 'px';

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
            document.addEventListener("mousemove", xxonMouseMove);
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
                let x = window.innerWidth - 20 - (leftPane.offsetWidth + offset + newMiddleWidth);

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
    get_pane(id) {
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

    getTemplate() {
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

    getStyle() {
        return `

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

    initResizableMessages() {
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

            let h = leftSeparator.offsetHeight + 0.025 * delta;
            //console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() + 'px';

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
            document.addEventListener("mousemove", xxonMouseMove);
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

                let subpanes = Array.from(leftPane.querySelectorAll('.pane')).concat(Array.from(middlePane.querySelectorAll('.pane')));
                subpanes.push(leftPane);
                subpanes.push(middlePane);
                //console.log('subpanes ', subpanes);
                for (let pane of subpanes) {
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
            let x = this.parentNode.offsetWidth - 20 - (leftPane.offsetWidth + offset + newMiddleWidth);
            rightPane.style.width = `${x}px`;
            lastDownXRight = e.clientX;



        });

        document.addEventListener('mouseup', () => {

            if (isResizingRight) {

                let subpanes = Array.from(rightPane.querySelectorAll('.pane')).concat(Array.from(middlePane.querySelectorAll('.pane')));
                subpanes.push(rightPane);
                subpanes.push(middlePane);
                for (let pane of subpanes) {

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
    addDynamicPlotlyChart(where, data, layout, config) {

        function relayout(container) {

            //container.style.padding = '20px';
            let inner_offset = 10;
            let pad = 50;
            const update = {
                //title: {text: 'some new title'}, // updates the title
                'width': (parseInt(container.offsetWidth) - pad).toString(),   // updates the xaxis range
                'height': (parseInt(container.offsetHeight) - pad / 2).toString(),   // updates the end of the yaxis range

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
        let container = this.get_pane(where)

        // Plotly chart initialization
        Plotly.newPlot(container, data, layout, config);
        this.addEventListener('pane-resized', (evt) => {
            if (evt.detail.id.includes(where)) {
                relayout(container);
            }
        });
        relayout(container);
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
    get_pane(id) {
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

    getTemplate() {
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

    getStyle() {
        return `

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

    initResizableMessages() {
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

            let h = leftSeparator.offsetHeight + 0.025 * delta;
            //console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() + 'px';

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
            document.addEventListener("mousemove", xxonMouseMove);
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

                let subpanes = Array.from(leftPane.querySelectorAll('.pane')).concat(Array.from(middlePane.querySelectorAll('.pane')));
                subpanes.push(leftPane);
                subpanes.push(middlePane);
                //console.log('subpanes ', subpanes);
                for (let pane of subpanes) {
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
            let x = this.parentNode.offsetWidth - 20 - (leftPane.offsetWidth + offset + newMiddleWidth);
            rightPane.style.width = `${x}px`;
            lastDownXRight = e.clientX;



        });

        document.addEventListener('mouseup', () => {

            if (isResizingRight) {

                let subpanes = Array.from(rightPane.querySelectorAll('.pane')).concat(Array.from(middlePane.querySelectorAll('.pane')));
                subpanes.push(rightPane);
                subpanes.push(middlePane);
                for (let pane of subpanes) {

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
    addDynamicPlotlyChart(where, data, layout, config) {

        function relayout(container) {

            //container.style.padding = '20px';
            let inner_offset = 10;
            let pad = 50;
            const update = {
                //title: {text: 'some new title'}, // updates the title
                'width': (parseInt(container.offsetWidth) - pad).toString(),   // updates the xaxis range
                'height': (parseInt(container.offsetHeight) - pad / 2).toString(),   // updates the end of the yaxis range

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
        let container = this.get_pane(where)

        // Plotly chart initialization
        Plotly.newPlot(container, data, layout, config);
        this.addEventListener('pane-resized', (evt) => {
            if (evt.detail.id.includes(where)) {
                relayout(container);
            }
        });
        relayout(container);
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
    get_pane(id) {
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

    getTemplate() {
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
        const validPanes = ['side-top', 'side-bottom'];

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
        const validPanes = ['side-top', 'side-bottom'];

        // Check if 'where' is valid
        if (validPanes.includes(where)) {
            const pane = this.querySelector(`#${where}`);
            pane.innerHTML = ''; // Clear existing content
        }


    }
    append(where, content) {
        const validPanes = ['side-top', 'side-bottom'];

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
    get_pane(id) {
        const validPanes = ['side-top', 'side-bottom'];

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

    getTemplate() {
        // Create the inner HTML structure
        return `
                        <div id="main-layout" class="caaontainer-fluid">
                            <div  class="arow">
                                <div id='columns-container' class="columns-container">
                                    <!-- Left Pane -->
                                    <div id="left-pane" class="col-2 column" style="xxwidth: 30%; position: relative;">
                                        <div id = 'left-top' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 60%;"></div>
                                        <div class="handler" style="flex-basis: 1%;"></div>
                                        <div id = 'left-bottom' class="pane flex-grow-1" style="overflow-y: auto;max-height: 100%; flex-basis: 55%;"></div>
                                    </div>

                                    <!-- Middle Pane -->
                                    <div id="middle-pane" class="col-5 column gx-2" style=xx"width: 35%; position: relative;">
                                        <div id="left-separator" class="separator"  ></div>
                                        <div id = 'middle-top'  class="pane flex-grow-1" style="overflow-y: auto;flex-basis: 100%;"></div>
                                        <div class="handler flex-grow-0 flex-basis: 1%;"></div>
                                        <div id = 'middle-bottom' class="pane flex-grow-0" style="overflow-y: auto;flex-basis: 100%;"></div>
                                    </div>

                                    <!-- Right Pane -->
                                    <div id="right-pane" class="col-5 column" style="xxwidth: 35%position: relative; xxleft:10px">
                                        <div  id = 'right-top' class="pane flex-grow-1" style="overflow-y: auto;flex-basis: 100%;"></div>
                                        <div class="handler flex-grow-0 flex-basis: 1%;"></div>
                                        <div  id = 'right-bottom' class="pane flex-grow-0" style="overflow-y: auto;flex-basis: 100%;">
                                  
                                        </div>
                                        <div id="right-separator" class="separator" style="xxleft:-12px"></div>
                                    </div>
                                </div>
                            </div>
                               
                             
                        </div>

                    `;


    }

    getStyle() {
        return "";
        return `

 
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

    initResizableMessages() {
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

            let h = leftSeparator.offsetHeight + 0.025 * delta;
            //console.log( 'h', h, delta)

            leftSeparator.style.height = h.toString() + 'px';

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
            document.addEventListener("mousemove", xxonMouseMove);
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

                let subpanes = Array.from(leftPane.querySelectorAll('.pane')).concat(Array.from(middlePane.querySelectorAll('.pane')));
                subpanes.push(leftPane);
                subpanes.push(middlePane);
                //console.log('subpanes ', subpanes);
                for (let pane of subpanes) {
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
            let x = this.parentNode.offsetWidth - 15 - (leftPane.offsetWidth + offset + newMiddleWidth);
            rightPane.style.width = `${x}px`;
            //rightPane.style.left = '100px';
            lastDownXRight = e.clientX;



        });

        document.addEventListener('mouseup', () => {

            if (isResizingRight) {

                let subpanes = Array.from(rightPane.querySelectorAll('.pane')).concat(Array.from(middlePane.querySelectorAll('.pane')));
                subpanes.push(rightPane);
                subpanes.push(middlePane);
                for (let pane of subpanes) {

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
    addDynamicPlotlyChart(where, data, layout, config) {

        function relayout(container) {

            //container.style.padding = '20px';
            let inner_offset = 10;
            let pad = 50;
            const update = {
                title: { text: 'some new title' }, // updates the title
                'width': (parseInt(container.offsetWidth) - pad).toString(),   // updates the xaxis range
                'height': (parseInt(container.offsetHeight) - pad / 2).toString(),   // updates the end of the yaxis range

                //'paper_bgcolor': 'orange',
                //'plot_bgcolor': 'lightgrey',

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
        let container = this.get_pane(where)

        // Plotly chart initialization
        Plotly.newPlot(container, data, layout, config);
        this.addEventListener('pane-resized', (evt) => {
            if (evt.detail.id.includes(where)) {
                relayout(container);
            }
        });
        relayout(container);
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
    get_pane(id) {
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

 
 

class ProjectListComponent extends HTMLElement {
    constructor() {
        super();
    }

    connectedCallback() {
        const defaultProjects = ["Project Alpha", "Project Beta", "Project Gamma"];
        this.renderProjects(defaultProjects);
    }

    renderProjects(names) {
        this.innerHTML = ""; // Clear previous content

        // Add the "Projects" heading
        const title = document.createElement("h3");
        title.classList.add("projects-component-title");
        title.textContent = "Projects ";
        this.appendChild(title);
        this.appendChild(document.createElement("hr"));

        names.forEach(name => {
            const card = document.createElement("div");
            card.classList.add("projects-component-card", "d-flex", "justify-content-between", "align-items-center");

            const projectName = document.createElement("span");
            projectName.textContent = name;

            const button = document.createElement("button");
            button.textContent = "Open";
            button.classList.add("projects-component-button", "btn", "btn-primary");
            button.onclick = () => this.emitClickEvent(name);

            card.appendChild(projectName);
            card.appendChild(button);
            this.appendChild(card);
        });
    }

    

    emitClickEvent(projectName) {
        const event = new CustomEvent("clicked", {
            detail: { projectName },
            bubbles: true,
            composed: true
        });
        this.dispatchEvent(event);
    }

    set projects(names) {
        this.renderProjects(names);
    }
}

// Register the custom element with the new name
customElements.define("project-list-component", ProjectListComponent);


class QuickJS_ConnectDatasetComponent extends HTMLElement {
    constructor() {
        super();
        this.folders = [];
        this.selectedFolder = null;
    }

    connectedCallback() {
        this.render();
    }

    setData(foldersArray) {
        if (Array.isArray(foldersArray)) {
            this.folders = foldersArray;
            this.selectedFolder = null;
            this.render();
        }
    }

    getData() {
        return this.folders;
    }



    getSelected() {
        return this.selectedFolder;
    }

    render() {
        this.innerHTML = `
        <div class="connect-dataset-grid connect-dataset-folder-grid"></div>
        <button class="connect-dataset-button">Connect</button>
      `;

        const grid = this.querySelector(".connect-dataset-folder-grid");

        this.folders.forEach(folderName => {
            const folderEl = document.createElement("div");
            folderEl.classList.add("connect-dataset-folder");
            folderEl.dataset.folder = folderName;
            folderEl.innerHTML = `
          <div class="connect-dataset-folder-icon"></div>
          <div class="connect-dataset-folder-label">${folderName}</div>
        `;

            folderEl.addEventListener("click", () => this.selectFolder(folderName));
            grid.appendChild(folderEl);
        });

        const button = this.querySelector(".connect-dataset-button");
        button.addEventListener("click", () => {
            if (this.selectedFolder) {
                this.dispatchEvent(new CustomEvent("clicked", {
                    detail: { folder: this.selectedFolder }
                }));
            } else {
                alert("Please select a folder before connecting.");
            }
        });
    }

    selectFolder(folderName) {
        this.selectedFolder = folderName;
        const allFolders = this.querySelectorAll(".connect-dataset-folder");

        allFolders.forEach(folderEl => {
            folderEl.classList.toggle("open", folderEl.dataset.folder === folderName);
        });
    }
}
customElements.define("connect-dataset-component", QuickJS_ConnectDatasetComponent);


class InjectorProducerTable extends HTMLElement {
    constructor() {
        super();
        this.data = {};
        this.originalInjectors = [];

        this.something_changed = false;
    }

    connectedCallback() {
        this.innerHTML = `
                    <table class="injector-producer-table">
                        <thead>
                            <tr>
                                <th>Producer</th>
                                <th>Injectors</th>
                                <th class="injector-producer-actions">Actions</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>

                    <div class="injector-producer-overlay"></div>

                    <div class="injector-producer-dialog" id="addInjectorDialog">
                        <div class="injector-producer-dialog-header">
                            <h3>Add Injectors</h3>
                            <button class="injector-producer-close-btn">X</button>
                        </div>
                        <div class="injector-producer-list"></div>
                    </div>

                    <div class="injector-producer-dialog" id="removeInjectorDialog">
                        <div class="injector-producer-dialog-header">
                            <h3>Remove Injectors</h3>
                            <button class="injector-producer-close-btn">X</button>
                        </div>
                        <div class="injector-producer-list"></div>
                    </div>
                `;
        this.renderTable();
        this.querySelectorAll(".injector-producer-close-btn").forEach(btn =>
            btn.addEventListener("click", () => this.closeDialog()));
    }

    setData(data) {

        console.log('setData called in the component');
        /*
        this.data = JSON.parse(JSON.stringify(data)); // Deep copy
        this.originalInjectors = [...new Set(Object.values(this.data).flat())];
        */
        this.data = data;
        this.originalInjectors = [...new Set(Object.values(this.data).flat())];
        this.renderTable();
    }

    getData() {
        return JSON.parse(JSON.stringify(this.data)); // Deep copy
    }

    producersInTable() {
        return Object.keys(this.data);
    }

    injectorsInTable() {

        let uniqueValues = [...new Set(Object.values(this.data).flat())];
        return uniqueValues;
    }



    renderTable() {

        //this.something_changed = false;

        const tableBody = this.querySelector("tbody");
        tableBody.innerHTML = "";
        Object.keys(this.data).forEach(producer => {
            const row = document.createElement("tr");

            const producerCell = document.createElement("td");
            producerCell.innerHTML = `${producer} <button class="injector-producer-trash-btn" onclick="this.closest('injector-producer-table-component').deleteProducer('${producer}')">x</button>`;
            row.appendChild(producerCell);

            const injectorsCell = document.createElement("td");
            injectorsCell.textContent = this.data[producer].join(", ");
            row.appendChild(injectorsCell);

            const actionsCell = document.createElement("td");
            actionsCell.classList.add("injector-producer-actions");

            const addButton = document.createElement("button");
            addButton.innerHTML = "+";
            addButton.classList.add(['injector-producer-add-btn', 'injector-producer-actions-button']);
            addButton.onclick = () => this.showAddDialog(producer);
            actionsCell.appendChild(addButton);

            const removeButton = document.createElement("button");
            removeButton.innerHTML = "-";
            removeButton.classList.add(['injector-producer-remove-btn', 'injector-producer-actions-button']);
            removeButton.onclick = () => this.showRemoveDialog(producer);
            actionsCell.appendChild(removeButton);

            row.appendChild(actionsCell);
            tableBody.appendChild(row);
        });

        //alert('rendering the rates charts ')

        this.render_charts();
    }//'injector-producer-actions-button'        


    render_charts() {
        this.dispatchEvent(new CustomEvent('table-changed'));
    }

    showAddDialog(producer) {

        this.something_changed = false;

        const dialog = this.querySelector("#addInjectorDialog");
        const list = dialog.querySelector(".injector-producer-list");
        list.innerHTML = "";

        const unusedInjectors = this.originalInjectors.filter(inj => !this.data[producer].includes(inj)).sort();
        unusedInjectors.forEach(injector => {
            const item = document.createElement("div");
            item.innerHTML = `<span class='xx'> ${injector} <button class='injector-producer-add-btn injector-producer-actions-button' onclick="this.closest('injector-producer-table-component').addInjector('${producer}', '${injector}')">+</button></span>`;
            list.appendChild(item);
        });

        this.querySelector(".injector-producer-overlay").style.display = "block";
        dialog.style.display = "block";
    }

    showRemoveDialog(producer) {

        this.something_changed = false;

        const dialog = this.querySelector("#removeInjectorDialog");
        const list = dialog.querySelector(".injector-producer-list");
        list.innerHTML = "";

        this.data[producer].forEach(injector => {
            const item = document.createElement("div");

            item.innerHTML = `<span class='xx'>  ${injector} <button class='injector-producer-remove-btn injector-producer-actions-button' onclick="this.closest('injector-producer-table-component').removeInjector('${producer}', '${injector}')">-</button></span>`;
            list.appendChild(item);
        });

        this.querySelector(".injector-producer-overlay").style.display = "block";
        dialog.style.display = "block";
    }

    closeDialog() {

        this.querySelectorAll(".injector-producer-dialog, .injector-producer-overlay").forEach(el => el.style.display = "none");

        if (this.something_changed == true) {
            alert('something changed');
        }

        this.something_changed = false;

    }

    addInjector(producer, injector) {

        this.something_changed = true;
        console.log('addInjector called');

        this.data[producer].push(injector);
        this.renderTable();
        this.showAddDialog(producer);
    }

    removeInjector(producer, injector) {

        this.something_changed = true;
        //console.log('removeInjector called');

        this.data[producer] = this.data[producer].filter(item => item !== injector);
        this.renderTable();
        this.showRemoveDialog(producer);
    }

    deleteInjector(injector_name) {

        this.something_changed = true;
        console.log('deleteInjector called');

        for (const producer in this.data) {
            this.data[producer] = this.data[producer].filter(item => item !== injector_name);

            if (this.data[producer].length == 0) {
                delete this.data[producer];
            }
        }

        this.renderTable();
    }

    deleteProducer(producer) {

        this.something_changed = true;
        //console.log('deleteProducer called');

        delete this.data[producer];
        this.renderTable();
    }



}

customElements.define("injector-producer-table-component", InjectorProducerTable);

class CRMSetupElement extends HTMLElement {
    constructor() {
        super();
    }

    distances_table;
    extracted_pairs;
    well_rates;
    date1
    date2

    _getMeanAndStdDistance(data) {
        // Step 1: Group by producer
        const groups = {};
        for (const item of data) {
            if (!groups[item.producer]) groups[item.producer] = [];
            groups[item.producer].push(item.distance);
        }

        // Step 2: Collect up to 3 closest distances per producer
        let filteredDistances = [];
        for (const distances of Object.values(groups)) {
            const top3 = distances.sort((a, b) => a - b).slice(0, 1);
            filteredDistances.push(...top3);
        }

        // Step 3: Compute mean and std over all selected distances
        const mean = filteredDistances.reduce((sum, val) => sum + val, 0) / filteredDistances.length;

        const std = filteredDistances.length === 1 ? 0 : Math.sqrt(filteredDistances.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / filteredDistances.length);


        return { mean, std }
    }
    _old_getMeanAndStdDistance(data) {

        //This gives you the mean and std for the 3 closest injectors per producer.

        const groups = {};
        for (const item of data) {
            if (!groups[item.producer]) groups[item.producer] = [];
            groups[item.producer].push(item.distance);
        }

        // Step 2: For each group, pick the 3 smallest distances
        const stats = {};
        let sum = 0.0;
        for (const [producer, distances] of Object.entries(groups)) {
            const top3 = distances.sort((a, b) => a - b).slice(0, 3);



            const mean = top3.reduce((sum, val) => sum + val, 0) / top3.length;

            const std = Math.sqrt(
                top3.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / top3.length
            );

            stats[producer] = { mean, std };
            console.log(stats);
        }
    }

    setData(input_distances_table, input_well_rates) {

        this.distances_table = input_distances_table;
        this.well_rates = input_well_rates;

        const { mean, std } = this._getMeanAndStdDistance(input_distances_table);
        const threshold = Math.round(mean + 0.000000025 * std);
        this.getElementsByClassName('model-distance-button')[0].value = threshold;
        this.getElementsByClassName('extract-pairs-button')[0].click();// = threshold;
        let track = this.getElementsByTagName('double-range-component')[0]

        track.setRanges(60.0, 90.0);// = threshold;


        //this.plotRates();


        return

        /*
                let n = -1
                let keys = ['liquid_production','water_injection']
                let containers = [ Id('liquid-production-rates-container'), Id('water-injection-rates-container')]
                for(let key of keys){
                            n = n + 1 
                            
                            
                            /*
                            let rates = resp[key]['data']
                            let dates =  resp[key]['dates']
                            const traces = [];
                            for (const well in rates) {
                            traces.push({
                                //works extra_stuff: dates, 
                                x: dates, y: rates[well], mode: 'lines', name: well,
                                type: 'scatter'
                            });
                            }
        
                            series_name = formatString( key )
                            let chart = containers[n];
                            chart.innerHTML = "";
                            Plotly.newPlot( chart, traces, {
                            title: {'text':series_name, font: {size:20}},
                            xaxis: { text: 'Date' },yaxis: { text: 'Value' }}, {'responsive': true});
                            *//*
    }

    




const layout = {
grid: {rows: 2, columns: 2, pattern: 'independent'},
autosize: true,
margin: {l: 40, r: 40, t: 20, b: 30},
xaxis: {matches: 'x'},
xaxis2: {matches: 'x'},
xaxis3: {matches: 'x'},
xaxis4: {matches: 'x'}
};

Plotly.newPlot('chart-grid', data, layout, {responsive: true});
*/

    }

    initPlots() {
        return;
        let ele1 = this.querySelector('.crm-chart-grid');
        let div1 = this.querySelector('#dd1'); div1.innerHTML = '';
        let div2 = this.querySelector('#dd2'); div2.innerHTML = '';
        div1.style.minHeight = '250px';  // can also use % or vh
        div2.style.minHeight = '250px';  // can also use % or vh
        div1.style.maxHeight = '350px';  // can also use % or vh
        div2.style.maxHeight = '350px';  // can also use % or vh
        div1.style.height= '250px'
        div2.style.height= '250px'
        

        Plotly.newPlot(div1, [], {}, { responsive: true })
        //let layout2 = structuredClone(layout);
        //layout['title'] = { text:'Liquid production', font: {size:24}}
        Plotly.newPlot(div2, [], {}, { responsive: true })


    }

    plotRates() {

 
        let ele1 = this.querySelector('.crm-chart-grid');
        //ele1.innerHTML = '';

        let theTable = this.getElementsByTagName('injector-producer-table-component')[0]
        let visibleProducers = theTable.producersInTable();
        let visibleInjectors = theTable.injectorsInTable();
        let well_rates = this.well_rates;
        if ((well_rates == undefined) || (visibleInjectors.length < 1) || (visibleProducers.length < 1)) {
            this.initPlots();
            return;
        }
        let allNames = [...visibleProducers, ...visibleInjectors];
        function formatString(str) {
            if (!str) return '';
            const noUnderscores = str.replace(/_/g, ' ');
            return noUnderscores.charAt(0).toUpperCase() + noUnderscores.slice(1);
        }





        /*lets build the traces groups*/
        let n = 0
        let keys = ['liquid_production', 'water_injection']
        //const allTraces = [];
        let traces1 = [];
        let traces2 = [];

        let traces_ptr = undefined;
        for (let key of keys) {
            n = n + 1
            let x_ = 'x' //+ n.toString();
            traces_ptr = traces1;
            let y_ = 'y' //+ n.toString();
            if (n == 1) {
                //x_ = 'x2';
                //y_ = 'y2';
                traces_ptr = traces2;
            }

            let rates = well_rates[key]['data']
            let dates = well_rates[key]['dates']

            let kk = 1;
            for (const well in rates) {


                kk = kk + 1;
                let visibility = allNames.includes(well);
                //if( kk > 10)
                //visibility = false;

                traces_ptr.push({
                    //works extra_stuff: dates, 
                    xaxis: x_, yaxis: y_,
                    x: dates, y: rates[well], mode: 'lines', name: well,
                    type: 'scatter',
                    visible: visibility
                    //legendgroup: 'group'+n.toString(),
                });
            }

        }

        const layout = {
            autosize: true,
            automargin: true,
            //height: 500,
            //margin: {l: 40, r: 40, t: 20, b: 30},
            //autosize: true 
        };


        //create brand-new charts 
        //let div1 = document.createElement('div');
        //div1.classList.add('col-6');
        //let div2 = document.createElement('div');
        //div2.classList.add('col-6');
        //ele1.appendChild(div1)
        //ele1.appendChild(div2)

 
        let div1 = this.querySelector('#dd1'); div1.innerHTML = '';
        let div2 = this.querySelector('#dd2'); div2.innerHTML = '';
        div1.style.minHeight = '500px';  // can also use % or vh
        div2.style.minHeight = '500px';  // can also use % or vh
        //div1.style.backgroundColor = 'lightblue'; // just to visualize it

        // Sync zoom/pan
        let isSyncing = false;
        function drelayout(e, target) {
            if (isSyncing) return;

            let x0 = e['xaxis.range[0]'];
            const x1 = e['xaxis.range[1]'];

            if (x0 !== undefined && x1 !== undefined) {
                isSyncing = true;
                Plotly.relayout(target, { 'xaxis.range': [x0, x1] }).then(() => {
                    isSyncing = false;
                });

                return;
            }


            x0 = e['xaxis.autorange'];
            if (x0 !== undefined) {
                isSyncing = true;
                console.log('it was an autoaxes? ', e)
                Plotly.relayout(target, {
                    'xaxis.autorange': true,
                    'yaxis.autorange': true
                }).then(() => {
                    isSyncing = false;
                });
            }



        }



        layout['title'] = { text: 'Water injection ', font: { size: chart_title_font_size } }
        Plotly.newPlot(div1, traces1, layout, { responsive: true }).then((plt) => {



            let layout2 = structuredClone(layout);
            layout2['title'] = { text: 'Liquid production', font: { size: chart_title_font_size } }

            Plotly.newPlot(div2, traces2, layout2, { responsive: true }).then(() => {
                div1.on('plotly_relayout', (e) => { drelayout(e, div2) });
                div2.on('plotly_relayout', (e) => { drelayout(e, div1) });


                
            this.displayDatesFromTrackbarAsText();
            this.displayDatesFromTrackbarInCharts();



            }) 

        })



        //div2.style.height = '500px';  // can also use % or vh
        //div2.style.backgroundColor = 'lightblue'; // just to visualize it








        return
        /*
                 layout = {
                    grid: {rows: 2, columns: 2, pattern: 'independent'},
                    autosize: true,
                    margin: {l: 40, r: 40, t: 20, b: 30},
        
                    /*xaxis: {title: 'X Axis'},
                    yaxis: {title: 'Y Axis'},
                    xaxis2: {title: 'X Axis (Right)', matches: 'x'},
                    yaxis2: {title: 'Y Axis (Right)'}
                    xaxis:  {matches: 'x'},
                    xaxis2: {matches: 'x'},
                    xaxis3: {matches: 'x'},
                    xaxis4: {matches: 'x'}
                };
        
                layout = {
                        grid: {rows: 1, columns: 2, pattern: 'independent'},
        
                        xaxis: {domain: [0, 0.4]},
                        yaxis: {domain: [0, 1]},
                        xaxis2: {domain: [0.5, 0.9]},
                        yaxis2: {domain: [0, 1]},
        
                        title: {text: 'Two Subplots with "Separate" Legends'},
        
                        // Simulate multiple legends by positioning text manually
                        legend: {
                            x: 0.42, y: 1,
                            bgcolor: 'rgba(255,255,255,0.8)',
                            borderwidth: 1
                        },
        
                        annotations: [
                            {
                            x: 0.92, y: 1,
                            xref: 'paper', yref: 'paper',
                            text: '<b>Group 2</b><br>▇ A<br>▇ B',
                            showarrow: false,
                            align: 'left'
                            }
                        ]
                        };
        
                
                let ele = this.querySelector('.crm-chart-grid');
                ele.innerHTML = '';
                
                Plotly.newPlot( ele, allTraces, layout);
        
                
                
                
                
                
                
                return 
                
                 div1 = document.createElement('div');
                 div2 = document.createElement('div');
                ele.appendChild(div1)
                Plotly.newPlot( div1, traces1, {}, {responsive: true}).then( (gd)=>{
        
        
                    function f (eventData) {
                        if (eventData['xaxis.range[0]'] && eventData['xaxis.range[1]']) {
                            const update = {
                                'xaxis.range': [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']],
                                //'xaxis2.range': [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']],
                                //'xaxis3.range': [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']]
                            };
        
                            Plotly.relayout(div2, update);
                        }
                    }
        
                    gd.on('plotly_relayout', (eventData) =>{ f(eventData) });
                    gd.on('plotly_restyle', (eventData) =>{ f(eventData) });    
        
                    //Plotly.relayout(div1, update);
                    //Plotly.relayout(div2, update);
        
                });
        
                
                ele.appendChild(div2)
                Plotly.newPlot( div2, traces2, {}, {responsive: true});
        
        
        
        
        
                let isSyncing = false;
        
        function syncZoom(sourceDiv, targetDiv, eventData) {
          // Only act on actual zoom events with x-axis range
          if (
            eventData['xaxis.range[0]'] !== undefined &&
            eventData['xaxis.range[1]'] !== undefined
          ) {
            const update = {
              'xaxis.range[0]': eventData['xaxis.range[0]'],
              'xaxis.range[1]': eventData['xaxis.range[1]']
            };
        
            isSyncing = true;
            Plotly.relayout(targetDiv, update).then(() => {
              isSyncing = false;
            });
          }
        }*/

        // div1 → div2
        /*
        div1.on('plotly_relayout', (eventData) => {
            
            let x1 = eventData['xaxis.range[0]'];// !== undefined &&
            let x2 = eventData['xaxis.range[1]'];// !== undefined
            if ( (x1==undefined) || (x2==undefined) ) return; 
        
            const update = {
              'xaxis.range[0]': eventData['xaxis.range[0]'],
              'xaxis.range[1]': eventData['xaxis.range[1]']
            };
        
            Plotly.relayout(div2, update).then( (err)=>{
                ;
        
            })
        
        
        
            console.log('syncing 1', x1, x2)
          if (!isSyncing) {
            console.log('syncing 1')
            //syncZoom(div1, div2, eventData);
          }
        });
        
        // div2 → div1
        div2.on('plotly_relayout', (eventData) => {
         
            let x1 = eventData['xaxis2.range[0]'];// !== undefined &&
            let x2 = eventData['xaxis2.range[1]'];// !== undefined
            if ( (x1==undefined) || (x2==undefined) ) return; 
            console.log('syncing 2', x1, x2)
        
            const update = {
              'xaxis2.range[0]': eventData['xaxis2.range[0]'],
              'xaxis2.range[1]': eventData['xaxis2.range[1]']
            };
        
            //Plotly.relayout(div1, update)
        
            
          if (!isSyncing) {
            console.log('syncing 2')
            //syncZoom(div2, div1, eventData);
          }
        });*/




    }

    groupByProducer(filteredPairs) {
        const grouped = {};

        filteredPairs.forEach(({ producer, injector }) => {
            if (!grouped[producer]) {
                grouped[producer] = [];
            }
            grouped[producer].push(injector);
        });

        return grouped; // Returns an object instead of an array
    }

    extractPairs(threshold) {

        if (threshold == undefined) threshold = 1750;


        let extracted_pairs = this.distances_table.filter(entry => entry.distance <= threshold);

        let filtered_for_visualization = this.groupByProducer(extracted_pairs);

        let table = this.getElementsByTagName('injector-producer-table-component')[0]

        table.setData(filtered_for_visualization);
        table.classList.remove('hidden');


        //this.plotRates();
        return;


        //console.log( 'extracted_pairs----------2-------------' );
        //console.log( extracted_pairs );
        //console.log( 'extracted_pairs----------3-------------' );
        /*
        const groupedPairs = this.groupByProducer(extracted_pairs);
        console.log( 'groupedPairs----------2-------------' );
        console.log( groupedPairs );
        console.log( 'groupedPairs----------3-------------' );

        const tableBody = this.getElementsByTagName("injector-producer-table-component")[0];
        console.log( 'tableBody----------2-------------' );
        console.log( tableBody );
        console.log( 'tableBody----------3-------------' );
        tableBody.setData( groupedPairs );*/


    }

    setState(state) {

        ;
    }

    getState() {

        ;
    }

    deleteInjector(injector_name) {

        this.getElementsByTagName('injector-producer-table-component')[0].deleteInjector(injector_name);
    }

    deleteProducer(producer_name) {

        this.getElementsByTagName('injector-producer-table-component')[0].deleteProducer(producer_name);
    }

    validateDistanceEntry() {
        let distance_entry = this.querySelector('.model-distance-button');
        let errorMessage = this.querySelector('.distance-entry-error-message');

        // Convert input value to a number

        let result = true;
        // Convert input value to a number
        const value = parseFloat(distance_entry.value);
        const min = parseFloat(distance_entry.min);
        const max = parseFloat(distance_entry.max);

        // Check if the value is out of range
        if (isNaN(value) || value < min || value > max) {
            errorMessage.textContent = 'Please enter a number between 250 and 5000.';
            distance_entry.style.borderColor = "red"; // Highlight input field
            result = false;
        } else {
            errorMessage.textContent = ""; // Clear error message
            distance_entry.style.borderColor = ""; // Reset input border
            result = true;
        }

        return result;
    }

    displayDatesFromTrackbarAsText() {

        let this_object = this;
        let track = this.getElementsByTagName('double-range-component')[0];
        const [percent1, percent2] = track.getValues();

        const dates = this_object.well_rates['dates'];
        const start = dates[0]; // months are 0-indexed
        const end = dates[dates.length - 1];
        const index1 = Math.round((percent1 / 100) * (dates.length - 1));
        const index2 = Math.round((percent2 / 100) * (dates.length - 1));
        //console.log(index1,index2)

        this_object.date1 = dates[Math.min(index1, index2)];
        this_object.date2 = dates[Math.max(index1, index2)];
        this_object.getElementsByClassName('date1-text')[0].textContent = `Selected range: ${this_object.date1} → ${this_object.date2}`;
    }


    displayDatesFromTrackbarInCharts(){

        let this_object = this;
        console.log('update dates shown in charts', this_object.date1, this_object.date2);

        let shape = {
            type: 'rect', xref: 'x', yref: 'paper',
            x0: this_object.date1, y0: 0.005,
            x1: this_object.date2, y1: 1,
            fillcolor: "green",
            opacity: 0.2,
            line: { width: 1, dash: 'dashdot', color: 'green' },
            name: "TimeControlIndicator"
        }

        let chart1 = this_object.querySelector('#dd1');
        let layout = chart1.layout;
        let shapes = undefined;
        shapes = 'shapes' in layout ? layout['shapes'] : [];
        shapes = shapes.filter((item) => !item.name.includes('TimeControlIndicator'));
        shapes.push(shape)
        layout['shapes'] = shapes;
        Plotly.relayout(chart1, layout);


        let chart2 = this_object.querySelector('#dd2');
        let layout2 = chart2.layout;
        shapes = 'shapes' in layout2 ? layout2['shapes'] : [];
        shapes = shapes.filter((item) => !item.name.includes('TimeControlIndicator'));
        shapes.push(shape)
        layout2['shapes'] = shapes;
        Plotly.relayout(chart2, layout2);
    }


    connectEvents() {

        let this_object = this;
   

        this.querySelector('.extract-pairs-button').addEventListener('click', () => {

            if (!this.validateDistanceEntry()) {
                alert('Enter a valid distance threshold')
                return;
            }


            /*extract-pairs-button*/
            if (this.distances_table == undefined) {
                alert('No data available');
                return;
            }


            try {
                let distance_threshold = this.querySelector('.model-distance-button').value;
                this.extractPairs(distance_threshold);
            }
            catch (err) {
                console.log('error', err);
                alert('unexpected error occured when extracting pairs data')
            }

            /*const event = new CustomEvent("clicked", {
            detail: { projectName },
            bubbles: true,
            composed: true
            });
            this.dispatchEvent(event);*/


        });


        let distance_entry = this.querySelector('.model-distance-button');
        let errorMessage = this.querySelector('.distance-entry-error-message');
  
        distance_entry.addEventListener('input', function () {

            this_object.validateDistanceEntry();
            // Convert input value to a number
            /*const value = parseFloat(distance_entry.value);
            const min = parseFloat(distance_entry.min);
            const max = parseFloat(distance_entry.max);

            // Check if the value is out of range
            if (value < min || value > max) {
                errorMessage.textContent = 'Please enter a number between 250 and 5000.';
                distance_entry.style.borderColor = "red"; // Highlight input field
            } else {
                errorMessage.textContent = ""; // Clear error message
                distance_entry.style.borderColor = ""; // Reset input border
            }*/
        });

        this.querySelector('injector-producer-table-component').addEventListener('table-changed', () => {
            this.plotRates();
        });

        let track = this.getElementsByTagName('double-range-component')[0];
        track.addEventListener('clicked', (evt) => {
            this_object.displayDatesFromTrackbarAsText();
        });

        /*show the time indicator*/
        track.addEventListener('mouse-up', () => {


            this_object.displayDatesFromTrackbarAsText();
            this_object.displayDatesFromTrackbarInCharts();



        });

        this.querySelector(".history-match-save-and-run").addEventListener('click', ()=>{
            //console.log('save and run clicked'); 
            this.exportData();
        } );
        this.querySelector(".history-match-close-button").addEventListener('click', ()=>{
            this.dispatchEvent(new CustomEvent('close-clicked', {detail: {}}));
        });
        
        
    }

    connectedCallback() {
        this.innerHTML = this.getTemplate();
        this.connectEvents();
        this.initPlots();

    }

      
    exportData() {
       
        /* #######################################

        ui client 
        start_simulation                
        {
        'project_name': 'NewProjectXavier', 
        'filters': {
        'zone': '', 
        'subzone': ['LW'], 
        'sector': [8, 4], 
        'name': ['BG-1723-1_I', 'BG-1768-1_I', 'BG-1925-1_I', 'BG-1935-1_I']
        }, 
        
        'managed_folder_name': 'azFolder', 
        'app_name': 'WF', 'data_folder_name': 'data', 
        'projects_folder_name': 'projects', 
        'studies_folder_name': 'studies'

        'dt': 1, 
        'max_running_time': 1000, 
        'optimizer': {'maxiter': 1000, 'name': 'SLSQP', 'tolerance': 0.001}, 
        'balance': {'type': 'quick', 'max_iter': 100, 'tolerance': 0.01}, 
        'primary': True, 
        'regularization': 0

        #control 

        'export_only': True, 
 
        'distance': 1234, 
        
        'explicit': 
        {
            'subzone': 
            {'LW': 
                {'BG-0052-6_P': ['BG-1925-1_I', 'BG-1935-1_I'], 
                'BG-0236-2_P': ['BG-1588-1_I', 'BG-1692-1_I'], 
                'BG-0724-3_P': ['BG-0756-1_I']
                }
            }
        }, 
            
        'simulation': {
            
                'name': 'TestModel1', 
                'type': 'crm_p', 
                'dates': ['2016-05-01', '2024-09-01'], 
            
                'parameters': {
                'tau': {'bounds': [0.5, 50], 'init_value': 1}, 
                'taup': {'bounds': [0.5, 50], 'init_value': 1}, 
                'lambda': {'bounds': [0, 1], 'init_value': 0.1}, 
                'productivity_index': {'bounds': [0, 1], 'init_value': 0}, 
                'qo_lambda': {'bounds': [0, 1], 'init_value': 1}
                },


        }, 
            

        }
        ########################################
        */
       
        let toExport = {

            export_only:  this.querySelector('#crm-setup-export-only').checked, 
            distance: parseFloat(this.querySelector('.model-distance-button').value),

            //explicit pairs 
            explicit: this.querySelector('injector-producer-table-component').data,

            simulation : {
                //simulation name 
                name: this.querySelector('#model-name').value,

                //crm-p, crm-ip,....
                type: this.querySelector('#model-type').value,

                balance: this.querySelector('#model-balance').value, //none, quick, full

                dates: [this.date1, this.date2],

                parameters : {            
                    tau :  {'bounds':[parseFloat(Id('tau-min').value), parseFloat(Id('tau-max').value )], 'init_value': parseFloat(Id('tau-initial').value)},
                    taup : {'bounds':[parseFloat(Id('taup-min').value),parseFloat(Id('taup-max').value)], 'init_value': parseFloat(Id('taup-initial').value)}, 
                    lambda : {'bounds':[parseFloat(Id('lambda-min').value),parseFloat(Id('lambda-max').value)], 'init_value': parseFloat(Id('lambda-initial').value)},
                    productivity_index : {'bounds':[parseFloat(Id('productivity-min').value),parseFloat(Id('productivity-max').value)], 'init_value': parseFloat(Id('productivity-initial').value)},
                    qo_lambda : {'bounds':[parseFloat(Id('primary-min').value),parseFloat(Id('primary-max').value)], 'init_value': parseFloat(Id('primary-initial').value)}
                    }  

            }            
        }
 

        //console.log(toExport)
        const event = new CustomEvent("clicked", {
            detail: { crm_setup: toExport },
            bubbles: true,
        })
        this.dispatchEvent(event);
        
    }

    getTemplate() {
        return `
            <div id='modelling-page' class='page'>

                <!-- h5>Well selection</h5>
                <div id='lasso-selected-indicator' style="line-height: 60px; vertical-align: middle;" class="hidden blue-indicator">Lasso selection active</div>
                <div id='all-selected-indicator' style="line-height: 60px; vertical-align: middle;" class="white-indicator">Applied filters in chart</div>
                <p></p -->

          
                <span class='subtitle'>Apply distance screener</span>
                <div>
                    <div  class="input-group">
                    <input type="number" step="250" value='1750' name="distance_threshold" 
                    placeholder = 'Enter a number (250-5000)'  
                    class='model-distance-button form-control form-control-sm' min="250" max="5000" required>
                    <button id='extract-pairs-button' class='extract-pairs-button btn btn-primary'>Apply</button>
                    </div>
                     <p class="distance-entry-error-message" style="color: red; margin-left: 10px;"></p> 
                </div>
            
                <br>

                <details open><summary>Well pairs</summary>
                <div>
                <injector-producer-table-component class='hidden'></injector-producer-table-component>
                </div>
                </details>

                <p></p>
                <!-- h5>Injetion/production signals</h5 -->
                <div class="chart-container" style='background-color:red; 
                aamin-height:305px; aamax-height:350; 
                display:flex; justify-content: space-evenly;'>
           
                        <div id= 'dd1' style="width:49%" class='sscol-6'></div>
                        <div id= 'dd2' style="width:50%"  class='sscol-6'></div>
                        
                    <!-- div class="crm-chart-grid"></div -->
        
                </div>
                <p></p>


                <span class='subtitle'>Training time frame</span>          
                <div>
                    <div style="margin:30px">
                    <span class='date1-text'>Date1</span><double-range-component></double-range-component>                    
                    </div>
                </div>


                <p></p>


    <p></p>
    <h5>Model type:</h5>
    <select id='model-type' name="balance" class="form-select" onchange="function s()
                    {  
                                                        
                        let model = document.getElementById('model-type').value
                        let disabled = (model=='crm_tank') || (model=='crmip')
                        console.log('here, model = ', model,' disabled ', disabled )  
                                                                         
                        if( disabled==true)                                   
                        document.getElementById('model-balance-placeholder').classList.add('hidden')
                        else
                        document.getElementById('model-balance-placeholder').classList.remove('hidden')
                                                           
                    }; 
                    s()">
        
        <option value="crm_tank">CRMT</option>
        <option value="crm_p">CRMP</option>
        <option value="crmip">CRMIP</option>
        <option selected value="crmp_constrained">CRMP Constrained</option>
        <option value="crmid_constrained">CRMID Constrained</option>
        

    </select>
        <div id='model-balance-placeholder'><label class='mt-3'>Balanced </label>
            <select class='form-control form-control-sm' name="balance" id='model-balance'>
                <option value="none">No</option>
                <option selected value="quick">Quick</option>
                <option value="full">Full</option>
            </select>
        </div>


 <p></p>

            
                <!-- *********************************************** -->
                <details><summary>Advanced parameters</summary> 
    <p></p>
    <div class='row'>
        <div class='col-3 text-end'><b>Parameter</b></div>
        <div class='col-3 text-center'>Initial</div>
        <div class='col-3 text-center'>Min</div>
        <div class='col-3 text-center'>Max</div>
        <hr>
    </div>

    <div class='row'>
        <div class='col-3 text-end'><b>Tau</b></div>
        <div class='col-3'><input class='form-control form-control-sm tau-initial' id=  'tau-initial' type="number" min="0.1" max="100" value="1" decimals="1" step="1"></div>
        <div class='col-3'><input class='form-control form-control-sm tau-min'     id = 'tau-min' type="number"     min="0.1" max="100" value="0.5" decimals="1" step="1"></div>
        <div class='col-3'><input class='form-control form-control-sm tau-max'     id = 'tau-max' type="number"     min="0.2" max="100" value="50"  decimals="1" step="1"></div>
    </div>

    <div class='row'>
        <div class='col-3 text-end'><b>Taup</b></div>
        <div class='col-3'><input class='form-control form-control-sm taup-initial' id='taup-initial' type="number" min="0.1" max="100" value="1" decimals="1" step="1"></div>
        <div class='col-3'><input class='form-control form-control-sm taup-min' id='taup-min' type="number" min="0.1" max="100" value="0.5"   decimals="1" step="1"></div>
        <div class='col-3'><input class='form-control form-control-sm taup-max' id='taup-max'  type="number" min="0.2" max="100" value="50" decimals="1" step="1"></div>
    </div>

    <div class='row'>
        <div class='col-3 text-end'><b>Lambda</b></div>
        <div class='col-3'><input class='form-control form-control-sm lambda-initial' id = 'lambda-initial' type="number" min="0.1" max="1.0" value="0.1"
                decimals="1" step="0.1">
        </div>

        <div class='col-3'><input class='form-control form-control-sm lambda-min' id = 'lambda-min' type="number" min="0.0" max="2" value="0.0"
                decimals="1" step="0.1"></div>
        <div class='col-3'><input class='form-control form-control-sm lambda-max' id = 'lambda-max' type="number" min="0.0" max="2.0" value="1.0"
                decimals="1" step="0.1"></div>
    </div>

    <div class='row'>
        <div class='col-3 text-end'><b>Primary coefficient</b></div>
        <div class='col-3'><input class='form-control form-control-sm primary-initial' id='primary-initial' type="number" min="0.1" max="1" value="1.0"
                decimals="1" step="0.1"></div>
        <div class='col-3'><input class='form-control form-control-sm primary-min' id='primary-min' type="number" min="0.0" max="2" value="0"
                decimals="1" step="0.1"></div>
        <div class='col-3'><input class='form-control form-control-sm primary-max'  id='primary-max' type="number" min="0.0" max="2.0" value="1.0"
                decimals="1" step="0.1"></div>
    </div>

    <div class='row'>
        <div class='col-3 text-end'><b>Productivity index</b></div>
        <div class='col-3'><input class='form-control form-control-sm productivity-initial' id='productivity-initial' type="number" min="0.1" max="1" value="0.0"
                decimals="1" step="0.1"></div>
        <div class='col-3'><input class='form-control form-control-sm productivity-min' id='productivity-min' type="number" min="0.0" max="2" value="0"
                decimals="1" step="0.1"></div>
        <div class='col-3'><input class='form-control form-control-sm productivity-max' id='productivity-max' type="number" min="0.0" max="2.0" value="1.0"
                decimals="1" step="0.1"></div>
    </div>

    <div class='hidden row'>
        <div class='col-3 text-end'><b>Regularization</b></div>
        <div class='col-3'>
            <input class='form-control form-control-sm regularization' id='regularization' type="number" min="0.0" max="0.5" value="0.0" decimals="2"
                step="0.01">
        </div>

    </div>
</details>
   <!-- *********************************************** -->

   <br>
   <br>

                 <span class='subtitle'>Simulation name</span>
                <input id='model-name' class="form-control form-control-sm" type="text" value="TestModel1">
                <p></p>
                <div>
                    <hr>
                    Export only? <input id='crm-setup-export-only' type="checkbox" checked>
                    <button style='margin:5px' class="history-match-save-and-run btn btn-success">Run</button>
                    <button style='margin:5px' class="history-match-close-button btn btn-danger">Close</button>
                </div>
            </div>
        `;
    }



    setWellPairs(data) {

        alert('setWellPairs called');
        this.querySelector('injector-producer-table-component').setData(data);
    }

 



}

customElements.define('crm-setup-element', CRMSetupElement);


 
class CRMResultsComponent extends HTMLElement {

        _crmpData
         //_lastSankeyData = null;
         //_lastSankeyLayout = null;

         lastWellSelected;// = { name: null, type: null };

        /*
        const sampleData = {
  case_name: "TestModel1",
  data: [
    { INJECTOR: "I01", PRODUCER: "P1", ALLOCATION: 0.992909593, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I02", PRODUCER: "P1", ALLOCATION: 0.474019881, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I03", PRODUCER: "P1", ALLOCATION: 0.089225377, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I04", PRODUCER: "P1", ALLOCATION: 0.217863424, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I05", PRODUCER: "P1", ALLOCATION: 0.088541907, TAU: 0.349081711, TAUP: 49.99999996, PRODUCTIVITY: 0, Lo: 0, MODEL: "CRMP", R2: 0.991063231, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I01", PRODUCER: "P2", ALLOCATION: 0.013931884, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I02", PRODUCER: "P2", ALLOCATION: 0, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I03", PRODUCER: "P2", ALLOCATION: 0, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I04", PRODUCER: "P2", ALLOCATION: 0.099183015, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" },
    { INJECTOR: "I05", PRODUCER: "P2", ALLOCATION: 0.102164928, TAU: 29.33999056, TAUP: 50, PRODUCTIVITY: 0, Lo: 0.959811962, MODEL: "CRMP", R2: 0.937868466, SUBZONE: "SUBZONEUNIQUE", SIMULATION: "TestModel1" }
    // ... add the rest of the rows similarly
  ]
};*/

  connectedCallback() {
    this._lastWellSelected = { name: null, type: null };
    this.render();

    this.connectEvents()

  }

      // Sankey Diagram
    drawSankey() {
      const data = {
        type: "sankey",
        orientation: "h",
        node: {
          pad: 15,
          thickness: 20,
          line: { color: "black", width: 0.5 },
          label: ["Injector A", "Injector B", "Producer X", "Producer Y"],
          color: ["blue", "blue", "green", "green"]
        },
        link: {
          source: [0, 1, 0, 1],
          target: [2, 2, 3, 3],
          value: [5, 2, 3, 4]
        }
      };
  
      Plotly.react("sankey-diagram", [data], {
  margin: { l:0, r: 0, t: 20, b: 20 },
  autosize: true,
  //height: 600, 
  responsive: true
}, {responsive: true});
    }
  
    // Line Chart
   drawLineChart() {
      const x = Array.from({ length: 50 }, (_, i) => i);
      const series = Array.from({ length: 5 }, (_, i) => ({
        x,
        y: x.map((xi) => Math.sin(xi / 5 + i)),
        mode: "lines",
        name: `Series ${i + 1}`
      }));
  
      Plotly.react("history-match-chart", series, {
  title: "History Match Chart",
  legend: { orientation: "v" }, // vertical legend
  margin: { t: 40 },
  autosize: true,
  responsive: true
}, {responsive: true});

    }
    
    drawSankeyInjector(injectorName) {
  const data = this._crmpData;

  const rows = data.filter(row => row.INJECTOR === injectorName && row.ALLOCATION > 0);
  const producers = [...new Set(rows.map(r => r.PRODUCER))];

  const nodeLabels = [injectorName, ...producers];
  const sourceIndex = 0;
  const sourceIndices = rows.map(_ => sourceIndex);
  const targetIndices = rows.map(r => producers.indexOf(r.PRODUCER) + 1); // offset by 1
  const values = rows.map(r => r.ALLOCATION);

  const sankeyData = {
    type: "sankey",
    orientation: "h",
    node: {
      pad: 15,
      thickness: 20,
      line: { color: "black", width: 0.5 },
      label: nodeLabels,
      color: [
        "blue",
        ...Array(producers.length).fill("green")
      ]
    },
    link: {
      source: sourceIndices,
      target: targetIndices,
      value: values,
      label: values.map(v => `Allocation: ${v.toFixed(3)}`)
    }
  };

  Plotly.react("sankey-diagram", [sankeyData], {
    margin: { t: 20, b: 20 },
    autosize: true,
    responsive: true,
    legend: { orientation: "v" },
    title: `Connections from ${injectorName}`
  });
}

drawSankeyInjectorWithContext(injectorName) {
  const data = this._crmpData;

  // Step 1: Get all producers connected to selected injector
  const directLinks = data.filter(row =>
    row.INJECTOR === injectorName && row.ALLOCATION > 0
  );
  const producers = [...new Set(directLinks.map(r => r.PRODUCER))];

  // Step 2: Get all other injectors connected to those producers (excluding selected injector)
  const secondLinks = data.filter(row =>
    producers.includes(row.PRODUCER) &&
    row.INJECTOR !== injectorName &&
    row.ALLOCATION > 0
  );

  const otherInjectors = [...new Set(secondLinks.map(r => r.INJECTOR))];

  // Create node labels: [selected injector], producers, other injectors
  const nodeLabels = [injectorName, ...producers, ...otherInjectors];

  // Utility to get index in node list
  const indexOf = label => nodeLabels.indexOf(label);

  // Step 3: Build first layer links: injector → producer
  const links1 = directLinks.map(row => ({
    source: indexOf(injectorName),
    target: indexOf(row.PRODUCER),
    value: row.ALLOCATION,
    label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));

  // Step 4: Build second layer links: producer → other injectors
  const links2 = secondLinks.map(row => ({
    source: indexOf(row.PRODUCER),
    target: indexOf(row.INJECTOR),
    value: row.ALLOCATION,
    label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));

  const allLinks = [...links1, ...links2];

  // Sankey plot data
  const sankeyData = {
    type: "sankey",
    orientation: "h",
    node: {
      pad: 15,
      thickness: 20,
      line: { color: "black", width: 0.5 },
      label: nodeLabels,
      color: nodeLabels.map(label =>
        label === injectorName
          ? "blue"
          : producers.includes(label)
          ? "green"
          : "orange"
      )
    },
    link: {
      source: allLinks.map(l => l.source),
      target: allLinks.map(l => l.target),
      value: allLinks.map(l => l.value),
      label: allLinks.map(l => l.label)
    }
  };

  Plotly.react("sankey-diagram", [sankeyData], {
    margin: { t: 20, b: 20 },
    autosize: true,
    responsive: true,
    title: `Injector ${injectorName} → Producers → Connected Injectors`,
    legend: { orientation: "v" }
  });

  //this._lastSankeyData = sankeyData;
  //this._lastSankeyLayout = layout;

}

no_locs_drawSankeyProducerWithContext(producerName) {
  const data = this._crmpData;

  // Step 1: Find all injectors connected to the selected producer
  const incoming = data.filter(row =>
    row.PRODUCER === producerName && row.ALLOCATION > 0
  );
  const injectors = [...new Set(incoming.map(r => r.INJECTOR))];

  // Step 2: For each of those injectors, find other producers they connect to
  const outgoing = data.filter(row =>
    injectors.includes(row.INJECTOR) &&
    row.PRODUCER !== producerName &&
    row.ALLOCATION > 0
  );

  const otherProducers = [...new Set(outgoing.map(r => r.PRODUCER))];

  // Step 3: Build full node list
  const nodeLabels = [...injectors, producerName, ...otherProducers];
  const indexOf = label => nodeLabels.indexOf(label);

  // Step 4: Build links
  const links1 = incoming.map(row => ({
    source: indexOf(row.INJECTOR),
    target: indexOf(producerName),
    value: row.ALLOCATION,
    label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));

  const links2 = outgoing.map(row => ({
    source: indexOf(row.INJECTOR),
    target: indexOf(row.PRODUCER),
    value: row.ALLOCATION,
    label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));

  const allLinks = [...links1, ...links2];

  // Sankey diagram
  const sankeyData = {
    type: "sankey",
    orientation: "h",
    node: {
      pad: 15,
      thickness: 20,
      line: { color: "black", width: 0.5 },
      label: nodeLabels,
      color: nodeLabels.map(label => {
        if (label === producerName) return "green";
        if (injectors.includes(label)) return "blue";
        return "orange"; // other producers
      })
    },
    link: {
      source: allLinks.map(l => l.source),
      target: allLinks.map(l => l.target),
      value: allLinks.map(l => l.value),
      label: allLinks.map(l => l.label)
    }
  };

  Plotly.react("sankey-diagram", [sankeyData], {
    margin: { t: 20, b: 20 },
    autosize: true,
    responsive: true,
    title: `Injectors → ${producerName} → Other Producers`,
    legend: { orientation: "v" }
  });
}

drawSankeyProducerWithContext(producerName) {
  const data = this._crmpData;

  // Step 1: Find injectors connected to selected producer
  const incoming = data.filter(row =>
    row.PRODUCER === producerName && row.ALLOCATION > 0
  );
  const injectors = [...new Set(incoming.map(r => r.INJECTOR))];

  // Step 2: Find other producers connected to those injectors
  const outgoing = data.filter(row =>
    injectors.includes(row.INJECTOR) &&
    row.PRODUCER !== producerName &&
    row.ALLOCATION > 0
  );
  const otherProducers = [...new Set(outgoing.map(r => r.PRODUCER))];

  // Step 3: Build full node list: [other producers, injectors, selected producer]
  const nodeLabels = [...otherProducers, ...injectors, producerName];
  const indexOf = label => nodeLabels.indexOf(label);

  const links1 = incoming.map(row => ({
    source: indexOf(row.INJECTOR),
    target: indexOf(producerName),
    value: row.ALLOCATION,
    label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));

  const links2 = outgoing.map(row => ({
    source: indexOf(row.PRODUCER),
    target: indexOf(row.INJECTOR),
    value: row.ALLOCATION,
    label: `Alloc: ${row.ALLOCATION.toFixed(3)}`
  }));

  const allLinks = [...links2, ...links1];

  // Step 4: Assign fixed horizontal positions (x)
  const x = nodeLabels.map(label => {
    if (label === producerName) return 0.9; // far right
    if (injectors.includes(label)) return 0.5; // middle
    return 0.1; // left for other producers
  });

  const sankeyData = {
    type: "sankey",
    orientation: "h",
    node: {
      pad: 15,
      thickness: 20,
      line: { color: "black", width: 0.5 },
      label: nodeLabels,
      color: nodeLabels.map(label => {
        if (label === producerName) return "green";
        if (injectors.includes(label)) return "blue";
        return "orange";
      }),
      x: x
    },
    link: {
      source: allLinks.map(l => l.source),
      target: allLinks.map(l => l.target),
      value: allLinks.map(l => l.value),
      label: allLinks.map(l => l.label)
    }
  };

  Plotly.react("sankey-diagram", [sankeyData], {
    margin: { t: 20, b: 20 },
    autosize: true,
    responsive: true,
    title: `Other Producers → Injectors → ${producerName}`,
    legend: { orientation: "v" }
  });

  //this._lastSankeyData = sankeyData;
  //this._lastSankeyLayout = layout;

}


    drawSankey2(producerName) {
  const data = this._crmpData;

  const rows = data.filter(row => row.PRODUCER === producerName && row.ALLOCATION > 0);
  const injectors = [...new Set(rows.map(r => r.INJECTOR))];

  const nodeLabels = [...injectors, producerName];
  const sourceIndices = rows.map(r => injectors.indexOf(r.INJECTOR));
  const targetIndex = injectors.length; // producer is last node
  const targets = rows.map(_ => targetIndex);
  const values = rows.map(r => r.ALLOCATION);

  console.log("Sankey Data:", {
    sourceIndices,
    targets,
    values
  });


  const sankeyData = {
    type: "sankey",
    orientation: "h",
    node: {
      pad: 15,
      thickness: 20,
      line: { color: "black", width: 0.5 },
      label: nodeLabels,
      color: [
        ...Array(injectors.length).fill("blue"),
        "red"  // producer
      ]
    },
    link: {
      source: sourceIndices,
      target: targets,
      value: values,
      label: values.map(v => `Alloc: ${v.toFixed(3)}`) 
    }
  };

  /*const annotations = values.map((val, i) => ({
  x: 0.5, // approximate center horizontally
  y: 1 - (i + 1) / (values.length + 1), // stagger vertically
  text: val.toFixed(3),
  showarrow: false,
  font: { color: 'black', size: 12 },
  align: 'center',
  }));*/

  Plotly.react("sankey-diagram", [sankeyData], {
    margin: { t: 20, b: 20 },
    autosize: true,
    responsive: true,
    legend: { orientation: "v" },
    title: `Connections to ${producerName}`,
    //annotations: annotations // 
  });
}


  connectEvents(){
   // sim-results-component-main tab switching
    const buttons = document.querySelectorAll(".tab-button");
    const pages = document.querySelectorAll(".sim-results-component-page-content");
  
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        buttons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
  
        pages.forEach((p) => p.classList.remove("active"));
        const target = document.getElementById(btn.dataset.target);
        target.classList.add("active");
  
        
        if (btn.dataset.target === "page1") {
  const { name, type } = this._lastWellSelected || {};
  if (name && type === "injector") {
    this.drawSankeyInjectorWithContext(name);
  } else if (name && type === "producer") {
    this.drawSankeyProducerWithContext(name);
  } else {
    this.drawSankey(); // default overview
  }
}
        
        if (btn.dataset.target === "page2") {;}
        
        //this.drawLineChart();
        //if (btn.dataset.target === "page0") populateFitTable();
        
      });
    });
  
    // Well tab toggle
    document.querySelectorAll(".sim-results-component-well-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".sim-results-component-well-tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
  
        document.querySelectorAll(".sim-results-component-well-tab-content").forEach(c => c.classList.remove("active"));
        document.getElementById(tab.dataset.target).classList.add("active");
      });
    });

    document.querySelector(".sim-results-component-close-button").addEventListener('click', () =>{

        this.dispatchEvent(new CustomEvent('close-clicked'));


    }); 

  }

  render() {
    this.innerHTML = `
   <div class>
    <!-- Top Bar -->
    <div class="sim-results-component-top-bar">
      <div class="sim-results-component-top-left">
        <div>
          <label><strong>Simulation Case</strong></label><br />
          <span id="case-name">Loading...</span>
        </div>
        <div>
          <label><strong>Overall fit quality</strong></label>
          <div id="sim-results-component-fit-box">Loading...</div>
        </div>
      </div>

      <div class="sim-results-component-top-right">
        <strong>Show in map</strong>
        <label><input type="checkbox" id="individual_fit" /> Individual fit quality</label>
        <label><input type="checkbox" id="connectivity" /> Connectivity</label>
        <label><input type="checkbox" id="recommendation" /> Recommendation</label>
      </div>
    </div>

    <!-- sim-results-component-pagination Row -->
    <div class="sim-results-component-pagination">
      <button class="tab-button active" data-target="page0">Well-fit quality</button>
      <!-- button class="tab-button" data-target="page2">AnotherOne</button -->
      <button class="tab-button" data-target="page1">Well-support Details</button>
      <!-- button class="tab-button" data-target="page3">AnotherTwo</button -->
    </div>

    <!-- sim-results-component-main Page Content -->
    <div class="sim-results-component-main">
<!-- Well-fit quality tab -->
<div id="page0" class="sim-results-component-page-content active">
  <div id="sim-results-component-bar-chart" style="width: 100%; height: 400px;"></div>
  <div class="sim-results-component-button-grid" id="sim-results-component-button-grid"></div>
  <input type="checkbox" id="show-all" checked />
  <label for="show-all">Show all</label>
  <div style='height:600px; background-color:red'>
  <div id="history-match-chart" style="width: 100%; height: 100%;"></div>
  </div>


  </div>












      <!-- Well-support Details -->
      <div id="page1" class="sim-results-component-page-content">
        <!-- h3>Well-support Details</h3 -->
        <div class="sim-results-component-well-support-container">
          <div class="sim-results-component-well-list">
            <div class="sim-results-component-sim-results-component-well-tabs">
              <button class="sim-results-component-well-tab active" data-target="injector-list">Injectors</button>
              <button class="sim-results-component-well-tab" data-target="producer-list">Producers</button>
            </div>
            <div id="injector-list" class="sim-results-component-well-tab-content active">
              <ul>
                <li>Injector A</li>
                <li>Injector B</li>
                <li>Injector C</li>
              </ul>
            </div>
            <div id="producer-list" class="sim-results-component-well-tab-content">
              <ul>
                <li>Producer X</li>
                <li>Producer Y</li>
                <li>Producer Z</li>
              </ul>
            </div>
          </div>
          <div id="sankey-diagram" style="flex: 1; min-width: 300px; height: 800px;"></div>
        </div>
      </div>
 
      <!-- AnotherOne -->
      <!-- div id="page2" class="sim-results-component-page-content">
        <!-- h2>AnotherOne</h2 -->
        <!-- div style="margin-bottom: 10px;">
          <input type="radio" id="liquid" name="match" checked />
          <label for="liquid">Liquid history match</label>
          <input type="radio" id="watercut" name="match" style="margin-left: 20px;" />
          <label for="watercut">Watercut history match</label>
        </div -->
        <div id="history-match-chart2" style="width: 100%; height: 400px;"></div>
      </div -->

      <!-- AnotherTwo -->
      <!-- div id="page3" class="sim-results-component-page-content">
      
        <p>This is the content for AnotherTwo.</p>
      </div -->
    </div>
        
    <button class='sim-results-component-close-button btn btn-danger'>Close </button>

  </div>
    `;

    // After injecting HTML, initialize script-based behavior:
    this.setup();
  }

  setup() {
    // Re-run all JavaScript logic (same as from your original <script>)
    // For example:
    document.getElementById("case-name").textContent = "Case_1234";
    // Add all other logic here (or modularize it externally and call it)
  }

  //api 
  setData = ( case_name, data) => {
    
  this._crmpData = data;
  this.drawLineChart();

  // Set case name
  this.querySelector("#case-name").textContent = case_name;

  // Convert raw data into a Map structure
  const df = data;

  const r2Values = df.map(row => row.R2);
  const avgR2 = r2Values.reduce((a, b) => a + b, 0) / r2Values.length;

  // Determine overall fit quality
  let overallQuality = "Unknown";
  if (avgR2 < 0.65) overallQuality = "poor";
  else if (avgR2 < 0.86) overallQuality = "medium";
  else overallQuality = "good";
  const qualityBox = this.querySelector("#sim-results-component-fit-box");
  const qualityMap = {
    poor: { bg: "red", label: "Poor" },
    medium: { bg: "orange", label: "Medium" },
    good: { bg: "green", label: "Good" }
  };

  const q = qualityMap[overallQuality];
  qualityBox.style.backgroundColor = q.bg;
  qualityBox.textContent = q.label;

  // List of unique producers and injectors
  const producers = [...new Set(df.map(row => row.PRODUCER))];
  const injectors = [...new Set(df.map(row => row.INJECTOR))];

  console.log( "Producers:", producers);
  console.log( "Injectors:", injectors);
  console.log( "DataFrame:", df);

 
  // Compute fit quality for each producer
// Compute fit quality for each producer
const producerMap = {};
producers.forEach(p => {
  const pRows = df.filter(row => row.PRODUCER === p);
  const avg = pRows.reduce((sum, r) => sum + r.R2, 0) / pRows.length;
  let fit = "poor";
  if (avg >= 0.86) fit = "good";
  else if (avg >= 0.65) fit = "medium";
  producerMap[p] = fit;
});

// Define producerNames array here
const producerNames = Object.keys(producerMap);

// Render fit buttons
const buttonGrid = this.querySelector(".sim-results-component-button-grid");
buttonGrid.innerHTML = "";
producerNames.forEach(name => {
  const btn = document.createElement("button");
  const quality = producerMap[name];
  btn.className = `fit-button fit-${quality}`;
  btn.textContent = name;
  buttonGrid.appendChild(btn);
});

// Bar chart
const counts = {
  good: producerNames.filter(p => producerMap[p] === 'good').length,
  medium: producerNames.filter(p => producerMap[p] === 'medium').length,
  poor: producerNames.filter(p => producerMap[p] === 'poor').length
};

Plotly.newPlot('sim-results-component-bar-chart', [{
  x: ['Good', 'Medium', 'Poor'],
  y: [counts.good, counts.medium, counts.poor],
  type: 'bar',
  marker: {
    color: ['#4caf50', '#ff9800', '#f44336']
  },
  text: [counts.good, counts.medium, counts.poor],
  textposition: 'auto'
}], {
  title: {'text':'Fit Quality Distribution'},
  yaxis: { title: 'Number of Wells' },
  autosize:true,automargin:true,
  x:{ automargin:true},  yaxis: {
  title: {
    text: 'Count',
    font: {
      size: 14
    }
  }
},

  responsive: true
}, {responsive: true});












  /*const tableBody = this.querySelector("#sim-results-component-fit-table tbody");
  tableBody.innerHTML = "";

  const producerNames = Object.keys(producerMap);
  for (let i = 0; i < producerNames.length; i += 3) {
    const row = document.createElement("tr");
    for (let j = 0; j < 3; j++) {
      const p = producerNames[i + j];
      const cell = document.createElement("td");
      if (p) {
        const quality = producerMap[p];
        cell.className = `fit-${quality}`;
        cell.textContent = p;
      }
      row.appendChild(cell);
    }
    tableBody.appendChild(row);
  }*/

  // Update Well-support injector/producer lists

  const injectorList = this.querySelector("#injector-list ul");
  const producerList = this.querySelector("#producer-list ul");
  injectorList.innerHTML = "";
  producerList.innerHTML = "";

  injectors.forEach(inj => {
  const li = document.createElement("li");
  li.textContent = inj;
  li.style.cursor = "pointer";
  li.addEventListener("click", () => {
    //this.drawSankeyInjector(inj);
    this._lastWellSelected = { name: inj, type: "injector" };
    this.drawSankeyInjectorWithContext(inj);


  });
  injectorList.appendChild(li);
});

  producers.forEach(p => {
    const li = document.createElement("li");
    li.textContent = p;
    li.style.cursor = "pointer";
    li.addEventListener("click", () => {
    //this.drawSankey2(p);
    this.drawSankeyProducerWithContext(p);
    this._lastWellSelected = { name: p, type: "producer" };

    });

    producerList.appendChild(li);
    });
}


}
customElements.define("crm-results-component", CRMResultsComponent);
 
