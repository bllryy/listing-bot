#!/bin/bash

# Listing Bot Docker Management Script
# Makes it easier to build, run, and manage Docker services

set -e

COMPOSE_CMD="docker-compose"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show help
show_help() {
    cat << EOF
Listing Bot Docker Management Script

Usage: ./docker-manage.sh [COMMAND] [OPTIONS]

Commands:
    build [SERVICE]      Build all services or a specific service
    up [SERVICE]         Start all services or a specific service
    down                 Stop all services
    logs [SERVICE]       View logs for all or specific service
    restart [SERVICE]    Restart all or specific service
    clean                Remove all containers and volumes
    status               Show container status
    help                 Show this help message

Examples:
    ./docker-manage.sh build                    # Build all
    ./docker-manage.sh build listing-bot        # Build one service
    ./docker-manage.sh up                       # Start all
    ./docker-manage.sh up ai-api                # Start one service
    ./docker-manage.sh logs listing-bot         # View logs
    ./docker-manage.sh restart parent-api       # Restart one service
    ./docker-manage.sh down                     # Stop all
    ./docker-manage.sh clean                    # Clean everything

EOF
}

# Build services
build_services() {
    if [ -z "$1" ]; then
        print_info "Building all services..."
        cd "$PROJECT_ROOT"
        $COMPOSE_CMD build
    else
        print_info "Building service: $1"
        cd "$PROJECT_ROOT"
        $COMPOSE_CMD build "$1"
    fi
    print_info "Build complete!"
}

# Start services
start_services() {
    if [ -z "$1" ]; then
        print_info "Starting all services..."
        cd "$PROJECT_ROOT"
        $COMPOSE_CMD up -d
        print_info "All services started!"
    else
        print_info "Starting service: $1"
        cd "$PROJECT_ROOT"
        $COMPOSE_CMD up -d "$1"
        print_info "Service started!"
    fi
}

# Stop services
stop_services() {
    print_info "Stopping all services..."
    cd "$PROJECT_ROOT"
    $COMPOSE_CMD down
    print_info "All services stopped!"
}

# View logs
view_logs() {
    cd "$PROJECT_ROOT"
    if [ -z "$1" ]; then
        print_info "Showing logs for all services (Ctrl+C to exit)..."
        $COMPOSE_CMD logs -f
    else
        print_info "Showing logs for service: $1 (Ctrl+C to exit)..."
        $COMPOSE_CMD logs -f "$1"
    fi
}

# Restart services
restart_services() {
    if [ -z "$1" ]; then
        print_info "Restarting all services..."
        cd "$PROJECT_ROOT"
        $COMPOSE_CMD restart
    else
        print_info "Restarting service: $1"
        cd "$PROJECT_ROOT"
        $COMPOSE_CMD restart "$1"
    fi
    print_info "Restart complete!"
}

# Show status
show_status() {
    print_info "Container Status:"
    cd "$PROJECT_ROOT"
    $COMPOSE_CMD ps
}

# Clean everything
clean_all() {
    print_warn "This will remove all containers, volumes, and networks for this project."
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        print_info "Cleaning up..."
        cd "$PROJECT_ROOT"
        $COMPOSE_CMD down -v
        print_info "Cleanup complete!"
    else
        print_info "Cleanup cancelled."
    fi
}

# Main logic
case "$1" in
    build)
        build_services "$2"
        ;;
    up)
        start_services "$2"
        ;;
    down)
        stop_services
        ;;
    logs)
        view_logs "$2"
        ;;
    restart)
        restart_services "$2"
        ;;
    status)
        show_status
        ;;
    clean)
        clean_all
        ;;
    help|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
