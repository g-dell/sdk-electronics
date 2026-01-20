import type { CartItem } from "../types";

export type CrossSellCategory = "pc" | "tv";

export type CrossSellItem = {
  id: string;
  sku: string;
  name: string;
  price: number;
  imageUrl?: string;
  tags?: string[];
  compatibleWith: CrossSellCategory[];
  priority: number;
};

type CartCategoryIntent = {
  categories: CrossSellCategory[];
  hasScreenDevice: boolean;
};

const PC_KEYWORDS = [
  "pc",
  "laptop",
  "notebook",
  "desktop",
  "computer",
  "ultrabook",
  "macbook",
  "gaming",
];
const TV_KEYWORDS = ["tv", "televisore", "television", "smart tv", "oled", "qled"];

const CLEANING_TAG = "screen-cleaning";
const POPULAR_TAG = "popular";
const RECOMMENDED_TAG = "recommended";

export const crossSellFallbackCatalog: CrossSellItem[] = [
  {
    id: "cs-clean-cloth-01",
    sku: "CS-CLEAN-CLOTH-01",
    name: "Panno in microfibra per schermi",
    price: 9.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-1.png",
    tags: [CLEANING_TAG, POPULAR_TAG],
    compatibleWith: ["pc", "tv"],
    priority: 95,
  },
  {
    id: "cs-clean-spray-01",
    sku: "CS-CLEAN-SPRAY-01",
    name: "Spray delicato per pulizia display",
    price: 12.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-2.png",
    tags: [CLEANING_TAG, RECOMMENDED_TAG],
    compatibleWith: ["pc", "tv"],
    priority: 90,
  },
  {
    id: "cs-usb-c-01",
    sku: "CS-USB-C-01",
    name: "Cavo USB-C 100W intrecciato",
    price: 19.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-3.png",
    tags: ["usb-c", RECOMMENDED_TAG],
    compatibleWith: ["pc"],
    priority: 80,
  },
  {
    id: "cs-charger-01",
    sku: "CS-CHARGER-01",
    name: "Caricatore USB-C 65W",
    price: 34.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-4.png",
    tags: ["charger", POPULAR_TAG],
    compatibleWith: ["pc"],
    priority: 78,
  },
  {
    id: "cs-hdmi-01",
    sku: "CS-HDMI-01",
    name: "Cavo HDMI 2.1 ad alta velocità",
    price: 24.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-5.png",
    tags: ["hdmi", POPULAR_TAG],
    compatibleWith: ["tv"],
    priority: 82,
  },
  {
    id: "cs-remote-01",
    sku: "CS-REMOTE-01",
    name: "Telecomando universale smart",
    price: 29.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-6.png",
    tags: ["remote", RECOMMENDED_TAG],
    compatibleWith: ["tv"],
    priority: 75,
  },
  {
    id: "cs-mount-01",
    sku: "CS-MOUNT-01",
    name: "Staffa TV slim orientabile",
    price: 49.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-1.png",
    tags: ["tv-mount", RECOMMENDED_TAG],
    compatibleWith: ["tv"],
    priority: 72,
  },
  {
    id: "cs-ups-01",
    sku: "CS-UPS-01",
    name: "Ciabatta con protezione UPS",
    price: 39.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-2.png",
    tags: ["power", POPULAR_TAG],
    compatibleWith: ["pc", "tv"],
    priority: 70,
  },
  {
    id: "cs-stand-01",
    sku: "CS-STAND-01",
    name: "Supporto da scrivania regolabile",
    price: 44.9,
    imageUrl: "https://persistent.oaistatic.com/electronics/electronics-3.png",
    tags: ["stand", RECOMMENDED_TAG],
    compatibleWith: ["pc"],
    priority: 68,
  },
];

function normalizeText(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function getCartText(cartItems: CartItem[]) {
  return cartItems
    .map((item) =>
      [
        item.name,
        item.description,
        item.shortDescription,
        item.detailSummary,
        ...(item.tags ?? []),
      ]
        .filter(Boolean)
        .join(" ")
    )
    .join(" ");
}

export function getCartCategoryIntent(cartItems: CartItem[]): CartCategoryIntent {
  if (!cartItems.length) {
    return { categories: [], hasScreenDevice: false };
  }

  const normalized = normalizeText(getCartText(cartItems));
  const tokens = new Set(normalized.split(/\s+/).filter(Boolean));

  const hasPc = PC_KEYWORDS.some((keyword) => tokens.has(keyword.replace(/\s+/g, ""))) ||
    PC_KEYWORDS.some((keyword) => normalized.includes(keyword));
  const hasTv = TV_KEYWORDS.some((keyword) => tokens.has(keyword.replace(/\s+/g, ""))) ||
    TV_KEYWORDS.some((keyword) => normalized.includes(keyword));

  const categories: CrossSellCategory[] = [];
  if (hasPc) {
    categories.push("pc");
  }
  if (hasTv) {
    categories.push("tv");
  }

  return { categories, hasScreenDevice: hasPc || hasTv };
}

function getCartIdentifiers(cartItems: CartItem[]) {
  const ids = new Set<string>();
  const names = new Set<string>();
  for (const item of cartItems) {
    if (item.id) {
      ids.add(normalizeText(item.id));
    }
    if (item.name) {
      names.add(normalizeText(item.name));
    }
  }
  return { ids, names };
}

function hasAccessoryKeyword(cartItems: CartItem[], keywords: string[]) {
  const normalized = normalizeText(getCartText(cartItems));
  return keywords.some((keyword) => normalized.includes(keyword));
}

function sortByPriority(items: CrossSellItem[]) {
  return [...items].sort((a, b) => b.priority - a.priority);
}

function dedupeBySku(items: CrossSellItem[]) {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.sku)) {
      return false;
    }
    seen.add(item.sku);
    return true;
  });
}

