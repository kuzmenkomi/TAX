# Central Registry for all LatAm countries
# This allows dynamic lookup and management of country implementations

from typing import Dict, Type, Optional, List, Any
from app.countries.base.definitions import BaseCountryDefinition


class CountryRegistry:
    """
    Central registry for all countries.
    
    This singleton pattern allows:
    - Auto-discovery of countries
    - Easy lookup by country code
    - Listing all supported countries
    - Dynamic registration of new countries
    
    No if/elif chains - pure plugin architecture!
    """

    _COUNTRIES: Dict[str, Type[BaseCountryDefinition]] = {}
    _INSTANCES: Dict[str, BaseCountryDefinition] = {}  # Cached instances

    @classmethod
    def register(
        cls,
        country_class: Type[BaseCountryDefinition],
        auto_instantiate: bool = True,
    ) -> None:
        """
        Register a new country.
        
        Args:
            country_class: Class implementing BaseCountryDefinition
            auto_instantiate: Create instance immediately?
        """
        code = country_class.country_code
        
        if code in cls._COUNTRIES:
            raise ValueError(f"Country {code} already registered")
        
        cls._COUNTRIES[code] = country_class
        
        if auto_instantiate:
            cls._INSTANCES[code] = country_class()

    @classmethod
    def get_country(cls, code: str) -> BaseCountryDefinition:
        """
        Get country instance by code.
        
        Args:
            code: Country code (e.g., "GT", "EC", "UY")
            
        Returns:
            Country instance
            
        Raises:
            ValueError: If country not registered
        """
        if code not in cls._COUNTRIES:
            available = ", ".join(cls.list_codes())
            raise ValueError(
                f"Country {code} not found. "
                f"Available: {available}"
            )
        
        # Return cached instance
        if code not in cls._INSTANCES:
            cls._INSTANCES[code] = cls._COUNTRIES[code]()
        
        return cls._INSTANCES[code]

    @classmethod
    def list_codes(cls) -> List[str]:
        """Get list of all registered country codes"""
        return sorted(cls._COUNTRIES.keys())

    @classmethod
    def list_all(cls) -> Dict[str, Dict[str, Any]]:
        """Get info for all registered countries"""
        return {
            code: cls.get_country(code).get_country_info()
            for code in cls.list_codes()
        }

    @classmethod
    def is_supported(cls, code: str) -> bool:
        """Check if country is supported"""
        return code in cls._COUNTRIES

    @classmethod
    def get_countries_by_region(cls, region: str) -> Dict[str, BaseCountryDefinition]:
        """Get all countries in a region"""
        return {
            code: cls.get_country(code)
            for code in cls.list_codes()
            if cls.get_country(code).country_region == region
        }

    @classmethod
    def get_countries_with_api(cls) -> Dict[str, BaseCountryDefinition]:
        """Get all countries that have tax authority APIs"""
        return {
            code: cls.get_country(code)
            for code in cls.list_codes()
            if cls.get_country(code).has_api
        }

    @classmethod
    def get_calculator(cls, code: str) -> Any:
        """
        Get country calculator instance by code.
        """
        # Ensure country is registered
        cls.get_country(code)
        
        # Dynamically import the calculator
        import importlib
        try:
            module_path = f"app.countries.{code.lower()}.calculator"
            module = importlib.import_module(module_path)
            calculator_class = getattr(module, "TaxCalculator")
            return calculator_class()
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Calculator not found for {code}: {str(e)}")

    @classmethod
    def reset(cls) -> None:
        """Clear registry (for testing)"""
        cls._COUNTRIES.clear()
        cls._INSTANCES.clear()
