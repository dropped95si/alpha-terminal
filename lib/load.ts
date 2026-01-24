import { CardsFile, IndustriesFile } from "./types";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return (await res.json()) as T;
}

export async function loadAll() {
  const [industries, early, ready, watch] = await Promise.all([
    fetchJson<IndustriesFile>("/data/industries.json"),
    fetchJson<CardsFile>("/data/early.json"),
    fetchJson<CardsFile>("/data/ready.json"),
    fetchJson<CardsFile>("/data/watch.json"),
  ]);
  return { industries, early, ready, watch };
}
