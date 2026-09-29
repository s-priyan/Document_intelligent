"use client";

/**
 * Sequential playback of the audio chunks streamed with a spoken answer.
 *
 * The backend emits one chunk per few sentences while the answer is still
 * being written, so chunks arrive faster than they can be heard. Each is
 * turned into a media element as it lands — which also buffers it ahead of its
 * turn — and they are played strictly in order.
 *
 * Media elements are used rather than the Web Audio API because they
 * time-stretch without shifting pitch, which is what makes the speed control
 * listenable; the cost is a small seam between chunks instead of a sample-
 * accurate join.
 */

/** Notified whenever playback starts or stops. */
export type SpeakingListener = (speaking: boolean) => void;

const WAV_MIME_TYPE = "audio/wav";

/** Build a buffered media element for one base64-encoded chunk. */
function createElement(audioBase64: string): HTMLAudioElement {
  const binary = atob(audioBase64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  const element = new Audio(
    URL.createObjectURL(new Blob([bytes], { type: WAV_MIME_TYPE })),
  );
  element.preload = "auto";
  element.preservesPitch = true;
  // Explicit because pitch-corrected time-stretching is the whole reason for
  // using a media element here, not the Web Audio API.
  return element;
}

/** Release the object URL backing an element that will not be played again. */
function release(element: HTMLAudioElement): void {
  URL.revokeObjectURL(element.src);
}

export class AudioQueuePlayer {
  private queue: HTMLAudioElement[] = [];
  private current: HTMLAudioElement | null = null;
  private finishCurrent: (() => void) | null = null;
  private draining = false;
  private rate = 1;
  /** Bumped by `stop()` so a drain started before it retires quietly. */
  private generation = 0;

  constructor(private readonly onSpeakingChange: SpeakingListener) {}

  /** Decode a chunk and add it to the back of the playback queue. */
  enqueue(audioBase64: string): void {
    this.queue.push(createElement(audioBase64));
    if (!this.draining) {
      void this.drain();
    }
  }

  /** Set the playback speed, applying it to the chunk already playing. */
  setRate(rate: number): void {
    this.rate = rate;
    if (this.current !== null) {
      this.current.playbackRate = rate;
    }
  }

  /** Halt playback immediately and discard anything still queued. */
  stop(): void {
    this.generation += 1;
    this.current?.pause();
    this.finishCurrent?.();
    this.queue.forEach(release);
    this.queue = [];
    this.draining = false;
    this.onSpeakingChange(false);
  }

  /** Release every buffered chunk; the player must not be used afterwards. */
  dispose(): void {
    this.stop();
  }

  /** Play queued chunks back to back until the queue runs dry. */
  private async drain(): Promise<void> {
    const generation = this.generation;
    this.draining = true;
    this.onSpeakingChange(true);

    while (this.queue.length > 0 && generation === this.generation) {
      await this.play(this.queue.shift() as HTMLAudioElement);
    }

    if (generation === this.generation) {
      this.draining = false;
      this.onSpeakingChange(false);
    }
  }

  /** Play one chunk, resolving when it ends, fails, or is stopped. */
  private play(element: HTMLAudioElement): Promise<void> {
    return new Promise((resolve) => {
      const finish = (): void => {
        if (this.finishCurrent !== finish) {
          return;
          // Already settled; `stop()` and `onended` can both fire.
        }
        this.finishCurrent = null;
        this.current = null;
        release(element);
        resolve();
      };

      element.playbackRate = this.rate;
      element.onended = finish;
      element.onerror = finish;
      this.current = element;
      this.finishCurrent = finish;
      void element.play().catch(finish);
      // Playback is only ever started from a user gesture, but a rejected
      // promise must still not strand the queue.
    });
  }
}
