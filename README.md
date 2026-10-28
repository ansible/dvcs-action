# Usage

This action validates the following in a PR:
1. A commit in the pull request has the JIRA issue key in the commit message. Note, that the commit cannot be a merge commit.
1. The JIRA issue key is at the beginning of the pull request title.
1. The source branch name also includes the JIRA issue key at the beginning of the branch name.

To use this action create a github workflow like:
```yaml
on:
  pull_request_target:
    type: opened, synchronize, reopened, edited
jobs:
  dvcs_pr_checker:
    permissions:
      contents: read
      pull-requests: read
    runs-on: ubuntu-latest
    name: Check the PR for DVCS integration
    steps:
      - id: foo
        uses: ansible/dvcs-action@v6
```

This action is read-only. It validates the pull request without modifying it, so the calling workflow only needs read permissions.


# Testing locally

In order to test locally we need to set an environment variable called `PULL_REQUEST`. 
This can be accomplished by doing a curl command (change <repo> and <pull number> to match what you want to test):
```
export GITHUB_TOKEN=<your github token>
export PULL_REQUEST=$(curl --header "Authorization: Bearer ${GITHUB_TOKEN}" https://api.github.com/repos/ansible/<repo>/pulls/<pull number>)
```

After that is set you can run the Python script:
```
./check_dvcs.py
```

The action uses the workflow's built-in `GITHUB_TOKEN` automatically. When testing locally, set `GITHUB_TOKEN` to a token with read access to pull requests and repository contents.
