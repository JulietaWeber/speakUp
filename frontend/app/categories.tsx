import { useEffect, useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ConstructionBar from "../components/ConstructionBar";
import { obtenerCategorias } from "../services/api";

export default function Categories() {
  const [categories, setCategories] = useState<any[]>([]);

  useEffect(() => {
    const cargarCategorias = async () => {
      try {
        const token = await AsyncStorage.getItem("token");

        if (!token) {
          console.log("No hay token");
          return;
        }

        const data = await obtenerCategorias(token);
        setCategories(data);
      } catch (error) {
        console.error("Error cargando categorías:", error);
      }
    };

    cargarCategorias();
  }, []);

  // Hace una versión más suave del color de la categoría
  const getBackgroundColor = (color: string) => {
    if (!color) {
      return "#F2F6F7";
    }

    if (color.startsWith("#")) {
      const hex = color.replace("#", "");

      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);

      // Mezcla el color con blanco para lograr
      // un fondo más claro
      const softR = Math.round(r + (255 - r) * 0.78);
      const softG = Math.round(g + (255 - g) * 0.78);
      const softB = Math.round(b + (255 - b) * 0.78);

      return `rgb(${softR}, ${softG}, ${softB})`;
    }

    return "#F2F6F7";
  };

  return (
    <View style={styles.container}>

      {/* =========================
          BARRA SUPERIOR
      ========================= */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Speak Up</Text>

        <TouchableOpacity style={styles.settingsButton}>
          <Ionicons
            name="settings-outline"
            size={25}
            color="#FFFFFF"
          />
        </TouchableOpacity>
      </View>

      {/* =========================
          CONTENIDO
      ========================= */}
      <View style={styles.content}>

        {/* Barra para construir frase */}
        <ConstructionBar />

        {/* =========================
            TÍTULO CATEGORÍAS
        ========================= */}
        <Text style={styles.categoriesTitle}>
          Categorías
        </Text>

        {/* =========================
            CATEGORÍAS
        ========================= */}
        <View style={styles.categoriesContainer}>
          {categories.map((cat) => {
            const categoryColor = cat.color || "#356879";
            const backgroundColor =
              getBackgroundColor(categoryColor);

            return (
              <TouchableOpacity
                key={cat.id_categorias}
                activeOpacity={0.75}
                onPress={() =>
                  router.push({
                    pathname: "/category",
                    params: {
                      id: cat.id_categorias.toString(),
                      nombre: cat.nombre,
                      color: cat.color,
                    },
                  })
                }
                style={[
                  styles.categoryButton,
                  {
                    backgroundColor: backgroundColor,
                    borderColor: categoryColor,
                  },
                ]}
              >
                <Text style={styles.categoryText}>
                  {cat.nombre}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* =========================
            TEXTO INFERIOR
        ========================= */}
        <View style={styles.bottomTextContainer}>
          <Text style={styles.bottomText}>
            Elegí una categoría para que aparezcan
          </Text>

          <Text style={styles.bottomText}>
            los pictogramas
          </Text>
        </View>

      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  // =========================
  // CONTENEDOR
  // =========================
  container: {
    flex: 1,
    backgroundColor: "#EEF3F5",
  },

  // =========================
  // HEADER
  // =========================
  header: {
    height: 90,
    backgroundColor: "#356879",
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    paddingHorizontal: 15,
    paddingBottom: 8,
  },

  headerTitle: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "bold",
    paddingBottom: 8,
  },

  settingsButton: {
    justifyContent: "center",
    alignItems: "center",
    paddingBottom: 8,
  },

  // =========================
  // CONTENIDO
  // =========================
  content: {
    flex: 1,
    paddingHorizontal: 8,
    paddingTop: 10,
  },

  // =========================
  // TÍTULO CATEGORÍAS
  // =========================
  categoriesTitle: {
    fontSize: 13,
    color: "#356879",
    fontWeight: "600",
    marginBottom: 8,
    marginLeft: 2,
  },

  // =========================
  // CONTENEDOR CATEGORÍAS
  // =========================
  categoriesContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "flex-start",
    gap: 10,
  },

  // =========================
  // CUADRADOS DE CATEGORÍAS
  // =========================
  categoryButton: {
    width: "31%",
    height: 82,

    borderRadius: 14,

    // El borde toma el color de la categoría
    borderWidth: 2,

    justifyContent: "center",
    alignItems: "center",

    paddingHorizontal: 8,
    paddingVertical: 8,

    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.08,
    shadowRadius: 2,

    elevation: 2,
  },

  // Todas las letras en gris
  categoryText: {
    fontSize: 12,
    color: "#5F6B70",
    textAlign: "center",
    fontWeight: "600",
  },

  // =========================
  // TEXTO INFERIOR
  // =========================
  bottomTextContainer: {
    position: "absolute",
    bottom: 90,
    left: 0,
    right: 0,
    alignItems: "center",
  },

  bottomText: {
    fontSize: 10,
    color: "#356879",
    textAlign: "center",
    fontWeight: "500",
  },
});