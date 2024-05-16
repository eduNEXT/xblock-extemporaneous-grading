/* Javascript for XBlockExtemporaneousGrading. */
function XBlockExtemporaneousGrading(runtime, element) {
  const setLateSubmission = runtime.handlerUrl(element, "set_late_submission");

  $(element)
    .find(`#late_submission`)
    .click(function () {
      const data = {};
      $.post(setLateSubmission, JSON.stringify(data))
        .done(function (response) {
          window.location.reload(false);
        })
        .fail(function () {
          console.log("Error to accept late submission");
        });
    });
}
