# Multi-Thread Architecture

```mermaid
flowchart TD
    COOKIE[Signed HTTP-only session cookie] --> API[FastAPI]
    API --> USER[Authenticated user]

    USER --> T1[Thread A]
    USER --> T2[Thread B]
    USER --> TN[Thread N]

    T1 --> D1[Documents A]
    T1 --> C1[Messages A]
    D1 --> V1[Vector chunks A]

    T2 --> D2[Documents B]
    T2 --> C2[Messages B]
    D2 --> V2[Vector chunks B]

    TN --> DN[Documents N]
    TN --> CN[Messages N]
    DN --> VN[Vector chunks N]

    Q[Question in Thread A] --> S[Retrieval filters user_id + Thread A id]
    S --> V1
    S -. no access .-> V2
    S -. no access .-> VN

    API --> ARCHIVE[Archive: status becomes archived]
    ARCHIVE --> RESTORE[Restore: status becomes active]
    API --> DELETE[Delete: database cascade + upload directory removal]
```

Users can own multiple independent threads. The default thread list hides archived threads; `include_archived=true` includes them. Archiving preserves documents and messages. Permanent deletion does not create a searchable archive.

Isolation is enforced by FastAPI ownership dependencies and user/thread filters in database queries. The current application does not use Supabase Auth, PostgreSQL RLS, cross-thread retrieval, or archived-chat vectors.
