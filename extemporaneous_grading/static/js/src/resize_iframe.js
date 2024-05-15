/*
This is a simplified version of this script:
https://github.com/openedx/edx-platform/blob/master/lms/templates/courseware/courseware-chromeless.html#L119-L217
The script is responsible for resizing the iframe containing the content restriction block.
By default, in edx-platform, the script is loaded in the courseware-chromeless.html template,
however, in chromium based browsers, the script is not executed when the content of the
component changes. So, we need to include the script manually.
*/
$(function () {
  if (window !== window.parent) {
    document.body.className += " view-in-mfe";
    var contentElement = document.getElementById("content");

    function dispatchResizeMessage(event) {
      var newHeight = contentElement.offsetHeight;
      var newWidth = contentElement.offsetWidth;

      window.parent.postMessage(
        {
          type: "plugin.resize",
          payload: {
            width: newWidth,
            height: newHeight,
          },
        },
        // In chromium based browsers `document.referrer` is not returning the URL of the
        // MFE, instead it returns the URL of the LMS, so we need to accept all destination
        // sources so that the message can be sent without problems.
        "*"
      );
    }
    const observer = new MutationObserver(dispatchResizeMessage);
    observer.observe(document.body, { attributes: true, childList: true, subtree: true });

    window.addEventListener("load", dispatchResizeMessage);

    const resizeObserver = new ResizeObserver(dispatchResizeMessage);
    resizeObserver.observe(document.body);
  }
})();
