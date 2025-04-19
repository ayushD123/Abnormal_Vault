# backend/Makefile
.PHONY: test coverage lint clean

# Run all tests
test:
	python manage.py test files

# Run tests with coverage
coverage:
	coverage run --source='.' manage.py test files
	coverage report
	coverage html

# Run tests with detailed output
test-verbose:
	python manage.py test files -v 2

# Run specific test file
test-models:
	python manage.py test files.tests.FileModelTests

test-api:
	python manage.py test files.tests.FileAPITests

test-integration:
	python manage.py test files.test_integration

# Run linter (requires flake8 installation)
lint:
	flake8 files --exclude migrations

# Clean up test artifacts
clean:
	rm -rf .coverage coverage_html test_media
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name 'db.sqlite3' -delete

# Install test dependencies
install-test:
	pip install -r requirements-test.txt

# Run all quality checks
check: lint test coverage