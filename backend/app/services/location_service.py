from app.services.http_service import get_json

NOMINATIM = "https://nominatim.openstreetmap.org"

# Only these widely recognized, large features are eligible as physical-region
# results. Nearby towns, local parks, small lakes, and minor landmarks are ignored.
MAJOR_FEATURES = {
    "sahara": ("Sahara", "desert"),
    "sahara desert": ("Sahara", "desert"),
    "arabian desert": ("Arabian Desert", "desert"),
    "gobi": ("Gobi Desert", "desert"),
    "gobi desert": ("Gobi Desert", "desert"),
    "kalahari": ("Kalahari Desert", "desert"),
    "kalahari desert": ("Kalahari Desert", "desert"),
    "namib": ("Namib Desert", "desert"),
    "namib desert": ("Namib Desert", "desert"),
    "atacama": ("Atacama Desert", "desert"),
    "atacama desert": ("Atacama Desert", "desert"),
    "thar desert": ("Thar Desert", "desert"),
    "taklamakan desert": ("Taklamakan Desert", "desert"),
    "mojave desert": ("Mojave Desert", "desert"),
    "sonoran desert": ("Sonoran Desert", "desert"),
    "chihuahuan desert": ("Chihuahuan Desert", "desert"),
    "great victoria desert": ("Great Victoria Desert", "desert"),
    "great sandy desert": ("Great Sandy Desert", "desert"),
    "patagonian desert": ("Patagonian Desert", "desert"),
    "himalaya": ("Himalayas", "mountain range"),
    "himalayas": ("Himalayas", "mountain range"),
    "andes": ("Andes", "mountain range"),
    "rocky mountains": ("Rocky Mountains", "mountain range"),
    "alps": ("Alps", "mountain range"),
    "atlas mountains": ("Atlas Mountains", "mountain range"),
    "ural mountains": ("Ural Mountains", "mountain range"),
    "appalachian mountains": ("Appalachian Mountains", "mountain range"),
    "great dividing range": ("Great Dividing Range", "mountain range"),
    "caucasus": ("Caucasus Mountains", "mountain range"),
    "carpathian mountains": ("Carpathian Mountains", "mountain range"),
    "pyrenees": ("Pyrenees", "mountain range"),
    "scandinavian mountains": ("Scandinavian Mountains", "mountain range"),
    "tibetan plateau": ("Tibetan Plateau", "plateau"),
    "deccan plateau": ("Deccan Plateau", "plateau"),
    "iranian plateau": ("Iranian Plateau", "plateau"),
    "altiplano": ("Altiplano", "plateau"),
    "ethiopian highlands": ("Ethiopian Highlands", "highlands"),
    "amazon rainforest": ("Amazon Rainforest", "rainforest"),
    "amazon basin": ("Amazon Rainforest", "rainforest"),
    "amazon forest": ("Amazon Rainforest", "rainforest"),
    "congo rainforest": ("Congo Rainforest", "rainforest"),
    "congo basin": ("Congo Rainforest", "rainforest"),
    "taiga": ("Taiga", "forest region"),
    "boreal forest": ("Taiga", "forest region"),
    "greenland ice sheet": ("Greenland Ice Sheet", "glacier"),
    "antarctic ice sheet": ("Antarctic Ice Sheet", "glacier"),
    "vatnajokull": ("Vatnajökull Glacier", "glacier"),
    "vatnajökull": ("Vatnajökull Glacier", "glacier"),
    "aletsch glacier": ("Aletsch Glacier", "glacier"),
    "siachen glacier": ("Siachen Glacier", "glacier"),
    "perito moreno glacier": ("Perito Moreno Glacier", "glacier"),
    "columbia icefield": ("Columbia Icefield", "glacier"),
    "lambert glacier": ("Lambert Glacier", "glacier"),
    "greenland": ("Greenland", "major island"),
    "madagascar": ("Madagascar", "major island"),
    "borneo": ("Borneo", "major island"),
    "new guinea": ("New Guinea", "major island"),
    "indonesian archipelago": ("Indonesian Archipelago", "archipelago"),
    "malay archipelago": ("Malay Archipelago", "archipelago"),
    "philippine archipelago": ("Philippine Archipelago", "archipelago"),
    "pacific ocean": ("Pacific Ocean", "ocean"),
    "atlantic ocean": ("Atlantic Ocean", "ocean"),
    "indian ocean": ("Indian Ocean", "ocean"),
    "arctic ocean": ("Arctic Ocean", "ocean"),
    "southern ocean": ("Southern Ocean", "ocean"),
    "mediterranean sea": ("Mediterranean Sea", "major sea"),
    "caribbean sea": ("Caribbean Sea", "major sea"),
    "south china sea": ("South China Sea", "major sea"),
    "arabian sea": ("Arabian Sea", "major sea"),
    "red sea": ("Red Sea", "major sea"),
    "black sea": ("Black Sea", "major sea"),
    "north sea": ("North Sea", "major sea"),
    "baltic sea": ("Baltic Sea", "major sea"),
    "banda sea": ("Banda Sea", "major sea"),
    "bering sea": ("Bering Sea", "major sea"),
    "coral sea": ("Coral Sea", "major sea"),
    "tasman sea": ("Tasman Sea", "major sea"),
    "sea of japan": ("Sea of Japan", "major sea"),
    "east china sea": ("East China Sea", "major sea"),
    "philippine sea": ("Philippine Sea", "major sea"),
    "andaman sea": ("Andaman Sea", "major sea"),
    "gulf of mexico": ("Gulf of Mexico", "major sea"),
    "persian gulf": ("Persian Gulf", "major sea"),
    "hudson bay": ("Hudson Bay", "major sea"),
    "bay of bengal": ("Bay of Bengal", "major sea"),
    "lake superior": ("Lake Superior", "major lake"),
    "lake victoria": ("Lake Victoria", "major lake"),
    "lake baikal": ("Lake Baikal", "major lake"),
    "lake tanganyika": ("Lake Tanganyika", "major lake"),
    "lake titicaca": ("Lake Titicaca", "major lake"),
    "nile": ("Nile River", "major river"),
    "nile river": ("Nile River", "major river"),
    "amazon river": ("Amazon River", "major river"),
    "yangtze": ("Yangtze River", "major river"),
    "yangtze river": ("Yangtze River", "major river"),
    "mississippi river": ("Mississippi River", "major river"),
    "congo river": ("Congo River", "major river"),
    "ganges": ("Ganges River", "major river"),
    "ganges river": ("Ganges River", "major river"),
    "danube": ("Danube River", "major river"),
    "danube river": ("Danube River", "major river"),
}


