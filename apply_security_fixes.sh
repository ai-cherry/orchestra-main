#!/bin/bash
# Apply security fixes from the SECURITY_FIX_PLAN.md

echo "Applying security fixes to vulnerable dependencies..."

# Update dependencies in ./shared
if [ -f "./shared/requirements.txt" ]; then
  echo "Updating ./shared/requirements.txt"
  sed -i 's/requests[=><].*/requests==2.31.0/g' ./shared/requirements.txt
  sed -i 's/pytest[=><].*/pytest==7.3.1/g' ./shared/requirements.txt
fi

# Update dependencies in ./wif_implementation
if [ -f "./wif_implementation/requirements.txt" ]; then
  echo "Updating ./wif_implementation/requirements.txt"
  sed -i 's/pyyaml[=><].*/pyyaml==6.0.1/g' ./wif_implementation/requirements.txt
fi

# Update dependencies in ./secret-management/python
if [ -f "./secret-management/python/requirements.txt" ]; then
  echo "Updating ./secret-management/python/requirements.txt"
  sed -i 's/requests[=><].*/requests==2.31.0/g' ./secret-management/python/requirements.txt
fi

# Update dependencies in ./secret-management/terraform/modules/secret-rotation/function
if [ -f "./secret-management/terraform/modules/secret-rotation/function/requirements.txt" ]; then
  echo "Updating ./secret-management/terraform/modules/secret-rotation/function/requirements.txt"
  sed -i 's/requests[=><].*/requests==2.31.0/g' ./secret-management/terraform/modules/secret-rotation/function/requirements.txt
fi

# Update dependencies in ./packages/shared
if [ -f "./packages/shared/requirements.txt" ]; then
  echo "Updating ./packages/shared/requirements.txt"
  sed -i 's/requests[=><].*/requests==2.31.0/g' ./packages/shared/requirements.txt
fi

# Update dependencies in ./packages/agents
if [ -f "./packages/agents/requirements.txt" ]; then
  echo "Updating ./packages/agents/requirements.txt"
  sed -i 's/requests[=><].*/requests==2.31.0/g' ./packages/agents/requirements.txt
fi

# Update all google-cloud-sdk dependencies (if they exist)
find . -name "requirements.txt" -path "*google-cloud-sdk*" | while read file; do
  echo "Checking $file"
  
  # Update requests
  if grep -q "requests" "$file"; then
    echo "  Updating requests in $file"
    sed -i 's/requests[=><].*/requests==2.31.0/g' "$file"
  fi
  
  # Update pyyaml
  if grep -q "pyyaml" "$file"; then
    echo "  Updating pyyaml in $file"
    sed -i 's/pyyaml[=><].*/pyyaml==6.0.1/g' "$file"
  fi
  
  # Update django
  if grep -q "django" "$file"; then
    echo "  Updating django in $file"
    sed -i 's/django[=><].*/django==4.2.5/g' "$file"
  fi
  
  # Update cryptography
  if grep -q "cryptography" "$file"; then
    echo "  Updating cryptography in $file"
    sed -i 's/cryptography[=><].*/cryptography==41.0.4/g' "$file"
  fi
  
  # Update pytest
  if grep -q "pytest" "$file"; then
    echo "  Updating pytest in $file"
    sed -i 's/pytest[=><].*/pytest==7.3.1/g' "$file"
  fi
  
  # Update flask
  if grep -q "flask" "$file"; then
    echo "  Updating flask in $file"
    sed -i 's/flask[=><].*/flask==2.3.3/g' "$file"
  fi
done

echo "Security fixes applied successfully!"
echo "Remember to run 'pip install -r requirements.txt' for each updated file to install the fixed versions."
