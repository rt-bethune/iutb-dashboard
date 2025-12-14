"""CAS (Central Authentication Service) adapter.

Implements CAS protocol for university SSO authentication.
Example: https://sso.univ-artois.fr/cas/
"""

import httpx
from typing import Optional, Any
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class CASAdapter:
    """
    CAS Protocol adapter for university authentication.
    
    CAS Flow:
    1. User visits protected page
    2. Redirect to CAS login: {cas_url}/login?service={callback_url}
    3. User authenticates with CAS
    4. CAS redirects back with ticket: {callback_url}?ticket=xxx
    5. Server validates ticket: GET {cas_url}/serviceValidate?ticket=xxx&service={callback_url}
    6. CAS returns XML with user info
    """
    
    def __init__(
        self,
        cas_url: str,
        service_url: str,
    ):
        """
        Initialize CAS adapter.
        
        Args:
            cas_url: CAS server URL (e.g., https://sso.univ-artois.fr/cas)
            service_url: Our service callback URL
        """
        self.cas_url = cas_url.rstrip('/')
        self.service_url = service_url
        self.client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        return self.client
    
    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    def get_login_url(self, return_url: Optional[str] = None) -> str:
        """
        Get CAS login URL for redirect.
        
        Args:
            return_url: Optional URL to return to after auth (encoded in service URL)
        
        Returns:
            Full CAS login URL with service parameter
        """
        service = self.service_url
        if return_url:
            service = f"{service}?return_url={return_url}"
        
        params = urlencode({'service': service})
        return f"{self.cas_url}/login?{params}"
    
    def get_logout_url(self, return_url: Optional[str] = None) -> str:
        """
        Get CAS logout URL.
        
        Args:
            return_url: Optional URL to redirect after logout
        
        Returns:
            CAS logout URL
        """
        if return_url:
            params = urlencode({'service': return_url})
            return f"{self.cas_url}/logout?{params}"
        return f"{self.cas_url}/logout"
    
    async def validate_ticket(self, ticket: str) -> Optional[dict[str, Any]]:
        """
        Validate CAS ticket and get user info.
        
        Args:
            ticket: CAS ticket from callback
        
        Returns:
            User info dict with 'user' key if valid, None if invalid
            {
                'user': 'username',
                'attributes': {
                    'email': 'user@example.com',
                    'displayName': 'John Doe',
                    ...
                }
            }
        """
        client = await self._get_client()
        
        # CAS 2.0/3.0 service validation endpoint
        validate_url = f"{self.cas_url}/serviceValidate"
        params = {
            'ticket': ticket,
            'service': self.service_url,
        }
        
        try:
            response = await client.get(validate_url, params=params)
            response.raise_for_status()
            
            return self._parse_cas_response(response.text)
            
        except httpx.HTTPError as e:
            logger.error(f"CAS validation error: {e}")
            return None
    
    def _parse_cas_response(self, xml_text: str) -> Optional[dict[str, Any]]:
        """
        Parse CAS XML response.
        
        CAS 2.0 success response:
        <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
            <cas:authenticationSuccess>
                <cas:user>username</cas:user>
                <cas:attributes>
                    <cas:email>user@example.com</cas:email>
                    <cas:displayName>John Doe</cas:displayName>
                </cas:attributes>
            </cas:authenticationSuccess>
        </cas:serviceResponse>
        
        CAS 2.0 failure response:
        <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
            <cas:authenticationFailure code="INVALID_TICKET">
                Ticket not recognized
            </cas:authenticationFailure>
        </cas:serviceResponse>
        """
        try:
            # Handle CAS namespace
            namespaces = {'cas': 'http://www.yale.edu/tp/cas'}
            root = ET.fromstring(xml_text)
            
            # Check for authentication failure
            failure = root.find('.//cas:authenticationFailure', namespaces)
            if failure is not None:
                code = failure.get('code', 'UNKNOWN')
                message = failure.text.strip() if failure.text else ''
                logger.warning(f"CAS authentication failed: {code} - {message}")
                return None
            
            # Check for authentication success
            success = root.find('.//cas:authenticationSuccess', namespaces)
            if success is None:
                logger.error("CAS response has no authenticationSuccess element")
                return None
            
            # Get username
            user_elem = success.find('cas:user', namespaces)
            if user_elem is None or not user_elem.text:
                logger.error("CAS response has no user element")
                return None
            
            result = {
                'user': user_elem.text.strip(),
                'attributes': {}
            }
            
            # Get attributes (CAS 3.0)
            attributes = success.find('cas:attributes', namespaces)
            if attributes is not None:
                for attr in attributes:
                    # Remove namespace prefix from tag
                    tag = attr.tag.split('}')[-1] if '}' in attr.tag else attr.tag
                    result['attributes'][tag] = attr.text.strip() if attr.text else ''
            
            logger.info(f"CAS authentication successful for user: {result['user']}")
            return result
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse CAS XML response: {e}")
            return None


class MockCASAdapter(CASAdapter):
    """Mock CAS adapter for development/testing."""
    
    def __init__(self, cas_url: str = "https://mock-cas.local", service_url: str = "http://localhost:8000"):
        super().__init__(cas_url, service_url)
        self._mock_users = {
            'admin': {'email': 'admin@univ.fr', 'displayName': 'Admin User', 'role': 'admin'},
            'teacher1': {'email': 'teacher1@univ.fr', 'displayName': 'Jean Dupont', 'role': 'teacher'},
            'teacher2': {'email': 'teacher2@univ.fr', 'displayName': 'Marie Martin', 'role': 'teacher'},
        }
    
    async def validate_ticket(self, ticket: str) -> Optional[dict[str, Any]]:
        """
        Mock ticket validation.
        
        Ticket format for mock: "mock-ticket-{username}"
        """
        if not ticket.startswith('mock-ticket-'):
            return None
        
        username = ticket.replace('mock-ticket-', '')
        
        if username in self._mock_users:
            return {
                'user': username,
                'attributes': self._mock_users[username]
            }
        
        # Accept any username for development
        return {
            'user': username,
            'attributes': {
                'email': f'{username}@univ.fr',
                'displayName': username.title(),
            }
        }


def get_cas_adapter(cas_url: str, service_url: str, use_mock: bool = False) -> CASAdapter:
    """
    Factory function to get CAS adapter.
    
    Args:
        cas_url: CAS server URL
        service_url: Our callback URL
        use_mock: Use mock adapter for development
    
    Returns:
        CAS adapter instance
    """
    if use_mock:
        return MockCASAdapter(cas_url, service_url)
    return CASAdapter(cas_url, service_url)
