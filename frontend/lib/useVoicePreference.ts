"use client";

/**
 * Remembers whether the user wants answers read aloud, and whether the backend
 * can actually do it.
 *
 * Speech needs an API key the deployment may not have, so the preference is
 * only honoured once `/health` confirms the feature is configured.
 */

import { useCallback, useEffect, useState } from "react";

import { getHealth } from "./api";

const ENABLED_KEY = "chat.voice-enabled";
const RATE_KEY = "chat.speech-rate";

/** Selectable playback speeds, cycled through in order. */
const SPEECH_RATES = [1, 1.25, 1.5, 2];

export interface VoicePreference {
  /** The user's stored choice, regardless of backend support. */
  voiceEnabled: boolean;
  setVoiceEnabled: (enabled: boolean) => void;
  /** Whether the backend has a speech engine configured. */
  voiceAvailable: boolean;
  /** The only flag worth acting on: wanted *and* supported. */
  speak: boolean;
  /** Playback speed multiplier for spoken answers. */
  speechRate: number;
  /** Advance to the next speed, wrapping back to 1x. */
  cycleSpeechRate: () => void;
}

export function useVoicePreference(): VoicePreference {
  const [voiceEnabled, setStoredPreference] = useState(false);
  const [voiceAvailable, setVoiceAvailable] = useState(false);
  const [speechRate, setStoredRate] = useState(SPEECH_RATES[0]);

  useEffect(() => {
    setStoredPreference(window.localStorage.getItem(ENABLED_KEY) === "true");
    const storedRate = Number(window.localStorage.getItem(RATE_KEY));
    if (SPEECH_RATES.includes(storedRate)) {
      setStoredRate(storedRate);
    }
    // Read after mount so the server-rendered markup matches the client's.
  }, []);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((health) => {
        if (active) setVoiceAvailable(health.tts_enabled);
      })
      .catch(() => {
        if (active) setVoiceAvailable(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const setVoiceEnabled = useCallback((enabled: boolean): void => {
    setStoredPreference(enabled);
    window.localStorage.setItem(ENABLED_KEY, String(enabled));
  }, []);

  const cycleSpeechRate = useCallback((): void => {
    setStoredRate((current) => {
      const next = SPEECH_RATES[(SPEECH_RATES.indexOf(current) + 1) % SPEECH_RATES.length];
      window.localStorage.setItem(RATE_KEY, String(next));
      return next;
    });
  }, []);

  return {
    voiceEnabled,
    setVoiceEnabled,
    voiceAvailable,
    speak: voiceEnabled && voiceAvailable,
    speechRate,
    cycleSpeechRate,
  };
}
