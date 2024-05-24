"""Extemporaneous Grading XBlock."""

from __future__ import annotations

import csv
import logging
import re
import tempfile
from datetime import datetime
from typing import Optional

import pkg_resources
from django.core.files.storage import default_storage
from django.utils import timezone, translation
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Boolean, DateTime, JSONField, List, Scope, String
from xblock.utils.resources import ResourceLoader
from xblock.utils.studio_editable import FutureFields, StudioContainerWithNestedXBlocksMixin, StudioEditableXBlockMixin
from xblock.utils.studio_editable import loader as studio_loader
from xblock.validation import Validation

from extemporaneous_grading.utils import _

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

ATTR_KEY_USER_ROLE = "edx-platform.user_role"
ATTR_ANONYMOUS_USER_ID = "edx-platform.anonymous_user_id"
ATTR_USER_EMAIL = "edx-platform.user_email"
ATTR_USER_USERNAME = "edx-platform.username"
TIME_PATTERN = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"


@XBlock.needs("user", "i18n")
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
            "The due date for this component. If the learner access it before this date, "
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
            "The late due date for this component. If the learner access it after the due date "
            "and before the late due date, the learner will see a message that the submission "
            "is late. If the learner accepts the late submission by pressing the button, the "
            "learner will see the content. When the late due date passes, the learner will not "
            "be able to see the content."
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
        help=_("The explanation text that will be shown to the learner when the due date has passed."),
        scope=Scope.settings,
        default=_(
            "The due date has passed. You can still submit this assignment until the "
            "late due date. After the late due date, you will not be able to submit "
            "this assignment or see the content. If you accept the late submission, "
            "press the button."
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

    late_submissions = List(
        display_name=_("Late Submissions"),
        help=_(
            "List of all students who accepted the late submission. Contains "
            "the anonymous_user_id, username, email, and datetime for each student."
        ),
        scope=Scope.user_state_summary,
        default=[],
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

    def get_current_user(self):
        """
        Get the current user.
        """
        return self.runtime.service(self, "user").get_current_user()

    @property
    def is_course_team(self) -> bool:
        """
        Check if the user is part of the course team (instructor or staff).
        """
        user = self.get_current_user()
        is_course_staff = user.opt_attrs.get("edx-platform.user_is_staff")
        is_instructor = user.opt_attrs.get(ATTR_KEY_USER_ROLE) == "instructor"
        return is_course_staff or is_instructor

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
    def parse_datetime(date: datetime | str, time: str) -> datetime:
        """
        Parse a datetime object from a date and time string.

        Args:
            date (datetime | str): The date object or the date string in the format MM/DD/YYYY.
            time (str): The time string in the format HH:MM.

        Returns:
            datetime: The datetime object.
        """
        if isinstance(date, str):
            date = datetime.strptime(date, "%m/%d/%Y")

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
        user = self.get_current_user()
        self.late_submissions.append(
            {
                "anonymous_user_id": user.opt_attrs[ATTR_ANONYMOUS_USER_ID],
                "username": user.opt_attrs[ATTR_USER_USERNAME],
                "email": user.emails[0] if user.emails else "",
                "datetime": timezone.now().isoformat(),
            }
        )
        return {
            "success": True,
        }

    @XBlock.json_handler
    def download_csv(self, data: dict, suffix: str = "") -> dict:  # pylint: disable=unused-argument
        """
        Download a CSV file with all late submissions data.

        Args:
            data (dict): The data received from the client.
            suffix (str, optional): The suffix of the handler.

        Returns:
            dict: The response to the client.
        """
        temporary_file = tempfile.NamedTemporaryFile(delete=True, suffix=".csv")
        csv_name = f"{self.CATEGORY}/late_submissions_{self.scope_ids.usage_id.block_id}.csv"

        with open(temporary_file.name, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["anonymous_user_id", "username", "email", "datetime"])
            for submission in self.late_submissions:
                writer.writerow(submission.values())

        default_storage.save(csv_name, temporary_file)

        return {
            "success": True,
            "download_url": default_storage.url(csv_name),
        }

    @staticmethod
    def validate_time_format(time: str) -> None:
        """
        Validate the time format.

        Args:
            time (str): The time string to validate.

        Raises:
            JsonHandlerError: If the time format is invalid.
        """
        if not re.match(TIME_PATTERN, time):
            raise JsonHandlerError(400, _("Invalid time format. The valid format is HH:MM."))

    def validate_datetime_fields(self, data: dict) -> None:
        """
        Validate the datetime fields.

        Args:
            data (dict): The data received from the client.

        Raises:
            JsonHandlerError: If the time format is invalid.
            JsonHandlerError: If the due date is after the late due date.
        """
        # pylint: disable=unsubscriptable-object
        due_time = data["values"].get("due_time") or self.fields["due_time"].default
        late_due_time = data["values"].get("late_due_time") or self.fields["late_due_time"].default

        self.validate_time_format(due_time)
        self.validate_time_format(late_due_time)

        due_date = data["values"].get("due_date") or self.fields["due_date"].default
        late_due_date = data["values"].get("late_due_date") or self.fields["late_due_date"].default

        due_datetime = self.parse_datetime(due_date, due_time)
        late_due_datetime = self.parse_datetime(late_due_date, late_due_time)

        if due_datetime > late_due_datetime:
            raise JsonHandlerError(400, _("The due date must be before the late due date."))

    @XBlock.json_handler
    def submit_studio_edits(self, data: dict, suffix: str = ""):  # pragma: no cover
        """
        AJAX handler for studio_view() Save button.
        """
        self.validate_datetime_fields(data)

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
