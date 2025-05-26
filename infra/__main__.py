# DigitalOcean entry-point for Orchestra AI
# --------------------------------------
# The stack definition now lives in `do_superagi_stack.py`.
# This thin shim simply imports that module so Pulumi picks up
# the resources.

from importlib import import_module

# Importing executes resource declarations immediately.
import_module("infra.do_superagi_stack")
