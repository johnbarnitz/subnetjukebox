        $(document).ready(function() {
            // Initialize form index to the last form index in the formset

            let formIdx = $('#id_formset_prefix-TOTAL_FORMS').val();

            // Click event handler to add a new form
            $('#add-form').click(function() {
                $('#formset').append($('#formset .form-row:last').clone().find('input').each(function() {
                    // Update the name attribute of the cloned form fields with the new form index
                    let name = $(this).attr('name').replace(/-\d+-/, '-' + formIdx + '-');

                  	// Clear the value of the input field
                    $(this).attr('name', name).val('');
                }).end().find('input[name$=-id]').val('').end().find('.remove-form').show().end());

                formIdx++; // Increment the form index

          		// Update the management form's TOTAL_FORMS field
                $('#id_formset_prefix-TOTAL_FORMS').val(formIdx);
            });

            // Click event handler to remove a form
            $('#formset').on('click', '.remove-form', function() {
              	// Remove the selected form row
                $(this).closest('.form-row').remove();
                formIdx--; // Decrement the form index

              	// Update the management form's TOTAL_FORMS field
                $('#id_formset_prefix-TOTAL_FORMS').val(formIdx);
            });
             $('#id_label-type').on('change', function () {
                if ($(this).val() === 'DR') {
                    $('#formset').show();
                    $('#add-form').show();
                } else {
                    $('#formset').hide();
                    $('#add-form').hide();
                }
            });

			// Initially hide the remove button for the existing forms
			if ($("#form").attr("data-operation") === "create") {
                $('.remove-form').hide();
			}

//            $('#formset').hide();
        });
