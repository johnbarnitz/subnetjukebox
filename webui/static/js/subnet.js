$("#tagvalueForm").on("change", ".select_dropdown", function () {

      var name = $(this).attr('name');
      var parent_div = $(this).parent().closest('div');
      var type = $(this).find('option:selected').attr('data-type');
      var id = name.match(/\d+/)[0];
      buttonname = name.split("-")[2];
      console.log("bb name", name)
      var url = $("#tagvalueForm").attr("data-"+ buttonname + "value-url");  // get the url of the `load_cities` view
      console.log("url", url);
      console.log("type", type);
      var optionId = $(this).val();  // get the selected tag ID from the HTML input
      if (type == "TF") {
        // if there is an input here nothing to do, otherwise
        // if there is a dropdown here remove it
        // add the input in
        data = '<input type="text" id="id_labelvalue-'+id+'-value"  name="labelvalue-'+id+'-value">'
        $(parent_div).append(data);  // replace the contents of the city input with the data that came from the server

      } else  {
          if (buttonname == "label") {
            // if there is a select  here continue
            // if there is an input here remove it.
            // add in the select

            data = '<select name="'+ buttonname +'value-' + id +'-value" id="id_'+buttonname +'value-' +id +
                '-value"> <option value="0">-------</option> </select>';
            $(parent_div).append(data);
          }
          ajaxdata = {};
          ajaxdata[buttonname] = optionId;
          $.ajax({                       // initialize an AJAX request
            url: url,                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
            data: ajaxdata,
            success: function (data) {   // `data` is the return of the `load_cities` view function
              $("#id_" + buttonname + "value-" + id + "-value").html(data);  // replace the contents of the city input with the data that came from the server
            }
          });
    }
    });
 $(document).ready(function() {
	var x = 0;

$('.add-btn').click(function(e) {
  	e.preventDefault();
  	var name = $(this).attr('name');
    console.log("btn Name", name);

    var parent_div = $(this).parent().closest('div');

    appendRow(name, parent_div); // appen dnew element to form
   // x++; // increment counter for form
    $('#save_btn').show(); // show save button for form
  });

$('.input_wrapper').on('click', '.deleteBtn', function(e) {
  	e.preventDefault();
    var id = e.currentTarget.id; // set the id based on the event 'e'
    $('div[id='+id+']').remove(); //find div based on id and remove
    x--; // decrement the counter for form.

    if (x === 0) {
    	$('#save_btn').hide(); // hides the save button if counter is equal to zero
    }
  });

 $('#save_btn').click(function(e) {
  	e.preventDefault();
    var formData = $('#test_form').serializeObject(); // serialize the form
    var obj; //obj can be use to send to ajax call
    if(Array.isArray(formData.fn)) {
    	for(var i = 0; i < formData.fn.length; i++) {
      	obj = {};
        // set the obj for submittion
        obj.firstName = formData.fn[i];
        obj.lastName = formData.ln[i];
        // This object could be push into an array
        console.log('object from form array ', obj);
      };
    } else {
    	obj = {};
      obj.firstName = formData.fn;
      obj.lastName = formData.ln;
      console.log('single obj from form ', obj);
    }
  });


   function appendRow(name, parent_div) {

      var url = $("#tagvalueForm").attr("data-"+name+"-url");  // get the url of the `data-tag-url` view
      if (name == "label") {
        widget = ""
      } else {
        widget =   '<select name="'+ name +'value-' + x +'-value" id="id_'+name +'value-' +x +
                '-value"> <option value="0">-------</option> </select>'
      }

      $.ajax({                       // initialize an AJAX request
        url: url,                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)

        success: function (data) {   // `data` is the return of the `data-tag-url` view function

            $(parent_div).append(
               '<div id="'+x+'" class="form-group" style="display:flex;">' +
            '<div>' +
              '<select name="' + name +'value-' + x +'-' + name +'" class="select_dropdown" id="id_' + name +'value-' +x +'-'
               +name + '">'
                +data + ' </select>' +
            '</div>' +
            '<div id=id_'+name +'div-' +x + '">'+  widget   +
            '</div>' +
             '<div>'+
            '<button id="'+x+'" class="btn btn-danger deleteBtn">Del<i class="glyphicon glyphicon-trash"></i></button>' +
          '</div>' +

      	    '</div>');
            x++;
         }
      });
       const totalFormsInput = document.getElementById('id_'+ name +'value-TOTAL_FORMS');
       const formCount = parseInt(totalFormsInput.value);
       totalFormsInput.value = formCount + 1;
    }
  $('#input_wrapper').on('click', '.deleteBtn', function(e) {
  	e.preventDefault();
    var id = e.currentTarget.id; // set the id based on the event 'e'
    $('div[id='+id+']').remove(); //find div based on id and remove
    x--; // decrement the counter for form.

//    if (x === 0) {
//    	$('#save_btn').hide(); // hides the save button if counter is equal to zero
//    }
  });
});

$.fn.serializeObject = function(asString) {
   var o = {};
   var a = this.serializeArray();
   $.each(a, function() {

       if($('#' + this.name).hasClass('date')) {
           this.value = new Date(this.value).setHours(12);
       }

       if (o[this.name] !== undefined) {
           if (!o[this.name].push) {
               o[this.name] = [o[this.name]];
           }
           o[this.name].push(this.value || '');
       } else {
           o[this.name] = this.value || '';
       }
   });
   if (asString) {
       return JSON.stringify(o);
   }
   return o;
};
