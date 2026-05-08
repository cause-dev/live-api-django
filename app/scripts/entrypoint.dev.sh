#!/bin/bash
set -e

echo "🚀 Starting Django API Development Environment..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run migrations with error handling
run_migrations() {
    echo "📊 Running database migrations..."
    if uv run python manage.py migrate --verbosity=1; then
        echo "✅ Migrations completed successfully"
    else
        echo "❌ Migration failed"
        exit 1
    fi
}

# Function to create superuser if it doesn't exist
create_superuser() {
    echo "👤 Setting up superuser..."
    
    uv run python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='root').exists():
    User.objects.create_superuser('root', 'root@example.com', 'root')
    print('✅ Superuser created: root/root')
else:
    print('✅ Superuser already exists')
EOF
}

# Function to show useful information
show_info() {
    echo ""
    echo "🎯 Development Server Information:"
    echo "   📍 API URL: http://localhost:8000/api/"
    echo "   📊 Admin Panel: http://localhost:8000/admin/"
    echo "   📚 API Docs: http://localhost:8000/api/docs/"
    echo "   👤 Superuser: root/root"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   • Create new app: uv run python manage.py startapp <appname>"
    echo "   • Run tests: uv run python manage.py test"
    echo "   • Collect static: uv run python manage.py collectstatic"
    echo "   • Create migrations: uv run python manage.py makemigrations"
    echo ""
}

# Main execution
main() {
    # Check if uv is installed
    if ! command_exists uv; then
        echo "❌ 'uv' command not found. Please install uv first."
        exit 1
    fi

    # Check if Django project is properly configured
    if [ ! -f "manage.py" ]; then
        echo "❌ manage.py not found. Please run from the project root."
        exit 1
    fi

    # Run migrations
    run_migrations

    # Create superuser (optional - only if in development)
    if [ "${CREATE_SUPERUSER:-true}" = "true" ]; then
        create_superuser
    fi

    # Show useful information
    show_info

    # Start the development server
    echo "🌟 Starting Django development server..."
    echo "   Server will be available at: http://localhost:8000"
    echo "   Press Ctrl+C to stop the server"
    echo ""
    
    exec uv run python manage.py runserver 0.0.0.0:8000
}

# Execute main function
main "$@"