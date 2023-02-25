$(document).ready(function(){     
    //Make script DOM ready

    $("#addProject").on('click',()=>{
      $("#loading").css('display', 'block');
    })
var opval = "" 

function hideUploadOtherResource() {
$('.upload-other-resource').each(function(i, obj) {
$( '#' + $(this).attr('id') ).hide();
});
}

hideUploadOtherResource()

$('#resourceFile').change(function(e) {   //jQuery Change Function
opval = $(this).val();                  //Get value from select element
// $('#awsS3bucket').show();
$('.upload-other-resource').each(function(i, obj) {
if (opval === $(this).attr('id') ) {
$('#' + opval).show();
} else {
$( '#' + $(this).attr('id') ).hide();
}
});
// if(opval=="awsS3bucket"){               //Compare it and if true
//   $('#resourceModal').modal("show");    //Open Modal
// } else if(opval=="gcpStorage") {
//   $('#resourceModal').modal("show");
// } else if(opval=="mySql") {
//   $('#resourceModal').modal("show");
// }
});

$('input:radio[id=uploadFile]').prop('checked', true);
$("label[for='uploadResource']").addClass('disabled-label');
$('#resourceFile').addClass('disabled-input');
$('#resourceFile').prop('disabled', true);
var selectedRadio = $('input:radio[id=uploadFile]')[0].id

$("input:radio[name=uploadFile]").click(function(e) {
selectedRadio = $(this)[0].id

$('#awsS3bucket').hide();

$("label[for='uploadFile']").removeClass('disabled-label');
$('#file').removeClass('disabled-input');
$('#file').prop('disabled', false);

$('input:radio[id=uploadResource]').prop('checked', false);
$("label[for='uploadResource']").addClass('disabled-label');
$('#resourceFile').addClass('disabled-input');
$('#resourceFile').prop('disabled', true);

})

$("input:radio[name=uploadResource]").click(function(e) {
selectedRadio = $(this)[0].id

$('input:radio[id=uploadFile]').prop('checked', false);
$("label[for='uploadFile']").addClass('disabled-label');
$('#file').addClass('disabled-input');
$('#file').prop('disabled', true);

$("label[for='uploadResource']").removeClass('disabled-label');
$('#resourceFile').removeClass('disabled-input');
$('#resourceFile').prop('disabled', false);

})


var tabularData = false
$('input[name="data_in_tabular"]').click(function(){
if($(this).prop("checked") == true){
tabularData = true
console.log("Checkbox is checked.");
}
else if($(this).prop("checked") == false){
tabularData = false
console.log("Checkbox is unchecked.");
}
});


$("#testConnection").click(function (event) {
//stop submit the form, we will post it manually.
event.preventDefault();

var formData = {
region_name: $("#region_name").val(),
aws_access_key_id: $("#aws_access_key_id").val(),
aws_secret_access_key: $("#aws_secret_access_key").val(),
bucket_name: $("#bucket_name").val(),
file_name: $("#file_name").val(),
resource_type: opval,
source_type: selectedRadio
};

// var object = {};
// data.forEach((value, key) => object[key] = value);
// console.log(JSON.stringify(object))

$.ajax({
  type: "POST",
  enctype: 'multipart/form-data',
  url: "/project",
  data: JSON.stringify(formData),
  processData: false,
  contentType: false,
  cache: false,
  timeout: 800000,
  success: function (data) {
      $("#output").text(data);
      console.log("SUCCESS : ", data);
      $("#btnSubmit").prop("disabled", false);
  },
  error: function (e) {
      $("#output").text(e.responseText);
      console.log("ERROR : ", e);
      $("#btnSubmit").prop("disabled", false);
  }
});
});

$("#addProject").click(function (event) {
//stop submit the form, we will post it manually.
event.preventDefault();

// Get form
var form = $('#project_form')[0];

$('.upload-other-resource').each(function(i, obj) {
var id = $(this).attr('id')
if ($(this).attr('id') !== opval) {
  $(form).each(function(){
    $(this).find('.' + id).remove()
  });
}
});

// FormData object 
var data = new FormData(form);

// If you want to add an extra field for the FormData
data.append("resource_type", opval);
data.append("source_type", selectedRadio);
data.delete("data_in_tabular");

// disabled the submit button
// $("#btnSubmit").prop("disabled", true);

// console the Form Data
// var object = {};
// data.forEach((value, key) => object[key] = value);
// console.log(JSON.stringify(object))

$.ajax({
  type: "POST",
  enctype: 'multipart/form-data',
  url: "/project",
  data: data,
  processData: false,
  contentType: false,
  cache: false,
  timeout: 800000,
  success: function(response) {
    if(response === '/') {
      window.location.href = response
    }
    else {
      document.write(response)
      document.close();
      window.onload = (event) => {
        hideUploadOtherResource()
      };
    }
  },
  error: function (e) {
    console.log("ERROR : ", e);
  }
});
});

});