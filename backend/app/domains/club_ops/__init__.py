"""Club Management (owner operations): resources, zones, pricing, promotions, CRM, occupancy.

Scoping rule for this whole domain: every query is filtered by `parlor_id`, and the
caller's right to that parlor is proven by `club_ops.repository.assert_club_access`
(owner match on gaming_place_extensions.owner_id, or platform admin). Never trust a
`parlor_id` that arrived in a request body/path without that check.
"""
