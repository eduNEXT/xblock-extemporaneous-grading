"""Extemporaneous Grading XBlock."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional

import pkg_resources
from django.utils import timezone, translation
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Boolean, DateTime, JSONField, Scope, String
from xblock.utils.resources import ResourceLoader
from xblock.utils.studio_editable import FutureFields, StudioContainerWithNestedXBlocksMixin, StudioEditableXBlockMixin
from xblock.utils.studio_editable import loader as studio_loader
from xblock.validation import Validation

from extemporaneous_grading.utils import _

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

TIME_PATTERN = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"


@XBlock.needs("i18n", "call_to_action")
class XBlockExtemporaneousGrading(StudioContainerWithNestedXBlocksMixin, StudioEditableXBlockMixin, XBlock):
    """
    Extemporaneous Grading XBlock.

    This XBlock provides a way to display content to students according to dates
    set as due date and late submission date.
    """

    CATEGORY = "extemporaneous_grading"

    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        scope=Scope.settings,
        default=_("Extemporaneous Grading"),
    )

    due_date = DateTime(
        display_name=_("Due Date"),
        help=_(
            "The due date for this component. If the learner access before this date, "
            "the learner will see the content without any restrictions."
        ),
        scope=Scope.settings,
        default=datetime.now(),
    )

    due_time = String(
        display_name=_("Due Time (UTC)"),
        help=_("The time of the due date. The valid format is HH:MM."),
        scope=Scope.settings,
        default="00:00",
    )

    late_due_date = DateTime(
        display_name=_("Late Due Date"),
        help=_(
            "The late due date for this component. If the learner access after the due date "
            "and before the late due date, the learner will see a message that the submission "
            "is late. If the learner accepts the late submission pressing the button, the "
            "learner will see the content."
        ),
        scope=Scope.settings,
        default=datetime.now(),
    )

    late_due_time = String(
        display_name=_("Late Due Time (UTC)"),
        help=_("The time of the late due date. The valid format is HH:MM."),
        scope=Scope.settings,
        default="00:00",
    )

    due_date_explanation_text = String(
        display_name=_("Due Date Explanation Text"),
        help=_("The explanation text that will be shown to the learner when the due date is passed."),
        scope=Scope.settings,
        default=_(
            "The due date has passed. You can still submit this assignment until the "
            "late due date. After the late due date, you will not be able to submit "
            "this assignment. If you accept the late submission, press the button."
        ),
    )

    late_due_date_explanation_text = String(
        display_name=_("Late Due Date Explanation Text"),
        help=_("The explanation text that will be shown to the learner when the late due date is passed."),
        scope=Scope.settings,
        default=_("The late due date has passed. You can not submit this assignment anymore."),
    )

    late_submission = Boolean(
        display_name=_("Late Submission"),
        help=_("Flag to indicate if the submission is late."),
        scope=Scope.user_state,
        default=False,
    )

    editable_fields = [
        "display_name",
        "due_date",
        "due_time",
        "late_due_date",
        "late_due_time",
        "due_date_explanation_text",
        "late_due_date_explanation_text",
    ]

    def resource_string(self, path: str) -> str:
        """
        Handy helper for getting resources from our kit.

        Args:
            path (str): The path to the resource.

        Returns:
            str: The resource as a string.
        """
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def render_template(self, template_path: str, context: Optional[dict] = None) -> str:
        """
        Render a template with the given context.

        The template is translated according to the user's language.

        Args:
            template_path (str): The path to the template
            context(dict, optional): The context to render in the template

        Returns:
            str: The rendered template
        """
        return loader.render_django_template(template_path, context, i18n_service=self.runtime.service(self, "i18n"))

    def author_view(self, context: dict) -> Fragment:
        """
        Render the Studio preview by rendering each child so that they can all be seen and edited.

        Args:
            context (dict): The context to render in the template

        Returns:
            Fragment: The fragment to be rendered
        """
        fragment = Fragment()
        root_xblock = context.get("root_xblock")
        is_root = root_xblock and root_xblock.location == self.location
        if is_root:
            # User has clicked the "View" link. Show a preview of all possible children:
            self.render_children(context, fragment, can_reorder=True, can_add=True)
        # else: When shown on a unit page, don't show any sort of preview -
        # just the status of this block in the validation area.

        return fragment

    def studio_view(self, context: dict) -> Fragment:  # pragma: no cover
        """
        Render a form for editing this XBlock.

        Args:
            context (dict): The context to render in the template

        Returns:
            Fragment: The fragment to be rendered
        """
        fragment = Fragment()
        context = {"fields": []}

        # Build a list of all the fields that can be edited:
        for field_name in self.editable_fields:
            field = self.fields[field_name]  # pylint: disable=unsubscriptable-object
            assert field.scope in (Scope.content, Scope.settings), (
                "Only Scope.content or Scope.settings fields can be used with "
                "StudioEditableXBlockMixin. Other scopes are for user-specific data and are "
                "not generally created/configured by content authors in Studio."
            )
            field_info = self._make_field_info(field_name, field)
            if field_info is not None:
                if field_info["type"] == "string":
                    field_info["default"] = self.ugettext(field_info.get("default"))
                    field_info["value"] = self.ugettext(field_info.get("value"))
                    if "values" in field_info:
                        for value in field_info["values"]:
                            value["display_name"] = self.ugettext(value.get("display_name"))
                context["fields"].append(field_info)

        fragment.content = studio_loader.render_django_template("templates/studio_edit.html", context)
        fragment.add_javascript(studio_loader.load_unicode("public/studio_edit.js"))
        fragment.initialize_js("StudioEditableXBlockMixin")

        return fragment

    def student_view(self, context: Optional[dict] = None) -> Fragment:
        """
        View for students according to the due date and late due date.

        If the due date did not pass, the student can see children blocks.
        If the due date passed, the student can accept late submission and see children blocks.
        If the late due date passed, the student can not see the children blocks.

        Args:
            context (dict, optional): The context to render in the template

        Returns:
            Fragment: The fragment to be rendered
        """
        fragment = Fragment()
        children_contents = []
        render_context = {
            "block": self,
            "due_datetime": self.due_datetime.isoformat(),
            "late_due_datetime": self.late_due_datetime.isoformat(),
            **context,
        }

        if (template_name := self.get_template()) == "children":
            for child_id in self.children:
                child = self.runtime.get_block(child_id)
                child_fragment = self._render_child_fragment(child, context, "student_view")
                fragment.add_fragment_resources(child_fragment)
                children_contents.append(child_fragment.content)

            render_context.update({"children_contents": children_contents})

        # Add i18n js
        statici18n_js_url = self._get_statici18n_js_url()
        if statici18n_js_url:
            fragment.add_javascript_url(self.runtime.local_resource_url(self, statici18n_js_url))

        fragment.add_content(self.render_template(f"static/html/{template_name}.html", render_context))
        fragment.add_css(self.resource_string("static/css/extemporaneous_grading.css"))
        fragment.add_javascript(self.resource_string("static/js/src/extemporaneous_grading.js"))
        fragment.add_javascript(self.resource_string("static/js/src/resize_iframe.js"))
        fragment.initialize_js("XBlockExtemporaneousGrading")

        return fragment

    def get_template(self) -> str:
        """
        Get the template name based on the current datetime.

        Returns:
            str: The template name.
        """
        current_datetime = timezone.now()
        if current_datetime > self.late_due_datetime:
            return "late_due_datetime"
        if self.due_datetime < current_datetime < self.late_due_datetime and not self.late_submission:
            return "due_datetime"
        return "children"

    @property
    def due_datetime(self) -> datetime:
        """
        Get the due date as a datetime object.

        Returns:
            datetime: The due date.
        """
        return self.parse_datetime(self.due_date, self.due_time)

    @property
    def late_due_datetime(self) -> datetime:
        """
        Get the late due date as a datetime object.

        Returns:
            datetime: The late due date.
        """
        return self.parse_datetime(self.late_due_date, self.late_due_time)

    @staticmethod
    def parse_datetime(date: datetime, time: str) -> datetime:
        """
        Parse a datetime object from a date and time string.

        Args:
            date (datetime): The date object.
            time (str): The time string in the format HH:MM.

        Returns:
            datetime: The datetime object.
        """
        time = datetime.strptime(time, "%H:%M").time()
        return datetime.combine(date, time).replace(tzinfo=timezone.utc)

    @XBlock.json_handler
    def set_late_submission(self, data: dict, suffix: str = "") -> dict:  # pylint: disable=unused-argument
        """
        Set the late submission flag to True.

        Args:
            data (dict): The data received from the client.
            suffix (str, optional): The suffix of the handler.

        Returns:
            dict: The response to the client.
        """
        self.late_submission = True
        return {
            "success": True,
        }

    @staticmethod
    def validate_time(time: Optional[str]) -> None:
        """
        Validate the time format.

        Args:
            time (str, optional): The time string to validate.

        Raises:
            JsonHandlerError: If the time format is invalid.
        """
        if time and not re.match(TIME_PATTERN, time):
            raise JsonHandlerError(400, _("Invalid time format. The valid format is HH:MM."))

    @XBlock.json_handler
    def submit_studio_edits(self, data: dict, suffix: str = ""):  # pragma: no cover
        """
        AJAX handler for studio_view() Save button.
        """
        self.validate_time(data["values"].get("due_time"))
        self.validate_time(data["values"].get("late_due_time"))

        values = {}  # dict of new field values we are updating
        to_reset = []  # list of field names to delete from this XBlock
        for field_name in self.editable_fields:
            field = self.fields[field_name]  # pylint: disable=unsubscriptable-object
            if field_name in data["values"]:
                if isinstance(field, JSONField):
                    values[field_name] = field.from_json(data["values"][field_name])
                else:
                    raise JsonHandlerError(400, f"Unsupported field type: {field_name}")
            elif field_name in data["defaults"] and field.is_set_on(self):
                to_reset.append(field_name)
        self.clean_studio_edits(values)
        validation = Validation(self.scope_ids.usage_id)
        # We cannot set the fields on self yet, because even if validation fails, studio is going to save any changes we
        # make. So we create a "fake" object that has all the field values we are about to set.
        preview_data = FutureFields(new_fields_dict=values, newly_removed_fields=to_reset, fallback_obj=self)
        self.validate_field_data(validation, preview_data)
        if validation:
            for field_name, value in values.items():
                setattr(self, field_name, value)
            for field_name in to_reset:
                self.fields[field_name].delete_from(self)  # pylint: disable=unsubscriptable-object
            return {"result": "success"}
        else:
            raise JsonHandlerError(400, validation.to_json())

    @staticmethod
    def workbench_scenarios() -> list:  # pragma: no cover
        """Create canned scenario for display in the workbench."""
        return [
            (
                "XBlockExtemporaneousGrading",
                """<extemporaneous_grading/>
             """,
            ),
            (
                "Multiple XBlockExtemporaneousGrading",
                """<vertical_demo>
                <extemporaneous_grading/>
                <extemporaneous_grading/>
                <extemporaneous_grading/>
                </vertical_demo>
             """,
            ),
        ]

    @staticmethod
    def _get_statici18n_js_url() -> str | None:  # pragma: no cover
        """
        Return the Javascript translation file for the currently selected language, if any.

        Defaults to English if available.
        """
        locale_code = translation.get_language()
        if locale_code is None:
            return None
        text_js = "public/js/translations/{locale_code}/text.js"
        lang_code = locale_code.split("-")[0]
        for code in (translation.to_locale(locale_code), lang_code, "en"):
            if pkg_resources.resource_exists(loader.module_name, text_js.format(locale_code=code)):
                return text_js.format(locale_code=code)
        return None
