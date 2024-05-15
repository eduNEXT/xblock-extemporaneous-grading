/* Javascript for XBlockExtemporaneousGrading. */
function XBlockExtemporaneousGrading(runtime, element) {
  const lateSubmission = runtime.handlerUrl(element, "late_submission");

  $(element)
    .find(`#late_submission`)
    .click(function () {
      const data = {};
      $.post(lateSubmission, JSON.stringify(data))
        .done(function (response) {
          window.location.reload(false);
        })
        .fail(function () {
          console.log("Error to accept late submission");
        });
    });
}
