"""Extemporaneous Grading XBlock"""

from __future__ import annotations

import logging
from typing import Optional

import pkg_resources
from django.utils import translation
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.utils.resources import ResourceLoader
from xblock.utils.studio_editable import StudioContainerWithNestedXBlocksMixin, StudioEditableXBlockMixin
from xblock.utils.studio_editable import loader as studio_loader

from extemporaneous_grading.utils import _

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


@XBlock.needs("i18n")
class XBlockExtemporaneousGrading(StudioContainerWithNestedXBlocksMixin, StudioEditableXBlockMixin, XBlock):
    """
    Extemporaneous Grading XBlock which provides a way to display content to students
    according to dates set as due date and late submission date.
    """

    CATEGORY = "extemporaneous_grading"

    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        scope=Scope.settings,
        default=_("Extemporaneous Grading"),
    )

    editable_fields = [
        "display_name",
    ]

    def resource_string(self, path) -> str:
        """Handy helper for getting resources from our kit."""
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

    def studio_view(self, context: dict) -> Fragment:
        """
        Render a form for editing this XBlock.
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

    def student_view(self, context=None) -> Fragment:
        """
        Create primary view of the XBlockExtemporaneousGrading, shown to students when viewing courses.
        """
        fragment = Fragment()
        children_contents = []

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            child_fragment = self._render_child_fragment(child, context, "student_view")
            fragment.add_fragment_resources(child_fragment)
            children_contents.append(child_fragment.content)

        render_context = {
            "block": self,
            "children_contents": children_contents,
            **context,
        }

        fragment.add_content(self.render_template("static/html/extemporaneous_grading.html", render_context))
        fragment.add_css(self.resource_string("static/css/extemporaneous_grading.css"))
        fragment.add_javascript(self.resource_string("static/js/src/extemporaneous_grading.js"))
        fragment.initialize_js("XBlockExtemporaneousGrading")

        return fragment

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
