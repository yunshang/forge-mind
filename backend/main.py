from litestar import Litestar
from litestar.config.cors import CORSConfig

from backend.routes.contracts import generate_contract
from backend.routes.sandbox import call_contract
from backend.routes.sessions import (
    create_session,
    delete_session,
    generate_in_session,
    get_session,
    list_sessions,
)
from backend.routes.visual import visualize_contract

cors_config = CORSConfig(
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app = Litestar(
    route_handlers=[
        generate_contract,
        call_contract,
        visualize_contract,
        create_session,
        list_sessions,
        get_session,
        delete_session,
        generate_in_session,
    ],
    cors_config=cors_config,
    debug=True,
)
