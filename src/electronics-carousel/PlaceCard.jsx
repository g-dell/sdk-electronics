import React from "react";
import { Star, ShoppingCart } from "lucide-react";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import SafeImage from "../electronics/SafeImage";
import { useProxyBaseUrl } from "../use-proxy-base-url";
import { useCart } from "../use-cart";

function PlaceCard({ place, onCardClick }) {
  const proxyBaseUrl = useProxyBaseUrl();
  const { addToCart, isInCart } = useCart();
  
  if (!place) return null;

  // Usa useCallback per evitare che l'handler venga ricreato ad ogni render
  // e per assicurarsi che ogni PlaceCard abbia il proprio handler specifico
  const handleAddToCart = React.useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Verifica che place.id esista e sia valido
    if (!place.id) {
      console.error("[PlaceCard] Cannot add to cart: place.id is missing", place);
      return;
    }
    
    console.log("[PlaceCard] Adding product to cart:", {
      id: place.id,
      name: place.name,
      cardId: place.id, // Per verificare che sia il prodotto corretto
    });
    
    // Aggiungi SOLO questo prodotto specifico
    addToCart({
      id: place.id,
      name: place.name,
      price: place.price,
      description: place.description,
      thumbnail: place.thumbnail,
    });
  }, [place.id, place.name, place.price, place.description, place.thumbnail, addToCart]);

  const inCart = isInCart(place.id);

  return (
    <div 
      className="min-w-[220px] select-none max-w-[220px] w-[65vw] sm:w-[220px] self-stretch flex flex-col cursor-pointer"
      onClick={(e) => {
        // Non aprire i dettagli se si clicca sul pulsante "Aggiungi al carrello"
        if (e.target && e.target.closest && e.target.closest('button')) {
          return;
        }
        if (onCardClick) {
          onCardClick(place);
        }
      }}
    >
      <div className="w-full">
        <SafeImage
          src={place.thumbnail}
          alt={place.name}
          className="w-full aspect-square rounded-2xl object-cover ring ring-black/5 shadow-[0px_2px_6px_rgba(0,0,0,0.06)]"
          proxyBaseUrl={proxyBaseUrl}
        />
      </div>
      <div className="mt-3 flex flex-col flex-1">
        <div className="text-base font-medium truncate line-clamp-1">
          {place.name}
        </div>
        <div className="text-xs mt-1 text-black/60 flex items-center gap-1">
          <Star className="h-3 w-3" aria-hidden="true" />
          {place.rating?.toFixed ? place.rating.toFixed(1) : place.rating}
          {place.price ? <span>· {place.price}</span> : null}
          <span>· San Francisco</span>
        </div>
        {place.description ? (
          <div className="text-sm mt-2 text-black/80 flex-auto">
            {place.description}
          </div>
        ) : null}
        <div className="mt-5 flex gap-2">
          <Button 
            color="primary" 
            size="sm" 
            variant="solid"
            onClick={handleAddToCart}
            disabled={inCart}
            className="flex-1"
          >
            {inCart ? (
              <>
                <ShoppingCart className="h-4 w-4 mr-1" />
                Nel carrello
              </>
            ) : (
              <>
                <ShoppingCart className="h-4 w-4 mr-1" />
                Aggiungi al carrello
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

// Memoize component to prevent unnecessary re-renders
// Only re-render if place object reference changes
export default React.memo(PlaceCard, (prevProps, nextProps) => {
  // Custom comparison: only re-render if place ID changes
  return prevProps.place?.id === nextProps.place?.id;
});
