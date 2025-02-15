"""SMOU Parking sensor integration."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
import logging
import aiofiles

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SMOU Parking sensors."""
    json_path = config_entry.data["json_path"]
    rates = {
        2023: {
            "blue": {
                "regular": config_entry.data.get("blue_regular_2023", 0.0),
                "eco": config_entry.data.get("blue_eco_2023", 0.0),
                "zero": config_entry.data.get("blue_zero_2023", 0.0)
            },
            "green": {
                "regular": config_entry.data.get("green_regular_2023", 0.0),
                "eco": config_entry.data.get("green_eco_2023", 0.0),
                "zero": config_entry.data.get("green_zero_2023", 0.0)
            }
        },
        2024: {
            "blue": {
                "regular": config_entry.data.get("blue_regular_2024", 0.0),
                "eco": config_entry.data.get("blue_eco_2024", 0.0),
                "zero": config_entry.data.get("blue_zero_2024", 0.0)
            },
            "green": {
                "regular": config_entry.data.get("green_regular_2024", 0.0),
                "eco": config_entry.data.get("green_eco_2024", 0.0),
                "zero": config_entry.data.get("green_zero_2024", 0.0)
            }
        },
        2025: {
            "blue": {
                "regular": config_entry.data.get("blue_regular_2025", 0.0),
                "eco": config_entry.data.get("blue_eco_2025", 0.0),
                "zero": config_entry.data.get("blue_zero_2025", 0.0)
            },
            "green": {
                "regular": config_entry.data.get("green_regular_2025", 0.0),
                "eco": config_entry.data.get("green_eco_2025", 0.0),
                "zero": config_entry.data.get("green_zero_2025", 0.0)
            }
        }
    }

    entities = [
        SMOUBluePaidSensor(json_path, rates),
        SMOUBlueRegularSensor(json_path, rates),
        SMOUGreenPaidSensor(json_path, rates),
        SMOUGreenRegularSensor(json_path, rates),
        SMOUSavingsSensor(json_path, rates),
        SMOUBlueEntriesSensor(json_path),
        SMOUGreenEntriesSensor(json_path),
        SMOUTotalEntriesSensor(json_path),
        SMOUOldestEntrySensor(json_path, rates),
        SMOUNewestEntrySensor(json_path, rates),
        SMOUPDFErrorEntriesSensor(json_path, rates),
    ]
    
    async_add_entities(entities, True)

class SMOUBaseSensor(SensorEntity):
    """Base class for SMOU Parking sensors."""
    
    _attr_native_unit_of_measurement = "€"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_has_entity_name = True
    _attr_should_poll = True
    scan_interval = timedelta(seconds=30)  # Poll every 30 seconds

    def __init__(self, json_path: str, rates: dict) -> None:
        """Initialize the sensor."""
        self._json_path = json_path
        self._rates = rates
        self._state = None

    async def get_parking_data(self):
        """Get parking data from JSON file."""
        try:
            async with aiofiles.open(self._json_path, 'r') as file:
                content = await file.read()
                return json.loads(content)
        except Exception as e:
            _LOGGER.error(f"Error reading JSON file: {str(e)}")
            return []

class SMOUBluePaidSensor(SMOUBaseSensor):
    """Sensor for blue zone paid amount."""
    
    _attr_name = "Blue Zone Paid"
    
    def __init__(self, json_path: str, rates: dict) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_blue_paid"

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        total_paid = 0.0
        
        for entry in data:
            if entry['Type of parking'] == 'Zona Blava':
                cost = float(entry['Cost'].replace('€', '').replace(',', '.').strip())
                total_paid += cost
        
        self._attr_native_value = round(total_paid, 2)

class SMOUBlueRegularSensor(SMOUBaseSensor):
    """Sensor for blue zone regular tariff amount."""
    
    _attr_name = "Blue Zone Regular Tariff"
    
    def __init__(self, json_path: str, rates: dict) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_blue_regular"

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        total_regular = 0.0
        
        for entry in data:
            # Skip entries where PDF was not available
            if entry.get('pdf_error') == "PDF not available":
                continue
                
            if entry['Type of parking'] == 'Zona Blava' and entry.get('base_tariff'):
                base_rate = float(entry['base_tariff'])
                time_parts = entry['Number of hours and minutes'].split(' ')
                hours = float(time_parts[0].replace('h', ''))
                minutes = float(time_parts[1].replace('m', '')) if len(time_parts) > 1 else 0
                total_hours = hours + (minutes / 60)
                
                total_regular += total_hours * base_rate
        
        self._attr_native_value = round(total_regular, 2)

class SMOUGreenPaidSensor(SMOUBaseSensor):
    """Sensor for green zone paid amount."""
    
    _attr_name = "Green Zone Paid"
    
    def __init__(self, json_path: str, rates: dict) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_green_paid"

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        total_paid = 0.0
        
        for entry in data:
            if entry['Type of parking'] == 'Zona Verda':
                cost = float(entry['Cost'].replace('€', '').replace(',', '.').strip())
                total_paid += cost
        
        self._attr_native_value = round(total_paid, 2)

