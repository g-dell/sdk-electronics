import React from "react";
import { useOpenAiGlobal } from "./use-openai-global";
import type { CartItem } from "./types";

type CartWidgetState = {
  cartId?: string;
  items?: CartItem[];
  [key: string]: unknown;
};

// Chiave specifica per il carrello condiviso tra widget (diversa da electronics-shop)
const CART_STATE_KEY = "sharedCartItems";

const createDefaultCartState = (): CartWidgetState => ({
  items: [],
});

/**
 * Hook per gestire il carrello condiviso tra tutti i widget
 * Usa widgetState globale per persistenza tra widget
 */
export function useCart() {
  // IMPORTANTE: Il carrello parte SEMPRE vuoto e legge SOLO dalla chiave specifica "sharedCartItems"
  // Ignora completamente qualsiasi altro dato in widgetState (es. da electronics-shop)
  // Usa useOpenAiGlobal per reagire ai cambiamenti di widgetState
  const widgetStateGlobal = useOpenAiGlobal("widgetState") as Record<string, unknown> | null;
  
  // Estrai SOLO la chiave specifica, ignora tutto il resto
  const widgetStateFromGlobal = React.useMemo(() => {
    if (widgetStateGlobal && typeof widgetStateGlobal === "object") {
      const globalState = widgetStateGlobal as Record<string, unknown>;
      // Leggi SOLO dalla chiave specifica "sharedCartItems", ignora qualsiasi altra chiave
      if (globalState[CART_STATE_KEY] && typeof globalState[CART_STATE_KEY] === "object") {
        const globalCartState = globalState[CART_STATE_KEY] as CartWidgetState;
        if (Array.isArray(globalCartState.items)) {
          return globalCartState;
        }
      }
    }
    return null;
  }, [widgetStateGlobal]);

  const [cartState, setCartState] = React.useState<CartWidgetState>(() => {
    // Se c'è uno stato valido nella chiave specifica, usalo
    if (widgetStateFromGlobal && Array.isArray(widgetStateFromGlobal.items) && widgetStateFromGlobal.items.length > 0) {
      console.log("[useCart] Initializing from global state:", widgetStateFromGlobal.items.length, "items");
      return widgetStateFromGlobal;
    }
    // Altrimenti parte sempre vuoto
    console.log("[useCart] Starting with empty cart (no valid global state found)");
    return createDefaultCartState();
  });

  // Ref per tracciare se stiamo aggiornando lo stato localmente (per evitare loop)
  const isUpdatingLocalRef = React.useRef(false);

  // Sincronizza quando widgetState globale cambia (solo per la chiave specifica)
  React.useEffect(() => {
    // Non sincronizzare se stiamo aggiornando localmente
    if (isUpdatingLocalRef.current) {
      return;
    }

    if (widgetStateFromGlobal && Array.isArray(widgetStateFromGlobal.items)) {
      setCartState((prevState) => {
        const currentItems = Array.isArray(prevState?.items) ? prevState.items : [];
        const globalItems = widgetStateFromGlobal.items;
        // Solo sincronizza se è diverso
        if (JSON.stringify(currentItems) !== JSON.stringify(globalItems)) {
          console.log("[useCart] Syncing from global state:", globalItems.length, "items");
          return widgetStateFromGlobal;
        }
        return prevState;
      });
    }
  }, [widgetStateFromGlobal]);

  // Aggiorna widgetState globale quando cambia cartState
  React.useEffect(() => {
    if (typeof window !== "undefined" && window.openai?.setWidgetState) {
      const currentGlobalState = (window.openai.widgetState || {}) as Record<string, unknown>;
      // Evita loop infiniti: non aggiornare se lo stato globale è già uguale
      const currentGlobalCart = currentGlobalState[CART_STATE_KEY] as CartWidgetState | undefined;
      if (JSON.stringify(currentGlobalCart) !== JSON.stringify(cartState)) {
        isUpdatingLocalRef.current = true;
        console.log("[useCart] Updating global widgetState with cart:", cartState.items?.length || 0, "items");
        void window.openai.setWidgetState({
          ...currentGlobalState,
          [CART_STATE_KEY]: cartState,
        }).then(() => {
          // Reset il flag dopo che setWidgetState è completato
          // Usa setTimeout per dare tempo all'evento di propagarsi
          setTimeout(() => {
            isUpdatingLocalRef.current = false;
          }, 100);
        }).catch(() => {
          isUpdatingLocalRef.current = false;
        });
      }
    }
  }, [cartState]);

  const cartItems = Array.isArray(cartState?.items) ? cartState.items : [];
  
  // Verifica che non ci siano prodotti indesiderati
  React.useEffect(() => {
    if (cartItems.length > 0) {
      // Log per debug: verifica quali prodotti sono nel carrello
      console.log("[useCart] Current cart items:", cartItems.map(item => ({
        id: item.id,
        name: item.name,
        quantity: item.quantity
      })));
    }
  }, [cartItems.length]); // Solo quando cambia il numero di items
  
  // Prevenzione chiamate multiple rapide (debounce per ID)
  const lastAddTimeRef = React.useRef<Map<string, number>>(new Map());

  /**
   * Aggiunge un prodotto al carrello
   * Se il prodotto esiste già, incrementa la quantità
   * IMPORTANTE: Aggiunge SOLO il prodotto specificato, non altri prodotti
   */
  function addToCart(product: {
    id: string;
    name: string;
    price?: string | number;
    description?: string;
    image?: string;
    thumbnail?: string;
  }) {
    if (!product.id || !product.name) {
      console.warn("Cannot add product to cart: missing id or name", product);
      return;
    }

    // Prevenzione chiamate multiple rapide (debounce di 500ms per ID)
    const now = Date.now();
    const lastAddTime = lastAddTimeRef.current.get(product.id) || 0;
    const timeSinceLastAdd = now - lastAddTime;
    
    if (timeSinceLastAdd < 500) {
      console.warn(
        `[useCart] Ignoring rapid duplicate add request for product "${product.name}" (${product.id}). ` +
        `Last add was ${timeSinceLastAdd}ms ago.`
      );
      return;
    }
    
    lastAddTimeRef.current.set(product.id, now);

    // Log per debug
    console.log("[useCart] Adding product to cart:", {
      id: product.id,
      name: product.name,
      timestamp: new Date().toISOString(),
    });

    setCartState((prevState) => {
      const baseState: CartWidgetState = prevState ?? createDefaultCartState();
      const items = Array.isArray(baseState.items)
        ? baseState.items.map((item) => ({ ...item }))
        : [];

      // Cerca se il prodotto esiste già nel carrello (solo per ID specifico)
      const existingIndex = items.findIndex((item) => item.id === product.id);
      
      // Debug: verifica se ci sono altri prodotti con lo stesso ID (non dovrebbe succedere)
      const duplicateIds = items.filter((item) => item.id === product.id);
      if (duplicateIds.length > 1) {
        console.warn(
          `[useCart] WARNING: Found ${duplicateIds.length} items with the same ID "${product.id}" in cart!`,
          duplicateIds
        );
      }

      // Converti prezzo da stringa a numero se necessario
      let price = 0;
      if (typeof product.price === "number") {
        price = product.price;
      } else if (typeof product.price === "string") {
        // Estrai numero da stringhe come "$", "$$", "$$$" o numeri
        if (product.price === "$") {
          price = 25; // Default per $
        } else if (product.price === "$$") {
          price = 75; // Default per $$
        } else if (product.price === "$$$") {
          price = 150; // Default per $$$
        } else {
          price = parseFloat(product.price.replace(/[^0-9.]/g, "")) || 0;
        }
      }

      const imageUrl = product.image || product.thumbnail || "";

      if (existingIndex >= 0) {
        // Prodotto già presente: incrementa quantità SOLO per questo prodotto specifico
        const current = items[existingIndex];
        items[existingIndex] = {
          ...current,
          quantity: (current.quantity ?? 0) + 1,
        };
        console.log(
          `[useCart] Product "${product.name}" (${product.id}) already in cart, incrementing quantity to ${items[existingIndex].quantity}`
        );
      } else {
        // Nuovo prodotto: aggiungi SOLO questo prodotto al carrello
        const newItem: CartItem = {
          id: product.id,
          name: product.name,
          price: price,
          description: product.description || "",
          quantity: 1,
          image: imageUrl,
        };
        items.push(newItem);
        console.log(
          `[useCart] Added new product "${product.name}" (${product.id}) to cart. Total items: ${items.length}`
        );
      }

      // Verifica finale: assicurati che non ci siano duplicati
      const finalItemIds = items.map((item) => item.id);
      const uniqueIds = new Set(finalItemIds);
      if (finalItemIds.length !== uniqueIds.size) {
        console.error(
          "[useCart] ERROR: Duplicate IDs detected in cart!",
          finalItemIds.filter((id, index) => finalItemIds.indexOf(id) !== index)
        );
        // Rimuovi duplicati, mantieni solo il primo
        const seen = new Set<string>();
        const deduplicatedItems = items.filter((item) => {
          if (seen.has(item.id)) {
            return false;
          }
          seen.add(item.id);
          return true;
        });
        const newState = { ...baseState, items: deduplicatedItems };
        return newState;
      }

      const newState = { ...baseState, items };
      return newState;
    });
  }

  /**
   * Rimuove un prodotto dal carrello o ne decrementa la quantità
   */
  function removeFromCart(productId: string) {
    setCartState((prevState) => {
      const baseState: CartWidgetState = prevState ?? createDefaultCartState();
      const items = Array.isArray(baseState.items)
        ? baseState.items.map((item) => ({ ...item }))
        : [];

      const index = items.findIndex((item) => item.id === productId);
      if (index >= 0) {
        const current = items[index];
        const newQuantity = (current.quantity ?? 0) - 1;
        if (newQuantity <= 0) {
          items.splice(index, 1);
        } else {
          items[index] = { ...current, quantity: newQuantity };
        }
      }

      const newState = { ...baseState, items };
      return newState;
    });
  }

  /**
   * Verifica se un prodotto è già nel carrello
   */
  function isInCart(productId: string): boolean {
    return cartItems.some((item) => item.id === productId);
  }

  return {
    cartItems,
    addToCart,
    removeFromCart,
    isInCart,
  };
}
