# Thread Lifecycle

```mermaid
flowchart TD
    ACTIVE[Active thread] -->|POST /archive| ARCHIVED[Archived thread]
    ARCHIVED -->|POST /restore| ACTIVE

    ACTIVE -->|user confirms in UI| DELETE[DELETE /api/threads/id]
    ARCHIVED -->|user confirms in UI| DELETE
    DELETE --> OWN{Authenticated user owns thread?}
    OWN -->|no| NOTFOUND[404]
    OWN -->|yes| DB[Delete thread row]
    DB --> CASCADE[Database cascades documents, conversations, chunks]
    CASCADE --> FILES[Remove user/thread upload directory]
    FILES --> DONE[204]
```

Archiving is reversible and keeps all data. It only changes `threads.status`.

Permanent deletion is not an archival workflow. The API does not accept `confirmDeletion`, `archiveConversations`, or `preserveVectors`; confirmation is a browser concern. Deletion does not call a chat or embedding provider and does not create a searchable conversation archive.
