import { useCallback, useRef, useState } from "react";
import AudioPlayer from "./components/AudioPlayer.jsx";
import EarthMap from "./components/EarthMap.jsx";
import FactorFilters from "./components/FactorFilters.jsx";
import LocationInfo, { locationTagline } from "./components/LocationInfo.jsx";
import ClimateFactorChart, { createClimateStory } from "./components/ClimateFactorChart.jsx";
import VoiceAssistant from "./components/VoiceAssistant.jsx";
import { audioUrl, createSoundscape, explorePoint, retrieveMonthlyClimate } from "./services/api.js";

export default function App() {
  const selectionGeneration = useRef(0);
  const audioGeneration = useRef(0);
  const [coordinates, setCoordinates] = useState(null);
  const [location, setLocation] = useState(null);
  const [error, setError] = useState("");
  const [speech, setSpeech] = useState("");
  const [speechRevision, setSpeechRevision] = useState(0);
  const [speechRate, setSpeechRate] = useState(1);
  const [speechFinished, setSpeechFinished] = useState(true);
  const [audio, setAudio] = useState("");
  const [audioStoryPaused, setAudioStoryPaused] = useState(false);
  const [audioStoryState, setAudioStoryState] = useState("idle");
  const [monthlyClimate, setMonthlyClimate] = useState([]);
  const monthlyClimateRef = useRef([]);
  const [climateLoading, setClimateLoading] = useState(false);
  const [playback, setPlayback] = useState({ currentTime: 0, duration: 0 });
  const [factors, setFactors] = useState([]);
  const factorsRef = useRef([]);
  const [locationReady, setLocationReady] = useState(false);
  const finishSpeech = useCallback(() => {
    setSpeechFinished(true);
    setAudioStoryState("idle");
  }, []);
  function announceSpeech(message, isAudioStory = false) {
    setAudioStoryState(isAudioStory ? "playing" : "idle");
    setSpeechRate(isAudioStory ? 0.8 : 1);
    setSpeech(message);
    setSpeechRevision((revision) => revision + 1);
  }

  async function generateSoundscape(point, selectedFactors, climateRequest) {
    const requestId = ++audioGeneration.current;
    setAudioStoryPaused(false);
    setAudio("");
    setPlayback({ currentTime: 0, duration: 0 });
    setError("");
    try {
      const soundscapeRequest = createSoundscape(point[0], point[1], selectedFactors).then(
        (result) => ({ result }),
        (error) => ({ error }),
      );
      if (climateRequest) {
        await climateRequest;
      }
      const soundscapeResult = await soundscapeRequest;
      if (requestId !== audioGeneration.current) return;
      if (soundscapeResult.error) throw soundscapeResult.error;
      const result = soundscapeResult.result;
      setAudio(audioUrl(result.audio_url));
      if (!monthlyClimateRef.current.length) {
        monthlyClimateRef.current = result.monthly_climate || [];
        setMonthlyClimate(monthlyClimateRef.current);
      }
      setClimateLoading(false);
    } catch (error) {
      if (requestId !== audioGeneration.current) return;
      setClimateLoading(false);
      setError(`Unable to create soundscape. ${error.message}`);
    }
  }

  async function explore(point) {
    const requestId = ++selectionGeneration.current;
    audioGeneration.current += 1;
    setCoordinates(point);
    setLocation(null);
    setAudio("");
    monthlyClimateRef.current = [];
    setMonthlyClimate([]);
    setClimateLoading(true);
    setPlayback({ currentTime: 0, duration: 0 });
    setError("");
    setSpeech("");
    setSpeechFinished(false);
    setLocationReady(false);
    const climateRequest = retrieveMonthlyClimate(point[0], point[1]).then(
      (monthlyClimate) => {
        if (requestId === selectionGeneration.current && monthlyClimate.length) {
          monthlyClimateRef.current = monthlyClimate;
          setMonthlyClimate(monthlyClimate);
          setClimateLoading(false);
        }
        return { monthlyClimate };
      },
      (error) => ({ error }),
    );
    try {
      const place = await explorePoint(point[0], point[1]);
      if (requestId !== selectionGeneration.current) return;
      setLocation(place.location);
      announceSpeech(place.location.name);
      setLocationReady(true);
      await generateSoundscape(point, factorsRef.current, climateRequest);
    } catch (error) {
      if (requestId !== selectionGeneration.current) return;
      setClimateLoading(false);
      setError(`Unable to identify this place. ${error.message}`);
      setSpeechFinished(true);
    }
  }

  function changeFactors(nextFactors, label) {
    factorsRef.current = nextFactors;
    setFactors(nextFactors);
    announceSpeech(label);
    setSpeechFinished(false);
    if (coordinates && locationReady) generateSoundscape(coordinates, nextFactors);
  }

  function tellAudioStory() {
    if (!location) return;
    if (audioStoryState === "playing") {
      window.speechSynthesis?.pause();
      setAudioStoryState("paused");
      return;
    }
    if (audioStoryState === "paused") {
      window.speechSynthesis?.resume();
      setAudioStoryState("playing");
      return;
    }
    setAudioStoryPaused(true);
    const graphStory = createClimateStory(monthlyClimate, factors);
    announceSpeech(`Let's take a journey through the climate of ${location.name}. ${graphStory} ${locationTagline(location.kind)}.`, true);
  }

  return <main className={`earth-app${coordinates ? " has-selection" : " home-screen"}`}>
    {!coordinates && <header className="brand-lockup">
      <h1 className="app-title">EARTHIFY</h1>
      <p className="app-tagline">Explore climate. Hear the Earth.</p>
      <p className="app-description">Explore NASA climate data and satellite imagery through sound. Choose a place to hear temperature, rainfall, wind, and humidity as an immersive soundscape—an alternative way to experience Earth observation.</p>
    </header>}
    <VoiceAssistant key={speechRevision} message={speech} rate={speechRate} onFinished={finishSpeech} />
    <div className="globe-stage">
      <EarthMap coordinates={coordinates} onSelect={explore} />
    </div>
    {coordinates && <nav className="factor-rail" aria-label="Climate sound factors">
      <FactorFilters selected={factors} onChange={changeFactors} />
    </nav>}
    {(location || error) && <aside className="control-panel">
      {location && <LocationInfo name={location.name} kind={location.kind} />}
      {location && climateLoading && monthlyClimate.length === 0 &&
        <p className="climate-loading" role="status">Loading climate graph...</p>}
      {monthlyClimate.length > 0 && <ClimateFactorChart points={monthlyClimate}
        selectedFactors={factors} currentTime={playback.currentTime} duration={playback.duration} />}
      {audio && <AudioPlayer src={audio} autoplay={speechFinished && !audioStoryPaused}
        onPlaybackError={(playbackError) => setError(`Audio playback failed. ${playbackError.message}`)}
        onTimeUpdate={(currentTime, duration) => setPlayback({ currentTime, duration })}
        onAudioStory={tellAudioStory}
        audioStoryState={audioStoryState}
        onManualPlay={() => setAudioStoryPaused(false)}
        pauseForStory={audioStoryPaused} />}
      {error && <p className="error-message" role="alert">{error}</p>}
    </aside>}
  </main>;
}

