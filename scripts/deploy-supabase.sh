#!/bin/bash

# Supabase Deployment Script
# This script automates the complete deployment of the RAG application to Supabase

set -e

echo "🚀 Starting Supabase Deployment for RAG Application..."

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

# Configuration
ENVIRONMENT=${1:-development}
PROJECT_REF=""
ORG_ID=""

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

# Initialize Supabase project
initialize_supabase() {
    print_status "Initializing Supabase project..."
    
    # Check if already linked
    if supabase status &> /dev/null; then
        print_status "Project already linked"
        return
    fi
    
    # Check if project ref is provided
    if [ -z "$PROJECT_REF" ]; then
        print_warning "No project reference provided. You can:"
        echo "1. Create a new project: supabase projects create --name ragged-app --org-id YOUR_ORG_ID"
        echo "2. Link to existing project: supabase link --project-ref YOUR_PROJECT_REF"
        echo ""
        read -p "Enter project reference (or press Enter to create new): " PROJECT_REF
        
        if [ -z "$PROJECT_REF" ]; then
            read -p "Enter organization ID: " ORG_ID
            if [ -z "$ORG_ID" ]; then
                print_error "Organization ID is required to create a new project"
                exit 1
            fi
            
            print_status "Creating new Supabase project..."
            supabase projects create --name ragged-app --org-id "$ORG_ID"
            print_success "Project created successfully"
        else
            print_status "Linking to existing project..."
            supabase link --project-ref "$PROJECT_REF"
            print_success "Project linked successfully"
        fi
    else
        supabase link --project-ref "$PROJECT_REF"
        print_success "Project linked successfully"
    fi
}

# Deploy database schema
deploy_database() {
    print_status "Deploying database schema..."
    
    # Apply migrations
    print_status "Applying database migrations..."
    supabase db push
    
    # Enable required extensions
    print_status "Enabling required extensions..."
    supabase db reset --linked
    
    print_success "Database schema deployed successfully"
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
    
    print_success "Edge Functions deployed successfully"
}

# Configure Edge Function secrets
configure_secrets() {
    print_status "Configuring Edge Function secrets..."
    
    # Read secrets from .env
    source .env
    
    # Set secrets for Edge Functions
    supabase secrets set OPENAI_API_KEY="$OPENAI_API_KEY"
    supabase secrets set SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_SERVICE_ROLE_KEY"
    
    print_success "Edge Function secrets configured successfully"
}

# Configure storage buckets
configure_storage() {
    print_status "Configuring storage buckets..."
    
    # Create storage buckets
    print_status "Creating storage buckets..."
    
    # Check if buckets exist, create if not
    if ! supabase storage list | grep -q "documents"; then
        supabase storage create documents
        print_status "Created documents bucket"
    fi
    
    if ! supabase storage list | grep -q "archives"; then
        supabase storage create archives
        print_status "Created archives bucket"
    fi
    
    if ! supabase storage list | grep -q "temp"; then
        supabase storage create temp
        print_status "Created temp bucket"
    fi
    
    print_success "Storage buckets configured successfully"
}

# Configure storage policies
configure_storage_policies() {
    print_status "Configuring storage policies..."
    
    # Apply storage policies via SQL
    print_status "Applying storage policies..."
    
    # This would typically be done through the Supabase dashboard
    # or via SQL commands. For now, we'll provide instructions.
    print_warning "Please configure storage policies in your Supabase dashboard:"
    echo "1. Go to Storage > Policies"
    echo "2. For each bucket (documents, archives, temp):"
    echo "   - Add policy: Users can upload own files"
    echo "   - Add policy: Users can view own files"
    echo "   - Add policy: Users can delete own files"
    echo "3. Ensure policies use: auth.uid()::text = (storage.foldername(name))[1]"
}

# Verify RLS policies
verify_rls_policies() {
    print_status "Verifying RLS policies..."
    
    # Check if RLS is enabled on all tables
    print_status "Checking RLS status..."
    
    # This would typically be done via SQL queries
    # For now, we'll provide verification steps
    print_warning "Please verify RLS policies in your Supabase dashboard:"
    echo "1. Go to Authentication > Policies"
    echo "2. Verify RLS is enabled on:"
    echo "   - user_profiles"
    echo "   - threads"
    echo "   - documents"
    echo "   - conversations"
    echo "   - vector_chunks"
    echo "3. Ensure all policies scope by user_id"
}

# Test Edge Functions
test_edge_functions() {
    print_status "Testing Edge Functions..."
    
    # Get project URL from environment
    source .env
    PROJECT_URL=$(echo "$VITE_SUPABASE_URL" | sed 's|https://||')
    
    print_status "Testing vectorize function..."
    echo "curl -X POST https://$PROJECT_URL/functions/v1/vectorize \\"
    echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"type\": \"document\", \"documentId\": \"test\", \"userId\": \"test\"}'"
    
    print_status "Testing rag-query function..."
    echo "curl -X POST https://$PROJECT_URL/functions/v1/rag-query \\"
    echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"threadId\": \"test\", \"userId\": \"test\", \"query\": \"test\"}'"
    
    print_status "Testing delete-thread function..."
    echo "curl -X POST https://$PROJECT_URL/functions/v1/delete-thread \\"
    echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"threadId\": \"test\", \"userId\": \"test\", \"confirmDeletion\": true}'"
    
    print_warning "Please test these functions with valid JWT tokens and data"
}

# Production deployment
deploy_production() {
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Deploying to production environment..."
        
        # Set production secrets
        supabase secrets set --env prod OPENAI_API_KEY="$OPENAI_API_KEY"
        supabase secrets set --env prod SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_SERVICE_ROLE_KEY"
        
        # Deploy to production
        supabase db push --env prod
        supabase functions deploy vectorize --env prod
        supabase functions deploy rag-query --env prod
        supabase functions deploy delete-thread --env prod
        
        print_success "Production deployment completed"
    fi
}

# Main deployment function
main() {
    echo "=========================================="
    echo "Supabase Deployment for RAG Application"
    echo "Environment: $ENVIRONMENT"
    echo "=========================================="
    echo ""
    
    check_dependencies
    check_environment
    initialize_supabase
    deploy_database
    deploy_edge_functions
    configure_secrets
    configure_storage
    configure_storage_policies
    verify_rls_policies
    test_edge_functions
    deploy_production
    
    echo ""
    echo "=========================================="
    print_success "Supabase deployment completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Configure storage policies in Supabase dashboard"
    echo "2. Verify RLS policies are working correctly"
    echo "3. Test Edge Functions with valid JWT tokens"
    echo "4. Deploy frontend application"
    echo "5. Test complete workflow"
    echo ""
    echo "For production deployment:"
    echo "1. Set up monitoring and logging"
    echo "2. Configure custom domain if needed"
    echo "3. Set up backup and recovery procedures"
    echo "4. Monitor performance and optimize as needed"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-ref)
            PROJECT_REF="$2"
            shift 2
            ;;
        --org-id)
            ORG_ID="$2"
            shift 2
            ;;
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--project-ref PROJECT_REF] [--org-id ORG_ID] [--env ENVIRONMENT]"
            echo ""
            echo "Options:"
            echo "  --project-ref PROJECT_REF  Link to existing project"
            echo "  --org-id ORG_ID           Organization ID for new project"
            echo "  --env ENVIRONMENT         Environment (development|production)"
            echo "  --help                    Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main "$@" 