# Ralph Fix Plan - TraceHub

## High Priority (Sprint 12 - Current)

- [ ] DateTime timezone standardization across all endpoints
- [ ] Shipment status state machine implementation
- [ ] EUDR compliance test coverage improvement
- [ ] Cache invalidation pattern fixes (phase 3)

## Medium Priority

- [ ] Buyer portal read-only access enhancements
- [ ] Document OCR accuracy improvements
- [ ] Analytics dashboard performance optimization
- [ ] Notification system enhancements

## Low Priority

- [ ] Extended audit logging
- [ ] Export functionality (PDF, Excel)
- [ ] Advanced search/filtering capabilities
- [ ] Mobile-responsive improvements

## Completed

- [x] Project initialization
- [x] Multi-tenancy architecture (Sprint 8)
- [x] Compliance matrix updates (Sprint 9)
- [x] Architecture cleanup (Sprint 10)
- [x] Schema fixes, buyer access (Sprint 11)
- [x] Cache invalidation pattern fix (phases 1-2)
- [x] Organization member management (Sprint 13)
- [x] Compliance feature hardening (Sprint 14)

## Notes

- Always check `docs/COMPLIANCE_MATRIX.md` before compliance work
- Horn/hoof products (HS 0506/0507) are NOT covered by EUDR
- All queries MUST filter by `organization_id` (multi-tenancy)
- Follow GitOps: feature branch -> develop -> main
- Update this file after each major milestone
