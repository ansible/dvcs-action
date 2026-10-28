from os import environ
from unittest import mock

import pytest
import requests_mock
from requests.exceptions import MissingSchema  # type: ignore

import check_dvcs


class TestDoesStringContainJira:

    @pytest.mark.parametrize(
        "input,allow_no_jira,expected_return",
        [
            ("testing", True, None),
            ("testing", False, None),
            ('AAP-2222 other stuff', True, 'AAP-2222'),
            ('AAP-2222 other stuff', False, 'AAP-2222'),
            ('other stuff AAP-3333', True, 'AAP-3333'),
            ('other stuff AAP-3333', False, 'AAP-3333'),
            ('other stuff AAP-4444 jira in the middle', True, 'AAP-4444'),
            ('other stuff AAP-4444 jira in the middle', False, 'AAP-4444'),
            ('a-hoopy-AAP-9999-frood', True, 'AAP-9999'),
            ('a-hoopy-AAP-9999-frood', False, 'AAP-9999'),
            ('a-hoopy-aap-9999-frood', True, None),
            ('a-hoopy-aap-9999-frood', False, None),
            ('aap-9999 hey', True, None),
            ('aap-9999 hey', False, None),
            ('Aap-9999 hey', True, None),
            ('Aap-9999 hey', False, None),
            ('AAP-9999 hey', True, 'AAP-9999'),
            ('AAP-9999 hey', False, 'AAP-9999'),
            ('NO_JIRA hey', True, 'NO_JIRA'),
            ('NO_JIRA hey', False, None),
            ('[NO_JIRA] hey', True, 'NO_JIRA'),
            ('[NO_JIRA] hey', False, None),
        ],
    )
    def test_does_string_contain_jira_function(self, input, allow_no_jira, expected_return):
        result = check_dvcs.does_string_contain_jira(input, allow_no_jira)
        assert result == expected_return


class TestGitCommitJiraNumbers:

    def test_uses_github_token(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        with requests_mock.Mocker() as m:
            m.register_uri("GET", "https://example.com", status_code=200, json=[])
            check_dvcs.get_commit_jira_numbers("https://example.com", True)
            assert m.last_request.headers["Authorization"] == "Bearer test-token"

    def test_invalid_url(self):
        with pytest.raises(MissingSchema):
            check_dvcs.get_commit_jira_numbers("www.example.com", True)

    def test_invalid_status_code(self):
        with pytest.raises(check_dvcs.CommandException):
            with requests_mock.Mocker() as m:
                m.register_uri('GET', 'https://example.com', status_code=404)
                check_dvcs.get_commit_jira_numbers("https://example.com", True)

    @pytest.mark.parametrize(
        "json,allow_no_jira,expected_result",
        [
            ([], True, []),
            ([], False, []),
            (
                [
                    {"commit": {"message": "This is wrong"}},
                ],
                True,
                [],
            ),
            (
                [
                    {"commit": {"message": "This is wrong"}},
                ],
                False,
                [],
            ),
            (
                [
                    {"commit": {"message": "AAP-1234 This has the jira marker"}},
                ],
                True,
                ['AAP-1234'],
            ),
            (
                [
                    {"commit": {"message": "AAP-1234 This has the jira marker"}},
                ],
                False,
                ['AAP-1234'],
            ),
            (
                [
                    {"commit": {"message": "NO_JIRA This has the no_jira marker"}},
                ],
                False,
                [],
            ),
            (
                [
                    {"commit": {"message": "NO_JIRA This has the no_jira marker"}},
                ],
                True,
                ['NO_JIRA'],
            ),
            (
                [
                    {"commit": {"message": "[NO_JIRA] This has the no_jira marker in brackets"}},
                ],
                False,
                [],
            ),
            (
                [
                    {"commit": {"message": "[NO_JIRA] This has the no_jira marker in brackets"}},
                ],
                True,
                ['NO_JIRA'],
            ),
            (
                [
                    {"commit": {"message": "ABC-0909 This has wrong jira marker format"}},
                ],
                True,
                [],
            ),
        ],
    )
    def test_json_return(self, json, allow_no_jira, expected_result):
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'https://example.com', status_code=200, json=json)
            response = check_dvcs.get_commit_jira_numbers("https://example.com", allow_no_jira)
            assert response == expected_result


class TestMain:

    @pytest.fixture(autouse=True)
    def github_token(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    @pytest.mark.parametrize(
        "json",
        [
            "{'bad': 'json',}",
            "",
        ],
    )
    def test_invalid_pull_input(self, capsys, json):
        environ['PULL_REQUEST'] = json
        with pytest.raises(SystemExit) as e:
            check_dvcs.main()
        output = capsys.readouterr()
        assert "Failed to load json from string" in output.out
        assert e.value.code == 255

    def test_fail_to_get_commits(self, capsys):
        """
        If we fail to get commits, don't bail out - we might have found a JIRA
        key in the PR title or branch name that we can use instead. But still
        report the failure to stdout.
        """
        environ['PULL_REQUEST'] = '{"title": "junk"}'
        with mock.patch('check_dvcs.get_commit_jira_numbers', side_effect=check_dvcs.CommandException("Failing on purpose")):
            try:
                check_dvcs.main()
            except SystemExit:
                pass  # We get to the end... This isn't what we're testing for.
            output = capsys.readouterr()
            assert "Failed to get commits" in output.out

    def test_failed_check(self):
        environ['PULL_REQUEST'] = '{"title": "junk"}'
        with mock.patch('check_dvcs.get_commit_jira_numbers', return_value=[]):
            with pytest.raises(SystemExit) as e:
                check_dvcs.main()
            assert e.value.code == 255

    def test_missing_github_token(self, monkeypatch, capsys):
        monkeypatch.delenv("GITHUB_TOKEN")
        environ['PULL_REQUEST'] = '{"title": "junk"}'

        with pytest.raises(SystemExit) as e:
            check_dvcs.main()

        output = capsys.readouterr()
        assert "Did not get a GitHub token" in output.out
        assert e.value.code == 255


class TestDoesPrReferenceTicket:

    @pytest.mark.parametrize(
        "pr_title_jira, possible_commit_jiras, source_branch_jira, expected_result",
        [
            (  # Key in PR title, multiple in commits, key in branch name
                'AAP-1234',
                ['AAP-1235', 'AAP-1235'],
                'AAP-1234',
                True,
            ),
            (  # Source branch does not match jira PR
                "AAP-56788",
                ['AAP-1234', 'AAP-1234'],
                'AAP-1234',
                True,
            ),
            (  # Key in PR title and branch name, not in commit
                "AAP-1234",
                [],
                'AAP-1235',
                True,
            ),
            (  # Key only in PR title
                'AAP-9009',
                [],
                None,
                True,
            ),
            (  # Key only in commit
                None,
                ['AAP-93993'],
                None,
                True,
            ),
            (  # Key only in PR title
                None,
                [],
                'AAP-77888',
                True,
            ),
            (  # No key in PR title, branch name, or commit.
                None,
                [],
                None,
                False,
            ),
        ],
        ids=[
            "Key in PR title, multiple in commits, key in branch name",
            "Source branch does not match jira PR",
            "Key in PR title and branch name, not in commit",
            "Key only in PR title",
            "Key only in commit",
            "Key only in PR title",
            "No key in PR title, branch name, or commit.",
        ],
    )
    def test_does_pr_reference_ticket(self, pr_title_jira, possible_commit_jiras, source_branch_jira, expected_result):
        result = check_dvcs.does_pr_reference_ticket(pr_title_jira, possible_commit_jiras, source_branch_jira)
        assert result == expected_result
