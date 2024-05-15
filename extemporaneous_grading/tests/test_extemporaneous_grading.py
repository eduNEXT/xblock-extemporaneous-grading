"""
Tests for XBlockExtemporaneousGrading
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from unittest.mock import Mock

from ddt import data, ddt, unpack
from django.test import TestCase
from xblock.exceptions import JsonHandlerError
from xblock.fields import ScopeIds
from xblock.test.toy_runtime import ToyRuntime

from extemporaneous_grading import XBlockExtemporaneousGrading


@ddt
class TestXBlockExtemporaneousGrading(TestCase):
    """Tests for XBlockExtemporaneousGrading"""

    def setUp(self) -> None:
        """Set up the test suite."""
        self.runtime = ToyRuntime()
        self.content = "XBlockExtemporaneousGrading Child Content"
        self.child_block = Mock(
            render=Mock(
                return_value=Mock(
                    content=self.content,
                    resources=[],
                ),
            ),
        )
        self.block = XBlockExtemporaneousGrading(
            runtime=self.runtime,
            field_data={},
            scope_ids=ScopeIds("1", "2", "3", "4"),
        )
        self.current_datetime = datetime.now()
        self.block.is_late_submission = False
        self.block.due_date = self.current_datetime + timedelta(days=1)
        self.block.due_time = "00:00"
        self.block.late_due_date = self.current_datetime + timedelta(days=2)
        self.block.late_due_time = "00:00"
        self.block.due_date_explanation_text = "Due date explanation text"
        self.block.late_due_date_explanation_text = "Late due date explanation text"
        self.request = Mock(
            body=json.dumps({}).encode("utf-8"),
            method="POST",
            status_code_success=HTTPStatus.OK,
        )

    def test_student_view_without_children(self):
        """Render the student view without children.

        Expected result: an empty div.
        """
        self.block.children = []

        fragment = self.block.student_view({})

        self.assertNotIn(self.content, fragment.content)

    def test_student_view_with_children(self):
        """Render the student view with children.

        Expected result: a div with the children content.
        """
        self.block.children = ["child1"]
        self.runtime.get_block = Mock(return_value=self.child_block)

        fragment = self.block.student_view({})

        self.assertIn(self.content, fragment.content)

    def test_student_view_with_due_datetime(self):
        """Render the student view when the due date is passed.

        Expected result: The due datetime template.
        """
        self.block.due_date -= timedelta(days=2)

        fragment = self.block.student_view({})

        self.assertIn(self.block.due_date_explanation_text, fragment.content)
        self.assertNotIn(self.content, fragment.content)

    def test_student_view_with_late_due_datetime(self):
        """Render the student view when the late due date is passed.

        Expected result: The late due datetime template.
        """
        self.block.late_due_date -= timedelta(days=2)

        fragment = self.block.student_view({})

        self.assertIn(self.block.late_due_date_explanation_text, fragment.content)
        self.assertNotIn(self.content, fragment.content)

    def test_author_view_root(self):
        """Render the author view with the root block.

        Expected result: a div with the children content.
        """
        self.block.location = "root"
        self.block.children = ["child1"]
        self.runtime.get_block = Mock(return_value=self.child_block)
        self.runtime.service = Mock(
            return_value=Mock(
                render_template=Mock(
                    return_value=f'<div class="content_restrictions_block"> {self.content} </div>',
                ),
            ),
        )

        fragment = self.block.author_view({"root_xblock": self.block})

        self.assertEqual(
            fragment.content.replace("\n", "").replace(" ", ""),
            f'<divclass="content_restrictions_block">{self.content.replace(" ", "")}</div>',
        )

    def test_author_view(self):
        """Render the author view without the root block.

        Expected result: an empty div.
        """
        fragment = self.block.author_view({})

        self.assertEqual(fragment.content.replace("\n", "").replace(" ", ""), "")

    @data(
        ({"due_date": 1, "late_due_date": 2, "is_late_submission": False}, "children"),
        ({"due_date": -1, "late_due_date": 1, "is_late_submission": False}, "due_datetime"),
        ({"due_date": -2, "late_due_date": -1, "is_late_submission": False}, "late_due_datetime"),
        ({"due_date": -1, "late_due_date": 1, "is_late_submission": True}, "children"),
    )
    @unpack
    def test_get_template_with_ddt(self, case_data: dict, expected_result: str):
        """
        Test `get_template` method.

        Expected result: the correct template name.
        """
        self.block.late_due_date = self.current_datetime + timedelta(days=case_data["late_due_date"])
        self.block.due_date = self.current_datetime + timedelta(days=case_data["due_date"])
        self.block.is_late_submission = case_data["is_late_submission"]

        result = self.block.get_template()

        self.assertEqual(result, expected_result)

    @data(
        (
            datetime.now(),
            "12:00",
            datetime.now().replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc),
        ),
        (
            datetime.now(),
            "00:00",
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc),
        ),
    )
    @unpack
    def test_parse_datetime(self, date: datetime, time: str, expected_datetime: datetime):
        """
        Test `parse_datetime` method.

        Expected result: the correct datetime.
        """
        self.assertEqual(self.block.parse_datetime(date, time), expected_datetime)

    @data(
        ("12:00", None),
        ("00:00", None),
        ("24:00", "Invalid time format. The valid format is HH:MM."),
        ("12:60", "Invalid time format. The valid format is HH:MM."),
    )
    @unpack
    def test_validate_time(self, time: str, expected_exception: str | None):
        """
        Test `validate_time` method.

        Expected result: the correct exception.
        """
        if expected_exception is None:
            self.block.validate_time(time)
        else:
            with self.assertRaises(JsonHandlerError) as context:
                self.block.validate_time(time)
            self.assertEqual(str(context.exception.message), expected_exception)

    def test_late_submission(self):
        """
        Test `late_submission` handler.

        Expected result: The field `is_late_submission` is True and the response is a success.
        """
        response = self.block.late_submission(self.request)

        self.assertEqual(self.block.is_late_submission, True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json, {"success": True})
