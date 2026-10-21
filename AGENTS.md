# Guidance for coding assistants

- Preserve explicit units, signed heat/work conventions and schema validation.
- Do not fabricate simulation outputs, adoption, convergence, benchmark improvements or citations.
- Run `python -m unittest discover -s tests -v` after calculation changes.
- For new physics, add an independently checkable example and document assumptions.
- Keep synthetic fixtures explicitly labeled. Do not add private user data or credentials.
- Never silently relax tolerances or label terminal approach as a full internal pinch calculation.
- Keep reports offline and escape all user-provided text.
- Do not claim Windows CI or hosted workflows have passed unless their results were observed.
- Avoid new runtime dependencies without a clear need. Do not submit applications or publish releases without maintainer instruction.
