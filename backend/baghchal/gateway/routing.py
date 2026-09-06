"""
Gateway routing notes.

Today the existing WebSocket routing still points at
`baghchal.consumers.AsyncGameConsumer`.

The intended next step is a gateway-aware consumer or consumer wrapper that
uses `GameGateway` and `GameSession` instead of doing group_send and
connection management ad hoc.

No existing routing has been changed yet.
"""
