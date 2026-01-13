import { useWidgetState } from "./use-widget-state";
import type { CartItem } from "./types";

type CartWidgetState = {
  cartId?: string;
  items?: CartItem[];
  [key: string]: unknown;
};

const createDefaultCartState = (): CartWidgetState => ({
  items: [],
});

/**
 * Hook per gestire il carrello condiviso tra tutti i widget
 * Usa widgetState globale per persistenza tra widget
 */
export function useCart() {
  const [cartState, setCartState] = useWidgetState<CartWidgetState>(
    createDefaultCartState
  );

  const cartItems = Array.isArray(cartState?.items) ? cartState.items : [];

  /**
   * Aggiunge un prodotto al carrello
   * Se il prodotto esiste già, incrementa la quantità
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

    setCartState((prevState) => {
      const baseState: CartWidgetState = prevState ?? createDefaultCartState();
      const items = Array.isArray(baseState.items)
        ? baseState.items.map((item) => ({ ...item }))
        : [];

      // Cerca se il prodotto esiste già nel carrello
      const existingIndex = items.findIndex((item) => item.id === product.id);

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
        // Prodotto già presente: incrementa quantità
        const current = items[existingIndex];
        items[existingIndex] = {
          ...current,
          quantity: (current.quantity ?? 0) + 1,
        };
      } else {
        // Nuovo prodotto: aggiungi al carrello
        const newItem: CartItem = {
          id: product.id,
          name: product.name,
          price: price,
          description: product.description || "",
          quantity: 1,
          image: imageUrl,
        };
        items.push(newItem);
      }

      return { ...baseState, items };
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

      return { ...baseState, items };
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
