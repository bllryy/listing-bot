#!/bin/bash

# Listing Bot Docker Quick Setup
# This script sets up Docker on your macOS machine and runs the project

set -e

print_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_warn() {
    echo -e "\033[1;33m[WARN]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    print_info "Docker is installed: $(docker --version)"
}

# Check if Docker Compose is installed
check_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        echo "Please install Docker Desktop which includes Docker Compose"
        exit 1
    fi
    print_info "Docker Compose is installed: $(docker-compose --version)"
}

# Check if Docker daemon is running
check_docker_daemon() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running!"
        echo "Please start Docker Desktop on your macOS machine"
        exit 1
    fi
    print_info "Docker daemon is running"
}

# Setup environment
setup_env() {
    if [ ! -f .env ]; then
        print_info "Creating .env file from template..."
        cp .env.example .env
        print_warn "Please update .env with your configuration values"
    else
        print_info ".env file already exists"
    fi
}

# Main setup
main() {
    print_info "Checking prerequisites..."
    check_docker
    check_compose
    check_docker_daemon
    
    print_info "Setting up environment..."
    setup_env
    
    echo ""
    print_info "Prerequisites check complete!"
    echo ""
    echo "Next steps:"
    echo "1. Review and update .env file with your configuration"
    echo "2. Run: ./docker-manage.sh build"
    echo "3. Run: ./docker-manage.sh up"
    echo "4. Access services:"
    echo "   - Parent API: http://localhost:8000"
    echo "   - AI API: http://localhost:8001"
    echo "   - Bot: http://localhost:8002"
    echo "   - Logger: http://localhost:8003"
    echo "   - Listing Dashboard: http://localhost:3000"
    echo "   - Seller Dashboard: http://localhost:3001"
    echo "   - Shop Sites: http://localhost:7878"
    echo ""
    echo "For help, run: ./docker-manage.sh help"
}

main "$@"
