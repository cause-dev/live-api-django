#!/bin/bash
set -e

echo "🚀 Starting Django API Production Environment..."

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

# Function to collect static files
collect_static() {
    echo "📦 Collecting static files..."
    if uv run python manage.py collectstatic --noinput --verbosity=1; then
        echo "✅ Static files collected successfully"
    else
        echo "❌ Static file collection failed"
        exit 1
    fi
}

# Function to validate production settings
validate_production() {
    echo "🔍 Validating production settings..."
    
    # Check critical production settings
    if [ "$DEBUG" = "True" ]; then
        echo "⚠️  WARNING: DEBUG is True in production!"
    fi
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here" ]; then
        echo "❌ ERROR: SECRET_KEY is not properly set for production"
        exit 1
    fi
    
    if [ -z "$ALLOWED_HOSTS" ] || [ "$ALLOWED_HOSTS" = "[]" ]; then
        echo "❌ ERROR: ALLOWED_HOSTS is not properly set for production"
        exit 1
    fi
    
    echo "✅ Production settings validated"
}

# Function to check database connection
check_database() {
    echo "🔗 Checking database connection..."
    if uv run python manage.py dbshell --command="SELECT 1;" >/dev/null 2>&1; then
        echo "✅ Database connection successful"
    else
        echo "❌ Database connection failed"
        exit 1
    fi
}

# Function to show production info
show_production_info() {
    echo ""
    echo "🎯 Production Server Information:"
    echo "   📍 API URL: ${SITE_URL:-https://yourdomain.com}/api/"
    echo "   📊 Admin Panel: ${SITE_URL:-https://yourdomain.com}/admin/"
    echo "   📚 API Docs: ${SITE_URL:-https://yourdomain.com}/api/docs/"
    echo ""
    echo "🔧 Production Commands:"
    echo "   • Check logs: docker logs <container_name>"
    echo "   • Run management commands: docker exec <container_name> uv run python manage.py <command>"
    echo ""
}

# Function to handle graceful shutdown
graceful_shutdown() {
    echo "📴 Received shutdown signal, gracefully stopping..."
    # Here you can add cleanup tasks if needed
    exit 0
}

# Set up signal handlers
trap graceful_shutdown SIGTERM SIGINT

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

    # Validate production settings
    validate_production

    # Check database connection
    check_database

    # Run migrations
    run_migrations

    # Collect static files (only for admin)
    collect_static

    # Show production information
    show_production_info

    # Start the production server
    echo "🌟 Starting Gunicorn production server..."
    echo "   Server will be available at: ${SITE_URL:-https://yourdomain.com}"
    echo ""
    
    # Use Gunicorn with production settings
    exec uv run gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers ${GUNICORN_WORKERS:-3} \
        --worker-class ${GUNICORN_WORKER_CLASS:-sync} \
        --worker-connections ${GUNICORN_WORKER_CONNECTIONS:-1000} \
        --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
        --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
        --timeout ${GUNICORN_TIMEOUT:-30} \
        --keep-alive ${GUNICORN_KEEP_ALIVE:-5} \
        --access-logfile - \
        --error-logfile - \
        --log-level ${GUNICORN_LOG_LEVEL:-info}
}

# Execute main function
main "$@"