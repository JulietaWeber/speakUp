import { useEffect, useState } from "react";
import { View, Text, TouchableOpacity } from "react-native";
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

  useEffect(() => {
    const cargarPictogramas = async () => {
      try {
        const data = await obtenerPictogramasPorCategoria(idCategoria);
        setPictogramas(data);
      } catch (error) {
        console.error("Error al cargar pictogramas:", error);
      }
    };

    cargarPictogramas();
  }, [idCategoria]);

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <ConstructionBar />

      <Text
        style={{
          fontSize: 28,
          marginBottom: 20,
          fontWeight: "bold",
        }}
      >
        {titulo}
      </Text>

      {pictogramas.map((pictograma) => (
        <TouchableOpacity
          key={pictograma.id_pictogramas}
          onPress={() => agregarPalabra(pictograma.nombre)}
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
      ))}
    </View>
  );
}