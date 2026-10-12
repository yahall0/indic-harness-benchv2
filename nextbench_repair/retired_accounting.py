"""Conservative settlement after all request-owning containers are retired."""


def settle_retired_requests(journal,run_id):
    if any(r['run_id']==run_id for r in journal.resources()):
        raise ValueError('Do not settle interrupted requests while owned resources remain')
    calls=journal.db.execute("SELECT id FROM calls WHERE run_id=? AND status='reserved'",(run_id,)).fetchall()
    for call in calls:
        journal.settle(call['id'],{'usage':None,'classification':'ambiguous_transport','status':0,
                                  'stage':'controller_retired_request','full_reservation_retained':True})
    if calls: journal.event(run_id,'retired_requests_accounted',{'unknown_calls':len(calls),'full_reservations_retained':True})
    return len(calls)
