    
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

