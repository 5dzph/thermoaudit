# Security and sensitive data

The initial 0.1.x branch is the only planned supported line. This package is not a security-certified application or an engineering safety system.

The CLI reads local JSON/CSV and writes local JSON/HTML. It makes no network requests and does not evaluate input as code. Reports contain submitted names and data: inspect them before sharing. Supply trusted output directories; do not run with elevated privileges. Local HTML uses escaped labels and contains no JavaScript.

Do not place secrets or exploitable details in a public issue. Repository owners should enable GitHub private vulnerability reporting; use that channel if available. Until a private channel exists, open an issue requesting private contact without disclosing sensitive details.

The CLI limits input files to 10 MiB; Pareto screening limits candidates to 2000. These bounds are not a hardened multi-tenant service boundary. Do not expose the library directly as an unauthenticated network service without independent review and resource limits.
