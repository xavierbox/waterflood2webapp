
function old_showDialog(element, title) {
    return new Promise((resolve) => {
      const dialog = document.createElement('dialog');
      dialog.innerHTML = `
        <form method="dialog" class="p-4 border rounded shadow-sm">
            <h5 class="mb-3">${title}</h5>
            <div class="dialog-content mb-3"></div>
            <div class="mb-3">
                <label for="inputText" class="form-label">Enter text:</label>
                <input type="text" id="inputText" name="inputText" class="form-control">
            </div>
            <div class="d-flex justify-content-end">
                <button id="cancelButton" value="cancel" class="btn btn-secondary me-2">Cancel</button>
                <button id="applyButton" value="apply" class="btn btn-primary">Apply</button>
            </div>
        </form>
      `;
  
      dialog.querySelector('.dialog-content').appendChild(element);
      document.body.appendChild(dialog);
      dialog.showModal();
  
      dialog.addEventListener('close', () => {
        resolve({
          action: dialog.returnValue,
          text: document.getElementById('inputText').value
        });
        dialog.remove();
      });
    });
  }
  
  function showDialog(element, title) {
    return new Promise((resolve) => {
      const dialog = document.createElement('div');
      dialog.classList.add('dialog');
      dialog.setAttribute('role', 'dialog');
      dialog.setAttribute('aria-labelledby', 'dialog-title');
      dialog.setAttribute('tabindex', '-1');
      dialog.style.zIndex = '9999';
  
      dialog.innerHTML = `
        <div id="dialog-title" class='drag-handle'>
            ${title}
            <button class="close-btn" aria-label="Close">&times;</button>
        </div>
        <div class="dialog-body">
            <div class="dialog-content"></div>
        </div>
        <div class="dialog-footer">
            <button data-action="cancel" type="button" class="btn btn-secondary">Cancel</button>
            <button data-action="apply" type="button" class="btn btn-primary">Apply</button>
        </div>
      `;
  
      dialog.querySelector('.dialog-content').appendChild(element);
      document.body.appendChild(dialog);
  
      // Center the dialog initially
      dialog.style.left = `${(window.innerWidth - dialog.offsetWidth) / 2}px`;
      dialog.style.top = `${(window.innerHeight - dialog.offsetHeight) / 2}px`;
      dialog.focus();
  
      const handle = dialog.querySelector('.drag-handle');
      let offsetX, offsetY, isDragging = false;
  
      handle.addEventListener('mousedown', (e) => {
        isDragging = true;
        offsetX = e.clientX - dialog.offsetLeft;
        offsetY = e.clientY - dialog.offsetTop;
        document.body.style.userSelect = 'none';
  
        const onMouseMove = (e) => {
          if (isDragging) {
            dialog.style.left = `${e.clientX - offsetX}px`;
            dialog.style.top = `${e.clientY - offsetY}px`;
          }
        };
  
        const onMouseUp = () => {
          isDragging = false;
          document.body.style.userSelect = 'auto';
          document.removeEventListener('mousemove', onMouseMove);
          document.removeEventListener('mouseup', onMouseUp);
        };
  
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp, { once: true });
      });
  
      dialog.addEventListener('click', (e) => {
        if (e.target.dataset.action === 'cancel' || e.target.classList.contains('close-btn')) {
          resolve({ action: 'cancel', text: '' });
          dialog.remove();
        } else if (e.target.dataset.action === 'apply') {
          const inputText = element.value || element.textContent || '';
          resolve({ action: 'apply', text: inputText });
          dialog.remove();
        }
      });
    });
  }


          /*let p  = showDialog(element, 'Data-driven model setup');
        p.then ( (resp) =>{
            console.log( resp ); 
        });*/
