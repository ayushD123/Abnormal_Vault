# backend/runtests.py
#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def run_tests():
    """Run all backend tests with proper configuration"""
    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    failures = test_runner.run_tests(['files'])
    sys.exit(bool(failures))

if __name__ == '__main__':
    run_tests()

# backend/files/test_settings.py
# Optional test settings to override main settings during tests
import os
from core.settings import *

# Use an in-memory SQLite database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use a temporary directory for media files during tests
MEDIA_ROOT = os.path.join(BASE_DIR, 'test_media')

# Disable password validation for test users
AUTH_PASSWORD_VALIDATORS = []

# Speed up tests by using simple password hasher
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]