/* Javascript for XBlockExtemporaneousGrading. */
function XBlockExtemporaneousGrading(runtime, element) {
  const setLateSubmission = runtime.handlerUrl(element, "set_late_submission");
  const downloadCSV = runtime.handlerUrl(element, "download_csv");

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

  $(element)
    .find(`#download_csv`)
    .click(function () {
      const data = {};
      $.post(downloadCSV, JSON.stringify(data))
        .done(function (response) {
          window.location.href = response.download_url;
        })
        .fail(function () {
          console.log("Error to download CSV");
        });
    });
}
