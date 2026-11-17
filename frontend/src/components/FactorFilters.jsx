import temperatureIcon from "../assets/temperature-icon.jpeg";
import rainfallIcon from "../assets/rainfall-icon.jpeg";
import windIcon from "../assets/wind-icon.jpeg";
import humidityIcon from "../assets/humidity-icon.jpeg";

const FACTORS = [
  ["temperature", "Temperature", temperatureIcon],
  ["rainfall", "Rainfall", rainfallIcon],
  ["wind", "Wind", windIcon],
  ["humidity", "Humidity", humidityIcon],
];

export default function FactorFilters({ selected, onChange }) {
  function toggle(factor, label) {
    onChange(selected.includes(factor)
      ? selected.filter((item) => item !== factor)
      : [...selected, factor], label);
  }

  return <section className="factor-panel" aria-label="Choose sound factors">
    <div className="factor-options">
      {FACTORS.map(([id, label, icon]) => <button
        className={`factor-option ${selected.includes(id) ? "is-selected" : ""}`}
        key={id}
        type="button"
        aria-pressed={selected.includes(id)}
        onClick={() => toggle(id, label)}
      >
        <img className="factor-icon" src={icon} alt="" aria-hidden="true" />
        <span className="factor-copy"><strong>{label}</strong></span>
      </button>)}
    </div>
  </section>;
}
