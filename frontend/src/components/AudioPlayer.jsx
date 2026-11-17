import { useEffect, useRef, useState } from "react";

export default function AudioPlayer({
  src,
  autoplay = true,
  onPlaybackError,
  onTimeUpdate,
  onAudioStory,
  onManualPlay,
  audioStoryState = "idle",
  pauseForStory = false,
}) {
  const audioRef = useRef(null);
  const errorHandler = useRef(onPlaybackError);
  const sourceRef = useRef(src);
  const manualPauseRef = useRef(false);
  const playRequestRef = useRef(0);
  const pauseForStoryRef = useRef(pauseForStory);
  pauseForStoryRef.current = pauseForStory;
  const [playing, setPlaying] = useState(false);
  useEffect(() => { errorHandler.current = onPlaybackError; }, [onPlaybackError]);
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (sourceRef.current !== src) {
      sourceRef.current = src;
      playRequestRef.current += 1;
      manualPauseRef.current = pauseForStory;
      setPlaying(false);
      audio.currentTime = 0;
    }
    if (pauseForStory) {
      manualPauseRef.current = true;
      playRequestRef.current += 1;
      audio.pause();
      return;
    }
    if (autoplay && !manualPauseRef.current && audio.paused) {
      requestPlayback(audio);
    }
  }, [src, autoplay, pauseForStory]);
  useEffect(() => () => audioRef.current?.pause(), []);

  async function requestPlayback(audio) {
    const requestId = ++playRequestRef.current;
    try {
      await audio.play();
    } catch (error) {
      if (requestId === playRequestRef.current) errorHandler.current?.(error);
      return;
    }
    if (requestId !== playRequestRef.current || manualPauseRef.current || pauseForStoryRef.current) {
      audio.pause();
    }
  }

  function pausePlayback(audio) {
    manualPauseRef.current = true;
    playRequestRef.current += 1;
    audio.pause();
  }

  async function togglePlayback() {
    const audio = audioRef.current;
    if (!audio) return;
    if (!audio.paused) {
      pausePlayback(audio);
      return;
    }
    manualPauseRef.current = false;
    pauseForStoryRef.current = false;
    onManualPlay?.();
    await requestPlayback(audio);
  }

  function playAudioStory() {
    const audio = audioRef.current;
    if (audio) pausePlayback(audio);
    onAudioStory?.();
  }

  const storyLabel = audioStoryState === "playing"
    ? "Pause story"
    : audioStoryState === "paused"
      ? "Resume story"
      : "Audio story";

  return <>
    <audio ref={audioRef} src={src} aria-label="Climate sound playback"
      onPlay={() => setPlaying(true)}
      onPause={() => setPlaying(false)}
      onEnded={() => setPlaying(false)}
      onTimeUpdate={(event) => onTimeUpdate?.(event.currentTarget.currentTime, event.currentTarget.duration)} />
    <div className="playback-controls">
      <button className={`playback-button playback-button--primary${playing ? " is-playing" : ""}`}
        type="button" onClick={togglePlayback} aria-label={playing ? "Pause climate sound" : "Play climate sound"}>
        {playing ? "Pause" : "Play"}
      </button>
      <button className="playback-button playback-button--story" type="button" onClick={playAudioStory}
        aria-label={storyLabel}>
        {storyLabel}
      </button>
    </div>
  </>;
}
