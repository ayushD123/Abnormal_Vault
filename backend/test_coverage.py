# backend/test_coverage.py
#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
import coverage

def run_tests_with_coverage():
    """Run tests with coverage reporting"""
    # Start coverage
    cov = coverage.Coverage(source=['files'])
    cov.start()
    
    # Run tests
    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    failures = test_runner.run_tests(['files'])
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    # Print coverage report
    print("\n\nCoverage Report:\n")
    cov.report()
    
    # Generate HTML report
    cov.html_report(directory='coverage_html')
    print("\nHTML coverage report generated in 'coverage_html' directory\n")
    
    sys.exit(bool(failures))

if __name__ == '__main__':
    run_tests_with_coverage()

