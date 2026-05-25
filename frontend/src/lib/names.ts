// ---------------------------------------------------------------------------
// Friendly random chat names: adjective-animal-#### (e.g. "amber-otter-3194").
// Used by the "surprise me" button when starting a new chat.
// ---------------------------------------------------------------------------

const ADJECTIVES = [
  "amber", "brisk", "calm", "dapper", "eager", "fuzzy", "gentle", "humble",
  "ivory", "jolly", "keen", "lucid", "mellow", "noble", "opal", "plucky",
  "quiet", "rapid", "sleek", "tidal", "umber", "vivid", "witty", "zesty",
];

const ANIMALS = [
  "otter", "lynx", "heron", "panda", "gecko", "raven", "tapir", "koala",
  "ferret", "marlin", "ibex", "puffin", "badger", "falcon", "narwhal",
  "quokka", "wombat", "axolotl", "manatee", "pangolin",
];

function pick<T>(items: readonly T[]): T {
  return items[Math.floor(Math.random() * items.length)];
}

export function randomChatName(): string {
  const n = Math.floor(1000 + Math.random() * 9000);
  return `${pick(ADJECTIVES)}-${pick(ANIMALS)}-${n}`;
}
