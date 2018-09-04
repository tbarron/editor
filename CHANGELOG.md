# Changelog

Notable changes for this project. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/). This project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] yyyy-mm-dd (conform to Keep a Changelog, CL)
### Added
- New file CHANGELOG.md with content copied from plain text CHANGELOG.
- New sections in README.md: "Release Cycle" and "CHANGELOG.md".

### Changed
- Updated content of CHANGELOG.md to conform to "Keep a Changelog" (see
  link above).

## [2.1.0] 2018-09-04 (add insert functionality, INS)
### Added
 - Insert test with incremental checking of results
 - Functions __len__() and insert() to editor to satisfy the test
 
## [2.0.0] 2018-09-03 (backup consolidation, BC)
### Added
 - Plain text CHANGELOG
 - Documentation about issues with consolidated backup behavior
 - Implement consolidated backup functionality
 - Put constants in text.py and eliminate fixture constants

### Changed
 - Test cleanup

### Removed
 - Drop copy_on_load functionality and tests

## [1.1.2] 2018-08-27 (trailing whitespace, TWS)
### Added
 - Verify complete test coverage
 - Add test to catch trailing whitespace on last line
 
### Changed
 - Fix the trailing whitespace bug

## [1.1.1] 2018-08-26 (test cleanup, CT)
### Changed
 - Alphabetize and document tests

## [1.1.0] / 2018-08-26 / copy on load, COL
### Added
 - Define and implement copy_on_load behavior

### Changed
 - Documentation improvements

## [1.0.0] / 2017-04-19 / continuous integration, CI
### Added
 - Work on README.md
 - Set up py.test, Makefile (for clean target), test coverage, flake8 code
   quality test, .gitignore, continuous integration with Travis
