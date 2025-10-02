# How to Contribute

This project is [GPL-3.0 licensed](COPYING) and accepts contributions through
GitHub pull requests.

## Certificate of Origin

By contributing to this project you agree to the Developer Certificate of
Origin (DCO). This document was created by the Linux Kernel community and is a
simple statement that you, as a contributor, have the legal right to make the
contribution. See the [DCO](DCO) file for details.

## Principles

This repository adheres to the following principles:

- Open: Contribution is always welcome.
- Respectful: See the [Code of Conduct](CODE_OF_CONDUCT.md).
- Transparent and accessible: Work and collaboration should be done in public.
  See [Governance](#governance) section for details.
- Merit: Ideas and contributions are accepted according to their merit and
  alignment with the project objectives principles.

## How to contribute

We are very happy to receive contributions from the community in any form!

Please use a GitHub pull request to submit your contributions. If you have a
question or are unsure if a contribution is wanted, please join us in
[TBD](#channel-name-here) on Matrix to discuss your change or on the Ansible forum
using the TBD tag if you prefer async discussion.
Open a GitHub issue to report bugs or request features.

## Running tests

This project uses [tox](https://tox.wiki/) for testing. To run tests:

```bash
# Run all default environments (check and py311)
tox

# Run specific test environments
tox -e py311        # Run pytest with coverage
tox -e flake8       # Run flake8 linter
tox -e black        # Run black formatter
tox -e isort        # Run isort import sorter

# Run using labels
tox -m test         # Run py311 tests
tox -m check        # Run check environment
tox -m lint         # Run all linters (flake8, black, isort)
```

## Governance

The Ansible PROJECTNAME uses the following governance model:

---
- A patch SHOULD have a minimum of 2 reviews from Members before it is merged.
- Members SHOULD NOT review/merge their own patches except in exceptional
  cases.
---
- All Contributions MUST be done using the GitHub PR process.
- Any Contributor MAY submit any patches they feel are suitable for inclusion.
- Any Contributor MAY review the patches of other Contributors. 
- Any Contributor who makes correct patches, writes good reviews, who clearly
  understands the project goals, and the process SHOULD be invited to become a
  Member of the WWG.
---

(inspired by the [C4 process](https://rfc.zeromq.org/spec/42))