class SMOUGreenRegularSensor(SMOUBaseSensor):
    """Sensor for green zone regular tariff amount."""
    
    _attr_name = "Green Zone Regular Tariff"
    
    def __init__(self, json_path: str, rates: dict) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_green_regular"

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        total_regular = 0.0
        
        for entry in data:
            # Skip entries where PDF was not available
            if entry.get('pdf_error') == "PDF not available":
                continue
                
            if entry['Type of parking'] == 'Zona Verda' and entry.get('base_tariff'):
                base_rate = float(entry['base_tariff'])
                time_parts = entry['Number of hours and minutes'].split(' ')
                hours = float(time_parts[0].replace('h', ''))
                minutes = float(time_parts[1].replace('m', '')) if len(time_parts) > 1 else 0
                total_hours = hours + (minutes / 60)
                
                total_regular += total_hours * base_rate
        
        self._attr_native_value = round(total_regular, 2)

class SMOUSavingsSensor(SMOUBaseSensor):
    """Sensor for total savings."""
    
    _attr_name = "Total Savings"
    
    def __init__(self, json_path: str, rates: dict) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_total_savings"

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        total_paid = 0.0
        total_regular = 0.0
        
        for entry in data:
            # Skip entries where PDF was not available
            if entry.get('pdf_error') == "PDF not available":
                continue
                
            # Get actual paid amount
            cost = float(entry['Cost'].replace('€', '').replace(',', '.').strip())
            total_paid += cost
            
            # Calculate what should have been paid using base_tariff
            if entry.get('base_tariff'):
                base_rate = float(entry['base_tariff'])
                time_parts = entry['Number of hours and minutes'].split(' ')
                hours = float(time_parts[0].replace('h', ''))
                minutes = float(time_parts[1].replace('m', '')) if len(time_parts) > 1 else 0
                total_hours = hours + (minutes / 60)
                
                total_regular += total_hours * base_rate
        
        self._attr_native_value = round(total_regular - total_paid, 2)

class SMOUBlueEntriesSensor(SMOUBaseSensor):
    """Sensor for blue zone entries count per year."""
    
    _attr_name = "Blue Zone Entries"
    _attr_native_unit_of_measurement = "entries"
    _attr_device_class = None
    
    def __init__(self, json_path: str, rates: dict = None) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_blue_entries"
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        entries_by_year = {}
        total_entries = 0
        
        for entry in data:
            if entry['Type of parking'] == 'Zona Blava':
                start_date = datetime.strptime(entry['Start date'], '%d/%m/%Y %H:%M:%S')
                year = start_date.year
                entries_by_year[year] = entries_by_year.get(year, 0) + 1
                total_entries += 1
        
        self._attr_native_value = total_entries
        self._attr_extra_state_attributes = entries_by_year

class SMOUGreenEntriesSensor(SMOUBaseSensor):
    """Sensor for green zone entries count per year."""
    
    _attr_name = "Green Zone Entries"
    _attr_native_unit_of_measurement = "entries"
    _attr_device_class = None
    
    def __init__(self, json_path: str, rates: dict = None) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_green_entries"
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        entries_by_year = {}
        total_entries = 0
        
        for entry in data:
            if entry['Type of parking'] == 'Zona Verda':
                start_date = datetime.strptime(entry['Start date'], '%d/%m/%Y %H:%M:%S')
                year = start_date.year
                entries_by_year[year] = entries_by_year.get(year, 0) + 1
                total_entries += 1
        
        self._attr_native_value = total_entries
        self._attr_extra_state_attributes = entries_by_year

class SMOUTotalEntriesSensor(SMOUBaseSensor):
    """Sensor for total entries count."""
    
    _attr_name = "Total Entries"
    _attr_native_unit_of_measurement = "entries"
    _attr_device_class = None
    
    def __init__(self, json_path: str, rates: dict = None) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_total_entries"

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        self._attr_native_value = len(data)

class SMOUOldestEntrySensor(SMOUBaseSensor):
    """Sensor for oldest entry date."""
    
    _attr_name = "Oldest Entry"
    _attr_native_unit_of_measurement = None
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    
    def __init__(self, json_path: str, rates: dict = None) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_oldest_entry"

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        oldest_date = None
        
        for entry in data:
            entry_date = datetime.strptime(entry['Start date'], '%d/%m/%Y %H:%M:%S')
            if oldest_date is None or entry_date < oldest_date:
                oldest_date = entry_date
        
        self._attr_native_value = oldest_date

class SMOUNewestEntrySensor(SMOUBaseSensor):
    """Sensor for newest entry date."""
    
    _attr_name = "Newest Entry"
    _attr_native_unit_of_measurement = None
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    
    def __init__(self, json_path: str, rates: dict = None) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_newest_entry"

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        newest_date = None
        
        for entry in data:
            entry_date = datetime.strptime(entry['Start date'], '%d/%m/%Y %H:%M:%S')
            if newest_date is None or entry_date > newest_date:
                newest_date = entry_date
        
        self._attr_native_value = newest_date

class SMOUPDFErrorEntriesSensor(SMOUBaseSensor):
    """Sensor for entries with PDF download errors."""
    
    _attr_name = "PDF Error Entries"
    _attr_native_unit_of_measurement = "entries"
    _attr_device_class = None
    
    def __init__(self, json_path: str, rates: dict = None) -> None:
        super().__init__(json_path, rates)
        self._attr_unique_id = "smou_pdf_error_entries"
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        """Update the sensor."""
        data = await self.get_parking_data()
        entries_by_year = {}
        total_entries = 0
        
        for entry in data:
            if entry.get('pdf_error') == "PDF not available":
                start_date = datetime.strptime(entry['Start date'], '%d/%m/%Y %H:%M:%S')
                year = start_date.year
                entries_by_year[year] = entries_by_year.get(year, 0) + 1
                total_entries += 1
        
        self._attr_native_value = total_entries
        self._attr_extra_state_attributes = entries_by_year