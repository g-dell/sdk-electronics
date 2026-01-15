import { useState } from "react";
import { createRoot } from "react-dom/client";
import { AnimatePresence } from "framer-motion";
import { useCart } from "../use-cart";
import { AvocadoIcon, BreadIcon, EggIcon, JarIcon, TomatoIcon } from "./icons";
import type { CartItem } from "../types";
import ProductDetails from "../utils/ProductDetails";

const iconMatchers = [
  { keywords: ["egg", "eggs"], Icon: EggIcon },
  { keywords: ["bread"], Icon: BreadIcon },
  { keywords: ["tomato", "tomatoes"], Icon: TomatoIcon },
  { keywords: ["avocado", "avocados"], Icon: AvocadoIcon },
];

function App() {
  // IMPORTANTE: shopping-cart usa useCart che gestisce il carrello condiviso tramite la chiave specifica "sharedCartItems"
  // Questo garantisce che il carrello mostri SOLO i prodotti aggiunti tramite i pulsanti "Aggiungi al carrello"
  // Ignora completamente qualsiasi altro dato in widgetState (es. da electronics-shop)
  const { cartItems, addToCart, removeFromCart } = useCart();
  const [selectedItem, setSelectedItem] = useState<CartItem | null>(null);
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

    // Usa removeFromCart per decrementare (che gestisce anche la rimozione quando quantity = 0)
    // Per incrementare, trova l'item e aggiungilo di nuovo (useCart incrementerà la quantità)
    if (delta < 0) {
      // Decrementa: usa removeFromCart che decrementa di 1
      for (let i = 0; i < Math.abs(delta); i++) {
        removeFromCart(id);
      }
    } else {
      // Incrementa: trova l'item e aggiungilo di nuovo (useCart incrementerà la quantità se esiste già)
      const item = cartItems.find((item) => item.id === id);
      if (item) {
        // useCart.addToCart incrementerà la quantità se l'item esiste già
        for (let i = 0; i < delta; i++) {
          addToCart({
            id: item.id,
            name: item.name,
            price: item.price,
            description: item.description,
            image: item.image,
          });
        }
      }
    }
  }

  // IMPORTANTE: Il carrello mostra SOLO gli items aggiunti tramite i pulsanti "Aggiungi al carrello" nei widget
  // NON sincronizziamo da widgetState perché potrebbe contenere prodotti da altri widget (es. electronics-shop)
  // Il carrello viene popolato direttamente tramite useWidgetState quando l'utente clicca sui pulsanti nei widget
  
  // Rimuoviamo completamente la sincronizzazione da widgetState per evitare prodotti indesiderati
  // Il carrello parte sempre vuoto e viene popolato solo tramite i pulsanti "Aggiungi al carrello"

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
          role="button"
          tabIndex={0}
          aria-label={`View details for ${item.name}`}
          onClick={() => setSelectedItem(item)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              setSelectedItem(item);
            }
          }}
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
              onClick={(event) => {
                event.stopPropagation();
                adjustQuantity(item.id, -1);
              }}
              className="h-8 w-8 rounded-full border border-black/30 text-lg font-semibold text-black/70 transition hover:bg-white"
              aria-label={`Decrease ${item.name}`}
            >
              -
            </button>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                adjustQuantity(item.id, 1);
              }}
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
      </div>
      <AnimatePresence>
        {selectedItem && (
          <ProductDetails
            place={{
              id: selectedItem.id,
              name: selectedItem.name,
              price: `$${selectedItem.price.toFixed(2)}`,
              description: selectedItem.description,
              thumbnail: selectedItem.image,
              stock: selectedItem.stock,
            }}
            onClose={() => setSelectedItem(null)}
            position="modal"
          />
        )}
      </AnimatePresence>
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