def ocean_name(lat: float, lon: float) -> str:
    if lat >= 65:
        return "Arctic Ocean"
    if lat <= -60:
        return "Southern Ocean"
    if 20 <= lon <= 120:
        return "Indian Ocean"
    if -70 <= lon < 20:
        return "Atlantic Ocean"
    return "Pacific Ocean"


def major_feature_name(data: dict) -> tuple[str, str] | None:
    candidates = [data.get("name", "")]
    address = data.get("address", {})
    candidates.extend((address.get("ocean", ""), address.get("sea", ""), address.get("island", "")))
    for candidate in candidates:
        normalized = " ".join(candidate.casefold().split())
        feature = MAJOR_FEATURES.get(normalized)
        if feature and (candidate != data.get("name") or data.get("category") in {
            "natural", "waterway", "water", "place"
        }):
            return feature
    return None


async def reverse_geocode(lat: float, lon: float) -> dict:
    try:
        detail = await get_json(f"{NOMINATIM}/reverse", {
            "lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10,
            "addressdetails": 1, "accept-language": "en",
        })
        country_result = await get_json(f"{NOMINATIM}/reverse", {
            "lat": lat, "lon": lon, "format": "jsonv2", "zoom": 3,
            "addressdetails": 1, "accept-language": "en",
        })
        country_address = country_result.get("address", {})
        country = country_address.get("country") or detail.get("address", {}).get("country")
        if country:
            return {"name": country, "kind": "country", "source": "OpenStreetMap Nominatim"}

        feature = major_feature_name(detail)
        if feature:
            name, kind = feature
            return {"name": name, "kind": kind, "source": "OpenStreetMap Nominatim"}

        address = detail.get("address", {})
        ocean = address.get("ocean") or address.get("sea")
        if ocean and ("ocean" in ocean.casefold() or "sea" in ocean.casefold()):
            return {"name": ocean, "kind": "ocean or sea", "source": "OpenStreetMap Nominatim"}
        if lat >= 65 or lat <= -60:
            name = "Arctic Region" if lat >= 65 else "Antarctic Region"
            return {"name": name, "kind": "polar region", "source": "coordinate region"}
        continent = country_address.get("continent") or address.get("continent")
        if continent:
            return {"name": continent, "kind": "continent", "source": "OpenStreetMap Nominatim"}
        return {"name": ocean_name(lat, lon), "kind": "ocean (approximate)", "source": "coordinate region"}
    except Exception:
        if lat >= 65 or lat <= -60:
            name = "Arctic Region" if lat >= 65 else "Antarctic Region"
            return {"name": name, "kind": "polar region", "source": "coordinate region"}
        return {"name": ocean_name(lat, lon), "kind": "ocean (approximate)", "source": "coordinate region"}


async def search_locations(query: str) -> list[dict]:
    results = await get_json(f"{NOMINATIM}/search", {
        "q": query, "format": "jsonv2", "limit": 5, "addressdetails": 1
    })
    return [{"name": item.get("name") or item.get("display_name", "Place"),
             "display_name": item.get("display_name", ""), "lat": float(item["lat"]),
             "lon": float(item["lon"])} for item in results]
