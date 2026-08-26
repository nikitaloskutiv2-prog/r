from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 5
LOGIN_BLOCK_MINUTES = 15

MAX_REGISTRATIONS_PER_HOUR = 3
REGISTRATION_WINDOW_HOURS = 1

failed_logins: dict[str, dict] = {}

registration_attempts: dict[str, list[datetime]] = {}

def check_login_block(ip: str) -> bool:
    data = failed_logins.get(ip)

    if not data:
        return False

    blocked_until = data.get("blocked_until")

    if blocked_until is None:
        return False

    now = datetime.utcnow()

    if now >= blocked_until:
        failed_logins.pop(ip, None)

        logger.info(
            "Login block expired: ip=%s",
            ip,
        )

        return False

    logger.warning(
        "Blocked login attempt: ip=%s blocked_until=%s",
        ip,
        blocked_until,
    )

    return True


def register_failed_login(ip: str) -> None:
    now = datetime.utcnow()

    data = failed_logins.get(
        ip,
        {
            "count": 0,
            "blocked_until": None,
        },
    )

    data["count"] += 1

    if data["count"] >= MAX_LOGIN_ATTEMPTS:
        blocked_until = (
            now +
            timedelta(minutes=LOGIN_BLOCK_MINUTES)
        )

        data["blocked_until"] = blocked_until

        logger.warning(
            "Login brute-force protection triggered: "
            "ip=%s attempts=%s blocked_until=%s",
            ip,
            data["count"],
            blocked_until,
        )

    failed_logins[ip] = data


def reset_login_attempts(ip: str) -> None:
    if ip in failed_logins:
        failed_logins.pop(ip, None)

        logger.info(
            "Login attempts reset after successful login: ip=%s",
            ip,
        )


def get_login_block_remaining(ip: str) -> int:
    data = failed_logins.get(ip)

    if not data:
        return 0

    blocked_until = data.get("blocked_until")

    if blocked_until is None:
        return 0

    remaining = (
        blocked_until -
        datetime.utcnow()
    ).total_seconds()

    if remaining <= 0:
        failed_logins.pop(ip, None)
        return 0

    return int(remaining)


def _cleanup_registration_attempts(ip: str) -> list[datetime]:
    now = datetime.utcnow()

    window_start = (
        now -
        timedelta(hours=REGISTRATION_WINDOW_HOURS)
    )

    attempts = registration_attempts.get(ip, [])

    attempts = [
        attempt
        for attempt in attempts
        if attempt > window_start
    ]

    if attempts:
        registration_attempts[ip] = attempts
    else:
        registration_attempts.pop(ip, None)

    return attempts


def check_registration_limit(ip: str) -> bool:
    attempts = _cleanup_registration_attempts(ip)

    if len(attempts) >= MAX_REGISTRATIONS_PER_HOUR:
        logger.warning(
            "Registration rate limit exceeded: "
            "ip=%s attempts=%s limit=%s",
            ip,
            len(attempts),
            MAX_REGISTRATIONS_PER_HOUR,
        )

        return True

    return False


def register_registration_attempt(ip: str) -> None:
    attempts = _cleanup_registration_attempts(ip)

    attempts.append(datetime.utcnow())

    registration_attempts[ip] = attempts

    logger.info(
        "Registration attempt recorded: ip=%s attempts_last_hour=%s",
        ip,
        len(attempts),
    )


def get_registration_count(ip: str) -> int:
    attempts = _cleanup_registration_attempts(ip)

    return len(attempts)


def check_login_rate_limit(ip: str, login: str) -> bool:
    return not check_login_block(ip)


def record_failed_login(ip: str, login: str) -> None:
    register_failed_login(ip)


def reset_login_rate_limit(ip: str, login: str) -> None:
    reset_login_attempts(ip)


def check_register_rate_limit(ip: str) -> bool:
    return not check_registration_limit(ip)


def record_registration(ip: str) -> None:
    register_registration_attempt(ip)