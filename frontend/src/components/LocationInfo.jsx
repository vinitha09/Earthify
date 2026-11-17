export function locationTagline(kind = "") {
  const normalized = String(kind || "").toLowerCase();
  if (normalized.includes("ocean")) return "Oceanic weather and sea-surface conditions shape this place.";
  if (normalized.includes("country")) return "Land climate and seasonal shifts are unfolding here.";
  if (normalized.includes("city")) return "Urban climate patterns ripple through this region.";
  if (normalized.includes("state")) return "Regional climate rhythms are moving across this landscape.";
  if (normalized.includes("region")) return "This region carries a distinct climate rhythm in every season.";
  return "Local climate conditions are moving through this place.";
}

export default function LocationInfo({ name, kind }) {
  return <section aria-label="Selected location">
    <h2>{name}</h2>
    <p className="location-tagline">{locationTagline(kind)}</p>
  </section>;
}
