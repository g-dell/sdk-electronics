import { useEffect, useMemo, useRef } from "react";
import { createRoot } from "react-dom/client";
import { useOpenAiGlobal } from "../use-openai-global";
import { useWidgetState } from "../use-widget-state";
import { AvocadoIcon, BreadIcon, EggIcon, JarIcon, TomatoIcon } from "./icons";
import type { CartItem } from "../types";

type CartWidgetState = {
  cartId?: string;
  items?: CartItem[];
  [key: string]: unknown;
};

const createDefaultCartState = (): CartWidgetState => ({
  items: [],
});

function usePrettyJson(value: unknown): string {
  return useMemo(() => {
    if (value === undefined || value === null) {
      return "null";
    }

    try {
      return JSON.stringify(value, null, 2);
    } catch (error) {
      return `<<unable to render: ${error}>>`;
    }
  }, [value]);
}

function JsonPanel({ label, value }: { label: string; value: unknown }) {
  const pretty = usePrettyJson(value);

  return (
    <section className="rounded-2xl border border-black/20 bg-[#fffaf5] p-4">
      <header className="mb-3">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-black/60">
          {label}
        </p>
      </header>
      <pre className="max-h-64 overflow-auto rounded-xl bg-white p-3 font-mono text-xs text-black/70 shadow-sm">
        {pretty}
      </pre>
    </section>
  );
}

const iconMatchers = [
  { keywords: ["egg", "eggs"], Icon: EggIcon },
  { keywords: ["bread"], Icon: BreadIcon },
  { keywords: ["tomato", "tomatoes"], Icon: TomatoIcon },
  { keywords: ["avocado", "avocados"], Icon: AvocadoIcon },
];

