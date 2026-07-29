"""
Comparison Service (Phase 7) — Response Comparison Engine.

Provides pure business logic to compare an original ApiLog
with its Replay result across four dimensions:
  1. HTTP Status Code
  2. Response Headers  (order-insensitive)
  3. Response Body     (JSON field-level diff)
  4. Response Time     (latency delta)

All methods are static so the service can be called without instantiation,
matching the pattern used by ProjectService, LogService, and ReplayService.
"""

from app.models.api_log import ApiLog
from app.models.replay import Replay
from app.schemas.comparison import (
    ComparisonResponse,
    StatusComparison,
    HeadersComparison,
    BodyComparison,
    ResponseTimeComparison,
)


class ComparisonService:
    """
    Stateless service that generates a structured comparison between
    an original API log and a replay execution result.
    """

    # ------------------------------------------------------------------
    # 1. Status Code Comparison
    # ------------------------------------------------------------------
    @staticmethod
    def compare_status(original: ApiLog, replay: Replay) -> StatusComparison:
        """
        Compares the HTTP status codes.
        Returns the old / new values and whether they differ.
        """
        old_status = original.status_code
        new_status = replay.replay_status_code

        return StatusComparison(
            old_status=old_status,
            new_status=new_status,
            status_changed=old_status != new_status,
        )

    # ------------------------------------------------------------------
    # 2. Response Headers Comparison (order-insensitive)
    # ------------------------------------------------------------------
    @staticmethod
    def compare_headers(original: ApiLog, replay: Replay) -> HeadersComparison:
        """
        Compares response headers while ignoring key ordering.
        Both sides are normalised to lowercase keys for a fair comparison.
        """
        # Normalise to lowercase-keyed dicts (headers are case-insensitive per HTTP spec)
        old_headers = {
            k.lower(): v
            for k, v in (original.response_headers or {}).items()
        }
        new_headers = {
            k.lower(): v
            for k, v in (replay.replay_response_headers or {}).items()
        }

        return HeadersComparison(headers_changed=old_headers != new_headers)

    # ------------------------------------------------------------------
    # 3. Response Body Comparison (JSON field-level diff)
    # ------------------------------------------------------------------
    @staticmethod
    def compare_body(original: ApiLog, replay: Replay) -> BodyComparison:
        """
        Compares JSON response bodies.

        When both bodies are dicts, also computes:
          - added_fields   : keys in replay but not in original
          - removed_fields : keys in original but not in replay
          - modified_fields: keys in both but with different values

        Falls back to a simple equality check when either side is
        not a dict (e.g. list, None, or raw text).
        """
        old_body = original.response_body
        new_body = replay.replay_response_body

        # Quick equality check
        body_changed = old_body != new_body

        added_fields: list[str] = []
        removed_fields: list[str] = []
        modified_fields: list[str] = []

        # Field-level diff only makes sense when both sides are dicts
        if isinstance(old_body, dict) and isinstance(new_body, dict):
            old_keys = set(old_body.keys())
            new_keys = set(new_body.keys())

            # Keys present in replay but not in original
            added_fields = sorted(new_keys - old_keys)

            # Keys present in original but not in replay
            removed_fields = sorted(old_keys - new_keys)

            # Keys present in both but with different values
            common_keys = old_keys & new_keys
            modified_fields = sorted(
                key for key in common_keys if old_body[key] != new_body[key]
            )

        return BodyComparison(
            body_changed=body_changed,
            added_fields=added_fields,
            removed_fields=removed_fields,
            modified_fields=modified_fields,
        )

    # ------------------------------------------------------------------
    # 4. Response Time Comparison
    # ------------------------------------------------------------------
    @staticmethod
    def compare_response_time(original: ApiLog, replay: Replay) -> ResponseTimeComparison:
        """
        Compares the original and replay response latencies.
        Returns the raw values and the signed delta (positive = replay was slower).
        If either side is None the delta is also None.
        """
        old_time = original.response_time_ms
        new_time = replay.replay_response_time_ms

        # Compute delta only when both values are available
        if old_time is not None and new_time is not None:
            latency_diff = new_time - old_time
        else:
            latency_diff = None

        return ResponseTimeComparison(
            old_response_time_ms=old_time,
            new_response_time_ms=new_time,
            latency_difference_ms=latency_diff,
        )

    # ------------------------------------------------------------------
    # 5. Full Comparison (orchestrator)
    # ------------------------------------------------------------------
    @staticmethod
    def generate_comparison(original: ApiLog, replay: Replay) -> ComparisonResponse:
        """
        Runs all four sub-comparisons and combines them into a single
        ComparisonResponse with an overall_changed flag.
        """
        status_cmp = ComparisonService.compare_status(original, replay)
        headers_cmp = ComparisonService.compare_headers(original, replay)
        body_cmp = ComparisonService.compare_body(original, replay)
        time_cmp = ComparisonService.compare_response_time(original, replay)

        # overall_changed is True if *any* dimension shows a difference
        overall_changed = any([
            status_cmp.status_changed,
            headers_cmp.headers_changed,
            body_cmp.body_changed,
        ])

        return ComparisonResponse(
            status=status_cmp,
            headers=headers_cmp,
            body=body_cmp,
            response_time=time_cmp,
            overall_changed=overall_changed,
        )
