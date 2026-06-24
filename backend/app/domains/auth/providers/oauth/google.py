"""
Google OAuth provider — STUB for future implementation.

FLOW:
  1. Client app uses Google Sign-In SDK → obtains id_token
  2. POST /auth/oauth/google { "id_token": "..." }
  3. This class verifies token with Google's JWKS
  4. AuthService finds or creates user, issues JWT

REQUIRED ENV:
  GOOGLE_OAUTH_ENABLED=true
  GOOGLE_CLIENT_ID=...
  GOOGLE_CLIENT_SECRET=...  (for server-side flows)
"""

from app.core.config import Settings
from app.domains.auth.providers.oauth.base import OAuthProvider, OAuthUserInfo
from app.domains.common.exceptions import DomainError


class GoogleOAuthProvider(OAuthProvider):
    """Verify Google ID tokens — scaffold only."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def provider_name(self) -> str:
        return "google"

    async def verify_id_token(self, id_token: str) -> OAuthUserInfo:
        if not self.settings.google_oauth_enabled:
            raise DomainError("Google OAuth is not enabled")

        raise NotImplementedError(
            "Google OAuth is scaffolded. "
            "Verify id_token against https://oauth2.googleapis.com/tokeninfo "
            "or use google-auth library."
        )