import React, { createContext, useContext, useState } from "react";
import { Pictograma } from "../services/api";

type ConstructionContextType = {
  palabras: Pictograma[];
  agregarPalabra: (palabra: Pictograma) => void;
  eliminarPalabra: (index: number) => void;
  borrarUltimaPalabra: () => void;
  limpiar: () => void;
};

const ConstructionContext = createContext<ConstructionContextType | undefined>(
  undefined
);

export function ConstructionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [palabras, setPalabras] = useState<Pictograma[]>([]);

  const agregarPalabra = (palabra: Pictograma) => {
    setPalabras((prev) => [...prev, palabra]);
  };

  const eliminarPalabra = (index: number) => {
    setPalabras((prev) => prev.filter((_, i) => i !== index));
  };

  const borrarUltimaPalabra = () => {
    setPalabras((prev) => prev.slice(0, -1));
  };

  const limpiar = () => {
    setPalabras([]);
  };

  return (
    <ConstructionContext.Provider
      value={{
        palabras,
        agregarPalabra,
        eliminarPalabra,
        borrarUltimaPalabra,
        limpiar,
      }}
    >
      {children}
    </ConstructionContext.Provider>
  );
}

export function useConstruction() {
  const context = useContext(ConstructionContext);

  if (!context) {
    throw new Error(
      "useConstruction debe usarse dentro de ConstructionProvider"
    );
  }

  return context;
}