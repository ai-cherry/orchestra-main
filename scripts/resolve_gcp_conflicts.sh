#!/bin/bash
# Resolve Poetry dependency conflicts for GCP packages
poetry add google-cloud-secretmanager==2.16.0 \
            google-auth==2.22.0 \
            google-api-python-client==2.108.0 \
            --group gcp