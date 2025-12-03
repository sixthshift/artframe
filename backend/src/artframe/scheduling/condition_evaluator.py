"""
Condition evaluator for determining when content should be displayed.

Supports various condition types like time of day, day of week,
and extensible custom conditions.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """
    Evaluates display conditions for schedule entries and playlist items.

    Conditions are dictionaries where each key is a condition type and
    the value contains the parameters for that condition.

    Example conditions:
        {"time_of_day": {"periods": ["morning", "afternoon"]}}
        {"day_of_week": {"days": [0, 1, 2, 3, 4]}}  # Weekdays
        {"all_of": [{"time_of_day": {...}}, {"day_of_week": {...}}]}
        {"any_of": [{"condition1": ...}, {"condition2": ...}]}
    """

    # Time period definitions (hour ranges)
    TIME_PERIODS = {
        "early_morning": (5, 7),  # 5:00 - 6:59
        "morning": (7, 12),  # 7:00 - 11:59
        "afternoon": (12, 17),  # 12:00 - 16:59
        "evening": (17, 21),  # 17:00 - 20:59
        "night": (21, 24),  # 21:00 - 23:59
        "late_night": (0, 5),  # 00:00 - 4:59
    }

    def __init__(self, timezone: str = "UTC"):
        """Initialize condition evaluator with built-in handlers.

        Args:
            timezone: IANA timezone string (e.g. "Australia/Sydney")
        """
        self._tz = ZoneInfo(timezone)
        self._handlers: Dict[str, Callable[[Dict[str, Any]], bool]] = {
            "time_of_day": self._eval_time_of_day,
            "day_of_week": self._eval_day_of_week,
            "date_range": self._eval_date_range,
            "time_range": self._eval_time_range,
            "all_of": self._eval_all_of,
            "any_of": self._eval_any_of,
            "not": self._eval_not,
        }
        # Store for external condition providers (e.g., weather, API status)
        self._external_providers: Dict[str, Callable[[], Any]] = {}

    def _now(self) -> datetime:
        """Get current time in configured timezone."""
        return datetime.now(self._tz)

    def register_provider(
        self, name: str, provider: Callable[[], Any]
    ) -> None:
        """
        Register an external condition provider.

        Providers are functions that return current state for a condition type.
        For example, a weather provider might return {"condition": "sunny", "temp": 72}.

        Args:
            name: Provider name (e.g., "weather", "api_status")
            provider: Function that returns current state
        """
        self._external_providers[name] = provider
        logger.debug(f"Registered condition provider: {name}")

    def register_handler(
        self, condition_type: str, handler: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Register a custom condition handler.

        Args:
            condition_type: Name of the condition type
            handler: Function that takes params dict and returns bool
        """
        self._handlers[condition_type] = handler
        logger.debug(f"Registered condition handler: {condition_type}")

    def evaluate(self, conditions: Optional[Dict[str, Any]]) -> bool:
        """
        Evaluate all conditions. Returns True if all pass (AND logic).

        Args:
            conditions: Dictionary of conditions to evaluate, or None

        Returns:
            True if all conditions pass or conditions is None/empty
        """
        if not conditions:
            return True

        for condition_type, params in conditions.items():
            handler = self._handlers.get(condition_type)

            if handler:
                try:
                    if not handler(params):
                        logger.debug(
                            f"Condition failed: {condition_type} with params {params}"
                        )
                        return False
                except Exception as e:
                    logger.warning(
                        f"Error evaluating condition {condition_type}: {e}"
                    )
                    # Fail open - if condition evaluation fails, allow it
                    continue
            else:
                # Unknown condition type - check external providers
                if condition_type in self._external_providers:
                    if not self._eval_external(condition_type, params):
                        return False
                else:
                    logger.warning(f"Unknown condition type: {condition_type}")
                    # Unknown conditions are ignored (fail open)

        return True

    def _eval_time_of_day(self, params: Dict[str, Any]) -> bool:
        """
        Check if current time is within specified periods.

        Args:
            params: {"periods": ["morning", "afternoon", ...]}

        Returns:
            True if current time is in any of the specified periods
        """
        periods = params.get("periods", [])
        if not periods:
            return True

        current_hour = self._now().hour

        for period in periods:
            if period in self.TIME_PERIODS:
                start, end = self.TIME_PERIODS[period]
                if start <= end:
                    if start <= current_hour < end:
                        return True
                else:
                    # Handles periods that cross midnight
                    if current_hour >= start or current_hour < end:
                        return True

        return False

    def _eval_day_of_week(self, params: Dict[str, Any]) -> bool:
        """
        Check if current day is in specified days.

        Args:
            params: {"days": [0, 1, 2, 3, 4]} where 0=Monday, 6=Sunday

        Returns:
            True if current day is in the list
        """
        days = params.get("days", [])
        if not days:
            return True

        current_day = self._now().weekday()
        return current_day in days

    def _eval_date_range(self, params: Dict[str, Any]) -> bool:
        """
        Check if current date is within a specified range.

        Args:
            params: {
                "start_date": "2024-01-01",  # Optional
                "end_date": "2024-12-31"     # Optional
            }

        Returns:
            True if current date is within range
        """
        today = self._now().date()

        start_str = params.get("start_date")
        end_str = params.get("end_date")

        try:
            if start_str:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                if today < start_date:
                    return False

            if end_str:
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                if today > end_date:
                    return False

            return True
        except ValueError as e:
            logger.warning(f"Invalid date format in date_range condition: {e}")
            return True  # Fail open

    def _eval_time_range(self, params: Dict[str, Any]) -> bool:
        """
        Check if current time is within a specified range.

        Args:
            params: {
                "start_time": "09:00",
                "end_time": "17:00"
            }

        Returns:
            True if current time is within range
        """
        start_str = params.get("start_time")
        end_str = params.get("end_time")

        if not start_str or not end_str:
            return True

        try:
            now = self._now()
            current_time = now.strftime("%H:%M")

            start_t = datetime.strptime(start_str, "%H:%M").time()
            end_t = datetime.strptime(end_str, "%H:%M").time()
            current_t = datetime.strptime(current_time, "%H:%M").time()

            if start_t <= end_t:
                # Normal range (e.g., 09:00 to 17:00)
                return start_t <= current_t < end_t
            else:
                # Overnight range (e.g., 22:00 to 06:00)
                return current_t >= start_t or current_t < end_t

        except ValueError as e:
            logger.warning(f"Invalid time format in time_range condition: {e}")
            return True  # Fail open

    def _eval_all_of(self, params: List[Dict[str, Any]]) -> bool:
        """
        Evaluate multiple conditions with AND logic.

        Args:
            params: List of condition dictionaries

        Returns:
            True if ALL conditions pass
        """
        if not params:
            return True

        return all(self.evaluate(condition) for condition in params)

    def _eval_any_of(self, params: List[Dict[str, Any]]) -> bool:
        """
        Evaluate multiple conditions with OR logic.

        Args:
            params: List of condition dictionaries

        Returns:
            True if ANY condition passes
        """
        if not params:
            return True

        return any(self.evaluate(condition) for condition in params)

    def _eval_not(self, params: Dict[str, Any]) -> bool:
        """
        Negate a condition.

        Args:
            params: Single condition dictionary to negate

        Returns:
            True if the nested condition is False
        """
        return not self.evaluate(params)

    def _eval_external(self, provider_name: str, params: Dict[str, Any]) -> bool:
        """
        Evaluate a condition using an external provider.

        Args:
            provider_name: Name of the registered provider
            params: Parameters for matching against provider state

        Returns:
            True if the provider state matches the params
        """
        provider = self._external_providers.get(provider_name)
        if not provider:
            logger.warning(f"External provider not found: {provider_name}")
            return True  # Fail open

        try:
            state = provider()

            # Simple matching: check if all params match state
            for key, expected in params.items():
                if key == "equals":
                    # Direct value comparison
                    if state != expected:
                        return False
                elif key == "contains":
                    # Check if state contains value
                    if expected not in state:
                        return False
                elif key == "in":
                    # Check if state is in list
                    if state not in expected:
                        return False
                elif isinstance(state, dict) and key in state:
                    # Compare nested value
                    if state[key] != expected:
                        return False

            return True

        except Exception as e:
            logger.warning(f"Error evaluating external condition {provider_name}: {e}")
            return True  # Fail open

    def get_current_context(self) -> Dict[str, Any]:
        """
        Get the current context for condition evaluation.

        Useful for debugging and UI display.

        Returns:
            Dictionary with current time, day, and external provider states
        """
        now = self._now()
        current_hour = now.hour

        # Determine current time period
        current_period = None
        for period, (start, end) in self.TIME_PERIODS.items():
            if start <= end:
                if start <= current_hour < end:
                    current_period = period
                    break
            else:
                if current_hour >= start or current_hour < end:
                    current_period = period
                    break

        context = {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "day_of_week": now.weekday(),
            "day_name": now.strftime("%A"),
            "time_period": current_period,
            "hour": current_hour,
        }

        # Add external provider states
        for name, provider in self._external_providers.items():
            try:
                context[f"external_{name}"] = provider()
            except Exception as e:
                context[f"external_{name}"] = f"Error: {e}"

        return context
