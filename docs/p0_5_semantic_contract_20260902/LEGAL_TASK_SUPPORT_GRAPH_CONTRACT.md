# Legal task-support graph contract

`G_task_0` is directed and layered: every Scout-to-Relay and every Relay-to-Terminal edge is legal; Scout-to-Terminal edges are illegal. For 2S+2R+2T, all eight `S_i -> R_j -> T_k` paths are legal. Each appears in `PATH_LEGALITY_MATRIX.csv` and has the same token-generation, relay, freshness, actor and mission-action semantics.

An actor can use a route only through a received message with source, route, age and validity fields. The graph is therefore task-active: without a fresh legal route, a terminal cannot claim supported completion. There is no direct Scout-to-Terminal recovery exception.
