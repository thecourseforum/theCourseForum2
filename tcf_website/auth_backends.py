"""Custom authentication backend for AWS Cognito."""

import json
import logging
import time
from urllib.request import urlopen

import jose.jwk
import jose.jwt
from jose.exceptions import JWKError
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class CognitoBackend:
    """
    Authentication backend for validating user against AWS Cognito
    """

    def authenticate(self, request, token=None):
        """
        Authenticate the user using the token provided by Cognito
        """
        if token is None:
            return None

        try:
            # Validate the token
            claims = self.validate_token(token)
            if not claims:
                return None

            # Get user info from the claims
            email = claims.get("email")
            username = email.split("@")[0]

            if not username:
                return None

            # Get or create the user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "computing_id": username,
                    "first_name": claims.get("given_name", ""),
                    "last_name": claims.get("family_name", ""),
                },
            )

            # Update user attributes if they've changed
            if not created:
                updated = False
                for attr, value in {
                    "email": email,
                    "computing_id": username,
                    "first_name": claims.get("given_name", user.first_name),
                    "last_name": claims.get("family_name", user.last_name),
                }.items():
                    if getattr(user, attr) != value:
                        setattr(user, attr, value)
                        updated = True

                if updated:
                    user.save()

            return user
        except (ValueError, jose.JWTError) as e:
            logger.exception("Error authenticating with Cognito: %s", str(e))
            return None

    def get_user(self, user_id):
        """
        Retrieve a user by their ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def validate_token(self, token):
        """
        Validate the JWT token from Cognito
        """
        # Get the JWKs from Cognito
        jwks_url = (
            f"https://cognito-idp.{settings.COGNITO_REGION_NAME}.amazonaws.com/"
            f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        )

        try:
            with urlopen(jwks_url) as response:
                jwks = json.loads(response.read())

            # Extract the key ID from the token
            headers = jose.jwt.get_unverified_header(token)
            kid = headers["kid"]

            # Find the matching key
            key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
            if not key:
                logger.warning("Matching key not found for kid %s", kid)
                return None

            # Construct the public key
            public_key = jose.jwk.construct(key)

            # Verify the token
            claims = jose.jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=settings.COGNITO_APP_CLIENT_ID,
                options={
                    "verify_at_hash": False,
                },
            )

            # Check if token is expired
            current_time = time.time()
            if current_time > claims["exp"]:
                logger.warning("Token has expired")
                return None

            return claims
        except (jose.JWTError, JWKError, KeyError, ValueError) as e:
            logger.exception("Error validating token: %s", str(e))
            return None
