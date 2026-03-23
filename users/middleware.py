from datetime import datetime, timedelta

from django.utils import timezone


class UpdateLastSeenMiddleware:
    SESSION_KEY = "plms_last_seen_ping"
    UPDATE_INTERVAL = timedelta(minutes=2)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return response

        now = timezone.now()
        last_ping = request.session.get(self.SESSION_KEY)
        if last_ping:
            try:
                ping_time = datetime.fromisoformat(last_ping)
                if timezone.is_naive(ping_time):
                    ping_time = timezone.make_aware(ping_time, timezone.get_current_timezone())
            except ValueError:
                ping_time = None
            if ping_time and (now - ping_time) < self.UPDATE_INTERVAL:
                return response

        user.__class__.objects.filter(pk=user.pk).update(last_seen_at=now)
        request.session[self.SESSION_KEY] = now.isoformat()
        return response
