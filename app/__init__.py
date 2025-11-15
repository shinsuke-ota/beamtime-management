"""Application package initialization hooks."""

from __future__ import annotations

import inspect
import sys
from typing import ForwardRef

# FastAPI 0.110 still relies on Pydantic v1 which, in turn, calls
# ``ForwardRef._evaluate`` using positional arguments.  Python 3.13 changed the
# ``typing.ForwardRef`` implementation so that ``recursive_guard`` must be
# provided as a keyword argument, which breaks the legacy call signature and
# results in ``TypeError: ForwardRef._evaluate() missing 1 required keyword-only
# argument: 'recursive_guard'`` when importing our FastAPI app.  To keep the
# application working on modern interpreters without waiting for a FastAPI
# upgrade, shim in a small compatibility layer that translates the positional
# call into the keyword-based form when necessary.  On interpreters where the
# positional call is still supported (≤ Python 3.12), this wrapper is a no-op.
if sys.version_info >= (3, 13):
    _original_forwardref_evaluate = ForwardRef._evaluate

    signature = inspect.signature(_original_forwardref_evaluate)
    if "recursive_guard" in signature.parameters:

        def _evaluate_with_recursive_guard(self, *args, **kwargs):
            """Allow positional and keyword recursive_guard arguments."""

            try:
                return _original_forwardref_evaluate(self, *args, **kwargs)
            except TypeError as exc:
                if "recursive_guard" not in str(exc) or "recursive_guard" in kwargs:
                    raise
                if len(args) < 3:
                    raise

                *prefix_args, recursive_guard = args
                if recursive_guard is None:
                    recursive_guard = set()

                return _original_forwardref_evaluate(
                    self,
                    *prefix_args,
                    recursive_guard=recursive_guard,
                    **kwargs,
                )

        ForwardRef._evaluate = _evaluate_with_recursive_guard

