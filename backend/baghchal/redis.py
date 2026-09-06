"""
Legacy Redis helpers have been removed.

All live-state access should now go through `baghchal.persistence.store`.
If any code still imports from `baghchal.redis`, update it to import from
`baghchal.persistence.store` (or from the higher-level persistence helpers
that use the store internally).
"""
