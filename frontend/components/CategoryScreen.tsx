import { useCallback, useState } from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { router, useFocusEffect } from "expo-router";
import ConstructionBar from "./ConstructionBar";
import { useConstruction } from "../context/ConstructionContext";
import {
  obtenerPictogramasPorCategoria,
  Pictograma,
} from "../services/api";

type Props = {
  titulo: string;
  idCategoria: number;
  color: string;
};

export default function CategoryScreen({
  titulo,
  idCategoria,
  color,
}: Props) {
  const [pictogramas, setPictogramas] = useState<Pictograma[]>([]);
  const { agregarPalabra } = useConstruction();

  useFocusEffect(
    useCallback(() => {
      const cargarPictogramas = async () => {
        try {
          const data = await obtenerPictogramasPorCategoria(idCategoria);
          setPictogramas(data);
        } catch (error) {
          console.error("Error al cargar pictogramas:", error);
        }
      };

      cargarPictogramas();
    }, [idCategoria])
  );

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <ConstructionBar />

      <TouchableOpacity
        onPress={() =>
          router.push({
            pathname: "/agregar-pictograma",
            params: {
              idCategoria: idCategoria.toString(),
            },
          })
        }
        style={{
          backgroundColor: color,
          padding: 15,
          borderRadius: 15,
          marginTop: 15,
          marginBottom: 20,
          alignItems: "center",
        }}
      >
        <Text
          style={{
            fontSize: 18,
            fontWeight: "bold",
          }}
        >
          + Agregar pictograma
        </Text>
      </TouchableOpacity>

      <Text
        style={{
          fontSize: 28,
          marginBottom: 20,
          fontWeight: "bold",
        }}
      >
        {titulo}
      </Text>

      {pictogramas.length === 0 ? (
        <Text
          style={{
            fontSize: 18,
            textAlign: "center",
            marginTop: 20,
          }}
        >
          No hay pictogramas disponibles.
        </Text>
      ) : (
        pictogramas.map((pictograma) => (
          <TouchableOpacity
            key={pictograma.id_pictogramas}
            onPress={() => agregarPalabra(pictograma)}
            style={{
              backgroundColor: color,
              padding: 20,
              borderRadius: 15,
              marginBottom: 10,
            }}
          >
            <Text style={{ fontSize: 18 }}>
              {pictograma.nombre}
            </Text>
          </TouchableOpacity>
        ))
      )}
    </View>
  );
}