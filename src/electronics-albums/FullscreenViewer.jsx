import React from "react";
import { ShoppingCart } from "lucide-react";
import { useMaxHeight } from "../use-max-height";
import FilmStrip from "./FilmStrip";
import SafeImage from "../electronics/SafeImage";
import { useProxyBaseUrl } from "../use-proxy-base-url";
import { useCart } from "../use-cart";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import QuantitySelector from "../utils/QuantitySelector";

export default function FullscreenViewer({ album }) {
  const maxHeight = useMaxHeight() ?? undefined;
  const [index, setIndex] = React.useState(0);
  const [quantity, setQuantity] = React.useState(1);
  const proxyBaseUrl = useProxyBaseUrl();
  const { addToCart, isInCart } = useCart();

  React.useEffect(() => {
    setIndex(0);
    setQuantity(1); // Reset quantità quando cambia l'album
  }, [album?.id]);

  const photo = album?.photos?.[index];
  // Stock disponibile (default: 10 se non specificato)
  // Nota: gli album potrebbero non avere stock, quindi usiamo un default
  const maxStock = photo?.stock ?? 10;
  const photoId = photo?.id || `album-${album.id}-photo-${index}`;

  const handleAddToCart = () => {
    if (photo) {
      addToCart({
        id: photoId,
        name: photo.title || album.title,
        description: album.title,
        thumbnail: photo.url,
        stock: maxStock,
        quantity: quantity,
      });
    }
  };

  return (
    <div
      className="relative w-full h-full bg-white"
      style={{
        maxHeight,
        height: maxHeight,
      }}
    >
      <div className="absolute inset-0 flex flex-row overflow-hidden">
        {/* Film strip */}
        <div className="hidden md:block absolute pointer-events-none z-10 left-0 top-0 bottom-0 w-40">
          <FilmStrip album={album} selectedIndex={index} onSelect={setIndex} proxyBaseUrl={proxyBaseUrl} />
        </div>
        {/* Main photo */}
        <div className="flex-1 min-w-0 px-40 py-10 relative flex items-center justify-center">
          <div className="relative w-full h-full">
            {photo ? (
              <>
                <SafeImage
                  src={photo.url}
                  alt={photo.title || album.title}
                  className="absolute inset-0 m-auto rounded-3xl shadow-sm border border-black/10 max-w-full max-h-full object-contain"
                  proxyBaseUrl={proxyBaseUrl}
                />
                {/* Add to cart button */}
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-2">
                  {!isInCart(photoId) && maxStock > 0 && (
                    <div className="flex items-center justify-center gap-2 bg-white/90 backdrop-blur-sm rounded-lg px-3 py-2">
                      <span className="text-sm text-black/70">Quantità:</span>
                      <QuantitySelector
                        quantity={quantity}
                        onQuantityChange={setQuantity}
                        maxQuantity={maxStock}
                        minQuantity={1}
                        size="sm"
                      />
                    </div>
                  )}
                  <Button
                    color="primary"
                    variant="solid"
                    size="md"
                    onClick={handleAddToCart}
                    disabled={isInCart(photoId) || maxStock === 0}
                  >
                    <ShoppingCart className="h-4 w-4 mr-2" />
                    {isInCart(photoId)
                      ? "Nel carrello"
                      : maxStock === 0
                      ? "Non disponibile"
                      : "Aggiungi al carrello"}
                  </Button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
