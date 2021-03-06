# Changelog

Notable changes for this project. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/). This project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each release header has the following format:

    [VERSION] / release date / title (branch, tag)

The title describes the overall update made with this release. The tag is a
short marker that begins each of the related commit messages.

## [2.3.1] / 2018-09-07 / fix build fail on Travis for python 2.x (twofix, TF)
### Changed
 - Use 'x' rather than '\_' as variable name on line 163 of \_\_init\_\_.py
   to address Travis failure: "editor/\_\_init\_\_.py:163:51: F812 list
   comprehension redefines '_' from line 161"
 - Adjusted the release header format in this file to put branch name and
   commit message tag together in parens after the title. Before, it was
   "title, tag (branch)".

## [2.3.0] / 2018-09-06 / resolve fiatjaf's pull request (fiatjaf, FJ)
### Added
 - Add build files to .gitignore
 - Add .edit() method for editing files in the default text editor

### Changed
 - Make editor.contents() into a static method
 - Accept a string for constructor argument content as well as a list of
   strings

### Removed
 - Remove unnecessary help text from python file


## [2.2.0] / 2018-09-06 / substitute limit (sublim, SL)
### Added
 - Test test_substitute_limit() to verify the functionality.
 - Argument count on method editor.sub()
 - Added entries in constant dictionary:
     - 'after'
     - 'before'
     - 'bkup'
     - 'lowa'
     - 'middle'
     - 'uppA'
 - Function comments for glob_assert() and fixture fx_chdir()

### Changed
 - Updated function editor.sub() to validate argument count and then pass
   it along to re.sub().
 - In test_insert(), make sure edited is a *copy* of K["orig_l"] rather
   than a pointer to it. We don't want to change the value of text
   dictionary entries.
 - Function comment improvements.
 - Replace literal strings with values from the constants dictionary K.
 - Improved test_version().

### Removed
 -  Removed pseudo-code and tags from function comments in tests


## [2.1.1] / 2018-09-04 / conform to Keep a Changelog (changelog, CL)
### Added
 - New file CHANGELOG.md with content copied from plain text CHANGELOG.
 - New sections in README.md: "Release Cycle" and "CHANGELOG.md".

### Changed
 - Updated content of CHANGELOG.md to conform to "Keep a Changelog" (see
   link above) albeit with a tweak to the format of release header lines
   (described in the introductory material at the top of this file).

### Removed
 - Plain text version of CHANGELOG.


## [2.1.0] / 2018-09-04 / add insert functionality (insert, INS)
### Added
 - Insert test with incremental checking of results
 - Functions \_\_len\_\_() and insert() to editor to satisfy the test


## [2.0.0] / 2018-09-03 / backup consolidation (backup, BC)
### Added
 - Plain text CHANGELOG
 - Documentation about issues with consolidated backup behavior
 - Implement consolidated backup functionality
 - Put constants in text.py and eliminate fixture constants

### Changed
 - Test cleanup

### Removed
 - Drop copy_on_load functionality and tests


## [1.1.2] / 2018-08-27 / trailing whitespace (tws, TWS)
### Added
 - Verify complete test coverage
 - Add test to catch trailing whitespace on last line

### Changed
 - Fix the trailing whitespace bug


## [1.1.1] / 2018-08-26 / test cleanup (cleanup, CT)
### Changed
 - Alphabetize and document tests


## [1.1.0] / 2018-08-26 / copy on load (copy_on_load, COL)
### Added
 - Define and implement copy_on_load behavior

### Changed
 - Documentation improvements


## [1.0.0] / 2017-04-19 / continuous integration, CI
### Added
 - Work on README.md
 - Set up py.test, Makefile (for clean target), test coverage, flake8 code
   quality test, .gitignore, continuous integration with Travis
