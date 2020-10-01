/* Dore Theme Select & Initializer Script

Table of Contents

01. Css Loading Util
02. Theme Selector And Initializer
*/

(function($) {
  if ($().dropzone) {
    Dropzone.autoDiscover = false;
  }
  var $dore = $("body").dore();

})(jQuery);
