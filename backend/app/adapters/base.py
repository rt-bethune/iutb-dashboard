"""Base adapter interface."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseAdapter(ABC, Generic[T]):
    """
    Abstract base class for all data source adapters.
    
    Each adapter must implement methods to:
    - Connect/authenticate to the data source
    - Fetch raw data
    - Transform data to internal models
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the data source is available/configured."""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate to the data source if required.
        Returns True if authentication successful or not required.
        """
        pass
    
    @abstractmethod
    async def fetch_raw(self, **kwargs) -> Any:
        """
        Fetch raw data from the source.
        Returns data in the source's native format.
        """
        pass
    
    @abstractmethod
    def transform(self, raw_data: Any) -> T:
        """
        Transform raw data to internal model format.
        """
        pass
    
    async def get_data(self, **kwargs) -> T:
        """
        Main method to fetch and transform data.
        Handles authentication if needed.
        """
        if not await self.is_available():
            raise RuntimeError(f"Data source {self.source_name} is not available")
        
        await self.authenticate()
        raw_data = await self.fetch_raw(**kwargs)
        return self.transform(raw_data)


class FileAdapter(BaseAdapter[T]):
    """
    Base class for file-based adapters (Excel, CSV).
    """
    
    async def is_available(self) -> bool:
        """File adapters are always available."""
        return True
    
    async def authenticate(self) -> bool:
        """File adapters don't need authentication."""
        return True
    
    @abstractmethod
    def parse_file(self, file_content: bytes, filename: str) -> Any:
        """Parse uploaded file content."""
        pass
