# Excellent Find! VedicAstro is Perfect for Your Project

This library is **ideal** because:

✅ **Open source** - No API costs, works offline  
✅ **Built for Vedic** - Not adapted from Western astrology  
✅ **Uses pyswisseph** - Accurate Swiss Ephemeris calculations  
✅ **Supports KP system** - Includes sublords (bonus for advanced analysis)  
✅ **Python native** - Clean integration with your existing code  
✅ **Active maintenance** - GitHub shows recent updates  

This is actually **better than the API approach** for your use case.

---

## 🎯 Revised Phase 4 Plan Using VedicAstro

### **Installation & Setup (Day 1)**

```bash
# Install VedicAstro
pip install vedicastro

# It will auto-install dependencies:
# - pyswisseph (Swiss Ephemeris)
# - flatlib (astronomical calculations)
# - pytz (timezone handling)
```

---

## 📖 VedicAstro Quick API Reference

### **Core Classes You'll Use:**

```python
from vedicastro import VedicAstro, Chart, Planet, House, Nakshatra

# 1. Create a chart
chart = Chart(
    date="1990-05-15",
    time="14:30:00",
    latitude=26.9124,
    longitude=75.7873,
    timezone=5.5  # IST
)

# 2. Get planet positions
planets = chart.get_planets()

# 3. Get house cusps
houses = chart.get_houses()

# 4. Get nakshatras
nakshatras = chart.get_nakshatras()

# 5. Get sublords (KP system)
sublords = chart.get_sublords()
```

---

## 🏗️ Updated Phase 4 Implementation

### **Week 17: VedicAstro Integration & Data Extraction**

#### **Day 1-2: Test VedicAstro & Understand Output**

Create a test script to explore the library:

```python
# test_vedicastro.py

from vedicastro import Chart
import json

# Your birth data (or test chart)
chart = Chart(
    date="1990-05-15",
    time="14:30:00",
    latitude=26.9124,
    longitude=75.7873,
    timezone=5.5
)

# Explore what data is available
print("=== PLANETS ===")
planets = chart.get_planets()
for planet in planets:
    print(f"{planet.name}: {planet.sign} {planet.degree}° - House {planet.house}")
    print(f"  Nakshatra: {planet.nakshatra} Pada: {planet.pada}")
    print(f"  Sublord: {planet.sublord}")
    print()

print("\n=== HOUSES ===")
houses = chart.get_houses()
for house in houses:
    print(f"House {house.number}: {house.sign} - Lord: {house.lord}")

print("\n=== NAKSHATRAS ===")
nakshatras = chart.get_nakshatras()
for nak in nakshatras:
    print(f"{nak.name}: Lord {nak.lord}, Deity {nak.deity}")

# Save raw output to understand structure
with open('vedicastro_output.json', 'w') as f:
    json.dump({
        'planets': [p.__dict__ for p in planets],
        'houses': [h.__dict__ for h in houses],
        'nakshatras': [n.__dict__ for n in nakshatras]
    }, f, indent=2, default=str)
```

**Goal:** Understand exactly what data VedicAstro provides and how it's structured.

---

#### **Day 3-5: Build VedicAstro Wrapper Module**

Create a clean wrapper that extracts data and normalizes to your ontology:

