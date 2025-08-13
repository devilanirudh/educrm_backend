#!/bin/bash

# Docker helper script for E-School Backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 {build|dev|prod|stop|clean|logs|shell}"
    echo ""
    echo "Commands:"
    echo "  build   - Build the Docker image"
    echo "  dev     - Start development environment"
    echo "  prod    - Start production environment"
    echo "  stop    - Stop all containers"
    echo "  clean   - Remove containers, images, and volumes"
    echo "  logs    - Show logs from containers"
    echo "  shell   - Open shell in running backend container"
    echo ""
}

# Function to build image
build_image() {
    print_status "Building Docker image..."
    docker build -t eschool-backend .
    print_success "Image built successfully!"
}

# Function to start development environment
start_dev() {
    print_status "Starting development environment..."
    docker-compose -f docker-compose.dev.yml up -d
    print_success "Development environment started!"
    print_status "Backend available at: http://localhost:8000"
    print_status "API docs available at: http://localhost:8000/docs"
}

# Function to start production environment
start_prod() {
    print_status "Starting production environment..."
    docker-compose up -d
    print_success "Production environment started!"
    print_status "Backend available at: http://localhost:8000"
    print_status "API docs available at: http://localhost:8000/docs"
}

# Function to stop containers
stop_containers() {
    print_status "Stopping containers..."
    docker-compose down
    docker-compose -f docker-compose.dev.yml down
    print_success "Containers stopped!"
}

# Function to clean everything
clean_all() {
    print_warning "This will remove all containers, images, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        docker-compose down -v --rmi all
        docker-compose -f docker-compose.dev.yml down -v --rmi all
        docker system prune -f
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing logs..."
    docker-compose logs -f
}

# Function to open shell
open_shell() {
    print_status "Opening shell in backend container..."
    docker-compose exec backend /bin/bash
}

# Main script logic
case "$1" in
    build)
        build_image
        ;;
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    stop)
        stop_containers
        ;;
    clean)
        clean_all
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
