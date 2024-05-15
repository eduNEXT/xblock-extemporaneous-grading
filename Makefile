.DEFAULT_GOAL := help

.PHONY: dev.clean dev.build dev.run upgrade help requirements
.PHONY: extract_translations compile_translations symlink_translations
.PHONY: detect_changed_source_translations dummy_translations build_dummy_translations
.PHONY: validate_translations pull_translations push_translations install_transifex_clients
.PHONY: test format coverage quality diff_cover clean validate

BROWSER := python -m webbrowser file://$(CURDIR)
REPO_NAME := xblock-extemporaneous-grading
PACKAGE_NAME := extemporaneous_grading
JS_TARGET := $(PACKAGE_NAME)/public/js/translations
TRANSLATIONS_DIR := $(PACKAGE_NAME)/translations
LOCALES := en es_ES
SOURCES=./setup.py ./$(PACKAGE_NAME)
BLACK_OPTS = --exclude ${SOURCES} --line-length 120

help:
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

# Define PIP_COMPILE_OPTS=-v to get more information during make upgrade.
PIP_COMPILE = pip-compile --upgrade $(PIP_COMPILE_OPTS)

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -qr requirements/pip-tools.txt
	# Make sure to compile files after any other files they include!
	$(PIP_COMPILE) --allow-unsafe -o requirements/pip.txt requirements/pip.in
	$(PIP_COMPILE) -o requirements/pip-tools.txt requirements/pip-tools.in
	pip install -qr requirements/pip.txt
	pip install -qr requirements/pip-tools.txt
	$(PIP_COMPILE) -o requirements/base.txt requirements/base.in
	$(PIP_COMPILE) -o requirements/test.txt requirements/test.in
	$(PIP_COMPILE) -o requirements/doc.txt requirements/doc.in
	$(PIP_COMPILE) -o requirements/quality.txt requirements/quality.in
	$(PIP_COMPILE) -o requirements/ci.txt requirements/ci.in
	$(PIP_COMPILE) -o requirements/dev.txt requirements/dev.in
	# Let tox control the Django version for tests
	sed '/^[dD]jango==/d' requirements/test.txt > requirements/test.tmp
	mv requirements/test.tmp requirements/test.txt

piptools: ## install pinned version of pip-compile and pip-sync
	pip install -r requirements/pip.txt
	pip install -r requirements/pip-tools.txt

requirements: piptools ## install development environment requirements
	pip-sync -q requirements/dev.txt requirements/private.*

dev.clean:
	-docker rm $(REPO_NAME)-dev
	-docker rmi $(REPO_NAME)-dev

dev.build:
	docker build -t $(REPO_NAME)-dev $(CURDIR)

dev.run: dev.clean dev.build ## Clean, build and run test image
	docker run -p 8000:8000 -v $(CURDIR):/usr/local/src/$(REPO_NAME) --name $(REPO_NAME)-dev $(REPO_NAME)-dev

## Useful commands

format: ## Format code automatically
	black $(BLACK_OPTS)
	isort $(SOURCES)

clean: ## Remove generated byte code, coverage reports, and build artifacts
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	coverage erase
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

test: clean ## Run the tests
	mkdir -p var
	rm -rf .coverage
	python -m coverage run --rcfile=.coveragerc -m pytest

coverage: clean ## Generate and view HTML coverage report
	pytest --cov-report html
	$(BROWSER)/htmlcov/index.html

quality: ## Check coding style with pycodestyle and pylint
	tox -e quality

diff_cover: test ## Find diff lines that need test coverage
	diff-cover coverage.xml

validate: quality test ## Run tests and quality checks

## Localization targets

symlink_translations:
	if [ ! -d "$(TRANSLATIONS_DIR)" ]; then ln -s conf/locale/ $(TRANSLATIONS_DIR); fi

rename_po_files: ## Rename .po files to django.po
	for locale in $(LOCALES); do \
        mv $(PACKAGE_NAME)/locale/$$locale/LC_MESSAGES/text.po $(PACKAGE_NAME)/locale/$$locale/LC_MESSAGES/django.po; \
    done

extract_translations: symlink_translations rename_po_files ## Extract strings to be translated, outputting .po files
	for locale in $(LOCALES); do \
        cd $(PACKAGE_NAME) && django-admin makemessages -l $$locale -v1 -d django --no-obsolete && cd ..; \
		mv $(PACKAGE_NAME)/locale/$$locale/LC_MESSAGES/django.po $(PACKAGE_NAME)/locale/$$locale/LC_MESSAGES/text.po; \
    done

compile_translations: symlink_translations ## Compile translation files, outputting .mo files for each supported language
	cd $(PACKAGE_NAME) && i18n_tool generate -v
	python manage.py compilejsi18n --namespace ExtemporaneousGradingI18n --output $(JS_TARGET)

detect_changed_source_translations:
	cd $(PACKAGE_NAME) && i18n_tool changed

dummy_translations: ## generate dummy translation (.po) files
	cd $(PACKAGE_NAME) && i18n_tool dummy

build_dummy_translations: dummy_translations compile_translations ## generate and compile dummy translation files

validate_translations: build_dummy_translations detect_changed_source_translations ## validate translations

pull_translations: ## pull translations from transifex
	cd $(PACKAGE_NAME) && i18n_tool transifex pull

push_translations: extract_translations ## push translations to transifex
	cd $(PACKAGE_NAME) && i18n_tool transifex push

check_translations_up_to_date: extract_translations compile_translations detect_changed_source_translations ## Extract, compile, and check if translation files are up-to-date

install_transifex_client: ## Install the Transifex client
	# Instaling client will skip CHANGELOG and LICENSE files from git changes
	# so remind the user to commit the change first before installing client.
	git diff -s --exit-code HEAD || { echo "Please commit changes first."; exit 1; }
	curl -o- https://raw.githubusercontent.com/transifex/cli/master/install.sh | bash
	git checkout -- LICENSE README.md ## overwritten by Transifex installer

selfcheck: ## check that the Makefile is well-formed
	@echo "The Makefile is well-formed."
