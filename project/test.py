from website import create_app

app = create_app()

print("=== Testing Flask App ===")

# Test if app created successfully
if app:
    print("✅ Flask app created successfully")
else:
    print("❌ Failed to create Flask app")
    exit()

# Test routes
with app.test_client() as client:
    print("\n=== Testing Routes ===")
    
    routes_to_test = ['/', '/login', '/flappy-bird', '/games']
    
    for route in routes_to_test:
        try:
            response = client.get(route)
            print(f"{route}: {response.status_code}")
        except Exception as e:
            print(f"{route}: ERROR - {e}")

print("\n=== Blueprint Check ===")
print("Registered blueprints:", list(app.blueprints.keys()))

print("\n=== Route Map ===")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}")