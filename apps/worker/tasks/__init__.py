"""Celery task implementations.

One module per domain, mirroring the API's feature modules. PHASE 6 fills these
in; PHASE 0 ships only ``ops`` so the worker can prove it is connected.

    ops      - health / diagnostics                     (PHASE 0)
    github   - repository sync, webhook processing      (PHASE 2)
    ml       - dataset build, model training            (PHASE 3)
    drive    - large-file upload/download, reconcile    (PHASE 4)
    readme   - evidence extraction, README generation   (PHASE 5)
"""