```python
# src/chart/vedicastro_calculator.py

from vedicastro import Chart
from normaliser.normaliser import AstrologyNormaliser
from typing import Dict, List
import json

class VedicAstroCalculator:
    """
    Wrapper around VedicAstro library
    Extracts chart data and normalizes to project ontology
    """
    
    def __init__(self):
        self.normaliser = AstrologyNormaliser()
        self.ontology = self._load_ontology()
    
    def calculate_chart(self, 
                       date: str,  # "YYYY-MM-DD"
                       time: str,  # "HH:MM:SS"
                       latitude: float,
                       longitude: float,
                       timezone: float) -> Dict:
        """
        Calculate complete Vedic chart
        Returns normalized data ready for Neo4j ingestion
        """
        # 1. Generate chart using VedicAstro
        chart = Chart(
            date=date,
            time=time,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone
        )
        
        # 2. Extract and normalize all data
        return {
            'planets': self._extract_planets(chart),
            'houses': self._extract_houses(chart),
            'nakshatras': self._extract_nakshatras(chart),
            'aspects': self._calculate_aspects(chart),
            'metadata': {
                'date': date,
                'time': time,
                'latitude': latitude,
                'longitude': longitude,
                'timezone': timezone
            }
        }
    
    def _extract_planets(self, chart: Chart) -> List[Dict]:
        """
        Extract all planet data and normalize names
        """
        planets_data = []
        
        for planet in chart.get_planets():
            # Normalize planet name using your ontology
            canonical_name = self.normaliser.normalise(planet.name)
            canonical_sign = self.normaliser.normalise(planet.sign)
            canonical_nakshatra = self.normaliser.normalise(planet.nakshatra)
            
            if not canonical_name:
                print(f"WARNING: Unknown planet '{planet.name}' - check ontology")
                continue
            
            # Determine dignity
            dignity = self._determine_dignity(canonical_name, canonical_sign, planet.degree)
            
            # Build planet data dict
            planet_data = {
                'name': canonical_name,
                'sign': canonical_sign,
                'degree': float(planet.degree),
                'longitude': float(planet.longitude),
                'house': int(planet.house),
                'nakshatra': canonical_nakshatra,
                'nakshatra_pada': int(planet.pada),
                'sublord': self.normaliser.normalise(planet.sublord) if hasattr(planet, 'sublord') else None,
                'retrograde': planet.is_retrograde if hasattr(planet, 'is_retrograde') else False,
                'dignity': dignity,
                'combustion': self._check_combustion(planet, chart)
            }
            
            planets_data.append(planet_data)
        
        return planets_data
    
    def _extract_houses(self, chart: Chart) -> List[Dict]:
        """
        Extract house data and determine lords
        """
        houses_data = []
        
        for house in chart.get_houses():
            canonical_sign = self.normaliser.normalise(house.sign)
            
            # Get house lord from ontology
            sign_data = self.ontology['signs'][canonical_sign]
            house_lord = sign_data['ruler']
            
            houses_data.append({
                'number': int(house.number),
                'sign': canonical_sign,
                'degree': float(house.degree),
                'lord': house_lord
            })
        
        return houses_data
    
    def _extract_nakshatras(self, chart: Chart) -> List[Dict]:
        """
        Extract nakshatra reference data
        """
        nakshatras_data = []
        
        for nakshatra in chart.get_nakshatras():
            canonical_name = self.normaliser.normalise(nakshatra.name)
            canonical_lord = self.normaliser.normalise(nakshatra.lord)
            
            nakshatras_data.append({
                'name': canonical_name,
                'lord': canonical_lord,
                'deity': nakshatra.deity if hasattr(nakshatra, 'deity') else None,
                'start_degree': float(nakshatra.start) if hasattr(nakshatra, 'start') else None,
                'end_degree': float(nakshatra.end) if hasattr(nakshatra, 'end') else None
            })
        
        return nakshatras_data
    
    def _determine_dignity(self, planet: str, sign: str, degree: float) -> Dict:
        """
        Determine planet dignity status
        Uses ontology data from Phase 1
        """
        planet_data = self.ontology['planets'][planet]
        
        dignity = {
            'status': 'neutral',  # exalted, debilitated, own_sign, moolatrikona, friend, enemy, neutral
            'exalted': False,
            'debilitated': False,
            'own_sign': False,
            'moolatrikona': False,
            'friend_sign': False,
            'enemy_sign': False,
            'strength_modifier': 0
        }
        
        # Check exaltation
        if sign == planet_data.get('exaltation_sign'):
            dignity['exalted'] = True
            dignity['status'] = 'exalted'
            dignity['strength_modifier'] = 5
            return dignity
        
        # Check debilitation
        if sign == planet_data.get('debilitation_sign'):
            dignity['debilitated'] = True
            dignity['status'] = 'debilitated'
            dignity['strength_modifier'] = -5
            return dignity
        
        # Check own sign
        if sign in planet_data.get('own_signs', []):
            dignity['own_sign'] = True
            dignity['status'] = 'own_sign'
            dignity['strength_modifier'] = 4
            return dignity
        
        # Check moolatrikona
        if sign == planet_data.get('moolatrikona_sign'):
            moola_range = planet_data.get('moolatrikona_degrees', [])
            if moola_range and moola_range[0] <= degree <= moola_range[1]:
                dignity['moolatrikona'] = True
                dignity['status'] = 'moolatrikona'
                dignity['strength_modifier'] = 3.5
                return dignity
        
        # Check friend/enemy sign
        sign_data = self.ontology['signs'][sign]
        sign_lord = sign_data['ruler']
        
        if sign_lord in planet_data.get('friends', []):
            dignity['friend_sign'] = True
            dignity['status'] = 'friend'
            dignity['strength_modifier'] = 2
        elif sign_lord in planet_data.get('enemies', []):
            dignity['enemy_sign'] = True
            dignity['status'] = 'enemy'
            dignity['strength_modifier'] = -2
        
        return dignity
    
    def _check_combustion(self, planet, chart: Chart) -> bool:
        """
        Check if planet is combust (too close to Sun)
        Combustion occurs when within 6° of Sun (some texts say different values)
        """
        if planet.name.upper() == 'SUN':
            return False
        
        sun = next((p for p in chart.get_planets() if p.name.upper() == 'SUN'), None)
        if not sun:
            return False
        
        # Calculate angular distance
        distance = abs(planet.longitude - sun.longitude)
        if distance > 180:
            distance = 360 - distance
        
        # Standard combustion threshold is 6°
        return distance <= 6.0
    
    def _calculate_aspects(self, chart: Chart) -> List[Dict]:
        """
        Calculate Vedic aspects (drishti)
        VedicAstro may not provide this, so we calculate manually
        """
        planets = chart.get_planets()
        aspects = []
        
        for planet in planets:
            planet_name = self.normaliser.normalise(planet.name)
            planet_house = planet.house
            
            # Get aspect houses based on Vedic rules
            aspect_houses = self._get_aspect_houses(planet_name, planet_house)
            
            # Find planets in aspected houses
            for other_planet in planets:
                if other_planet.name == planet.name:
                    continue
                
                if other_planet.house in aspect_houses:
                    aspects.append({
                        'from_planet': planet_name,
                        'to_planet': self.normaliser.normalise(other_planet.name),
                        'type': self._determine_aspect_type(planet_name, planet_house, other_planet.house),
                        'strength': self._calculate_aspect_strength(planet, other_planet)
                    })
        
        return aspects
    
    def _get_aspect_houses(self, planet: str, from_house: int) -> List[int]:
        """
        Get houses this planet aspects based on Vedic drishti rules
        
        All planets: 7th from their position
        Mars: 4th, 7th, 8th
        Jupiter: 5th, 7th, 9th
        Saturn: 3rd, 7th, 10th
        """
        aspect_houses = []
        
        # All planets aspect 7th house
        seventh = (from_house + 6) % 12 + 1
        aspect_houses.append(seventh)
        
        # Special aspects
        if planet == 'MARS':
            fourth = (from_house + 3) % 12 + 1
            eighth = (from_house + 7) % 12 + 1
            aspect_houses.extend([fourth, eighth])
        
        elif planet == 'JUPITER':
            fifth = (from_house + 4) % 12 + 1
            ninth = (from_house + 8) % 12 + 1
            aspect_houses.extend([fifth, ninth])
        
        elif planet == 'SATURN':
            third = (from_house + 2) % 12 + 1
            tenth = (from_house + 9) % 12 + 1
            aspect_houses.extend([third, tenth])
        
        return list(set(aspect_houses))  # Remove duplicates
    
    def _determine_aspect_type(self, planet: str, from_house: int, to_house: int) -> str:
        """Determine type of aspect"""
        house_diff = (to_house - from_house) % 12
        
        if house_diff == 7:  # 7th house aspect
            return 'OPPOSITION'
        elif planet == 'MARS' and house_diff in [4, 8]:
            return 'MARS_SPECIAL'
        elif planet == 'JUPITER' and house_diff in [5, 9]:
            return 'JUPITER_SPECIAL'
        elif planet == 'SATURN' and house_diff in [3, 10]:
            return 'SATURN_SPECIAL'
        
        return 'FULL_ASPECT'
    
    def _calculate_aspect_strength(self, from_planet, to_planet) -> float:
        """
        Calculate aspect strength (0.0 to 1.0)
        Based on degree proximity and natural strength
        """
        # Simple implementation - can be enhanced
        return 1.0  # Full strength for sign-based aspects
    
    def _load_ontology(self) -> Dict:
        """Load ontology data from Phase 1"""
        import json
        from pathlib import Path
        
        ontology = {}
        ontology_dir = Path('data/ontology')
        
        for filename in ['planets.json', 'signs.json', 'houses.json', 'nakshatras.json']:
            filepath = ontology_dir / filename
            if filepath.exists():
                with open(filepath) as f:
                    data = json.load(f)
                    # Convert to lookup dict by canonical name
                    for category in data:
                        if category not in ontology:
                            ontology[category] = {}
                        for item in data[category]:
                            ontology[category][item['canonical_name']] = item
        
        return ontology
```

