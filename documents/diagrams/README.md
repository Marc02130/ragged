# RAGged Application Diagrams

This directory contains comprehensive diagrams for the RAGged application architecture, data flows, and processes.

## Diagrams Overview

### 1. **Data Flow Diagrams**
- **Upload-to-Query Process**: Complete flow from document upload to RAG query
- **Thread Deletion Flow**: Archive and deletion process with vector preservation
- **Multi-Thread Architecture**: How multiple threads are managed per user

### 2. **Database Schema Diagrams**
- **Table Relationships**: Entity relationship diagram
- **RLS Policy Flow**: Row Level Security implementation

### 3. **System Architecture Diagrams**
- **Component Architecture**: Overall system components
- **Security Model**: Authentication and authorization flow

## Viewing Diagrams

### GitHub/GitLab
These diagrams use Mermaid syntax and will render automatically in:
- GitHub README files
- GitLab markdown files
- GitHub/GitLab issue descriptions
- Pull request descriptions

### Local Development
To view diagrams locally:

1. **VS Code**: Install "Mermaid Preview" extension
2. **Browser**: Use online Mermaid editor at [mermaid.live](https://mermaid.live)
3. **CLI**: Use `@mermaid-js/mermaid-cli` for generating images

### Generating Images
```bash
# Install mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Generate PNG from diagram
mmdc -i upload-flow.md -o upload-flow.png

# Generate SVG from diagram
mmdc -i upload-flow.md -o upload-flow.svg
```

## Diagram Conventions

### Colors
- **Blue**: User actions and UI components
- **Green**: Database operations and storage
- **Orange**: Edge Functions and API calls
- **Purple**: Vector operations and AI processing
- **Red**: Error handling and validation
- **Gray**: External services (OpenAI, Supabase)

### Shapes
- **Rectangle**: Processes and operations
- **Diamond**: Decision points and validation
- **Cylinder**: Database tables
- **Cloud**: External services
- **Document**: File operations
- **Storage**: File storage buckets

### Arrows
- **Solid**: Data flow and API calls
- **Dashed**: Optional or conditional flows
- **Dotted**: Error handling and fallbacks

## Diagram Files

1. `upload-to-query-flow.md` - Document upload to RAG query process
2. `thread-deletion-flow.md` - Thread archival and deletion process
3. `multi-thread-architecture.md` - Multi-thread user management
4. `database-schema.md` - Database table relationships
5. `system-architecture.md` - Overall system components
6. `security-flow.md` - Authentication and authorization flow

## Updating Diagrams

When updating diagrams:

1. **Version Control**: Always commit diagram changes with code changes
2. **Documentation**: Update this README if adding new diagrams
3. **Consistency**: Follow the established color and shape conventions
4. **Testing**: Verify diagrams render correctly in target platforms

## Tools and Resources

- **Mermaid Documentation**: [mermaid.js.org](https://mermaid.js.org/)
- **Online Editor**: [mermaid.live](https://mermaid.live)
- **VS Code Extension**: "Mermaid Preview"
- **CLI Tool**: `@mermaid-js/mermaid-cli`
- **GitHub Support**: [GitHub Mermaid Support](https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/) 