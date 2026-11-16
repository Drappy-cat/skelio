/**
 * Client-side One-Euro Filter untuk meredam jitter keypoint pada 60 FPS overlay
 * di antara paket telemetri yang datang dari server FastAPI.
 */
export class OneEuroKeypointFilter {
  private readonly minCutoff: number;
  private readonly beta: number;
  private readonly dCutoff: number;
  private xPrev: number[] | null = null;
  private dxPrev: number[] | null = null;
  private tPrev: number | null = null;

  constructor(minCutoff = 1.2, beta = 0.02, dCutoff = 1.0) {
    this.minCutoff = minCutoff;
    this.beta = beta;
    this.dCutoff = dCutoff;
  }

  private smoothingFactor(te: number, cutoff: number): number {
    const r = 2 * Math.PI * cutoff * te;
    return r / (r + 1.0);
  }

  private expSmooth(a: number, x: number, xPrev: number): number {
    return a * x + (1.0 - a) * xPrev;
  }

  public filterFlat(coords: number[], timestampMs = Date.now()): number[] {
    if (this.xPrev === null || this.dxPrev === null || this.tPrev === null || this.xPrev.length !== coords.length) {
      this.tPrev = timestampMs;
      this.xPrev = [...coords];
      this.dxPrev = new Array(coords.length).fill(0);
      return [...coords];
    }

    const te = Math.max(1e-4, (timestampMs - this.tPrev) / 1000.0);
    this.tPrev = timestampMs;

    const aD = this.smoothingFactor(te, this.dCutoff);
    const out = new Array<number>(coords.length);

    for (let i = 0; i < coords.length; i++) {
      const dx = (coords[i] - this.xPrev[i]) / te;
      const dxHat = this.expSmooth(aD, dx, this.dxPrev[i]);
      this.dxPrev[i] = dxHat;

      const cutoff = this.minCutoff + this.beta * Math.abs(dxHat);
      const a = this.smoothingFactor(te, cutoff);
      const xHat = this.expSmooth(a, coords[i], this.xPrev[i]);
      this.xPrev[i] = xHat;
      out[i] = xHat;
    }

    return out;
  }

  public reset(): void {
    this.xPrev = null;
    this.dxPrev = null;
    this.tPrev = null;
  }
}
