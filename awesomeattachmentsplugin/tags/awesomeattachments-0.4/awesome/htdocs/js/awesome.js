jQuery(document).ready(function ($) {

  var $propertyform = $('#propertyform');
  var $properties = $('#properties', $propertyform);
  $propertyform.attr('enctype', 'multipart/form-data');

  var addhref = $('.add-image').attr('href');
  var edithref = $('.edit-image').attr('href');
  var deletehref = $('.delete-image').attr('href');

  var upload = '\
    <div class="upload">\
      <span>\
        <a class="uploadDescription" href="#"><img src="' + edithref + '"></a>\
        <input class="fileInput" type="file" name="attachment[]" />\
      </span>\
      <div class="field">\
        <label>Description of the file (optional):<br />\
        <input type="text" class="trac-fullwidth" name="description[]" \
               size="60" />\
        </label>\
      </div>\
    </div>';

  var uploadContainer = '\
    <fieldset>\
      <legend>Add Files</legend>\
      <div id="uploads" class="uploads">\
      </div>\
      <a class="addUpload" href="#" style="float:right"><img src="' + addhref + '"></a>\
    </fieldset>';

  var remove = '<a class="removeUpload" href="#"><img src="' + deletehref + '"></a>'

  var $container = $(uploadContainer);
  $properties.after($container);

  function addUpload () {
    var $upload = $(upload);
    $container.append($upload);
    $('.uploadDescription', $upload).click(function () {
      addToDescription($(this).next().val());
      return false;
    });
    $('.fileInput', $upload).change(function () {
      if ($(this).val().match(/.((jpg)|(gif)|(jpeg)|(png))$/i)) {
        addToDescription($(this).val());
      }
    });
    return $upload;
  }

  function addToDescription (upload) {
    if (upload.length) {
      var name = upload.replace('C:\\fakepath\\', '');
      $('#field-description', $properties).insertAtCaret('[[Image(' + name + ')]]');
    }
  }

  $.fn.insertAtCaret = function (myValue) {
    return this.each(function () {
      //IE support
      if (document.selection) {
        this.focus();
        sel = document.selection.createRange();
        sel.text = myValue;
        this.focus();
      }
      //MOZILLA / NETSCAPE support
      else if (this.selectionStart || this.selectionStart == '0') {
        var startPos = this.selectionStart;
        var endPos = this.selectionEnd;
        var scrollTop = this.scrollTop;
        this.value = this.value.substring(0, startPos) + myValue +
          this.value.substring(endPos, this.value.length);
        this.focus();
        this.selectionStart = startPos + myValue.length;
        this.selectionEnd = startPos + myValue.length;
        this.scrollTop = scrollTop;
      } else {
        this.value += myValue;
        this.focus();
      }
    });
  };

  $('.addUpload', $container).click(function () {
    var $upload = addUpload();
    var $remove = $(remove);
    $('.fileInput', $upload).after($remove);
    $remove.click(function () {
      $upload.remove();
      return false;
    });
    return false;
  });

  addUpload();

  // Hide the "I have files to attach to this ticket" checkbox.
  $('input[name="attachment"]', $propertyform).closest('p').hide();

});
