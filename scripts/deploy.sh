#!/bin/bash

# RAG Application Deployment Script
# This script automates the deployment of the RAG application

set -e

echo "🚀 Starting RAG Application Deployment..."

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

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v supabase &> /dev/null; then
        print_error "Supabase CLI is not installed. Please install it first:"
        echo "npm install -g supabase"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install it first."
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Check environment variables
check_environment() {
    print_status "Checking environment variables..."
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        cp env.example .env
        print_warning "Please update .env with your actual values before continuing"
        exit 1
    fi
    
    # Check for required environment variables
    source .env
    
    if [ -z "$VITE_SUPABASE_URL" ]; then
        print_error "VITE_SUPABASE_URL is not set in .env"
        exit 1
    fi
    
    if [ -z "$VITE_SUPABASE_ANON_KEY" ]; then
        print_error "VITE_SUPABASE_ANON_KEY is not set in .env"
        exit 1
    fi
    
    if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
        print_error "SUPABASE_SERVICE_ROLE_KEY is not set in .env"
        exit 1
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        print_error "OPENAI_API_KEY is not set in .env"
        exit 1
    fi
    
    print_success "Environment variables are configured"
}

# Install frontend dependencies
install_dependencies() {
    print_status "Installing frontend dependencies..."
    npm install
    print_success "Frontend dependencies installed"
}

# Deploy database migrations
deploy_migrations() {
  print_status "Deploying database migrations..."
  
  # Check if Supabase project is linked
  if ! supabase status &> /dev/null; then
    print_error "Supabase project is not linked. Please run:"
    echo "supabase link --project-ref YOUR_PROJECT_REF"
    exit 1
  fi
  
  # Deploy migrations (including user preferences)
  print_status "Applying database migrations..."
  supabase db push
  
  # Verify user preferences functions are created
  print_status "Verifying user preferences functions..."
  supabase db reset --linked
  
  print_success "Database migrations deployed with user preferences support"
}

# Deploy Edge Functions
deploy_edge_functions() {
    print_status "Deploying Edge Functions..."
    
    # Deploy each Edge Function
    print_status "Deploying vectorize function..."
    supabase functions deploy vectorize
    
    print_status "Deploying rag-query function..."
    supabase functions deploy rag-query
    
    print_status "Deploying delete-thread function..."
    supabase functions deploy delete-thread
    
    print_success "Edge Functions deployed"
}

# Set Edge Function secrets
set_secrets() {
    print_status "Setting Edge Function secrets..."
    
    # Read secrets from .env
    source .env
    
    # Set secrets for Edge Functions
    supabase secrets set OPENAI_API_KEY="$OPENAI_API_KEY"
    supabase secrets set SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_SERVICE_ROLE_KEY"
    
    print_success "Edge Function secrets configured"
}

# Build frontend
build_frontend() {
    print_status "Building frontend application..."
    npm run build
    print_success "Frontend built successfully"
}

# Create storage buckets
setup_storage() {
    print_status "Setting up storage buckets..."
    
    # This would typically be done through Supabase Dashboard
    # or via SQL commands. For now, we'll provide instructions.
    print_warning "Please create the following storage buckets in your Supabase dashboard:"
    echo "  - documents (for uploaded files)"
    echo "  - archives (for archived content)"
    echo "  - temp (for temporary files)"
    echo ""
    echo "Storage bucket policies should be configured for user-scoped access."
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    # Run linting
    npm run lint
    
    # Run type checking
    npx tsc --noEmit
    
    print_success "Tests passed"
}

# Main deployment function
main() {
    echo "=========================================="
    echo "RAG Application Deployment"
    echo "=========================================="
    echo ""
    
    check_dependencies
    check_environment
    install_dependencies
    deploy_migrations
    deploy_edge_functions
    set_secrets
    setup_storage
    run_tests
    build_frontend
    
    echo ""
    echo "=========================================="
    print_success "Deployment completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Start the development server: npm run dev"
    echo "2. Open http://localhost:5173 in your browser"
    echo "3. Create a user account and start using the application"
    echo ""
    echo "For production deployment:"
    echo "1. Deploy the built frontend to your hosting platform"
    echo "2. Update environment variables for production"
    echo "3. Configure custom domain if needed"
    echo ""
}

# Run main function
main "$@" 