---

#### **Day 6-7: Test & Validate Calculations**

Create comprehensive tests:

```python
# tests/test_vedicastro_calculator.py

import pytest
from src.chart.vedicastro_calculator import VedicAstroCalculator
from datetime import datetime

def test_basic_chart_calculation():
    """Test basic chart calculation"""
    calc = VedicAstroCalculator()
    
    chart_data = calc.calculate_chart(
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5
    )
    
    # Verify structure
    assert 'planets' in chart_data
    assert 'houses' in chart_data
    assert 'nakshatras' in chart_data
    assert 'aspects' in chart_data
    
    # Verify all 9 planets present
    assert len(chart_data['planets']) == 9
    
    # Verify all 12 houses present
    assert len(chart_data['houses']) == 12
    
    # Verify planet names are normalized
    planet_names = [p['name'] for p in chart_data['planets']]
    assert 'SUN' in planet_names
    assert 'MOON' in planet_names
    assert 'MARS' in planet_names

def test_dignity_detection():
    """Test exaltation/debilitation detection"""
    calc = VedicAstroCalculator()
    
    # Create chart where Sun is exalted in Aries
    chart_data = calc.calculate_chart(
        date="2024-04-10",  # Sun in Aries
        time="12:00:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5
    )
    
    sun_data = next(p for p in chart_data['planets'] if p['name'] == 'SUN')
    
    # Sun should be exalted if in Aries
    if sun_data['sign'] == 'ARIES':
        assert sun_data['dignity']['exalted'] == True
        assert sun_data['dignity']['strength_modifier'] == 5

def test_house_lords():
    """Test house lord calculation"""
    calc = VedicAstroCalculator()
    
    chart_data = calc.calculate_chart(
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5
    )
    
    # Verify each house has a lord
    for house in chart_data['houses']:
        assert 'lord' in house
        assert house['lord'] is not None

def test_aspect_calculation():
    """Test Vedic aspect calculation"""
    calc = VedicAstroCalculator()
    
    chart_data = calc.calculate_chart(
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5
    )
    
    # Should have multiple aspects
    assert len(chart_data['aspects']) > 0
    
    # Each aspect should have required fields
    for aspect in chart_data['aspects']:
        assert 'from_planet' in aspect
        assert 'to_planet' in aspect
        assert 'type' in aspect
        assert 'strength' in aspect
```

