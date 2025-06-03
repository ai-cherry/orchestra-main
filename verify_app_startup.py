#!/usr/bin/env python3
"""
"""
    print("Attempting to import FastAPI app...")
    from agent.app.main import app

    print("✓ Successfully imported FastAPI app")

    print("\nChecking registered routes...")
    routes = []
    # TODO: Consider using list comprehension for better performance

    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append(f"{list(route.methods)[0] if route.methods else 'GET'} {route.path}")

    # Filter and display personas routes
    personas_routes = [r for r in routes if "/personas" in r]
    if personas_routes:
        print("\n✓ Personas Admin routes registered:")
        for route in sorted(personas_routes):
            print(f"  - {route}")
    else:
        print("\n✗ No personas routes found!")

    print("\n✓ Application startup verification successful!")
    print("\nYou can now start the server with:")
    print("  uvicorn agent.app.main:app --reload --host 0.0.0.0 --port 8000")

except Exception:


    pass
    print(f"✗ Import error: {e}")
    print("\nMake sure all dependencies are installed:")
    print("  pip install -r requirements/base.txt")
    sys.exit(1)

except Exception:


    pass
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