function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const toolResponseMetadata = useOpenAiGlobal("toolResponseMetadata");
  const widgetState = useOpenAiGlobal("widgetState");
  const [cartState, setCartState] = useWidgetState<CartWidgetState>(
    createDefaultCartState
  );
  const cartItems = Array.isArray(cartState?.items) ? cartState.items : [];
  const animationStyles = `
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;

  function adjustQuantity(id: string, delta: number) {
    if (!id || delta === 0) {
      return;
    }

    setCartState((prevState) => {
      const baseState: CartWidgetState = prevState ?? {};
      const items = Array.isArray(baseState.items)
        ? baseState.items.map((item) => ({ ...item }))
        : [];

      const idx = items.findIndex((item) => item.id === id);
      if (idx === -1) {
        return baseState;
      }

      const current = items[idx];
      const nextQuantity = Math.max(0, (current.quantity ?? 0) + delta);
      if (nextQuantity === 0) {
        items.splice(idx, 1);
      } else {
        items[idx] = { ...current, quantity: nextQuantity };
      }

      return { ...baseState, items };
    });
  }

  // Rimuoviamo la logica che aggiunge items da toolOutput
  // Ora il carrello mostra solo gli items aggiunti tramite i pulsanti "Aggiungi al carrello" nei widget
  // Il carrello viene popolato direttamente tramite useWidgetState quando l'utente clicca sui pulsanti
  
  // Sincronizza lo stato iniziale da widgetState se presente (per persistenza tra sessioni)
  useEffect(() => {
    if (widgetState && typeof widgetState === "object") {
      const stateFromWindow = widgetState as CartWidgetState;
      if (stateFromWindow.items && Array.isArray(stateFromWindow.items)) {
        // Se widgetState ha items e il nostro stato locale è vuoto, sincronizza
        if (!cartState?.items || cartState.items.length === 0) {
          setCartState(stateFromWindow);
        }
      }
    }
  }, [widgetState]);

  function getIconForItem(name: string) {
    const words = name
      .toLowerCase()
      .replace(/[^a-z]/g, " ")
      .split(/\s+/)
      .filter(Boolean);
    for (const entry of iconMatchers) {
      if (entry.keywords.some((keyword) => words.includes(keyword))) {
        return entry.Icon;
      }
    }
    return JarIcon;
  }

  const itemCards = cartItems.length ? (
    <div className="space-y-3">
      {cartItems.map((item) => (
        <div
          key={item.name}
          className="flex items-center justify-between rounded-2xl border border-black/20 bg-[#fffaf5] p-3"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white shadow-sm">
              {(() => {
                const Icon = getIconForItem(item.name);
                return <Icon className="h-6 w-6" />;
              })()}
            </div>
            <div>
              <p className="text-sm font-semibold text-black">{item.name}</p>
              <p className="text-xs text-black/60">
                Qty <span className="font-mono">{item.quantity ?? 0}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => adjustQuantity(item.id, -1)}
              className="h-8 w-8 rounded-full border border-black/30 text-lg font-semibold text-black/70 transition hover:bg-white"
              aria-label={`Decrease ${item.name}`}
            >
              -
            </button>
            <button
              type="button"
              onClick={() => adjustQuantity(item.id, 1)}
              className="h-8 w-8 rounded-full border border-black/30 text-lg font-semibold text-black/70 transition hover:bg-white"
              aria-label={`Increase ${item.name}`}
            >
              +
            </button>
          </div>
        </div>
      ))}
    </div>
  ) : (
    <div className="rounded-2xl border border-dashed border-black/40 bg-[#fffaf5] p-8 text-center">
      <p className="text-base font-medium text-black/70 mb-2">
        Carrello vuoto
      </p>
      <p className="text-sm text-black/60">
        Non hai aggiunto nessun articolo al carrello.
        <br />
        Usa i pulsanti "Aggiungi al carrello" nei widget per aggiungere prodotti.
      </p>
    </div>
  );

  return (
    <div
      className="min-h-screen w-full bg-white text-black bg-[radial-gradient(circle_at_top_left,_#fff7ed_0,_#ffffff_55%),radial-gradient(circle_at_bottom_right,_#eef2ff_0,_#ffffff_45%)]"
      style={{
        fontFamily: '"Trebuchet MS", "Gill Sans", "Lucida Grande", sans-serif',
      }}
      data-theme="light"
    >
      <style>{animationStyles}</style>
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-4 py-8 md:px-6 lg:px-8">
        <header
          className="space-y-2"
          style={{ animation: "fadeUp 0.6s ease-out both" }}
        >
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-black/60">
            Simple cart
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">
            Il tuo carrello
          </h1>
          <p className="text-sm text-black/70">
            Il carrello contiene solo i prodotti che hai aggiunto tramite i pulsanti "Aggiungi al carrello" nei widget.
          </p>
        </header>

        <div
          className="grid gap-8 lg:grid-cols-[1.4fr_1fr]"
          style={{
            animation: "fadeUp 0.7s ease-out both",
            animationDelay: "80ms",
          }}
        >
          <section className="space-y-4">
            <header className="flex items-center justify-between">
              <p className="text-sm font-semibold uppercase tracking-widest text-black/70">
                Cart
              </p>
              <span className="text-xs text-black/60">
                {cartItems.length} items
              </span>
            </header>
            {itemCards}
            <button
              type="button"
              disabled={cartItems.length === 0}
              className="w-full rounded-2xl border border-black/30 bg-white py-3 text-sm font-semibold text-black/70 transition hover:border-black/50 disabled:cursor-not-allowed disabled:opacity-70"
            >
              Check out
            </button>
          </section>
        </div>

        <section className="space-y-3">
          <header className="flex items-center justify-between">
            <p className="text-sm font-semibold uppercase tracking-widest text-black/70">
              Widget state & output
            </p>
            <span className="text-xs text-black/60">Debug view</span>
          </header>
          <div className="grid gap-4 lg:grid-cols-2">
            <JsonPanel label="window.openai.widgetState" value={cartState} />
            <JsonPanel label="window.openai.toolOutput" value={toolOutput} />
          </div>
        </section>
      </div>
    </div>
  );
}

const rootElement = document.getElementById("shopping-cart-root");
if (!rootElement) {
  throw new Error("Missing shopping-cart-root element");
}

createRoot(rootElement).render(<App />);

export { App };
export default App;
