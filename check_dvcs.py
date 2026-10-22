#!/usr/bin/env python

import argparse
import json
import re
from os import getenv
from sys import argv, exit
from typing import Optional

import requests

_AAP_RE = "AAP-[0-9]+"
http_headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


class CommandException(Exception):
    pass


def does_string_contain_jira(string_to_match: str, allow_no_jira: bool) -> Optional[str]:
    if allow_no_jira and "NO_JIRA" in string_to_match:
        print(f"NO_JIRA found in {string_to_match}")
        return "NO_JIRA"
    pr_title_re = re.compile(f"({_AAP_RE})")
    matches = pr_title_re.search(string_to_match)
    print(f"Checking if {string_to_match} contains our RE ... ", end="")
    if not matches:
        print("Failed!")
        return None
    else:
        print("Good!")
    return matches.groups()[0]


def get_commit_jira_numbers(commit_url: str, allow_no_jira: bool) -> list[str]:
    print(f"Getting commits ({commit_url}) ... ", end="")
    commits = requests.get(commit_url, headers=http_headers)
    print(commits.status_code)
    if commits.status_code != 200:
        raise CommandException("Failed to get commits!")
    possible_jiras = []
    for commit in commits.json():
        # TODO: How to check if this is a merge commit or a regular comment?
        jira_key = does_string_contain_jira(commit["commit"]["message"], allow_no_jira)
        if jira_key:
            possible_jiras.append(jira_key)
        else:
            print("None detected")

    return possible_jiras


def does_pr_reference_ticket(
    pr_title_jira: Optional[str],
    possible_commit_jiras: list[str],
    source_branch_jira: Optional[str],
) -> bool:
    """
    Does the PR reference at least one JIRA ticket?

    Although it seems to be sparsely documented, the JIRA "DVCS" plugin expects
    *at least one* of the following:

    - A ticket key (AAP-nnnnnn) in the PR title
    - A ticket key in the branch name
    - A ticket key in a commit message in the set of commits in the PR

    It seems there is no notion of conflict handling: If multiple different
    ticket keys are found, it will simply attach the PR to all referenced
    tickets.
    """

    print("")
    print("Checking validity based on the following:")
    print(f"JIRA from title: {pr_title_jira}")
    print(f"JIRA from source branch: {source_branch_jira}")
    print(f"JIRAS from commits: {', '.join(possible_commit_jiras)}")
    print("")

    # PR title or source branch is truthy means we found a regex match on the
    # ticket key
    # A non-empty possible_commit_jiras means at least one commit matched
    return any([pr_title_jira, source_branch_jira, possible_commit_jiras])


def main(args=[]):
    parser = argparse.ArgumentParser(
        description="A tool for checking if a PR matches the DVCS rules.\n\n"
        "This program requires the body of the pull request as an environment variable PULL_REQUEST.\n"
        "To generate this you can do a curl command line: export PULL_REQUEST=$(curl https://api.github.com/repos/ansible/dvcs-action/pulls/8)",
        add_help=True,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('--allow-no-jira', help='Allow PRs which use NO_JIRA to pass (true or false)')
    args = parser.parse_args(args)

    allow_no_jira = args.allow_no_jira == "true"
    print(f"allow_no_jira: {allow_no_jira}")

    # Get and validate the data from the environment (the GitHub action should pass this in)
    try:
        pull_request = json.loads(getenv("PULL_REQUEST", {}))
    except json.JSONDecodeError as jde:
        print(f"Failed to load json from string: {jde}")
        exit(255)

    print("Running DVCS v6")

    pull_urls = pull_request.get("_links", {})

    # Check the PR title
    pr_title_jira = does_string_contain_jira(pull_request.get("title"), allow_no_jira)

    # Check the PR commits
    try:
        possible_commit_jiras = get_commit_jira_numbers(pull_urls.get("commits", {}).get("href"), allow_no_jira)
    except CommandException as ce:
        # Don't fail out in this case, if we already found a JIRA key, we might
        # not even care about commits here.
        print(f"Failed to get commits: {ce}")
        possible_commit_jiras = []

    # Check the PR source branch
    source_branch_jira = does_string_contain_jira(pull_request.get("head", {}).get("ref", ""), allow_no_jira)

    pr_is_valid = does_pr_reference_ticket(pr_title_jira, possible_commit_jiras, source_branch_jira)

    exit(0 if pr_is_valid else 255)


if __name__ == '__main__':
    main(argv[1:])
