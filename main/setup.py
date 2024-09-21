# This script setup django
# Turn off bytecode generation
import sys
sys.dont_write_bytecode = True

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

# setup django environment
import django
django.setup()
