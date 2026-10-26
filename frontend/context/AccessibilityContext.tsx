
import React, {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

type AccessibilityContextType = {
  tamanoGlobal: number;
  escala: number;
  cambiarTamanoGlobal: (valor: number) => Promise<void>;
};

const AccessibilityContext = createContext<
  AccessibilityContextType | undefined
>(undefined);

const ESCALAS = [0.85, 1, 1.2];

export function AccessibilityProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [tamanoGlobal, setTamanoGlobal] = useState(1);

  useEffect(() => {
    const cargarTamano = async () => {
      try {
        const guardado = await AsyncStorage.getItem("tamano_global");

        if (guardado !== null) {
          const valor = Number(guardado);

          if (Number.isInteger(valor) && valor >= 0 && valor <= 2) {
            setTamanoGlobal(valor);
          }
        }
      } catch (error) {
        console.error("Error cargando el tamaño global:", error);
      }
    };

    cargarTamano();
  }, []);

  const cambiarTamanoGlobal = async (valor: number) => {
    if (!Number.isInteger(valor) || valor < 0 || valor > 2) return;

    setTamanoGlobal(valor);

    try {
      await AsyncStorage.setItem("tamano_global", String(valor));
    } catch (error) {
      console.error("Error guardando el tamaño global:", error);
    }
  };

  return (
    <AccessibilityContext.Provider
      value={{
        tamanoGlobal,
        escala: ESCALAS[tamanoGlobal],
        cambiarTamanoGlobal,
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);

  if (!context) {
    throw new Error(
      "useAccessibility debe usarse dentro de AccessibilityProvider"
    );
  }

  return context;
}
