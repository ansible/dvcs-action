#!/usr/bin/env python
import unittest
from check_dvcs import does_string_start_with_jira
from check_dvcs import delete_previous_comment_if_needed

class TestStringStartWithJira(unittest.Testcase):

    def test_string_start_with_jira_ticket(self):
        self.assertEqual(does_string_start_with_jira("JIRA-123 This is a PR"), "JIRA-123")

    def test_string_with_no_jira_ticket(self):
        self.assertEqual(does_string_start_with_jira("NO-JIRA: Minor changes"), "NO-JIRA")

    def test_empty_string(self):
        """Test with an empty string."""
        self.assertIsNone(does_string_start_with_jira(""))

class TestDeletePreviousComment(unittest.Testcase):

    def test_delete_previous_comment(self):
        self.assertEqual(delete_previous_comment_if_needed("Deleting previous comment ... "))

    def test_fail_delete_previous_comment(self):
        self.assertEqual(delete_previous_comment_if_needed("Failed to delete previous comment"))

if __name__ == '__main__':
    unittest.main()
