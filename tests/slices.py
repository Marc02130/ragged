"""Which conversion slices have landed. Later-slice tests skip until these exist."""

from tests.paths import (
    ALEMBIC_INITIAL,
    API_MAIN,
    AUTH_ROUTER,
    COMPOSE,
    DOCUMENTS_ROUTER,
    MESSAGES_ROUTER,
    SMOKE,
    THREADS_ROUTER,
    VITE_CONFIG,
    WEB_APP,
    WEB_PACKAGE,
    WEBPACK,
)


def slice_ready(n: int) -> bool:
    checks = {
        1: API_MAIN.exists() and COMPOSE.exists(),
        2: ALEMBIC_INITIAL.exists(),
        3: AUTH_ROUTER.exists(),
        4: THREADS_ROUTER.exists(),
        5: DOCUMENTS_ROUTER.exists(),
        6: MESSAGES_ROUTER.exists(),
        7: WEBPACK.exists() and WEB_PACKAGE.exists(),
        8: WEB_APP.exists()
        and (WEB_APP.parent / "components" / "Chat" / "ChatInterface.tsx").exists(),
        9: SMOKE.exists(),
        10: not VITE_CONFIG.exists(),
    }
    return checks[n]


def skip_reason(n: int) -> str:
    return f"slice {n:02d} not implemented yet"