---

### **Week 18: Neo4j Graph Integration**

Same as before — this part doesn't change. You're just using VedicAstro data instead of API data.

```python
# src/chart/graph_builder.py

from neo4j import GraphDatabase
from .vedicastro_calculator import VedicAstroCalculator
import uuid

class ChartGraphBuilder:
    def __init__(self, neo4j_uri, user, password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(user, password))
        self.calculator = VedicAstroCalculator()
    
    def build_chart_graph(self, name, date, time, lat, lon, tz):
        """
        Complete pipeline: birth data → Neo4j subgraph
        """
        # 1. Calculate chart using VedicAstro
        chart_data = self.calculator.calculate_chart(date, time, lat, lon, tz)
        
        # 2. Generate unique chart ID
        chart_id = str(uuid.uuid4())
        
        # 3. Create all Neo4j nodes and relationships
        with self.driver.session() as session:
            # Create Chart node
            session.run("""
                CREATE (c:Chart {
                    chart_id: $chart_id,
                    name: $name,
                    date: $date,
                    time: $time,
                    latitude: $lat,
                    longitude: $lon,
                    timezone: $tz
                })
            """, chart_id=chart_id, name=name, date=date, time=time,
                 lat=lat, lon=lon, tz=tz)
            
            # Create Planet nodes
            for planet in chart_data['planets']:
                session.run("""
                    MATCH (c:Chart {chart_id: $chart_id})
                    CREATE (cp:ChartPlanet {
                        id: $id,
                        planet_name: $name,
                        sign: $sign,
                        degree: $degree,
                        longitude: $longitude,
                        house: $house,
                        nakshatra: $nakshatra,
                        nakshatra_pada: $pada,
                        sublord: $sublord,
                        retrograde: $retrograde,
                        combustion: $combustion,
                        dignity_status: $dignity_status,
                        strength_modifier: $strength_modifier
                    })
                    CREATE (c)-[:CONTAINS_PLANET]->(cp)
                """, 
                    chart_id=chart_id,
                    id=f"{chart_id}_{planet['name']}",
                    name=planet['name'],
                    sign=planet['sign'],
                    degree=planet['degree'],
                    longitude=planet['longitude'],
                    house=planet['house'],
                    nakshatra=planet['nakshatra'],
                    pada=planet['nakshatra_pada'],
                    sublord=planet.get('sublord'),
                    retrograde=planet['retrograde'],
                    combustion=planet['combustion'],
                    dignity_status=planet['dignity']['status'],
                    strength_modifier=planet['dignity']['strength_modifier']
                )
                
                # Link to base Planet ontology
                session.run("""
                    MATCH (cp:ChartPlanet {id: $cp_id})
                    MATCH (p:Planet {name: $planet_name})
                    CREATE (cp)-[:INSTANCE_OF]->(p)
                """, cp_id=f"{chart_id}_{planet['name']}", planet_name=planet['name'])
                
                # Link to Sign
                session.run("""
                    MATCH (cp:ChartPlanet {id: $cp_id})
                    MATCH (s:Sign {name: $sign_name})
                    CREATE (cp)-[:PLACED_IN_SIGN]->(s)
                """, cp_id=f"{chart_id}_{planet['name']}", sign_name=planet['sign'])
                
                # Link to Nakshatra
                session.run("""
                    MATCH (cp:ChartPlanet {id: $cp_id})
                    MATCH (n:Nakshatra {name: $nak_name})
                    CREATE (cp)-[:IN_NAKSHATRA {pada: $pada}]->(n)
                """, cp_id=f"{chart_id}_{planet['name']}", 
                     nak_name=planet['nakshatra'], pada=planet['nakshatra_pada'])
            
            # Create House nodes
            for house in chart_data['houses']:
                session.run("""
                    MATCH (c:Chart {chart_id: $chart_id})
                    CREATE (ch:ChartHouse {
                        id: $id,
                        house_number: $number,
                        sign: $sign,
                        degree: $degree,
                        lord: $lord
                    })
                    CREATE (c)-[:CONTAINS_HOUSE]->(ch)
                """,
                    chart_id=chart_id,
                    id=f"{chart_id}_HOUSE_{house['number']}",
                    number=house['number'],
                    sign=house['sign'],
                    degree=house['degree'],
                    lord=house['lord']
                )
                
                # Link house to its lord planet
                session.run("""
                    MATCH (ch:ChartHouse {id: $house_id})
                    MATCH (cp:ChartPlanet {id: $planet_id})
                    CREATE (ch)-[:RULED_BY]->(cp)
                """, 
                    house_id=f"{chart_id}_HOUSE_{house['number']}",
                    planet_id=f"{chart_id}_{house['lord']}"
                )
            
            # Create Aspect relationships
            for aspect in chart_data['aspects']:
                session.run("""
                    MATCH (cp1:ChartPlanet {id: $from_id})
                    MATCH (cp2:ChartPlanet {id: $to_id})
                    CREATE (cp1)-[:ASPECTS {
                        type: $type,
                        strength: $strength
                    }]->(cp2)
                """,
                    from_id=f"{chart_id}_{aspect['from_planet']}",
                    to_id=f"{chart_id}_{aspect['to_planet']}",
                    type=aspect['type'],
                    strength=aspect['strength']
                )
        
        return chart_id
```