export function getCrossSellSuggestions(
  cartItems: CartItem[],
  catalog: CrossSellItem[]
): CrossSellItem[] {
  if (!cartItems.length || !catalog.length) {
    return [];
  }

  const { categories, hasScreenDevice } = getCartCategoryIntent(cartItems);
  const { ids, names } = getCartIdentifiers(cartItems);
  const normalizedCartText = normalizeText(getCartText(cartItems));

  const eligible = dedupeBySku(
    catalog.filter((item) => {
      const normalizedSku = normalizeText(item.sku);
      const normalizedId = normalizeText(item.id);
      const normalizedName = normalizeText(item.name);
      if (
        ids.has(normalizedSku) ||
        ids.has(normalizedId) ||
        names.has(normalizedName)
      ) {
        return false;
      }
      return true;
    })
  );

  const suggestions: CrossSellItem[] = [];
  const seenSkus = new Set<string>();

  const pushSuggestion = (item: CrossSellItem) => {
    if (seenSkus.has(item.sku)) {
      return;
    }
    seenSkus.add(item.sku);
    suggestions.push(item);
  };

  if (hasScreenDevice) {
    const cleaningCandidates = sortByPriority(
      eligible.filter(
        (item) =>
          item.tags?.includes(CLEANING_TAG) &&
          item.compatibleWith.some((category) => categories.includes(category))
      )
    );
    cleaningCandidates.slice(0, 2).forEach(pushSuggestion);
  }

  if (categories.includes("pc")) {
    const needsUsbC = !hasAccessoryKeyword(cartItems, ["usb-c", "usb c"]);
    const needsCharger = !hasAccessoryKeyword(cartItems, ["charger", "caricatore"]);
    const pcCandidates = eligible.filter((item) => item.compatibleWith.includes("pc"));

    if (needsUsbC) {
      sortByPriority(pcCandidates.filter((item) => item.tags?.includes("usb-c")))
        .slice(0, 1)
        .forEach(pushSuggestion);
    }

    if (needsCharger) {
      sortByPriority(pcCandidates.filter((item) => item.tags?.includes("charger")))
        .slice(0, 1)
        .forEach(pushSuggestion);
    }
  }

  if (categories.includes("tv")) {
    const needsHdmi = !normalizedCartText.includes("hdmi");
    const tvCandidates = eligible.filter((item) => item.compatibleWith.includes("tv"));

    if (needsHdmi) {
      sortByPriority(tvCandidates.filter((item) => item.tags?.includes("hdmi")))
        .slice(0, 1)
        .forEach(pushSuggestion);
    }

    sortByPriority(tvCandidates.filter((item) => item.tags?.includes("remote")))
      .slice(0, 1)
      .forEach(pushSuggestion);

    sortByPriority(
      tvCandidates.filter((item) => item.tags?.some((tag) => tag === "tv-mount" || tag === "stand"))
    )
      .slice(0, 1)
      .forEach(pushSuggestion);
  }

  const categorySet = new Set(categories);
  const scored = eligible
    .filter((item) => {
      if (seenSkus.has(item.sku)) {
        return false;
      }
      if (categories.length === 0) {
        return true;
      }
      return item.compatibleWith.some((category) => categorySet.has(category));
    })
    .map((item) => {
      let score = item.priority;
      if (hasScreenDevice && item.tags?.includes(CLEANING_TAG)) {
        score += 15;
      }
      if (categories.includes("pc") && item.compatibleWith.includes("pc")) {
        score += 10;
      }
      if (categories.includes("tv") && item.compatibleWith.includes("tv")) {
        score += 10;
      }
      if (item.tags?.includes(POPULAR_TAG)) {
        score += 4;
      }
      return { item, score };
    })
    .sort((a, b) => b.score - a.score)
    .map(({ item }) => item);

  scored.forEach(pushSuggestion);

  return suggestions.slice(0, 8);
}

export function getCrossSellTagLabel(tags?: string[]) {
  if (tags?.includes(POPULAR_TAG)) {
    return "Molto richiesto";
  }
  if (tags?.includes(RECOMMENDED_TAG)) {
    return "Consigliato";
  }
  return null;
}