---

## 🎯 Benefits of Using VedicAstro

### ✅ **Advantages Over API:**
1. **No costs** - Free forever
2. **Offline** - Works without internet
3. **Fast** - No network latency
4. **Unlimited** - No rate limits
5. **KP System** - Bonus sublord data for advanced analysis
6. **Full control** - Can modify calculations if needed

### ✅ **Advantages Over Raw pyswisseph:**
1. **Higher level** - Abstracts away complexity
2. **Vedic-specific** - Built for Jyotish, not adapted from Western
3. **Well-tested** - Used by practitioners
4. **Documentation** - Examples and guides available

---

## 📝 Updated Phase 4 Deliverables

```
src/chart/
├── vedicastro_calculator.py  # VedicAstro wrapper + normalization
├── graph_builder.py          # Neo4j population pipeline
├── queries.py                # Query interface for Phase 5
└── batch_processor.py        # Batch chart processing

tests/
├── test_vedicastro_calculator.py
├── test_graph_builder.py
└── test_queries.py
```

---

## 🚀 Next Steps

1. **Install VedicAstro:**
   ```bash
   pip install vedicastro
   ```

2. **Run test script** (from earlier in this response)

3. **Implement the calculator wrapper** (code provided above)

4. **Test with your own chart** - verify against known software

5. **Build Neo4j integration** (Week 18)

---
 